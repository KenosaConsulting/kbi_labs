-- KBI Labs Complete Database Schema
-- Stores all enriched data from multiple sources

-- Main enriched companies table
CREATE TABLE IF NOT EXISTS enriched_companies_full (
    -- Primary identifier
    uei VARCHAR(50) PRIMARY KEY,
    
    -- Basic company information (from DSBS)
    organization_name VARCHAR(500) NOT NULL,
    primary_naics VARCHAR(10),
    state VARCHAR(50),
    city VARCHAR(100),
    zipcode VARCHAR(10),
    website VARCHAR(500),
    phone_number VARCHAR(50),
    email VARCHAR(255),
    legal_structure VARCHAR(100),
    active_sba_certifications TEXT,
    capabilities_narrative TEXT,
    capabilities_statement_link VARCHAR(500),
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    job_title VARCHAR(255),
    
    -- SAM.gov enrichment
    sam_registration_status VARCHAR(50),
    sam_registration_date DATE,
    sam_expiration_date DATE,
    cage_code VARCHAR(20),
    duns_number VARCHAR(20),
    naics_codes JSON,
    business_types JSON,
    socio_economic_types JSON,
    federal_contract_vehicles JSON,
    past_performance_rating JSON,
    
    -- Federal contracting history
    federal_contracts_count INTEGER DEFAULT 0,
    federal_contracts_value DECIMAL(20,2) DEFAULT 0,
    latest_contract_date DATE,
    largest_contract_value DECIMAL(20,2),
    primary_contract_naics VARCHAR(10),
    contract_set_asides JSON,
    
    -- Census economic data
    industry_employment_state INTEGER,
    industry_payroll_state DECIMAL(20,2),
    industry_establishments_state INTEGER,
    zip_population INTEGER,
    zip_median_income DECIMAL(12,2),
    zip_business_density FLOAT,
    county_gdp DECIMAL(20,2),
    
    -- Patent data (USPTO)
    patent_count INTEGER DEFAULT 0,
    patents JSON,
    latest_patent_date DATE,
    patent_categories JSON,
    patent_citations_received INTEGER DEFAULT 0,
    patent_quality_score FLOAT,
    
    -- NSF grant data
    nsf_grant_count INTEGER DEFAULT 0,
    nsf_total_funding DECIMAL(20,2) DEFAULT 0,
    nsf_grants JSON,
    nsf_latest_grant_date DATE,
    nsf_research_areas JSON,
    sbir_sttr_awards INTEGER DEFAULT 0,
    sbir_sttr_funding DECIMAL(20,2) DEFAULT 0,
    
    -- FRED economic indicators
    state_unemployment_rate FLOAT,
    state_unemployment_date DATE,
    state_gdp_growth_rate FLOAT,
    state_business_formation_rate FLOAT,
    regional_economic_index FLOAT,
    
    -- Calculated scores and grades
    pe_investment_score FLOAT,
    business_health_grade VARCHAR(2),
    innovation_score FLOAT,
    growth_potential_score FLOAT,
    market_position_score FLOAT,
    financial_stability_score FLOAT,
    acquisition_readiness_score FLOAT,
    
    -- Risk assessments
    operational_risk_score FLOAT,
    financial_risk_score FLOAT,
    compliance_risk_score FLOAT,
    succession_risk_score FLOAT,
    overall_risk_rating VARCHAR(20),
    
    -- Market analysis
    market_size_estimate DECIMAL(20,2),
    market_growth_rate FLOAT,
    competitive_density_score FLOAT,
    market_share_potential FLOAT,
    expansion_opportunities JSON,
    
    -- Digital presence analysis
    website_quality_score FLOAT,
    seo_ranking_score FLOAT,
    social_media_presence JSON,
    online_reviews_count INTEGER,
    average_rating FLOAT,
    digital_maturity_level VARCHAR(20),
    
    -- Peer comparison
    industry_percentile_score FLOAT,
    size_percentile_score FLOAT,
    growth_percentile_score FLOAT,
    innovation_percentile_score FLOAT,
    
    -- Recommendations and insights
    key_strengths JSON,
    improvement_areas JSON,
    investment_thesis TEXT,
    recommended_actions JSON,
    
    -- Metadata
    enrichment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enrichment_version VARCHAR(10) DEFAULT '2.0',
    data_completeness_score FLOAT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    scoring_metadata JSON,
    data_sources_used JSON,
    
    -- Indexes for performance
    INDEX idx_pe_score (pe_investment_score DESC),
    INDEX idx_health_grade (business_health_grade),
    INDEX idx_state (state),
    INDEX idx_naics (primary_naics),
    INDEX idx_city_state (city, state),
    INDEX idx_sam_status (sam_registration_status),
    INDEX idx_patent_count (patent_count DESC),
    INDEX idx_nsf_funding (nsf_total_funding DESC),
    INDEX idx_enrichment_date (enrichment_timestamp)
);

