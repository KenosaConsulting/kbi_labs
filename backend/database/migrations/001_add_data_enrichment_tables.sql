-- Data Enrichment Database Schema
-- Migration 001: Add core data enrichment tables

-- ==============================================================================
-- Data Enrichment Jobs Table
-- Tracks all data enrichment operations and their status
-- ==============================================================================

CREATE TABLE IF NOT EXISTS data_enrichment_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_code VARCHAR(10) NOT NULL,
    agency_name VARCHAR(255),
    
    -- Job Configuration
    data_types TEXT[] NOT NULL DEFAULT '{}', -- ['budget', 'personnel', 'contracts', 'organizational', 'strategic']
    enrichment_depth VARCHAR(20) NOT NULL DEFAULT 'standard', -- 'basic', 'standard', 'comprehensive'
    priority VARCHAR(10) NOT NULL DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    
    -- Job Status
    status VARCHAR(20) NOT NULL DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    records_processed INTEGER DEFAULT 0,
    overall_quality_score DECIMAL(5,2) CHECK (overall_quality_score >= 0 AND overall_quality_score <= 100),
    data_completeness DECIMAL(5,2) CHECK (data_completeness >= 0 AND data_completeness <= 100),
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Metadata
    requested_by_user_id UUID,
    execution_node VARCHAR(100), -- Which server/worker processed this
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    
    -- Indexes for common queries
    CONSTRAINT valid_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    CONSTRAINT valid_depth CHECK (enrichment_depth IN ('basic', 'standard', 'comprehensive'))
);

-- Create indexes for performance
CREATE INDEX idx_enrichment_jobs_agency_code ON data_enrichment_jobs(agency_code);
CREATE INDEX idx_enrichment_jobs_status ON data_enrichment_jobs(status);
CREATE INDEX idx_enrichment_jobs_created_at ON data_enrichment_jobs(created_at DESC);
CREATE INDEX idx_enrichment_jobs_priority_status ON data_enrichment_jobs(priority DESC, status);

-- ==============================================================================
-- Enriched Data Cache Table
-- Stores the actual enriched data with expiration and versioning
-- ==============================================================================

CREATE TABLE IF NOT EXISTS enriched_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Data Identification
    agency_code VARCHAR(10) NOT NULL,
    agency_name VARCHAR(255),
    data_type VARCHAR(50) NOT NULL, -- 'budget', 'personnel', 'contracts', 'organizational', 'strategic'
    data_subtype VARCHAR(50), -- 'line_items', 'org_chart', 'key_personnel', etc.
    
    -- Data Content
    data JSONB NOT NULL,
    data_schema_version VARCHAR(10) DEFAULT '1.0',
    
    -- Quality Metrics
    quality_score DECIMAL(5,2) NOT NULL CHECK (quality_score >= 0 AND quality_score <= 100),
    confidence_level VARCHAR(20), -- 'very_high', 'high', 'medium', 'low', 'very_low'
    data_completeness DECIMAL(5,2) CHECK (data_completeness >= 0 AND data_completeness <= 100),
    
    -- Source Information
    source_apis TEXT[] DEFAULT '{}',
    enrichment_job_id UUID REFERENCES data_enrichment_jobs(id),
    
    -- Timing and Expiration
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    
    -- Data Lineage
    processing_steps TEXT[],
    validation_results JSONB,
    
    -- Storage Optimization
    data_size_bytes INTEGER,
    compression_used BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT valid_data_type CHECK (data_type IN ('budget', 'personnel', 'contracts', 'organizational', 'strategic', 'general')),
    CONSTRAINT non_empty_data CHECK (jsonb_typeof(data) = 'object' AND data != '{}')
);

