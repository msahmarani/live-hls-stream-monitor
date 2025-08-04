"""
Performance optimizations for HLS Stream Monitor
"""

import time
import functools
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

# Connection pooling and session management
class OptimizedHTTPSession:
    """Singleton HTTP session with connection pooling and retry logic"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Disable SSL verification for HLS streams
        self.session.verify = False
        
        # Set reasonable timeouts
        self.session.timeout = (5, 10)  # (connect, read)
        
    def get_session(self):
        return self.session

# Caching decorator
def timed_cache(seconds=300):
    """Cache results for specified seconds"""
    def decorator(func):
        cache = {}
        cache_times = {}
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            
            with lock:
                # Check if cached and not expired
                if key in cache and time.time() - cache_times[key] < seconds:
                    return cache[key]
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache[key] = result
                cache_times[key] = time.time()
                
                # Clean old entries (keep cache size manageable)
                if len(cache) > 100:
                    oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                    del cache[oldest_key]
                    del cache_times[oldest_key]
                
                return result
        
        return wrapper
    return decorator

# Concurrent segment checking
def check_segments_concurrent(segment_urls, max_workers=5):
    """Check multiple segments concurrently"""
    session = OptimizedHTTPSession().get_session()
    results = {}
    
    def check_single_segment(url):
        try:
            response = session.head(url, timeout=(2, 5))
            return url, response.status_code, response.elapsed.total_seconds()
        except Exception:
            return url, 0, 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(check_single_segment, url): url for url in segment_urls}
        
        for future in as_completed(future_to_url, timeout=10):
            try:
                url, status, response_time = future.result()
                results[url] = {
                    'status_code': status,
                    'response_time': response_time * 1000  # Convert to ms
                }
            except Exception:
                url = future_to_url[future]
                results[url] = {'status_code': 0, 'response_time': 0}
    
    return results

# Memory-efficient data structures
class CircularBuffer:
    """Memory-efficient circular buffer for metrics history"""
    def __init__(self, maxsize=50):
        self.maxsize = maxsize
        self.data = []
        self.index = 0
    
    def append(self, item):
        if len(self.data) < self.maxsize:
            self.data.append(item)
        else:
            self.data[self.index] = item
            self.index = (self.index + 1) % self.maxsize
    
    def get_recent(self, n=None):
        if n is None:
            return self.data[:]
        return self.data[-n:] if len(self.data) >= n else self.data[:]
    
    def __len__(self):
        return len(self.data)

# Optimized ffprobe execution
@timed_cache(seconds=600)  # Cache ffprobe results for 10 minutes
def optimized_ffprobe(segment_url):
    """Optimized ffprobe with caching and reduced command complexity"""
    import subprocess
    import json
    
    try:
        # Enhanced ffprobe command with all necessary fields
        cmd = [
            'ffprobe', 
            '-v', 'error',
            '-show_entries', 'stream=codec_name,codec_type,width,height,r_frame_rate,bit_rate,sample_rate,channels:format=duration,bit_rate,size',
            '-of', 'json',
            '-analyzeduration', '2000000',  # Analyze first 2 seconds for better accuracy
            '-probesize', '2000000',        # Increase probe size slightly
            segment_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"ffprobe failed with return code {result.returncode}: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"ffprobe timeout for {segment_url}")
        return None
    except Exception as e:
        print(f"ffprobe error: {e}")
        return None

# Batch processing for segments
def process_segments_batch(segments, base_url, batch_size=3):
    """Process segments in batches to avoid overwhelming the server"""
    results = []
    
    for i in range(0, len(segments), batch_size):
        batch = segments[i:i + batch_size]
        segment_urls = [base_url + seg.uri for seg in batch]
        
        # Check status concurrently
        status_results = check_segments_concurrent(segment_urls)
        
        for j, segment in enumerate(batch):
            segment_url = segment_urls[j]
            status_info = status_results.get(segment_url, {'status_code': 0, 'response_time': 0})
            
            results.append({
                'index': i + j + 1,
                'uri': segment.uri,
                'duration': segment.duration,
                'status_code': status_info['status_code'],
                'response_time': status_info['response_time'],
                'timestamp': time.time()
            })
        
        # Small delay between batches to be respectful
        if i + batch_size < len(segments):
            time.sleep(0.1)
    
    return results

# Performance monitoring
class PerformanceMonitor:
    """Monitor application performance metrics"""
    def __init__(self):
        self.metrics = {
            'request_times': CircularBuffer(100),
            'memory_usage': CircularBuffer(50),
            'error_count': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def record_request_time(self, duration):
        self.metrics['request_times'].append(duration)
    
    def record_memory_usage(self, usage_mb):
        self.metrics['memory_usage'].append(usage_mb)
    
    def increment_error(self):
        self.metrics['error_count'] += 1
    
    def record_cache_hit(self):
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        self.metrics['cache_misses'] += 1
    
    def get_stats(self):
        request_times = self.metrics['request_times'].get_recent()
        memory_usage = self.metrics['memory_usage'].get_recent()
        
        return {
            'avg_request_time': sum(request_times) / len(request_times) if request_times else 0,
            'max_request_time': max(request_times) if request_times else 0,
            'avg_memory_usage': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            'error_count': self.metrics['error_count'],
            'cache_hit_rate': (
                self.metrics['cache_hits'] / 
                max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
            ) * 100
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Smart adaptive refresh rates
class AdaptiveRefresh:
    """Automatically adjust refresh rates based on stream stability"""
    def __init__(self):
        self.success_history = CircularBuffer(20)
        self.base_interval = 10  # seconds
        self.min_interval = 5
        self.max_interval = 60
    
    def record_success_rate(self, rate):
        self.success_history.append(rate)
    
    def get_optimal_interval(self):
        recent_rates = self.success_history.get_recent(10)
        if not recent_rates:
            return self.base_interval
        
        avg_success = sum(recent_rates) / len(recent_rates)
        
        # Adjust interval based on stability
        if avg_success > 95:
            # Very stable, can refresh less frequently
            return min(self.max_interval, self.base_interval * 1.5)
        elif avg_success < 80:
            # Unstable, refresh more frequently
            return max(self.min_interval, self.base_interval * 0.7)
        else:
            return self.base_interval

# Resource cleanup utilities
def cleanup_resources():
    """Clean up resources and connections"""
    try:
        session = OptimizedHTTPSession().get_session()
        session.close()
    except Exception:
        pass

# Response compression
def compress_response_data(data):
    """Compress large response data"""
    import gzip
    import json
    
    if isinstance(data, dict):
        json_str = json.dumps(data, separators=(',', ':'))
        if len(json_str) > 1024:  # Only compress if > 1KB
            return gzip.compress(json_str.encode('utf-8'))
    
    return data
