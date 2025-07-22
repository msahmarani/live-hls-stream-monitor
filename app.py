from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
import m3u8
import requests
import urllib3
import subprocess
import json
import re
from urllib.parse import urljoin, urlparse
import os
import time
import threading
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global storage for live metrics
live_metrics = {
    'current_playlist': None,
    'segments': [],
    'stats': {
        'total_segments': 0,
        'failed_segments': 0,
        'avg_bitrate': 0,
        'avg_frame_rate': 0,
        'total_duration': 0
    },
    'history': [],
    'last_updated': None
}

# Add JSON filter for templates
@app.template_filter('tojson')
def to_json(value):
    return json.dumps(value)

def is_valid_url(url):
    """Check if the provided URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_ffprobe_info(segment_url):
    """Get video and audio info from segment using ffprobe"""
    try:
        # First check if ffprobe is available
        cmd_test = ['ffprobe', '-version']
        test_result = subprocess.run(cmd_test, capture_output=True, text=True, timeout=5)
        if test_result.returncode != 0:
            print("ffprobe not found or not working")
            return get_fallback_info()
            
        # Enhanced ffprobe command with video and audio information
        cmd = [
            'ffprobe', 
            '-v', 'error',  # Show only errors
            '-show_entries', 'stream=codec_name,codec_type,width,height,r_frame_rate,bit_rate,sample_rate,channels:format=duration,bit_rate,size',
            '-of', 'json',
            segment_url
        ]
        
        print(f"Running ffprobe on: {segment_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # Extract stream info
            streams = data.get('streams', [])
            video_stream = None
            audio_stream = None
            
            # Separate video and audio streams
            for stream in streams:
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                elif stream.get('codec_type') == 'audio':
                    audio_stream = stream
            
            # Process video stream
            if video_stream:
                # Calculate frame rate safely
                frame_rate = 0
                r_frame_rate = video_stream.get('r_frame_rate', '0/1')
                if r_frame_rate and '/' in r_frame_rate:
                    try:
                        num, den = r_frame_rate.split('/')
                        if int(den) > 0:
                            frame_rate = float(num) / float(den)
                    except:
                        frame_rate = 0
                
                # Get video bitrate
                video_bitrate = 0
                if video_stream.get('bit_rate'):
                    video_bitrate = int(video_stream['bit_rate'])
                
                video_info = {
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'frame_rate': round(frame_rate, 2),
                    'bitrate': video_bitrate
                }
            else:
                video_info = {
                    'codec': 'unknown',
                    'width': 0,
                    'height': 0,
                    'frame_rate': 0,
                    'bitrate': 0
                }
            
            # Process audio stream
            if audio_stream:
                audio_bitrate = 0
                if audio_stream.get('bit_rate'):
                    audio_bitrate = int(audio_stream['bit_rate'])
                
                audio_info = {
                    'codec': audio_stream.get('codec_name', 'unknown'),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0)),
                    'bitrate': audio_bitrate
                }
            else:
                audio_info = {
                    'codec': 'unknown',
                    'sample_rate': 0,
                    'channels': 0,
                    'bitrate': 0
                }
            
            # Get format info
            format_info = data.get('format', {})
            total_bitrate = 0
            if format_info.get('bit_rate'):
                total_bitrate = int(format_info['bit_rate'])
            else:
                # Estimate from file size and duration
                size = format_info.get('size')
                duration = format_info.get('duration')
                if size and duration:
                    try:
                        total_bitrate = int((int(size) * 8) / float(duration))
                    except:
                        total_bitrate = 0
            
            return {
                'video': video_info,
                'audio': audio_info,
                'duration': float(format_info.get('duration', 0)),
                'total_bitrate': total_bitrate,
                # Legacy fields for backward compatibility
                'codec': video_info['codec'],
                'width': video_info['width'],
                'height': video_info['height'],
                'frame_rate': video_info['frame_rate'],
                'bitrate': total_bitrate or video_info['bitrate']
            }
        else:
            print(f"ffprobe error (code {result.returncode}): {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"ffprobe timeout for {segment_url}")
    except Exception as e:
        print(f"Error getting ffprobe info for {segment_url}: {e}")
    
    return get_fallback_info()

def get_fallback_info():
    """Fallback video and audio info when ffprobe fails"""
    return {
        'video': {
            'codec': 'unknown',
            'width': 0,
            'height': 0,
            'frame_rate': 0,
            'bitrate': 0
        },
        'audio': {
            'codec': 'unknown',
            'sample_rate': 0,
            'channels': 0,
            'bitrate': 0
        },
        'duration': 0,
        'total_bitrate': 0,
        # Legacy fields for backward compatibility
        'codec': 'unknown',
        'width': 0,
        'height': 0,
        'frame_rate': 0,
        'bitrate': 0
    }

def check_segment_status(url):
    """Check HTTP status of a segment"""
    try:
        response = requests.head(url, timeout=10, verify=False)
        return response.status_code
    except:
        return 0

@app.route('/')
def index():
    # Check if ffprobe is available
    ffprobe_available = check_ffprobe_availability()
    return render_template('index.html', ffprobe_available=ffprobe_available, live_only=True)

@app.route('/monitor', methods=['POST'])
def start_monitor():
    """Start live monitoring for a playlist URL"""
    playlist_url = request.form.get('playlist_url', '').strip()
    
    if not playlist_url:
        return render_template('index.html', error="Please provide a playlist URL", live_only=True)
    
    if not is_valid_url(playlist_url):
        return render_template('index.html', error="Please provide a valid URL", live_only=True)
    
    # Redirect to live monitoring
    import urllib.parse
    encoded_url = urllib.parse.quote(playlist_url, safe='')
    return redirect(f'/live/{encoded_url}')

@app.route('/check-ffprobe')
def check_ffprobe():
    """Check if ffprobe is available and return status"""
    available = check_ffprobe_availability()
    return jsonify({'available': available})

def check_ffprobe_availability():
    """Check if ffprobe is installed and accessible"""
    try:
        result = subprocess.run(['ffprobe', '-version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

@app.route('/live/<path:playlist_url>')
def live_monitor(playlist_url):
    """Live monitoring page for a playlist"""
    print(f"Live monitor requested for URL: {playlist_url}")
    import urllib.parse
    decoded_url = urllib.parse.unquote(playlist_url)
    print(f"Decoded URL: {decoded_url}")
    return render_template('live.html', playlist_url=decoded_url)
def live_monitor(playlist_url):
    """Live monitoring page for a playlist"""
    print(f"Live monitor requested for URL: {playlist_url}")
    import urllib.parse
    decoded_url = urllib.parse.unquote(playlist_url)
    print(f"Decoded URL: {decoded_url}")
    return render_template('live.html', playlist_url=decoded_url)

@app.route('/api/live-metrics/<path:playlist_url>')
def get_live_metrics(playlist_url):
    """API endpoint for live metrics"""
    try:
        # Decode the URL
        import urllib.parse
        playlist_url = urllib.parse.unquote(playlist_url)
        print(f"Loading playlist: {playlist_url}")
        
        # Load and analyze the playlist with manual SSL handling
        session = requests.Session()
        session.verify = False
        
        print(f"Fetching playlist manually: {playlist_url}")
        response = session.get(playlist_url, timeout=10)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code} when fetching playlist")
        
        # Parse with m3u8
        playlist = m3u8.loads(response.text)
        print(f"Playlist loaded successfully. Is variant: {playlist.is_variant}")
        
        analysis_url = playlist_url
        master_video_info = None
        
        # Store original master playlist reference
        original_playlist = playlist
        master_bitrate = 0
        
        if playlist.is_variant:
            # For master playlists, get bitrate from playlist info and analyze first variant
            if playlist.playlists:
                # Debug: print all available variants with their bitrates
                print(f"Found {len(playlist.playlists)} variants:")
                for i, variant in enumerate(playlist.playlists):
                    bandwidth = variant.stream_info.bandwidth if variant.stream_info else 0
                    resolution = variant.stream_info.resolution if variant.stream_info else None
                    print(f"  Variant {i}: {bandwidth} bps, resolution: {resolution}")
                
                # Get bitrate from master playlist (first variant)
                first_variant = playlist.playlists[0]
                master_bitrate = first_variant.stream_info.bandwidth if first_variant.stream_info else 0
                print(f"Using first variant bitrate: {master_bitrate} bps")
                
                variant_url = urljoin(playlist_url, first_variant.uri)
                print(f"Loading variant for analysis: {variant_url}")
                
                # Load variant with manual SSL handling
                variant_response = session.get(variant_url, timeout=10)
                if variant_response.status_code == 200:
                    playlist = m3u8.loads(variant_response.text)
                else:
                    print(f"Failed to load variant: HTTP {variant_response.status_code}")
                    # Keep original master playlist
                    
                analysis_url = variant_url
        else:
            analysis_url = playlist_url
        
        # Analyze first segment for video details
        master_video_info = None
        if playlist.segments:
            base_url = analysis_url.rsplit('/', 1)[0] + '/'
            first_segment_url = urljoin(base_url, playlist.segments[0].uri)
            print(f"Analyzing first segment: {first_segment_url}")
            master_video_info = get_ffprobe_info(first_segment_url)
            
            # Use master playlist bitrate if available and ffprobe didn't find one
            if master_bitrate > 0:
                # If ffprobe didn't find bitrates, estimate them from master playlist
                if master_video_info['total_bitrate'] == 0:
                    master_video_info['total_bitrate'] = master_bitrate
                    master_video_info['bitrate'] = master_bitrate  # Legacy compatibility
                    
                    # Estimate video/audio split if individual streams don't have bitrates
                    if master_video_info['video']['bitrate'] == 0 and master_video_info['audio']['bitrate'] == 0:
                        # Typical audio bitrate is 128-256k, assume 256k max for audio
                        estimated_audio_bitrate = min(256000, master_bitrate * 0.1)  # 10% or 256k, whichever is smaller
                        estimated_video_bitrate = master_bitrate - estimated_audio_bitrate
                        
                        master_video_info['video']['bitrate'] = int(estimated_video_bitrate)
                        master_video_info['audio']['bitrate'] = int(estimated_audio_bitrate)
                        print(f"Estimated video bitrate: {estimated_video_bitrate}, audio bitrate: {estimated_audio_bitrate}")
                
                print(f"Using master playlist bitrate: {master_bitrate}")
            
            print(f"Final video info: {master_video_info}")
        
        # Fallback if all analysis failed
        if not master_video_info:
            master_video_info = get_fallback_info()
        
        print(f"Final video info: {master_video_info}")
        print(f"Total segments found: {len(playlist.segments)}")
        
        # Analyze recent segments (last 5 for faster response)
        base_url = analysis_url.rsplit('/', 1)[0] + '/'
        recent_segments = playlist.segments[-5:] if len(playlist.segments) > 5 else playlist.segments
        
        live_data = {
            'timestamp': datetime.now().isoformat(),
            'total_segments': len(playlist.segments),
            'recent_segments': [],
            'stats': {
                'avg_duration': 0,
                'success_rate': 0,
                'total_duration': sum(seg.duration for seg in playlist.segments),
                'avg_bitrate': 0,
                'total_bitrate_samples': 0
            }
        }
        
        success_count = 0
        total_duration = 0
        
        # Fast segment status checking only (no individual ffprobe calls)
        for i, segment in enumerate(recent_segments):
            segment_url = urljoin(base_url, segment.uri)
            print(f"Checking segment {i+1}/{len(recent_segments)} status: {segment.uri}")
            
            try:
                status_code = check_segment_status(segment_url)
                if status_code == 200:
                    success_count += 1
                print(f"Segment {i+1} status: {status_code}")
            except Exception as e:
                print(f"Error checking segment {i+1}: {e}")
                status_code = 0
            
            total_duration += segment.duration
            
            segment_info = {
                'index': len(playlist.segments) - len(recent_segments) + i + 1,
                'uri': segment.uri,
                'duration': segment.duration,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat()
            }
            live_data['recent_segments'].append(segment_info)
        
        live_data['stats']['avg_duration'] = total_duration / len(recent_segments) if recent_segments else 0
        live_data['stats']['avg_bitrate'] = master_video_info['bitrate'] if master_video_info['bitrate'] > 0 else 0
        live_data['stats']['total_bitrate_samples'] = 1 if master_video_info['bitrate'] > 0 else 0
        live_data['stats']['success_rate'] = (success_count / len(recent_segments)) * 100 if recent_segments else 0
        
        # Add master playlist video and audio info to response
        live_data['video_info'] = {
            'codec': master_video_info['video']['codec'],
            'width': master_video_info['video']['width'],
            'height': master_video_info['video']['height'],
            'resolution': f"{master_video_info['video']['width']}x{master_video_info['video']['height']}" if master_video_info['video']['width'] > 0 else "Unknown",
            'frame_rate': master_video_info['video']['frame_rate'],
            'video_bitrate': master_video_info['video']['bitrate'] if master_video_info['video']['bitrate'] > 0 else (master_bitrate if master_bitrate > 0 else 0),
            'duration': master_video_info['duration'],
            'source': 'segment_analysis'
        }
        
        live_data['audio_info'] = {
            'codec': master_video_info['audio']['codec'],
            'sample_rate': master_video_info['audio']['sample_rate'],
            'channels': master_video_info['audio']['channels'],
            'audio_bitrate': master_video_info['audio']['bitrate'],
            'channel_layout': f"{master_video_info['audio']['channels']} ch" if master_video_info['audio']['channels'] > 0 else "Unknown"
        }
        
        # Update stats to use total bitrate (video + audio)
        live_data['stats']['avg_bitrate'] = master_video_info['total_bitrate'] if master_video_info['total_bitrate'] > 0 else master_bitrate
        live_data['stats']['video_bitrate'] = master_video_info['video']['bitrate']
        live_data['stats']['audio_bitrate'] = master_video_info['audio']['bitrate']
        
        print(f"Video info: {live_data['video_info']}")
        print(f"Audio info: {live_data['audio_info']}")
        print(f"Master bitrate from playlist: {master_bitrate}")
        print(f"Video bitrate from ffprobe: {master_video_info['video']['bitrate']}")
        print(f"Total bitrate: {master_video_info['total_bitrate']}")
        
        print(f"Live data prepared successfully. Success rate: {live_data['stats']['success_rate']:.1f}%")
        return jsonify(live_data)
        
    except Exception as e:
        print(f"Error in live-metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/api/test-url/<path:playlist_url>')
def test_url(playlist_url):
    """Test if a playlist URL is accessible"""
    try:
        import urllib.parse
        playlist_url = urllib.parse.unquote(playlist_url)
        
        print(f"Testing URL: {playlist_url}")
        
        # Test basic connectivity
        response = requests.head(playlist_url, timeout=10)
        print(f"HTTP Response: {response.status_code}")
        
        if response.status_code == 200:
            # Try to load with m3u8
            playlist = m3u8.load(playlist_url, timeout=10)
            return jsonify({
                'success': True,
                'http_status': response.status_code,
                'is_variant': playlist.is_variant,
                'segments_count': len(playlist.segments),
                'variants_count': len(playlist.playlists) if playlist.is_variant else 0
            })
        else:
            return jsonify({
                'success': False,
                'http_status': response.status_code,
                'error': f'HTTP {response.status_code}'
            })
            
    except Exception as e:
        print(f"Error testing URL: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/segment-details/<path:segment_url>')
def get_segment_details(segment_url):
    """Get detailed info for a specific segment"""
    try:
        import urllib.parse
        segment_url = urllib.parse.unquote(segment_url)
        
        # Get detailed analysis
        ffprobe_info = get_ffprobe_info(segment_url)
        status_code = check_segment_status(segment_url)
        
        return jsonify({
            'url': segment_url,
            'status_code': status_code,
            'codec': ffprobe_info['codec'],
            'width': ffprobe_info['width'],
            'height': ffprobe_info['height'],
            'frame_rate': ffprobe_info['frame_rate'],
            'duration': ffprobe_info['duration'],
            'bitrate': ffprobe_info['bitrate'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/test-bitrate')
def test_bitrate():
    """Test bitrate extraction with manual SSL handling"""
    try:
        # Test URL
        playlist_url = "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8"
        
        # Manual loading with SSL disabled
        session = requests.Session()
        session.verify = False
        
        print(f"Fetching playlist manually: {playlist_url}")
        response = session.get(playlist_url, timeout=10)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse with m3u8
            playlist = m3u8.loads(response.text)
            print(f"Playlist parsed. Is variant: {playlist.is_variant}")
            
            if playlist.is_variant and playlist.playlists:
                variants_info = []
                total_bitrate = 0
                for i, variant in enumerate(playlist.playlists):
                    bandwidth = variant.stream_info.bandwidth if variant.stream_info else 0
                    resolution = variant.stream_info.resolution if variant.stream_info else None
                    variants_info.append({
                        'index': i,
                        'bandwidth': bandwidth,
                        'resolution': resolution
                    })
                    total_bitrate += bandwidth
                
                avg_bitrate = total_bitrate / len(playlist.playlists) if playlist.playlists else 0
                
                return jsonify({
                    'success': True,
                    'is_variant': True,
                    'variants': variants_info,
                    'avg_bitrate': avg_bitrate,
                    'total_variants': len(playlist.playlists)
                })
            else:
                return jsonify({
                    'success': True,
                    'is_variant': False,
                    'segments_count': len(playlist.segments) if hasattr(playlist, 'segments') else 0
                })
        else:
            return jsonify({
                'success': False,
                'error': f'HTTP {response.status_code}'
            })
            
    except Exception as e:
        print(f"Test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/system-metrics')
def get_system_metrics():
    """Get system metrics for Cockpit.js dashboard"""
    try:
        import psutil
        import platform
        
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get network information
        network = psutil.net_io_counters()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'hostname': platform.node()
            },
            'cpu': {
                'usage_percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        }
        
        return jsonify(metrics)
        
    except ImportError:
        # psutil not available, return simulated metrics
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'system': {
                'platform': 'Unknown',
                'architecture': 'x64',
                'hostname': 'hls-analyzer'
            },
            'cpu': {
                'usage_percent': 25.0,
                'count': 4
            },
            'memory': {
                'total': 8589934592,  # 8GB
                'available': 4294967296,  # 4GB
                'used': 4294967296,  # 4GB
                'percent': 50.0
            },
            'disk': {
                'total': 1099511627776,  # 1TB
                'used': 549755813888,   # 512GB
                'free': 549755813888,   # 512GB
                'percent': 50.0
            },
            'network': {
                'bytes_sent': 1024000,
                'bytes_recv': 2048000,
                'packets_sent': 1000,
                'packets_recv': 2000
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/health-check')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ffprobe_available': check_ffprobe_availability()
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8181, debug=True)
