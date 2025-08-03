/**
 * Real-time Data Updater for KBI Labs Platform
 * Handles automatic data refresh and live updates
 */

class RealtimeUpdater {
    constructor(apiService) {
        this.apiService = apiService;
        this.updateIntervals = new Map();
        this.subscribers = new Map();
        this.isActive = false;
        
        // Default update frequencies (in milliseconds)
        this.defaultIntervals = {
            opportunities: 5 * 60 * 1000,    // 5 minutes
            regulations: 10 * 60 * 1000,    // 10 minutes
            congressional: 15 * 60 * 1000,  // 15 minutes
            dashboard: 2 * 60 * 1000,       // 2 minutes
            health: 30 * 1000               // 30 seconds
        };
    }

    /**
     * Start real-time updates
     */
    start() {
        if (this.isActive) return;
        
        this.isActive = true;
        console.log('Real-time updater started');

        // Start periodic updates for each data type
        Object.entries(this.defaultIntervals).forEach(([dataType, interval]) => {
            this.startPeriodicUpdate(dataType, interval);
        });

        // Update page visibility handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pause();
            } else {
                this.resume();
            }
        });
    }

    /**
     * Stop all real-time updates
     */
    stop() {
        this.isActive = false;
        this.updateIntervals.forEach(intervalId => clearInterval(intervalId));
        this.updateIntervals.clear();
        console.log('Real-time updater stopped');
    }

    /**
     * Pause updates (when page is hidden)
     */
    pause() {
        this.updateIntervals.forEach(intervalId => clearInterval(intervalId));
        this.updateIntervals.clear();
        console.log('Real-time updater paused');
    }

    /**
     * Resume updates
     */
    resume() {
        if (!this.isActive) return;
        
        Object.entries(this.defaultIntervals).forEach(([dataType, interval]) => {
            this.startPeriodicUpdate(dataType, interval);
        });
        console.log('Real-time updater resumed');
    }

    /**
     * Start periodic update for specific data type
     */
    startPeriodicUpdate(dataType, interval) {
        if (this.updateIntervals.has(dataType)) {
            clearInterval(this.updateIntervals.get(dataType));
        }

        const intervalId = setInterval(async () => {
            await this.updateData(dataType);
        }, interval);

        this.updateIntervals.set(dataType, intervalId);
    }

    /**
     * Subscribe to data updates
     */
    subscribe(dataType, callback) {
        if (!this.subscribers.has(dataType)) {
            this.subscribers.set(dataType, new Set());
        }
        this.subscribers.get(dataType).add(callback);
    }

    /**
     * Unsubscribe from data updates
     */
    unsubscribe(dataType, callback) {
        if (this.subscribers.has(dataType)) {
            this.subscribers.get(dataType).delete(callback);
        }
    }

    /**
     * Update specific data type and notify subscribers
     */
    async updateData(dataType) {
        try {
            let data = null;
            
            switch (dataType) {
                case 'opportunities':
                    data = await this.apiService.getProcurementOpportunities();
                    break;
                case 'regulations':
                    data = await this.apiService.getRegulatoryIntelligence();
                    break;
                case 'congressional':
                    data = await this.apiService.getCongressionalIntelligence();
                    break;
                case 'dashboard':
                    data = await this.apiService.getContractorDashboard();
                    break;
                case 'health':
                    data = await this.apiService.getHealthStatus();
                    break;
            }

            if (data && this.subscribers.has(dataType)) {
                this.subscribers.get(dataType).forEach(callback => {
                    try {
                        callback(data, dataType);
                    } catch (error) {
                        console.error(`Error in subscriber callback for ${dataType}:`, error);
                    }
                });
            }

            // Update last update timestamp
            this.showUpdateNotification(dataType);

        } catch (error) {
            console.error(`Error updating ${dataType}:`, error);
        }
    }

    /**
     * Show subtle update notification
     */
    showUpdateNotification(dataType) {
        // Create or update status indicator
        let indicator = document.getElementById('realtime-status');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'realtime-status';
            indicator.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                z-index: 1000;
                transition: all 0.3s ease;
                opacity: 0;
                transform: translateY(-10px);
            `;
            document.body.appendChild(indicator);
        }

        indicator.innerHTML = `
            <i class="fas fa-sync-alt fa-spin"></i>
            Updated ${dataType} - ${new Date().toLocaleTimeString()}
        `;
        
        // Show notification
        indicator.style.opacity = '1';
        indicator.style.transform = 'translateY(0)';
        
        // Hide after 3 seconds
        setTimeout(() => {
            indicator.style.opacity = '0';
            indicator.style.transform = 'translateY(-10px)';
        }, 3000);
    }

    /**
     * Force immediate update of all data types
     */
    async forceUpdate() {
        const dataTypes = Object.keys(this.defaultIntervals);
        const updatePromises = dataTypes.map(dataType => this.updateData(dataType));
        
        try {
            await Promise.allSettled(updatePromises);
            console.log('Force update completed for all data types');
        } catch (error) {
            console.error('Error during force update:', error);
        }
    }

    /**
     * Set custom update interval for specific data type
     */
    setUpdateInterval(dataType, intervalMs) {
        this.defaultIntervals[dataType] = intervalMs;
        if (this.isActive) {
            this.startPeriodicUpdate(dataType, intervalMs);
        }
    }

    /**
     * Get update statistics
     */
    getStats() {
        return {
            isActive: this.isActive,
            activeIntervals: this.updateIntervals.size,
            subscriberCounts: Object.fromEntries(
                Array.from(this.subscribers.entries()).map(([key, set]) => [key, set.size])
            ),
            updateIntervals: { ...this.defaultIntervals }
        };
    }
}

// Create global instance
if (window.kbiAPI) {
    window.realtimeUpdater = new RealtimeUpdater(window.kbiAPI);
    
    // Auto-start if on main dashboard
    if (window.location.pathname.includes('smb_government_contractor_platform.html')) {
        // Start updates after page load
        window.addEventListener('load', () => {
            setTimeout(() => {
                window.realtimeUpdater.start();
            }, 2000); // Start after 2 seconds
        });
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeUpdater;
}

console.log('Real-time updater loaded successfully');