-- Create indexes for cache performance
CREATE INDEX idx_enriched_cache_agency_type ON enriched_data_cache(agency_code, data_type);
CREATE INDEX idx_enriched_cache_expires_at ON enriched_data_cache(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_enriched_cache_last_updated ON enriched_data_cache(last_updated DESC);
CREATE INDEX idx_enriched_cache_quality_score ON enriched_data_cache(quality_score DESC);

-- GIN index for JSONB data queries
CREATE INDEX idx_enriched_cache_data_gin ON enriched_data_cache USING GIN (data);

-- ==============================================================================
-- Data Source Health Table
-- Monitors the health and performance of external data sources
-- ==============================================================================

CREATE TABLE IF NOT EXISTS data_source_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source Identification
    source_name VARCHAR(100) NOT NULL, -- 'usaspending', 'treasury', 'fedscope', etc.
    source_url VARCHAR(500),
    source_type VARCHAR(50), -- 'api', 'website', 'file_download'
    
    -- Health Metrics
    status VARCHAR(20) NOT NULL DEFAULT 'unknown', -- 'healthy', 'degraded', 'down', 'unknown'
    response_time_ms INTEGER,
    success_rate DECIMAL(5,2), -- Percentage of successful requests
    error_rate DECIMAL(5,2),
    
    -- Rate Limiting Info
    rate_limit_per_minute INTEGER,
    current_usage_rate INTEGER,
    rate_limit_exceeded_count INTEGER DEFAULT 0,
    
    -- Monitoring Data
    last_check_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_successful_request TIMESTAMP WITH TIME ZONE,
    last_failed_request TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER DEFAULT 0,
    
    -- Error Details
    last_error_message TEXT,
    last_error_code VARCHAR(20),
    
    -- Performance Trends (JSON for flexibility)
    performance_history JSONB DEFAULT '[]',
    
    CONSTRAINT valid_source_status CHECK (status IN ('healthy', 'degraded', 'down', 'unknown')),
    CONSTRAINT valid_rates CHECK (success_rate >= 0 AND success_rate <= 100 AND error_rate >= 0 AND error_rate <= 100)
);

-- Index for monitoring queries
CREATE INDEX idx_data_source_health_name ON data_source_health(source_name);
CREATE INDEX idx_data_source_health_status ON data_source_health(status);
CREATE INDEX idx_data_source_health_last_check ON data_source_health(last_check_at DESC);

-- ==============================================================================
-- Enrichment Schedules Table
-- Manages automatic refresh schedules for agencies
-- ==============================================================================

CREATE TABLE IF NOT EXISTS enrichment_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Schedule Target
    agency_code VARCHAR(10) NOT NULL,
    data_types TEXT[] NOT NULL DEFAULT '{}',
    
    -- Schedule Configuration
    schedule_type VARCHAR(20) NOT NULL, -- 'cron', 'interval', 'trigger_based'
    cron_expression VARCHAR(100), -- For cron-based schedules
    interval_hours INTEGER, -- For interval-based schedules
    
    -- Schedule Status
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- Trigger Conditions (for trigger-based schedules)
    trigger_conditions JSONB, -- e.g., {"fiscal_year_change": true, "data_age_hours": 168}
    
    -- Configuration
    enrichment_depth VARCHAR(20) DEFAULT 'standard',
    priority VARCHAR(10) DEFAULT 'normal',
    
    -- Metadata
    created_by_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_schedule_type CHECK (schedule_type IN ('cron', 'interval', 'trigger_based')),
    CONSTRAINT valid_schedule_depth CHECK (enrichment_depth IN ('basic', 'standard', 'comprehensive')),
    CONSTRAINT valid_schedule_priority CHECK (priority IN ('low', 'normal', 'high'))
);

-- Index for schedule management
CREATE INDEX idx_enrichment_schedules_agency ON enrichment_schedules(agency_code);
CREATE INDEX idx_enrichment_schedules_next_run ON enrichment_schedules(next_run_at) WHERE is_active = TRUE;
CREATE INDEX idx_enrichment_schedules_active ON enrichment_schedules(is_active);

-- ==============================================================================
-- Data Quality Reports Table
-- Stores detailed data quality assessment reports
-- ==============================================================================

CREATE TABLE IF NOT EXISTS data_quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Report Context
    enrichment_job_id UUID REFERENCES data_enrichment_jobs(id),
    agency_code VARCHAR(10) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    
    -- Quality Metrics
    overall_score DECIMAL(5,2) NOT NULL CHECK (overall_score >= 0 AND overall_score <= 100),
    quality_level VARCHAR(20), -- 'excellent', 'good', 'fair', 'poor', 'critical'
    
    -- Validation Results by Category
    format_validation_score DECIMAL(5,2),
    completeness_validation_score DECIMAL(5,2),
    consistency_validation_score DECIMAL(5,2),
    accuracy_validation_score DECIMAL(5,2),
    timeliness_validation_score DECIMAL(5,2),
    
    -- Issue Counts
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    
    -- Detailed Report Data
    validation_details JSONB,
    improvement_recommendations TEXT[],
    
    -- Metadata
    total_records_validated INTEGER,
    validation_duration_ms INTEGER,
    validator_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_quality_level CHECK (quality_level IN ('excellent', 'good', 'fair', 'poor', 'critical'))
);

