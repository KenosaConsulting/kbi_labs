/**
 * KBI Labs Performance Optimizer
 * 
 * Comprehensive solution for fast loading, progressive enhancement,
 * and optimal user experience with multiple data sources
 */

class PerformanceOptimizer {
    constructor() {
        this.loadingStates = new Map();
        this.loadingPriorities = new Map();
        this.performanceMetrics = new Map();
        this.deferredOperations = [];
        this.webWorkers = new Map();
        this.intersectionObservers = new Map();
        
        // Loading priorities (lower number = higher priority)
        this.PRIORITIES = {
            CRITICAL: 1,    // Must load immediately (< 1s)
            HIGH: 2,        // Load after critical (1-3s)
            MEDIUM: 3,      // Load in background (3-10s)
            LOW: 4          // Load on demand (when needed)
        };

        this.initializePerformanceOptimizer();
    }

    /**
     * Initialize performance optimization system
     */
    initializePerformanceOptimizer() {
        console.log('🚀 Initializing Performance Optimizer...');
        
        // Setup performance monitoring
        this.setupPerformanceMonitoring();
        
        // Initialize skeleton UI
        this.initializeSkeletonUI();
        
        // Setup resource loading strategy
        this.setupResourceLoadingStrategy();
        
        // Initialize intersection observers for lazy loading
        this.setupIntersectionObservers();
        
        // Setup web workers for heavy processing
        this.setupWebWorkers();
        
        console.log('✅ Performance Optimizer initialized');
    }

    /**
     * Progressive loading strategy
     */
    async progressiveLoad() {
        const startTime = performance.now();
        console.log('🔄 Starting progressive load sequence...');

        try {
            // Phase 1: Critical UI (< 1 second)
            await this.loadCriticalUI();
            this.logPhaseComplete('Critical UI', startTime);

            // Phase 2: Essential Data (1-3 seconds)  
            this.loadEssentialData();
            
            // Phase 3: Background Data (3-10 seconds)
            setTimeout(() => this.loadBackgroundData(), 2000);
            
            // Phase 4: Enhanced Features (on-demand)
            this.setupLazyFeatures();
            
        } catch (error) {
            console.error('❌ Progressive load failed:', error);
            this.fallbackToBasicLoad();
        }
    }

    /**
     * Phase 1: Load critical UI components immediately
     */
    async loadCriticalUI() {
        const operations = [
            { name: 'skeleton-ui', fn: () => this.showSkeletonUI() },
            { name: 'navigation', fn: () => this.loadNavigation() },
            { name: 'header', fn: () => this.loadHeader() }
        ];

        await this.executePriorityOperations(operations, this.PRIORITIES.CRITICAL);
    }

    /**
     * Phase 2: Load essential data for immediate user value
     */
    async loadEssentialData() {
        const operations = [
            { 
                name: 'health-check', 
                fn: () => this.loadWithTimeout(() => window.kbiAPI?.getHealthStatus(), 2000),
                priority: this.PRIORITIES.CRITICAL
            },
            { 
                name: 'basic-kpis', 
                fn: () => this.loadBasicKPIs(),
                priority: this.PRIORITIES.HIGH
            },
            { 
                name: 'recent-opportunities', 
                fn: () => this.loadWithTimeout(() => window.kbiAPI?.getProcurementOpportunities(), 3000),
                priority: this.PRIORITIES.HIGH
            }
        ];

        // Execute high priority operations
        const highPriorityOps = operations.filter(op => op.priority <= this.PRIORITIES.HIGH);
        await Promise.allSettled(highPriorityOps.map(op => op.fn()));
        
        // Start replacing skeleton UI with real content
        this.startSkeletonReplacement();
    }

    /**
     * Phase 3: Load comprehensive data in background
     */
    async loadBackgroundData() {
        console.log('📊 Loading background data...');
        
        const backgroundOperations = [
            { name: 'regulations', fn: () => window.kbiAPI?.getRegulatoryIntelligence(), delay: 0 },
            { name: 'congressional', fn: () => window.kbiAPI?.getCongressionalIntelligence(), delay: 1000 },
            { name: 'comprehensive', fn: () => window.kbiAPI?.getComprehensiveIntelligence(), delay: 2000 },
            { name: 'agency-profiles', fn: () => window.kbiAPI?.getContractorDashboard(), delay: 3000 }
        ];

        // Stagger requests to avoid overwhelming APIs
        backgroundOperations.forEach(({ name, fn, delay }) => {
            setTimeout(async () => {
                try {
                    const data = await fn();
                    this.handleBackgroundDataLoaded(name, data);
                } catch (error) {
                    console.warn(`⚠️ Background load failed for ${name}:`, error);
                }
            }, delay);
        });
    }

