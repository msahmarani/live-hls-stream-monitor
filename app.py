"""
Live HLS Stream Monitor

A privacy-first, local-only HLS stream monitoring and analysis tool.

Privacy Notice:
- All processing is performed locally on your machine
- No data is transmitted to external servers (except HLS streams you analyze)
- Stream URLs and analysis results are not stored persistently
- See PRIVACY.md for complete privacy policy

Security Notice:
- Runs on localhost (127.0.0.1) by default for security
- SSL certificate verification disabled for HTTPS streams
- See SECURITY.md for security considerations
"""

from flask import Flask, render_template, request, jsonify, redirect, g
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
import psutil
import logging

# Import optimizations
from optimizations import (
    OptimizedHTTPSession, 
    timed_cache, 
    check_segments_concurrent,
    CircularBuffer,
    optimized_ffprobe,
    process_segments_batch,
    performance_monitor,
    AdaptiveRefresh,
    cleanup_resources
)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging for better performance monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global storage for live metrics (optimized)
live_metrics = {
    'current_playlist': None,
    'segments': CircularBuffer(maxsize=100),  # Use circular buffer to limit memory
    'stats': {
        'total_segments': 0,
        'failed_segments': 0,
        'avg_bitrate': 0,
        'avg_frame_rate': 0,
        'total_duration': 0
    },
    'history': CircularBuffer(maxsize=50),  # Limit history size
    'last_updated': None,
    'adaptive_refresh': AdaptiveRefresh()
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

@timed_cache(seconds=300)  # Cache for 5 minutes
def get_ffprobe_info(segment_url):
    """Get video and audio info from segment using ffprobe (optimized)"""
    start_time = time.time()
    
    try:
        # Use optimized ffprobe function
        data = optimized_ffprobe(segment_url)
        
        if data:
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
            
            result = {
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
            
            performance_monitor.record_cache_hit()
            return result
        else:
            logging.warning(f"ffprobe returned no data for {segment_url}")
            
    except Exception as e:
        logging.error(f"Error getting ffprobe info: {e}")
    finally:
        duration = time.time() - start_time
        performance_monitor.record_request_time(duration)
    
    performance_monitor.record_cache_miss()
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
    """Check HTTP status of a segment (optimized)"""
    try:
        session = OptimizedHTTPSession().get_session()
        response = session.head(url, timeout=(2, 5))  # Faster timeout
        return response.status_code
    except Exception:
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
    print(f"Live monitor requested")
    import urllib.parse
    decoded_url = urllib.parse.unquote(playlist_url)
    print(f"Starting live monitoring session")
    return render_template('live.html', playlist_url=decoded_url)
def live_monitor(playlist_url):
    """Live monitoring page for a playlist"""
    print(f"Live monitor requested")
    import urllib.parse
    decoded_url = urllib.parse.unquote(playlist_url)
    print(f"Starting live monitoring session")
    return render_template('live.html', playlist_url=decoded_url)

@app.route('/api/live-metrics/<path:playlist_url>')
def get_live_metrics(playlist_url):
    """API endpoint for live metrics (optimized)"""
    start_time = time.time()
    
    try:
        # Decode the URL
        import urllib.parse
        playlist_url = urllib.parse.unquote(playlist_url)
        logging.info(f"Processing live metrics for: {playlist_url}")
        
        # Use optimized session
        session = OptimizedHTTPSession().get_session()
        
        logging.info("Fetching playlist...")
        response = session.get(playlist_url, timeout=(5, 10))
        logging.info(f"HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code} when fetching playlist")
        
        # Parse with m3u8
        playlist = m3u8.loads(response.text)
        logging.info(f"Playlist loaded successfully. Is variant: {playlist.is_variant}")
        
        analysis_url = playlist_url
        master_video_info = None
        
        # Store original master playlist reference
        original_playlist = playlist
        master_bitrate = 0
        
        if playlist.is_variant:
            # For master playlists, get bitrate from playlist info and analyze first variant
            if playlist.playlists:
                # Get bitrate from master playlist (first variant)
                first_variant = playlist.playlists[0]
                master_bitrate = first_variant.stream_info.bandwidth if first_variant.stream_info else 0
                logging.info(f"Using first variant bitrate: {master_bitrate} bps")
                
                variant_url = urljoin(playlist_url, first_variant.uri)
                
                # Load variant with optimized session
                variant_response = session.get(variant_url, timeout=(5, 10))
                if variant_response.status_code == 200:
                    playlist = m3u8.loads(variant_response.text)
                    analysis_url = variant_url
                else:
                    logging.warning(f"Failed to load variant: HTTP {variant_response.status_code}")
        
        # Analyze first segment for video details (cached)
        master_video_info = None
        if playlist.segments:
            base_url = analysis_url.rsplit('/', 1)[0] + '/'
            first_segment_url = urljoin(base_url, playlist.segments[0].uri)
            logging.info("Analyzing first segment...")
            master_video_info = get_ffprobe_info(first_segment_url)
            
            # Use master playlist bitrate if available and ffprobe didn't find one
            if master_bitrate > 0:
                if master_video_info['total_bitrate'] == 0:
                    master_video_info['total_bitrate'] = master_bitrate
                    master_video_info['bitrate'] = master_bitrate
                
                # Estimate video bitrate if not found by ffprobe
                if master_video_info['video']['bitrate'] == 0 and master_bitrate > 0:
                    audio_bitrate = master_video_info['audio']['bitrate']
                    if audio_bitrate > 0:
                        # Use actual audio bitrate from ffprobe
                        estimated_video_bitrate = master_bitrate - audio_bitrate
                    else:
                        # Estimate both video and audio
                        estimated_audio_bitrate = min(256000, master_bitrate * 0.1)
                        estimated_video_bitrate = master_bitrate - estimated_audio_bitrate
                        master_video_info['audio']['bitrate'] = int(estimated_audio_bitrate)
                    
                    master_video_info['video']['bitrate'] = max(0, int(estimated_video_bitrate))
                    logging.info(f"Estimated video bitrate: {master_video_info['video']['bitrate']}, audio bitrate: {master_video_info['audio']['bitrate']}")
        
        # Fallback if analysis failed
        if not master_video_info:
            master_video_info = get_fallback_info()
        
        # Analyze recent segments with batching (optimized)
        base_url = analysis_url.rsplit('/', 1)[0] + '/'
        recent_segments = playlist.segments[-5:] if len(playlist.segments) > 5 else playlist.segments
        
        # Use optimized batch processing
        segment_results = process_segments_batch(recent_segments, base_url, batch_size=3)
        
        # Calculate statistics
        success_count = sum(1 for seg in segment_results if seg['status_code'] == 200)
        total_duration = sum(seg['duration'] for seg in segment_results)
        success_rate = (success_count / len(segment_results)) * 100 if segment_results else 0
        
        # Record success rate for adaptive refresh
        live_metrics['adaptive_refresh'].record_success_rate(success_rate)
        
        live_data = {
            'timestamp': datetime.now().isoformat(),
            'total_segments': len(playlist.segments),
            'recent_segments': segment_results,
            'stats': {
                'avg_duration': total_duration / len(segment_results) if segment_results else 0,
                'success_rate': success_rate,
                'total_duration': sum(seg.duration for seg in playlist.segments),
                'avg_bitrate': master_video_info['total_bitrate'] if master_video_info['total_bitrate'] > 0 else master_bitrate,
                'video_bitrate': master_video_info['video']['bitrate'],
                'audio_bitrate': master_video_info['audio']['bitrate']
            },
            'video_info': {
                'codec': master_video_info['video']['codec'],
                'width': master_video_info['video']['width'],
                'height': master_video_info['video']['height'],
                'resolution': f"{master_video_info['video']['width']}x{master_video_info['video']['height']}" if master_video_info['video']['width'] > 0 else "Unknown",
                'frame_rate': master_video_info['video']['frame_rate'],
                'video_bitrate': master_video_info['video']['bitrate'],
                'duration': master_video_info['duration'],
                'source': 'segment_analysis'
            },
            'audio_info': {
                'codec': master_video_info['audio']['codec'],
                'sample_rate': master_video_info['audio']['sample_rate'],
                'channels': master_video_info['audio']['channels'],
                'audio_bitrate': master_video_info['audio']['bitrate'],
                'channel_layout': f"{master_video_info['audio']['channels']} ch" if master_video_info['audio']['channels'] > 0 else "Unknown"
            },
            'performance': {
                'recommended_refresh_interval': live_metrics['adaptive_refresh'].get_optimal_interval()
            }
        }
        
        # Store in circular buffer
        live_metrics['segments'].append(live_data)
        live_metrics['last_updated'] = datetime.now()
        
        processing_time = time.time() - start_time
        performance_monitor.record_request_time(processing_time)
        
        logging.info(f"Live metrics processed in {processing_time:.2f}s. Success rate: {success_rate:.1f}%")
        return jsonify(live_data)
        
    except Exception as e:
        performance_monitor.increment_error()
        logging.error(f"Error in live-metrics: {str(e)}")
        processing_time = time.time() - start_time
        performance_monitor.record_request_time(processing_time)
        return jsonify({'error': str(e), 'processing_time': processing_time})

@app.route('/api/test-url/<path:playlist_url>')
def test_url(playlist_url):
    """Test if a playlist URL is accessible"""
    try:
        import urllib.parse
        playlist_url = urllib.parse.unquote(playlist_url)
        
        print(f"Testing URL connectivity...")
        
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

@app.route('/api/health-check')
def health_check():
    """Health check endpoint"""
    try:
        # Record memory usage
        memory_usage = psutil.virtual_memory().percent
        performance_monitor.record_memory_usage(memory_usage)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'memory_usage': f"{memory_usage:.1f}%",
            'performance': performance_monitor.get_stats()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/system-metrics')
def get_system_metrics():
    """Get system performance metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network info (if available)
        network_info = {}
        try:
            network_stats = psutil.net_io_counters()
            network_info = {
                'bytes_sent': network_stats.bytes_sent,
                'bytes_recv': network_stats.bytes_recv,
                'packets_sent': network_stats.packets_sent,
                'packets_recv': network_stats.packets_recv
            }
        except:
            pass
        
        return jsonify({
            'cpu': {
                'usage_percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            },
            'network': network_info,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/performance-stats')
def get_performance_stats():
    """Get application performance statistics"""
    stats = performance_monitor.get_stats()
    stats['adaptive_refresh_interval'] = live_metrics['adaptive_refresh'].get_optimal_interval()
    stats['cache_size'] = len(live_metrics['segments'])
    stats['last_updated'] = live_metrics['last_updated'].isoformat() if live_metrics['last_updated'] else None
    
    return jsonify(stats)

# Cleanup function
@app.teardown_appcontext
def cleanup(error):
    """Cleanup resources after each request"""
    if error:
        performance_monitor.increment_error()

# Register cleanup on app shutdown
import atexit
atexit.register(cleanup_resources)

if __name__ == '__main__':
    # Security: Binds to localhost only by default
    # For production deployment, set debug=False and configure proper security
    app.run(host='127.0.0.1', port=8181, debug=True)
