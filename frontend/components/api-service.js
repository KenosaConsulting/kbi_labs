/**
 * KBI Labs API Service Layer
 * Connects frontend dashboards to backend government intelligence APIs
 */

class KBIAPIService {
    constructor(baseURL = 'http://localhost:8000/api') {
        this.baseURL = baseURL;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Generic API request handler with error handling and caching
     */
    async makeRequest(endpoint, options = {}) {
        const cacheKey = `${endpoint}_${JSON.stringify(options)}`;
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Cache successful responses
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });

            return data;
        } catch (error) {
            console.error(`API Request failed for ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Get comprehensive government intelligence data
     */
    async getComprehensiveIntelligence() {
        return await this.makeRequest('/government-intelligence/comprehensive-intelligence');
    }

    /**
     * Get procurement opportunities from SAM.gov
     */
    async getProcurementOpportunities() {
        return await this.makeRequest('/government-intelligence/procurement-opportunities');
    }

    /**
     * Get regulatory intelligence from Federal Register
     */
    async getRegulatoryIntelligence() {
        return await this.makeRequest('/government-intelligence/regulatory-intelligence');
    }

    /**
     * Get congressional intelligence from Congress.gov
     */
    async getCongressionalIntelligence() {
        return await this.makeRequest('/government-intelligence/congressional-intelligence');
    }

    /**
     * Get agency-specific procurement opportunities
     */
    async getAgencyOpportunities(agencyName) {
        return await this.makeRequest(`/government-intelligence/agency-opportunities/${encodeURIComponent(agencyName)}`);
    }

    /**
     * Get agency digital profile and regulatory activity
     */
    async getAgencyProfile(agencyName) {
        const [digitalProfile, regulatoryProfile] = await Promise.allSettled([
            this.makeRequest(`/government-intelligence/agency-digital-profile/${encodeURIComponent(agencyName)}`),
            this.makeRequest(`/government-intelligence/agency-regulatory-profile/${encodeURIComponent(agencyName)}`)
        ]);

        return {
            digital: digitalProfile.status === 'fulfilled' ? digitalProfile.value : null,
            regulatory: regulatoryProfile.status === 'fulfilled' ? regulatoryProfile.value : null
        };
    }

    /**
     * Get contractor intelligence dashboard data
     */
    async getContractorDashboard() {
        return await this.makeRequest('/government-intelligence/contractor-intelligence-dashboard');
    }

    /**
     * Get GovInfo documents and congressional intelligence
     */
    async getGovInfoIntelligence() {
        return await this.makeRequest('/government-intelligence/govinfo-intelligence');
    }

    /**
     * Get enhanced GSA intelligence with site scanning data
     */
    async getEnhancedGSAIntelligence() {
        return await this.makeRequest('/government-intelligence/enhanced-gsa-intelligence');
    }

    /**
     * Get API health status
     */
    async getHealthStatus() {
        return await this.makeRequest('/government-intelligence/health');
    }

    /**
     * Refresh intelligence cache
     */
    async refreshCache() {
        return await this.makeRequest('/government-intelligence/refresh-cache', { method: 'POST' });
    }

    /**
     * Get USASpending data for specific UEI
     */
    async getUSASpendingData(uei, fiscalYear = null) {
        const endpoint = fiscalYear 
            ? `/usaspending/search/${uei}?fiscal_year=${fiscalYear}`
            : `/usaspending/search/${uei}`;
        return await this.makeRequest(endpoint);
    }

    /**
     * Get recipient profile from USASpending
     */
    async getRecipientProfile(uei) {
        return await this.makeRequest(`/usaspending/profile/${uei}`);
    }

    /**
     * Clear all cached data
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Get cached data size and statistics
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys()),
            memory: JSON.stringify(Array.from(this.cache.entries())).length
        };
    }
}

// Export singleton instance
const kbiAPI = new KBIAPIService();
window.kbiAPI = kbiAPI;

/**
 * Utility functions for data processing and display
 */
window.KBIUtils = {
    /**
     * Format currency values for display
     */
    formatCurrency(amount) {
        if (!amount) return '$0';
        if (amount >= 1e9) return `$${(amount / 1e9).toFixed(1)}B`;
        if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}M`;
        if (amount >= 1e3) return `$${(amount / 1e3).toFixed(1)}K`;
        return `$${amount.toLocaleString()}`;
    },

    /**
     * Format dates for display
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    /**
     * Calculate days until deadline
     */
    daysUntil(dateString) {
        if (!dateString) return null;
        const deadline = new Date(dateString);
        const now = new Date();
        const diffTime = deadline - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    },

    /**
     * Get urgency level based on days remaining
     */
    getUrgencyLevel(daysRemaining) {
        if (daysRemaining <= 3) return 'critical';
        if (daysRemaining <= 7) return 'high';
        if (daysRemaining <= 14) return 'medium';
        return 'low';
    },

    /**
     * Extract NAICS codes from opportunity data
     */
    extractNAICS(opportunity) {
        return opportunity.naics_codes || opportunity.naics || [];
    },

    /**
     * Calculate AI confidence level
     */
    getConfidenceLevel(score) {
        if (score >= 90) return 'very-high';
        if (score >= 75) return 'high';
        if (score >= 60) return 'medium';
        if (score >= 40) return 'low';
        return 'very-low';
    },

    /**
     * Generate color classes for impact levels
     */
    getImpactColor(impact) {
        const colorMap = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'primary',
            'low': 'success',
            'very-low': 'secondary'
        };
        return colorMap[impact] || 'primary';
    },

    /**
     * Debounce function for search inputs
     */
    debounce(func, wait) {
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

    /**
     * Show loading state
     */
    showLoading(element, message = 'Loading...') {
        if (!element) return;
        element.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <span>${message}</span>
            </div>
        `;
    },

    /**
     * Show error state
     */
    showError(element, message = 'Unable to load data') {
        if (!element) return;
        element.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button onclick="location.reload()">Retry</button>
            </div>
        `;
    },

    /**
     * Process regulatory data for display
     */
    processRegulatoryData(regulatoryData) {
        if (!regulatoryData?.data?.recent_regulations) return [];
        
        return regulatoryData.data.recent_regulations.map(reg => ({
            id: reg.document_number || Math.random().toString(36),
            title: reg.title || 'Untitled Regulation',
            agency: reg.agency_names?.[0] || 'Unknown Agency',
            impact: this.getImpactLevel(reg.contractor_relevance_score || 0),
            impactScore: reg.contractor_relevance_score || 0,
            publicationDate: reg.publication_date,
            summary: reg.abstract || 'No summary available.',
            tags: this.extractRegulationTags(reg),
            url: reg.html_url || reg.pdf_url
        }));
    },

    /**
     * Extract regulation tags
     */
    extractRegulationTags(regulation) {
        const tags = [];
        if (regulation.type?.includes('Rule')) tags.push('final-rule');
        if (regulation.type?.includes('Notice')) tags.push('notice');
        if (regulation.significant) tags.push('significant');
        if (regulation.contractor_relevance_score > 75) tags.push('high-impact');
        return tags;
    },

    /**
     * Get impact level from score
     */
    getImpactLevel(score) {
        if (score >= 90) return 'critical';
        if (score >= 75) return 'high';
        if (score >= 50) return 'medium';
        return 'low';
    }
};

// Add CSS for loading and error states
const apiServiceStyles = `
<style>
.loading-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 40px;
    color: #64748b;
}

.loading-spinner i {
    font-size: 1.5rem;
    color: #3b82f6;
}

.error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    padding: 40px;
    color: #ef4444;
    text-align: center;
}

.error-state i {
    font-size: 2rem;
}

.error-state button {
    padding: 8px 16px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}

.error-state button:hover {
    background: #2563eb;
}

.api-status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.api-status-indicator.healthy {
    background: #dcfce7;
    color: #16a34a;
}

.api-status-indicator.unhealthy {
    background: #fef2f2;
    color: #dc2626;
}

.api-status-indicator i {
    font-size: 0.75rem;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', apiServiceStyles);

console.log('KBI API Service Layer loaded successfully');