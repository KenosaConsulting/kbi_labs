/**
 * Enrichment API Service
 * Handles all API calls related to government data enrichment
 */

class EnrichmentApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'EnrichmentApiError';
    this.status = status;
    this.data = data;
  }
}

class EnrichmentApi {
  constructor() {
    this.baseUrl = this.getBaseUrl();
    this.timeout = 30000; // 30 seconds default timeout
  }

  getBaseUrl() {
    if (process.env.NODE_ENV === 'development') {
      return 'http://localhost:8000/api/data-enrichment';
    }
    return `${window.location.origin}/api/data-enrichment`;
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: this.timeout,
    };

    const config = { ...defaultOptions, ...options };

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.timeout);
    config.signal = controller.signal;

    try {
      console.log(`Making API request to: ${url}`);
      
      const response = await fetch(url, config);
      clearTimeout(timeoutId);

      let data;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMessage = data?.detail || data?.message || `HTTP ${response.status}: ${response.statusText}`;
        throw new EnrichmentApiError(errorMessage, response.status, data);
      }

      console.log(`API request successful: ${url}`);
      return data;

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new EnrichmentApiError('Request timeout', 408);
      }
      
      if (error instanceof EnrichmentApiError) {
        throw error;
      }
      
      console.error(`API request failed: ${url}`, error);
      throw new EnrichmentApiError(
        `Network error: ${error.message}`, 
        0, 
        { originalError: error }
      );
    }
  }

  // ============================================================================
  // Enrichment Operations
  // ============================================================================

  /**
   * Request enrichment for an agency
   * @param {Object} config - Enrichment configuration
   * @param {string} config.agency_code - Agency code (e.g., '9700')
   * @param {string} [config.agency_name] - Human-readable agency name
   * @param {string[]} [config.data_types] - Types of data to enrich
   * @param {string} [config.enrichment_depth] - Level of enrichment detail
   * @param {string} [config.priority] - Job priority level
   * @param {string} [config.user_id] - ID of requesting user
   * @returns {Promise<Object>} Enrichment response
   */
  async requestEnrichment(config) {
    if (!config.agency_code) {
      throw new EnrichmentApiError('Agency code is required', 400);
    }

    const payload = {
      agency_code: config.agency_code,
      agency_name: config.agency_name || null,
      data_types: config.data_types || ['budget', 'personnel', 'contracts', 'organizational'],
      enrichment_depth: config.enrichment_depth || 'standard',
      priority: config.priority || 'normal',
      user_id: config.user_id || null,
    };

    return this.makeRequest('/enrich', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Get job status
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} Job status information
   */
  async getJobStatus(jobId) {
    if (!jobId) {
      throw new EnrichmentApiError('Job ID is required', 400);
    }

    return this.makeRequest(`/job/${jobId}/status`);
  }

  /**
   * Get enriched agency data
   * @param {string} agencyCode - Agency code
   * @param {Object} options - Query options
   * @param {string[]} [options.dataTypes] - Specific data types to retrieve
   * @param {boolean} [options.includeMetadata] - Include quality and metadata
   * @returns {Promise<Object>} Agency data
   */
  async getAgencyData(agencyCode, options = {}) {
    if (!agencyCode) {
      throw new EnrichmentApiError('Agency code is required', 400);
    }

    const params = new URLSearchParams();
    
    if (options.dataTypes && options.dataTypes.length > 0) {
      options.dataTypes.forEach(type => params.append('data_types', type));
    }
    
    if (typeof options.includeMetadata === 'boolean') {
      params.append('include_metadata', options.includeMetadata);
    }

    const queryString = params.toString();
    const endpoint = `/agency/${agencyCode}/data${queryString ? `?${queryString}` : ''}`;
    
    return this.makeRequest(endpoint);
  }

  /**
   * Get agency enrichment summary
   * @param {string} agencyCode - Agency code
   * @returns {Promise<Object>} Enrichment summary
   */
  async getAgencySummary(agencyCode) {
    if (!agencyCode) {
      throw new EnrichmentApiError('Agency code is required', 400);
    }

    return this.makeRequest(`/agency/${agencyCode}/summary`);
  }

  /**
   * Invalidate cached data for an agency
   * @param {string} agencyCode - Agency code
   * @param {string[]} [dataTypes] - Specific data types to invalidate
   * @returns {Promise<Object>} Success response
   */
  async invalidateCache(agencyCode, dataTypes = null) {
    if (!agencyCode) {
      throw new EnrichmentApiError('Agency code is required', 400);
    }

    const params = new URLSearchParams();
    
    if (dataTypes && dataTypes.length > 0) {
      dataTypes.forEach(type => params.append('data_types', type));
    }

    const queryString = params.toString();
    const endpoint = `/agency/${agencyCode}/cache${queryString ? `?${queryString}` : ''}`;
    
    return this.makeRequest(endpoint, {
      method: 'DELETE',
    });
  }

  // ============================================================================
  // System Information
  // ============================================================================

  /**
   * Get list of supported agencies
   * @returns {Promise<Object>} List of supported agencies
   */
  async getSupportedAgencies() {
    return this.makeRequest('/agencies');
  }

  /**
   * Get list of supported data types
   * @returns {Promise<Object>} List of supported data types
   */
  async getSupportedDataTypes() {
    return this.makeRequest('/data-types');
  }

  /**
   * Get active enrichment jobs
   * @returns {Promise<Object>} List of active jobs
   */
  async getActiveJobs() {
    return this.makeRequest('/jobs/active');
  }

  /**
   * Get system health status
   * @returns {Promise<Object>} Health status information
   */
  async getHealthStatus() {
    return this.makeRequest('/health');
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  /**
   * Cancel a job (if supported by backend)
   * @param {string} jobId - Job ID to cancel
   * @returns {Promise<Object>} Cancellation response
   */
  async cancelJob(jobId) {
    if (!jobId) {
      throw new EnrichmentApiError('Job ID is required', 400);
    }

    return this.makeRequest(`/job/${jobId}/cancel`, {
      method: 'POST',
    });
  }

  /**
   * Retry a failed job (if supported by backend)
   * @param {string} jobId - Job ID to retry
   * @returns {Promise<Object>} Retry response
   */
  async retryJob(jobId) {
    if (!jobId) {
      throw new EnrichmentApiError('Job ID is required', 400);
    }

    return this.makeRequest(`/job/${jobId}/retry`, {
      method: 'POST',
    });
  }

  /**
   * Get job history for an agency
   * @param {string} agencyCode - Agency code
   * @param {Object} options - Query options
   * @param {number} [options.limit] - Maximum number of jobs to return
   * @param {number} [options.offset] - Number of jobs to skip
   * @returns {Promise<Object>} Job history
   */
  async getJobHistory(agencyCode, options = {}) {
    if (!agencyCode) {
      throw new EnrichmentApiError('Agency code is required', 400);
    }

    const params = new URLSearchParams();
    
    if (options.limit) {
      params.append('limit', options.limit);
    }
    
    if (options.offset) {
      params.append('offset', options.offset);
    }

    const queryString = params.toString();
    const endpoint = `/agency/${agencyCode}/jobs${queryString ? `?${queryString}` : ''}`;
    
    return this.makeRequest(endpoint);
  }

  /**
   * Bulk invalidate cache for multiple agencies
   * @param {string[]} agencyCodes - Array of agency codes
   * @param {string[]} [dataTypes] - Specific data types to invalidate
   * @returns {Promise<Object>} Bulk operation response
   */
  async bulkInvalidateCache(agencyCodes, dataTypes = null) {
    if (!agencyCodes || !Array.isArray(agencyCodes) || agencyCodes.length === 0) {
      throw new EnrichmentApiError('Agency codes array is required', 400);
    }

    const payload = {
      agency_codes: agencyCodes,
      data_types: dataTypes,
    };

    return this.makeRequest('/cache/bulk-invalidate', {
      method: 'DELETE',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Get cache statistics
   * @returns {Promise<Object>} Cache statistics
   */
  async getCacheStats() {
    return this.makeRequest('/cache/stats');
  }

  // ============================================================================
  // Configuration
  // ============================================================================

  /**
   * Set request timeout
   * @param {number} timeout - Timeout in milliseconds
   */
  setTimeout(timeout) {
    this.timeout = timeout;
  }

  /**
   * Set base URL (useful for testing)
   * @param {string} baseUrl - Base URL for API
   */
  setBaseUrl(baseUrl) {
    this.baseUrl = baseUrl;
  }
}

// Create and export singleton instance
const enrichmentApi = new EnrichmentApi();

export { enrichmentApi, EnrichmentApiError };