-- Summary statistics table (updated after each batch)
CREATE TABLE IF NOT EXISTS enrichment_statistics (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_companies INTEGER,
    companies_enriched INTEGER,
    avg_pe_score FLOAT,
    median_pe_score FLOAT,
    grade_distribution JSON,
    top_industries JSON,
    top_states JSON,
    sam_registered_count INTEGER,
    total_patents INTEGER,
    total_nsf_grants INTEGER,
    total_nsf_funding DECIMAL(20,2),
    avg_enrichment_time_seconds FLOAT,
    data_quality_metrics JSON
);

-- Top opportunities view for quick access
CREATE VIEW top_investment_opportunities AS
SELECT 
    uei,
    organization_name,
    city,
    state,
    primary_naics,
    pe_investment_score,
    business_health_grade,
    patent_count,
    nsf_total_funding,
    federal_contracts_value,
    growth_potential_score,
    website
FROM enriched_companies_full
WHERE pe_investment_score >= 70
    AND business_health_grade IN ('A', 'B')
ORDER BY pe_investment_score DESC;

-- Industry analysis view
CREATE VIEW industry_analysis AS
SELECT 
    SUBSTRING(primary_naics, 1, 2) as naics_sector,
    COUNT(*) as company_count,
    AVG(pe_investment_score) as avg_pe_score,
    SUM(patent_count) as total_patents,
    SUM(nsf_total_funding) as total_nsf_funding,
    SUM(federal_contracts_value) as total_federal_contracts,
    AVG(growth_potential_score) as avg_growth_potential
FROM enriched_companies_full
WHERE primary_naics IS NOT NULL
GROUP BY SUBSTRING(primary_naics, 1, 2)
ORDER BY avg_pe_score DESC;

-- Geographic analysis view
CREATE VIEW geographic_analysis AS
SELECT 
    state,
    city,
    COUNT(*) as company_count,
    AVG(pe_investment_score) as avg_pe_score,
    SUM(CASE WHEN business_health_grade IN ('A', 'B') THEN 1 ELSE 0 END) as high_grade_companies,
    AVG(market_size_estimate) as avg_market_size,
    AVG(state_unemployment_rate) as unemployment_rate,
    SUM(patent_count) as total_patents
FROM enriched_companies_full
WHERE state IS NOT NULL
GROUP BY state, city
HAVING company_count >= 5
ORDER BY avg_pe_score DESC;

-- API access log for tracking usage
CREATE TABLE IF NOT EXISTS api_access_log (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    api_name VARCHAR(50),
    endpoint VARCHAR(255),
    uei VARCHAR(50),
    status_code INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_api_timestamp (api_name, timestamp)
);

-- User activity tracking for the UI
CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(100),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_timestamp (user_id, timestamp)
);

-- Saved searches and alerts
CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(100),
    search_name VARCHAR(255),
    search_criteria JSON,
    alert_enabled BOOLEAN DEFAULT FALSE,
    alert_frequency VARCHAR(20),
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_searches (user_id)
);

-- Export history
CREATE TABLE IF NOT EXISTS export_history (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(100),
    export_type VARCHAR(50),
    filters_applied JSON,
    company_count INTEGER,
    file_format VARCHAR(20),
    file_size_bytes BIGINT,
    download_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX idx_user_exports (user_id, created_at)
);
# (Copy all the CREATE TABLE statements)
