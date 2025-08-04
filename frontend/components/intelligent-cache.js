/**
 * KBI Labs Intelligent Cache System
 * 
 * Advanced caching strategy for optimal performance with government APIs
 * Includes multi-layer caching, intelligent prefetching, and cache warming
 */

class IntelligentCache {
    constructor() {
        this.memoryCache = new Map();
        this.persistentCache = this.initializePersistentCache();
        this.cacheMetrics = new Map();
        this.prefetchQueue = [];
        this.cacheWorker = null;
        
        // Cache configuration
        this.config = {
            // Memory cache limits
            maxMemoryEntries: 100,
            maxMemorySize: 50 * 1024 * 1024, // 50MB
            
            // TTL settings (milliseconds)
            ttl: {
                critical: 2 * 60 * 1000,      // 2 minutes - health, opportunities
                standard: 10 * 60 * 1000,     // 10 minutes - dashboard data
                stable: 30 * 60 * 1000,       // 30 minutes - agency profiles
                static: 60 * 60 * 1000        // 1 hour - regulatory data
            },
            
            // Prefetch settings
            prefetchThreshold: 0.8, // Prefetch when 80% of TTL elapsed
            prefetchConcurrency: 3,  // Max 3 concurrent prefetch requests
            
            // Storage quotas
            persistentQuota: 100 * 1024 * 1024 // 100MB for IndexedDB
        };

        this.initialize();
    }

    /**
     * Initialize the intelligent cache system
     */
    async initialize() {
        console.log('🧠 Initializing Intelligent Cache System...');
        
        try {
            // Setup cache worker for background operations
            await this.setupCacheWorker();
            
            // Initialize persistent storage
            await this.initializePersistentStorage();
            
            // Setup cache warming
            this.setupCacheWarming();
            
            // Setup cleanup routines
            this.setupCacheCleanup();
            
            // Setup performance monitoring
            this.setupCacheMetrics();
            
            console.log('✅ Intelligent Cache System initialized');
            
        } catch (error) {
            console.error('❌ Cache initialization failed:', error);
            // Fallback to memory-only caching
            this.config.persistentCache = false;
        }
    }

    /**
     * Smart cache retrieval with multiple fallback layers
     */
    async get(key, options = {}) {
        const startTime = performance.now();
        let result = null;
        let source = null;

        try {
            // Layer 1: Memory cache (fastest)
            result = this.getFromMemory(key);
            if (result && !this.isExpired(result)) {
                source = 'memory';
                this.recordCacheHit(key, 'memory', performance.now() - startTime);
                return this.processResult(result.data, options);
            }

            // Layer 2: Persistent cache (fast)
            if (this.persistentCache) {
                result = await this.getFromPersistent(key);
                if (result && !this.isExpired(result)) {
                    source = 'persistent';
                    // Promote to memory cache
                    this.setInMemory(key, result.data, result.ttl, result.priority);
                    this.recordCacheHit(key, 'persistent', performance.now() - startTime);
                    return this.processResult(result.data, options);
                }
            }

            // Layer 3: Background prefetch check
            result = await this.checkBackgroundPrefetch(key);
            if (result) {
                source = 'prefetch';
                this.recordCacheHit(key, 'prefetch', performance.now() - startTime);
                return this.processResult(result, options);
            }

            // Cache miss - record and return null
            this.recordCacheMiss(key, performance.now() - startTime);
            return null;

        } catch (error) {
            console.error(`❌ Cache retrieval error for ${key}:`, error);
            this.recordCacheError(key, error);
            return null;
        }
    }

    /**
     * Smart cache storage with intelligent prioritization
     */
    async set(key, data, options = {}) {
        const {
            ttl = this.config.ttl.standard,
            priority = 'normal',
            tags = [],
            prefetchEnabled = true
        } = options;

        const cacheEntry = {
            data,
            ttl,
            priority,
            tags,
            createdAt: Date.now(),
            expiresAt: Date.now() + ttl,
            accessCount: 0,
            lastAccessed: Date.now(),
            size: this.calculateSize(data)
        };

        try {
            // Always store in memory for fast access
            this.setInMemory(key, data, ttl, priority);

            // Store in persistent cache based on priority and size
            if (this.shouldPersist(cacheEntry)) {
                await this.setInPersistent(key, cacheEntry);
            }

            // Setup prefetching if enabled
            if (prefetchEnabled) {
                this.schedulePrefetch(key, cacheEntry);
            }

            // Update metrics
            this.updateCacheMetrics(key, 'set', cacheEntry);

        } catch (error) {
            console.error(`❌ Cache storage error for ${key}:`, error);
        }
    }

