# HLS Stream Monitor - Optimized Configuration

class OptimizedConfig:
    """Configuration for optimized HLS Stream Monitor"""
    
    # Flask Configuration
    DEBUG = True
    TESTING = False
    
    # Performance Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    SEND_FILE_MAX_AGE_DEFAULT = 3600  # Cache static files for 1 hour
    
    # HLS Processing Settings
    DEFAULT_TIMEOUT = 10  # seconds
    MAX_CONCURRENT_SEGMENTS = 5  # Concurrent segment checks
    SEGMENT_BATCH_SIZE = 3  # Segments to process in each batch
    CACHE_TTL = 300  # Cache TTL in seconds (5 minutes)
    
    # Memory Management
    MAX_SEGMENTS_HISTORY = 100  # Maximum segments to keep in memory
    MAX_METRICS_HISTORY = 50   # Maximum metrics entries to keep
    CLEANUP_INTERVAL = 300     # Cleanup interval in seconds (5 minutes)
    
    # Adaptive Refresh Settings
    MIN_REFRESH_INTERVAL = 5   # Minimum refresh interval in seconds
    MAX_REFRESH_INTERVAL = 60  # Maximum refresh interval in seconds
    DEFAULT_REFRESH_INTERVAL = 10  # Default refresh interval
    
    # Performance Monitoring
    ENABLE_PERFORMANCE_MONITORING = True
    PERFORMANCE_LOG_INTERVAL = 60  # Log performance stats every 60 seconds
    
    # Connection Pooling
    CONNECTION_POOL_SIZE = 10
    CONNECTION_POOL_MAXSIZE = 20
    CONNECTION_RETRY_TOTAL = 3
    CONNECTION_RETRY_BACKOFF = 0.3
    
    # SSL/TLS Settings
    VERIFY_SSL = False  # Disabled for HLS streams with self-signed certs
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # API Rate Limiting
    API_RATE_LIMIT_PER_MINUTE = 120  # Max API calls per minute
    
    # Chart/UI Settings
    MAX_CHART_DATA_POINTS = 20  # Maximum data points in charts
    CHART_UPDATE_ANIMATION = False  # Disable animations for performance
    
    # System Metrics
    ENABLE_SYSTEM_METRICS = True
    SYSTEM_METRICS_INTERVAL = 30  # Update system metrics every 30 seconds
    
    @classmethod
    def get_config_dict(cls):
        """Get configuration as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }

# Export the configuration
config = OptimizedConfig()