-- Index for quality tracking
CREATE INDEX idx_quality_reports_agency_type ON data_quality_reports(agency_code, data_type);
CREATE INDEX idx_quality_reports_score ON data_quality_reports(overall_score DESC);
CREATE INDEX idx_quality_reports_created_at ON data_quality_reports(created_at DESC);

-- ==============================================================================
-- Agency Enrichment Summary View
-- Convenient view for getting agency enrichment status
-- ==============================================================================

CREATE OR REPLACE VIEW agency_enrichment_summary AS
SELECT 
    j.agency_code,
    j.agency_name,
    
    -- Latest job info
    MAX(j.created_at) as last_enrichment_request,
    MAX(j.completed_at) as last_successful_enrichment,
    
    -- Current status
    (SELECT status FROM data_enrichment_jobs 
     WHERE agency_code = j.agency_code 
     ORDER BY created_at DESC LIMIT 1) as current_status,
    
    -- Data availability
    COUNT(DISTINCT c.data_type) as available_data_types,
    
    -- Quality metrics
    AVG(c.quality_score) as average_quality_score,
    MIN(c.expires_at) as next_expiration,
    
    -- Cache stats
    SUM(c.access_count) as total_access_count,
    MAX(c.last_accessed) as last_accessed
    
FROM data_enrichment_jobs j
LEFT JOIN enriched_data_cache c ON j.agency_code = c.agency_code
GROUP BY j.agency_code, j.agency_name;

-- ==============================================================================
-- Functions and Triggers
-- ==============================================================================

-- Function to update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for enriched_data_cache
CREATE TRIGGER update_enriched_data_cache_last_updated 
    BEFORE UPDATE ON enriched_data_cache 
    FOR EACH ROW EXECUTE FUNCTION update_last_updated_column();

-- Function to calculate job duration
CREATE OR REPLACE FUNCTION calculate_job_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.actual_duration_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for job duration calculation
CREATE TRIGGER calculate_enrichment_job_duration 
    BEFORE UPDATE ON data_enrichment_jobs 
    FOR EACH ROW EXECUTE FUNCTION calculate_job_duration();

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM enriched_data_cache 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- ==============================================================================
-- Initial Data and Configuration
-- ==============================================================================

-- Insert default data source health records
INSERT INTO data_source_health (source_name, source_url, source_type, status) VALUES
('usaspending', 'https://api.usaspending.gov/api/v2/', 'api', 'unknown'),
('treasury', 'https://api.fiscaldata.treasury.gov/services/api/v1/', 'api', 'unknown'),
('fedscope', 'https://www.fedscope.opm.gov/api/', 'api', 'unknown'),
('sam_gov', 'https://api.sam.gov/data-services/v1/', 'api', 'unknown'),
('performance_gov', 'https://www.performance.gov/api/', 'api', 'unknown'),
('gsa_api', 'https://api.gsa.gov/', 'api', 'unknown')
ON CONFLICT DO NOTHING;

-- Create indexes for JSONB data based on common query patterns
CREATE INDEX IF NOT EXISTS idx_enriched_cache_budget_data 
ON enriched_data_cache USING GIN ((data->'budget_line_items')) 
WHERE data_type = 'budget';

CREATE INDEX IF NOT EXISTS idx_enriched_cache_personnel_data 
ON enriched_data_cache USING GIN ((data->'personnel_list')) 
WHERE data_type = 'personnel';

-- ==============================================================================
-- Comments for Documentation
-- ==============================================================================

COMMENT ON TABLE data_enrichment_jobs IS 'Tracks all data enrichment operations and their execution status';
COMMENT ON TABLE enriched_data_cache IS 'Stores enriched government data with quality metrics and expiration';
COMMENT ON TABLE data_source_health IS 'Monitors health and performance of external government data sources';
COMMENT ON TABLE enrichment_schedules IS 'Manages automatic refresh schedules for agency data';
COMMENT ON TABLE data_quality_reports IS 'Stores detailed data quality assessment reports';

COMMENT ON COLUMN data_enrichment_jobs.data_types IS 'Array of data types to enrich: budget, personnel, contracts, organizational, strategic';
COMMENT ON COLUMN enriched_data_cache.data IS 'JSONB containing the actual enriched data structure';
COMMENT ON COLUMN enriched_data_cache.quality_score IS 'Overall quality score from 0-100 based on validation results';
COMMENT ON COLUMN data_source_health.performance_history IS 'JSON array of historical performance metrics';

-- ==============================================================================
-- Grants and Permissions (adjust based on your user setup)
-- ==============================================================================

-- Grant permissions to application user (replace 'app_user' with your actual user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_user;