    /**
     * Memory cache operations
     */
    getFromMemory(key) {
        const entry = this.memoryCache.get(key);
        if (entry) {
            entry.accessCount++;
            entry.lastAccessed = Date.now();
            return entry;
        }
        return null;
    }

    setInMemory(key, data, ttl, priority) {
        // Check memory limits
        if (this.memoryCache.size >= this.config.maxMemoryEntries) {
            this.evictFromMemory();
        }

        const entry = {
            data,
            ttl,
            priority,
            createdAt: Date.now(),
            expiresAt: Date.now() + ttl,
            accessCount: 1,
            lastAccessed: Date.now(),
            size: this.calculateSize(data)
        };

        this.memoryCache.set(key, entry);
    }

    /**
     * Persistent cache operations
     */
    async initializePersistentStorage() {
        if (!('indexedDB' in window)) {
            console.warn('⚠️ IndexedDB not available, using memory-only cache');
            this.persistentCache = null;
            return;
        }

        return new Promise((resolve, reject) => {
            const request = indexedDB.open('KBICache', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.persistentCache = request.result;
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create cache store
                const cacheStore = db.createObjectStore('cache', { keyPath: 'key' });
                cacheStore.createIndex('expiresAt', 'expiresAt');
                cacheStore.createIndex('priority', 'priority');
                cacheStore.createIndex('tags', 'tags', { multiEntry: true });
                
                // Create metrics store
                const metricsStore = db.createObjectStore('metrics', { keyPath: 'key' });
                metricsStore.createIndex('timestamp', 'timestamp');
            };
        });
    }

