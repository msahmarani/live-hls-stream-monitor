// Optimized JavaScript utilities for better performance

class PerformanceOptimizer {
    constructor() {
        this.requestQueue = [];
        this.isProcessing = false;
        this.rateLimitDelay = 100; // ms between requests
        this.adaptiveInterval = 10000; // Default 10 seconds
        this.performanceMetrics = {
            requestTimes: [],
            errorCount: 0,
            cacheHits: 0
        };
    }

    // Throttled fetch with automatic retry
    async throttledFetch(url, options = {}) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({ url, options, resolve, reject });
            this.processQueue();
        });
    }

    async processQueue() {
        if (this.isProcessing || this.requestQueue.length === 0) return;
        
        this.isProcessing = true;
        
        while (this.requestQueue.length > 0) {
            const { url, options, resolve, reject } = this.requestQueue.shift();
            
            try {
                const startTime = performance.now();
                const response = await this.fetchWithRetry(url, options);
                const endTime = performance.now();
                
                this.recordRequestTime(endTime - startTime);
                resolve(response);
            } catch (error) {
                this.performanceMetrics.errorCount++;
                reject(error);
            }
            
            // Rate limiting
            if (this.requestQueue.length > 0) {
                await this.sleep(this.rateLimitDelay);
            }
        }
        
        this.isProcessing = false;
    }

    async fetchWithRetry(url, options = {}, maxRetries = 3) {
        let lastError;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
                
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return response;
            } catch (error) {
                lastError = error;
                if (i < maxRetries - 1) {
                    await this.sleep(1000 * Math.pow(2, i)); // Exponential backoff
                }
            }
        }
        
        throw lastError;
    }

    recordRequestTime(duration) {
        this.performanceMetrics.requestTimes.push(duration);
        if (this.performanceMetrics.requestTimes.length > 50) {
            this.performanceMetrics.requestTimes.shift();
        }
    }

    getAverageRequestTime() {
        const times = this.performanceMetrics.requestTimes;
        return times.length > 0 ? times.reduce((a, b) => a + b, 0) / times.length : 0;
    }

    updateAdaptiveInterval(successRate, recommendedInterval) {
        if (recommendedInterval) {
            this.adaptiveInterval = recommendedInterval * 1000; // Convert to ms
        } else {
            // Fallback adaptive logic
            if (successRate > 95) {
                this.adaptiveInterval = Math.min(30000, this.adaptiveInterval * 1.2);
            } else if (successRate < 80) {
                this.adaptiveInterval = Math.max(5000, this.adaptiveInterval * 0.8);
            }
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Enhanced Chart Management
class OptimizedChartManager {
    constructor() {
        this.charts = new Map();
        this.dataBuffers = new Map();
        this.maxDataPoints = 20;
        this.updateQueue = [];
        this.isUpdating = false;
    }

    registerChart(id, chart) {
        this.charts.set(id, chart);
        this.dataBuffers.set(id, []);
    }

    queueUpdate(chartId, data) {
        this.updateQueue.push({ chartId, data });
        this.processUpdates();
    }

    async processUpdates() {
        if (this.isUpdating) return;
        this.isUpdating = true;

        const updates = [...this.updateQueue];
        this.updateQueue = [];

        // Batch updates to minimize reflows
        requestAnimationFrame(() => {
            updates.forEach(({ chartId, data }) => {
                this.updateChart(chartId, data);
            });
            this.isUpdating = false;
        });
    }

    updateChart(chartId, data) {
        const chart = this.charts.get(chartId);
        const buffer = this.dataBuffers.get(chartId);
        
        if (!chart || !buffer) return;

        // Add new data
        buffer.push(data);
        
        // Limit buffer size
        if (buffer.length > this.maxDataPoints) {
            buffer.shift();
        }

        // Update chart data
        chart.data.labels = buffer.map((_, index) => index);
        chart.data.datasets[0].data = buffer;
        
        // Use 'none' animation for better performance
        chart.update('none');
    }

    clearChart(chartId) {
        const buffer = this.dataBuffers.get(chartId);
        if (buffer) {
            buffer.length = 0;
        }
    }
}

// Memory Management for Large Datasets
class MemoryManager {
    constructor() {
        this.caches = new Map();
        this.maxCacheSize = 100;
        this.cleanupInterval = 300000; // 5 minutes
        this.startCleanupTimer();
    }

    set(key, value, ttl = 300000) { // 5 minutes default TTL
        const cache = this.caches.get('default') || new Map();
        cache.set(key, {
            value,
            timestamp: Date.now(),
            ttl
        });
        this.caches.set('default', cache);
        
        // Cleanup if cache is too large
        if (cache.size > this.maxCacheSize) {
            this.cleanup('default');
        }
    }

    get(key) {
        const cache = this.caches.get('default');
        if (!cache) return null;
        
        const item = cache.get(key);
        if (!item) return null;
        
        // Check if expired
        if (Date.now() - item.timestamp > item.ttl) {
            cache.delete(key);
            return null;
        }
        
        return item.value;
    }

    cleanup(cacheName = 'default') {
        const cache = this.caches.get(cacheName);
        if (!cache) return;
        
        const now = Date.now();
        const toDelete = [];
        
        cache.forEach((item, key) => {
            if (now - item.timestamp > item.ttl) {
                toDelete.push(key);
            }
        });
        
        toDelete.forEach(key => cache.delete(key));
    }

    startCleanupTimer() {
        setInterval(() => {
            this.caches.forEach((_, cacheName) => {
                this.cleanup(cacheName);
            });
        }, this.cleanupInterval);
    }
}

// Optimized DOM updates
class DOMOptimizer {
    constructor() {
        this.updateQueue = [];
        this.isProcessing = false;
    }

    queueUpdate(elementId, content, type = 'text') {
        this.updateQueue.push({ elementId, content, type });
        this.processUpdates();
    }

    async processUpdates() {
        if (this.isProcessing || this.updateQueue.length === 0) return;
        
        this.isProcessing = true;
        
        requestAnimationFrame(() => {
            const updates = [...this.updateQueue];
            this.updateQueue = [];
            
            updates.forEach(({ elementId, content, type }) => {
                const element = document.getElementById(elementId);
                if (element) {
                    switch (type) {
                        case 'text':
                            element.textContent = content;
                            break;
                        case 'html':
                            element.innerHTML = content;
                            break;
                        case 'class':
                            element.className = content;
                            break;
                        case 'style':
                            Object.assign(element.style, content);
                            break;
                    }
                }
            });
            
            this.isProcessing = false;
        });
    }
}

// Utility functions
const utils = {
    formatBitrate: (bps) => {
        if (bps === 0) return '0 bps';
        
        const units = ['bps', 'Kbps', 'Mbps', 'Gbps'];
        let size = bps;
        let unitIndex = 0;
        
        while (size >= 1000 && unitIndex < units.length - 1) {
            size /= 1000;
            unitIndex++;
        }
        
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    },

    formatDuration: (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },

    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    throttle: (func, limit) => {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Global instances
window.performanceOptimizer = new PerformanceOptimizer();
window.chartManager = new OptimizedChartManager();
window.memoryManager = new MemoryManager();
window.domOptimizer = new DOMOptimizer();
window.utils = utils;