    /**
     * Load with timeout to prevent hanging
     */
    async loadWithTimeout(operation, timeoutMs = 5000) {
        return Promise.race([
            operation(),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs)
            )
        ]);
    }

    /**
     * Execute operations by priority
     */
    async executePriorityOperations(operations, maxPriority) {
        const prioritizedOps = operations.filter(op => 
            (op.priority || this.PRIORITIES.HIGH) <= maxPriority
        );
        
        const results = await Promise.allSettled(
            prioritizedOps.map(async op => {
                const startTime = performance.now();
                try {
                    const result = await op.fn();
                    this.recordMetric(op.name, performance.now() - startTime, 'success');
                    return result;
                } catch (error) {
                    this.recordMetric(op.name, performance.now() - startTime, 'error', error);
                    throw error;
                }
            })
        );

        return results;
    }

    /**
     * Skeleton UI management
     */
    showSkeletonUI() {
        const skeletonHTML = `
            <div id="skeleton-overlay" class="skeleton-overlay">
                <div class="skeleton-header">
                    <div class="skeleton-logo"></div>
                    <div class="skeleton-nav">
                        <div class="skeleton-nav-item"></div>
                        <div class="skeleton-nav-item"></div>
                        <div class="skeleton-nav-item"></div>
                    </div>
                </div>
                <div class="skeleton-content">
                    <div class="skeleton-kpis">
                        <div class="skeleton-kpi-card"></div>
                        <div class="skeleton-kpi-card"></div>
                        <div class="skeleton-kpi-card"></div>
                        <div class="skeleton-kpi-card"></div>
                    </div>
                    <div class="skeleton-charts">
                        <div class="skeleton-chart"></div>
                        <div class="skeleton-chart"></div>
                    </div>
                </div>
            </div>
        `;

        // Insert skeleton at the beginning of body
        document.body.insertAdjacentHTML('afterbegin', skeletonHTML);
        this.addSkeletonStyles();
    }

    startSkeletonReplacement() {
        // Gradually fade out skeleton as real content loads
        const skeleton = document.getElementById('skeleton-overlay');
        if (skeleton) {
            skeleton.style.transition = 'opacity 0.5s ease-out';
            setTimeout(() => {
                skeleton.style.opacity = '0.5';
            }, 1000);
            
            setTimeout(() => {
                skeleton.remove();
            }, 3000);
        }
    }

    addSkeletonStyles() {
        if (document.getElementById('skeleton-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'skeleton-styles';
        styles.textContent = `
            .skeleton-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: #f8fafc;
                z-index: 9999;
                animation: skeleton-pulse 1.5s ease-in-out infinite alternate;
            }
            
            .skeleton-header {
                height: 64px;
                background: white;
                display: flex;
                align-items: center;
                padding: 0 24px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .skeleton-logo {
                width: 120px;
                height: 32px;
                background: #e2e8f0;
                border-radius: 4px;
                margin-right: 40px;
            }
            
            .skeleton-nav {
                display: flex;
                gap: 24px;
            }
            
            .skeleton-nav-item {
                width: 80px;
                height: 20px;
                background: #e2e8f0;
                border-radius: 4px;
            }
            
            .skeleton-content {
                padding: 24px;
            }
            
            .skeleton-kpis {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }
            
            .skeleton-kpi-card {
                height: 120px;
                background: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
            
            .skeleton-charts {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 24px;
            }
            
            .skeleton-chart {
                height: 300px;
                background: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
            
            @keyframes skeleton-pulse {
                0% { opacity: 1; }
                100% { opacity: 0.4; }
            }
        `;
        document.head.appendChild(styles);
    }

    /**
     * Lazy loading with Intersection Observer
     */
    setupIntersectionObservers() {
        // Chart lazy loading
        const chartObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadChart(entry.target);
                    chartObserver.unobserve(entry.target);
                }
            });
        }, { 
            rootMargin: '100px' // Load 100px before coming into view
        });

        this.intersectionObservers.set('charts', chartObserver);

        // Table lazy loading
        const tableObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadTable(entry.target);
                    tableObserver.unobserve(entry.target);
                }
            });
        });

        this.intersectionObservers.set('tables', tableObserver);
    }

    /**
     * Smart chart loading
     */
    async loadChart(chartElement) {
        const chartId = chartElement.id;
        const chartType = chartElement.dataset.chartType;
        
        try {
            // Show loading indicator
            chartElement.innerHTML = '<div class="chart-loading"><i class="fas fa-spinner fa-spin"></i> Loading chart...</div>';
            
            // Load chart data if needed
            const data = await this.getChartData(chartType);
            
            // Render chart
            if (window.dataVisualizer) {
                switch (chartType) {
                    case 'funnel':
                        window.dataVisualizer.createOpportunityFunnel(chartId, data);
                        break;
                    case 'distribution':
                        window.dataVisualizer.createValueDistributionChart(chartId, data);
                        break;
                    case 'spending':
                        window.dataVisualizer.createAgencySpendingChart(chartId, data);
                        break;
                    default:
                        console.warn(`Unknown chart type: ${chartType}`);
                }
            }
            
        } catch (error) {
            chartElement.innerHTML = `<div class="chart-error">Failed to load chart: ${error.message}</div>`;
        }
    }

    /**
     * Web Workers for heavy processing
     */
    setupWebWorkers() {
        // Create data processing worker
        const dataWorkerCode = `
            self.onmessage = function(e) {
                const { type, data } = e.data;
                
                switch (type) {
                    case 'processOpportunities':
                        const processed = processOpportunities(data);
                        self.postMessage({ type: 'opportunitiesProcessed', data: processed });
                        break;
                    case 'calculateKPIs':
                        const kpis = calculateKPIs(data);
                        self.postMessage({ type: 'kpisCalculated', data: kpis });
                        break;
                }
            };
            
            function processOpportunities(opportunities) {
                return opportunities.map((opp, index) => ({
                    ...opp,
                    aiScore: Math.floor(70 + Math.random() * 30),
                    processed: true,
                    processedAt: Date.now()
                }));
            }
            
            function calculateKPIs(data) {
                // Heavy calculations here
                return {
                    totalValue: data.reduce((sum, item) => sum + (item.value || 0), 0),
                    averageScore: data.reduce((sum, item) => sum + (item.score || 0), 0) / data.length,
                    calculatedAt: Date.now()
                };
            }
        `;

        const blob = new Blob([dataWorkerCode], { type: 'application/javascript' });
        const dataWorker = new Worker(URL.createObjectURL(blob));
        
        dataWorker.onmessage = (e) => {
            const { type, data } = e.data;
            this.handleWorkerMessage(type, data);
        };

        this.webWorkers.set('dataProcessor', dataWorker);
    }

    /**
     * Handle background data loading completion
     */
    handleBackgroundDataLoaded(dataType, data) {
        console.log(`📊 Background data loaded: ${dataType}`);
        
        // Update UI components that depend on this data
        if (window.dataOrchestrator) {
            window.dataOrchestrator.processAndDistributeData(dataType, data);
        }
        
        // Show subtle notification
        this.showDataUpdateNotification(dataType);
    }

    showDataUpdateNotification(dataType) {
        const notification = document.createElement('div');
        notification.className = 'data-update-notification';
        notification.innerHTML = `
            <i class="fas fa-check-circle"></i>
            ${dataType} data updated
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    this.recordWebVital(entry);
                });
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input'] });
        }
        
        // Monitor custom metrics
        this.startTime = performance.now();
    }

    recordMetric(name, duration, status, error = null) {
        this.performanceMetrics.set(name, {
            duration,
            status,
            error,
            timestamp: Date.now()
        });
    }

    recordWebVital(entry) {
        const { name, value } = entry;
        console.log(`📊 ${name}: ${value}ms`);
        this.performanceMetrics.set(name, { value, timestamp: Date.now() });
    }

    /**
     * Get performance report
     */
    getPerformanceReport() {
        const report = {
            metrics: Object.fromEntries(this.performanceMetrics),
            totalLoadTime: performance.now() - this.startTime,
            timestamp: new Date().toISOString()
        };
        
        return report;
    }

    /**
     * Fallback for when progressive loading fails
     */
    fallbackToBasicLoad() {
        console.log('⚠️ Falling back to basic loading...');
        
        // Remove skeleton
        const skeleton = document.getElementById('skeleton-overlay');
        if (skeleton) skeleton.remove();
        
        // Show basic error state
        document.body.innerHTML = `
            <div style="padding: 40px; text-align: center;">
                <h2>Loading KBI Labs Platform...</h2>
                <p>Please wait while we load your data...</p>
                <div style="margin: 20px 0;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3b82f6;"></i>
                </div>
            </div>
        `;
    }

    /**
     * Utility methods
     */
    logPhaseComplete(phase, startTime) {
        const duration = performance.now() - startTime;
        console.log(`✅ ${phase} loaded in ${duration.toFixed(2)}ms`);
        this.recordMetric(phase, duration, 'success');
    }

    async getChartData(chartType) {
        // Return cached data if available, otherwise load
        const cacheKey = `chart-${chartType}`;
        if (this.loadingStates.has(cacheKey)) {
            return this.loadingStates.get(cacheKey);
        }
        
        // Load data based on chart type
        let data = [];
        switch (chartType) {
            case 'funnel':
                data = await window.kbiAPI?.getProcurementOpportunities() || { data: [] };
                break;
            case 'distribution':
                data = await window.kbiAPI?.getComprehensiveIntelligence() || { data: [] };
                break;
            case 'spending':
                data = await window.kbiAPI?.getContractorDashboard() || { data: [] };
                break;
        }
        
        this.loadingStates.set(cacheKey, data);
        return data;
    }
}

// Global performance optimizer instance
window.performanceOptimizer = new PerformanceOptimizer();

// Auto-start progressive loading when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.performanceOptimizer.progressiveLoad();
    });
} else {
    window.performanceOptimizer.progressiveLoad();
}

console.log('⚡ KBI Labs Performance Optimizer loaded successfully');