    async getFromPersistent(key) {
        if (!this.persistentCache) return null;

        return new Promise((resolve, reject) => {
            const transaction = this.persistentCache.transaction(['cache'], 'readonly');
            const store = transaction.objectStore('cache');
            const request = store.get(key);
            
            request.onsuccess = () => {
                const result = request.result;
                if (result && !this.isExpired(result)) {
                    resolve(result);
                } else {
                    resolve(null);
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    async setInPersistent(key, entry) {
        if (!this.persistentCache) return;

        return new Promise((resolve, reject) => {
            const transaction = this.persistentCache.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            
            const cacheEntry = {
                key,
                ...entry,
                storedAt: Date.now()
            };
            
            const request = store.put(cacheEntry);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Intelligent prefetching system
     */
    schedulePrefetch(key, entry) {
        const prefetchTime = entry.createdAt + (entry.ttl * this.config.prefetchThreshold);
        const delay = Math.max(0, prefetchTime - Date.now());
        
        setTimeout(() => {
            this.addToPrefetchQueue(key, entry);
        }, delay);
    }

    addToPrefetchQueue(key, entry) {
        const prefetchItem = {
            key,
            priority: entry.priority,
            addedAt: Date.now(),
            retryCount: 0
        };
        
        this.prefetchQueue.push(prefetchItem);
        this.processPrefetchQueue();
    }

    async processPrefetchQueue() {
        if (this.prefetchQueue.length === 0) return;
        
        // Sort by priority
        this.prefetchQueue.sort((a, b) => {
            const priorities = { high: 3, normal: 2, low: 1 };
            return priorities[b.priority] - priorities[a.priority];
        });

        const concurrent = Math.min(this.config.prefetchConcurrency, this.prefetchQueue.length);
        const batch = this.prefetchQueue.splice(0, concurrent);
        
        const prefetchPromises = batch.map(item => this.executePrefetch(item));
        await Promise.allSettled(prefetchPromises);
        
        // Continue processing if queue not empty
        if (this.prefetchQueue.length > 0) {
            setTimeout(() => this.processPrefetchQueue(), 1000);
        }
    }

    async executePrefetch(item) {
        try {
            // This would trigger the actual data fetch
            // For now, we'll simulate the prefetch
            console.log(`🔄 Prefetching data for ${item.key}`);
            
            // Emit event for external data loading
            window.dispatchEvent(new CustomEvent('cache-prefetch', {
                detail: { key: item.key, priority: item.priority }
            }));
            
        } catch (error) {
            console.error(`❌ Prefetch failed for ${item.key}:`, error);
            
            // Retry logic
            if (item.retryCount < 3) {
                item.retryCount++;
                setTimeout(() => this.addToPrefetchQueue(item.key, item), 5000);
            }
        }
    }

    /**
     * Cache warming strategies
     */
    setupCacheWarming() {
        // Warm cache with critical data on startup
        setTimeout(() => this.warmCriticalData(), 2000);
        
        // Periodic cache warming
        setInterval(() => this.warmPopularData(), 15 * 60 * 1000); // Every 15 minutes
    }

    async warmCriticalData() {
        const criticalKeys = [
            'health-status',
            'recent-opportunities',
            'dashboard-kpis'
        ];
        
        console.log('🔥 Warming critical cache data...');
        
        criticalKeys.forEach(key => {
            window.dispatchEvent(new CustomEvent('cache-warm', {
                detail: { key, priority: 'critical' }
            }));
        });
    }

    async warmPopularData() {
        // Identify popular data based on access patterns
        const popularKeys = this.getPopularKeys();
        
        console.log('🔥 Warming popular cache data...', popularKeys);
        
        popularKeys.forEach(key => {
            window.dispatchEvent(new CustomEvent('cache-warm', {
                detail: { key, priority: 'normal' }
            }));
        });
    }

    /**
     * Cache cleanup and maintenance
     */
    setupCacheCleanup() {
        // Clean expired entries every 5 minutes
        setInterval(() => this.cleanupExpiredEntries(), 5 * 60 * 1000);
        
        // Full cleanup every hour
        setInterval(() => this.performFullCleanup(), 60 * 60 * 1000);
    }

    cleanupExpiredEntries() {
        let cleanedCount = 0;
        
        // Cleanup memory cache
        for (const [key, entry] of this.memoryCache.entries()) {
            if (this.isExpired(entry)) {
                this.memoryCache.delete(key);
                cleanedCount++;
            }
        }
        
        if (cleanedCount > 0) {
            console.log(`🧹 Cleaned ${cleanedCount} expired cache entries`);
        }
    }

    async performFullCleanup() {
        console.log('🧹 Performing full cache cleanup...');
        
        // Cleanup memory cache
        this.cleanupExpiredEntries();
        
        // Cleanup persistent cache
        if (this.persistentCache) {
            await this.cleanupPersistentCache();
        }
        
        // Cleanup metrics older than 24 hours
        this.cleanupOldMetrics();
    }

    async cleanupPersistentCache() {
        return new Promise((resolve, reject) => {
            const transaction = this.persistentCache.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            const index = store.index('expiresAt');
            
            const range = IDBKeyRange.upperBound(Date.now());
            const request = index.openCursor(range);
            
            let deletedCount = 0;
            
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    deletedCount++;
                    cursor.continue();
                } else {
                    console.log(`🗑️ Deleted ${deletedCount} expired persistent cache entries`);
                    resolve();
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Cache metrics and analytics
     */
    setupCacheMetrics() {
        this.metricsTimer = setInterval(() => {
            this.calculateCacheEfficiency();
        }, 60 * 1000); // Every minute
    }

    recordCacheHit(key, source, responseTime) {
        const metric = this.cacheMetrics.get(key) || {
            hits: 0,
            misses: 0,
            errors: 0,
            totalResponseTime: 0,
            sources: { memory: 0, persistent: 0, prefetch: 0 }
        };
        
        metric.hits++;
        metric.totalResponseTime += responseTime;
        metric.sources[source]++;
        
        this.cacheMetrics.set(key, metric);
    }

    recordCacheMiss(key, responseTime) {
        const metric = this.cacheMetrics.get(key) || {
            hits: 0,
            misses: 0,
            errors: 0,
            totalResponseTime: 0,
            sources: { memory: 0, persistent: 0, prefetch: 0 }
        };
        
        metric.misses++;
        metric.totalResponseTime += responseTime;
        
        this.cacheMetrics.set(key, metric);
    }

    recordCacheError(key, error) {
        const metric = this.cacheMetrics.get(key) || {
            hits: 0,
            misses: 0,
            errors: 0,
            totalResponseTime: 0,
            sources: { memory: 0, persistent: 0, prefetch: 0 }
        };
        
        metric.errors++;
        this.cacheMetrics.set(key, metric);
    }

    calculateCacheEfficiency() {
        let totalHits = 0;
        let totalMisses = 0;
        let totalResponseTime = 0;
        
        for (const metric of this.cacheMetrics.values()) {
            totalHits += metric.hits;
            totalMisses += metric.misses;
            totalResponseTime += metric.totalResponseTime;
        }
        
        const hitRate = totalHits / (totalHits + totalMisses) * 100;
        const avgResponseTime = totalResponseTime / (totalHits + totalMisses);
        
        console.log(`📊 Cache Efficiency: ${hitRate.toFixed(1)}% hit rate, ${avgResponseTime.toFixed(2)}ms avg response`);
    }

    /**
     * Utility methods
     */
    isExpired(entry) {
        return Date.now() > entry.expiresAt;
    }

    calculateSize(data) {
        return JSON.stringify(data).length;
    }

    shouldPersist(entry) {
        // Persist high priority items and large datasets
        return entry.priority === 'high' || entry.size > 10000;
    }

    evictFromMemory() {
        // LRU eviction strategy
        let oldestKey = null;
        let oldestTime = Date.now();
        
        for (const [key, entry] of this.memoryCache.entries()) {
            if (entry.lastAccessed < oldestTime) {
                oldestTime = entry.lastAccessed;
                oldestKey = key;
            }
        }
        
        if (oldestKey) {
            this.memoryCache.delete(oldestKey);
        }
    }

    getPopularKeys() {
        const keyStats = [];
        
        for (const [key, metric] of this.cacheMetrics.entries()) {
            const popularity = metric.hits / (metric.hits + metric.misses + 1);
            keyStats.push({ key, popularity });
        }
        
        return keyStats
            .sort((a, b) => b.popularity - a.popularity)
            .slice(0, 5)
            .map(stat => stat.key);
    }

    processResult(data, options) {
        // Apply any post-processing options
        if (options.transform) {
            return options.transform(data);
        }
        return data;
    }

    cleanupOldMetrics() {
        const cutoff = Date.now() - (24 * 60 * 60 * 1000); // 24 hours ago
        
        for (const [key, metric] of this.cacheMetrics.entries()) {
            if (metric.lastUpdated && metric.lastUpdated < cutoff) {
                this.cacheMetrics.delete(key);
            }
        }
    }

    updateCacheMetrics(key, operation, entry) {
        // Update metrics for cache operations
        const metric = this.cacheMetrics.get(key) || {
            sets: 0,
            gets: 0,
            size: 0,
            lastUpdated: Date.now()
        };
        
        if (operation === 'set') {
            metric.sets++;
            metric.size = entry.size;
        }
        
        metric.lastUpdated = Date.now();
        this.cacheMetrics.set(key, metric);
    }

    /**
     * Public API methods
     */
    getMetrics() {
        return {
            memoryCache: {
                size: this.memoryCache.size,
                maxSize: this.config.maxMemoryEntries
            },
            persistentCache: {
                available: !!this.persistentCache
            },
            prefetchQueue: {
                size: this.prefetchQueue.length
            },
            efficiency: this.calculateEfficiencyStats()
        };
    }

    calculateEfficiencyStats() {
        let totalHits = 0;
        let totalMisses = 0;
        
        for (const metric of this.cacheMetrics.values()) {
            totalHits += metric.hits || 0;
            totalMisses += metric.misses || 0;
        }
        
        return {
            hitRate: totalHits / (totalHits + totalMisses + 1) * 100,
            totalOperations: totalHits + totalMisses
        };
    }

    clear() {
        this.memoryCache.clear();
        this.cacheMetrics.clear();
        this.prefetchQueue.length = 0;
        
        if (this.persistentCache) {
            const transaction = this.persistentCache.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            store.clear();
        }
        
        console.log('🧹 Cache cleared');
    }
}

// Global intelligent cache instance
window.intelligentCache = new IntelligentCache();

console.log('🧠 KBI Labs Intelligent Cache System loaded successfully');