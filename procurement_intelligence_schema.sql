-- Procurement Intelligence Platform Database Schema
-- Extends existing KBI Labs schema with procurement intelligence capabilities

-- Data Sources Registry
CREATE TABLE IF NOT EXISTS procurement_data_sources (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) UNIQUE NOT NULL,
    source_name VARCHAR(500) NOT NULL,
    source_url VARCHAR(1000) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    data_format VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 1,
    refresh_interval_hours INTEGER DEFAULT 24,
    requires_auth BOOLEAN DEFAULT FALSE,
    api_key_env_var VARCHAR(100),
    rate_limit_per_hour INTEGER DEFAULT 100,
    extraction_config JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Procurement Opportunities
CREATE TABLE IF NOT EXISTS procurement_opportunities (
    id SERIAL PRIMARY KEY,
    notice_id VARCHAR(200) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    department VARCHAR(500),
    sub_agency VARCHAR(500),
    office VARCHAR(500),
    posted_date DATE,
    response_deadline DATE,
    award_date DATE,
    estimated_value DECIMAL(20,2),
    awarded_amount DECIMAL(20,2),
    naics_code VARCHAR(10),
    set_aside_type VARCHAR(200),
    place_of_performance_state VARCHAR(10),
    contract_type VARCHAR(100),
    competition_type VARCHAR(100),
    
    -- Classification and Analysis
    opportunity_type VARCHAR(100),
    complexity_score DECIMAL(5,2),
    competition_level VARCHAR(50),
    small_business_suitable BOOLEAN DEFAULT TRUE,
    
    -- Source Information
    source_id VARCHAR(100) NOT NULL,
    source_url VARCHAR(1000),
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Full text search
    search_vector tsvector,
    
    FOREIGN KEY (source_id) REFERENCES procurement_data_sources(source_id)
);

-- Create full-text search index
CREATE INDEX IF NOT EXISTS idx_opportunities_search ON procurement_opportunities USING GIN(search_vector);

-- Contract Awards History
CREATE TABLE IF NOT EXISTS contract_awards (
    id SERIAL PRIMARY KEY,
    award_id VARCHAR(200) NOT NULL,
    piid VARCHAR(200),
    recipient_uei VARCHAR(50),
    recipient_name VARCHAR(500),
    recipient_duns VARCHAR(20),
    award_amount DECIMAL(20,2),
    award_date DATE,
    start_date DATE,
    end_date DATE,
    awarding_agency VARCHAR(500),
    funding_agency VARCHAR(500),
    award_type VARCHAR(100),
    naics_code VARCHAR(10),
    place_of_performance_state VARCHAR(10),
    
    -- Contract details
    contract_description TEXT,
    competition_type VARCHAR(100),
    set_aside_type VARCHAR(200),
    number_of_offers_received INTEGER,
    
    -- Source Information
    source_id VARCHAR(100) NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_id) REFERENCES procurement_data_sources(source_id),
    FOREIGN KEY (recipient_uei) REFERENCES enriched_companies_full(uei)
);

-- Budget Forecasts
CREATE TABLE IF NOT EXISTS budget_forecasts (
    id SERIAL PRIMARY KEY,
    agency VARCHAR(500) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    naics_code VARCHAR(10),
    program_name VARCHAR(500),
    forecasted_amount DECIMAL(20,2),
    forecast_confidence VARCHAR(50),
    procurement_method VARCHAR(200),
    anticipated_solicitation_date DATE,
    contract_type VARCHAR(100),
    set_aside_type VARCHAR(200),
    
    -- Forecast details
    description TEXT,
    requirements_summary TEXT,
    place_of_performance VARCHAR(500),
    
    -- Source Information
    source_id VARCHAR(100) NOT NULL,
    forecast_date DATE,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_id) REFERENCES procurement_data_sources(source_id)
);

-- Intelligence Reports
CREATE TABLE IF NOT EXISTS intelligence_reports (
    id SERIAL PRIMARY KEY,
    report_id VARCHAR(200) UNIQUE NOT NULL,
    company_uei VARCHAR(50) NOT NULL,
    opportunity_id VARCHAR(200),
    
    -- Analysis Results
    win_probability DECIMAL(5,4),
    confidence_score DECIMAL(5,4),
    opportunity_assessment JSONB,
    competitive_landscape JSONB,
    market_intelligence JSONB,
    historical_context JSONB,
    
    -- Recommendations
    recommended_actions JSONB,
    teaming_recommendations JSONB,
    proposal_strategy JSONB,
    risk_assessment JSONB,
    
    -- Metadata
    analysis_depth VARCHAR(50),
    data_sources JSONB,
    analysis_duration_seconds DECIMAL(10,2),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    FOREIGN KEY (company_uei) REFERENCES enriched_companies_full(uei)
);

-- Living Library - Knowledge Base
CREATE TABLE IF NOT EXISTS knowledge_base_articles (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(200) UNIQUE NOT NULL,
    title VARCHAR(1000) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(200) NOT NULL,
    subcategory VARCHAR(200),
    
    -- Classification
    article_type VARCHAR(100), -- guide, template, example, analysis
    complexity_level VARCHAR(50), -- basic, intermediate, advanced
    agency_focus VARCHAR(500),
    naics_focus VARCHAR(50),
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    related_articles JSONB DEFAULT '[]',
    source_documents JSONB DEFAULT '[]',
    
    -- Content Management
    author VARCHAR(200),
    reviewed_by VARCHAR(200),
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    
    -- Full text search
    search_vector tsvector
);

-- Create full-text search index for knowledge base
CREATE INDEX IF NOT EXISTS idx_knowledge_search ON knowledge_base_articles USING GIN(search_vector);

-- Proposal Templates
CREATE TABLE IF NOT EXISTS proposal_templates (
    id SERIAL PRIMARY KEY,
    template_id VARCHAR(200) UNIQUE NOT NULL,
    template_name VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Template Classification
    template_type VARCHAR(100), -- technical_approach, past_performance, pricing, etc.
    agency_type VARCHAR(200),
    contract_type VARCHAR(100),
    naics_codes JSONB DEFAULT '[]',
    
    -- Template Content
    template_content TEXT NOT NULL,
    template_structure JSONB,
    required_sections JSONB DEFAULT '[]',
    optional_sections JSONB DEFAULT '[]',
    
    -- Usage Metrics
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4),
    last_used TIMESTAMP,
    
    -- Metadata
    created_by VARCHAR(200),
    template_version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Best Practices Repository
CREATE TABLE IF NOT EXISTS best_practices (
    id SERIAL PRIMARY KEY,
    practice_id VARCHAR(200) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    
    -- Classification
    practice_category VARCHAR(200), -- proposal_writing, teaming, compliance, etc.
    practice_type VARCHAR(100), -- do, dont, tip, warning
    applicability VARCHAR(200), -- universal, agency_specific, naics_specific
    
    -- Context
    applicable_agencies JSONB DEFAULT '[]',
    applicable_naics JSONB DEFAULT '[]',
    contract_types JSONB DEFAULT '[]',
    
    -- Content
    detailed_guidance TEXT,
    examples JSONB DEFAULT '[]',
    related_regulations JSONB DEFAULT '[]',
    
    -- Evidence and Results
    success_stories JSONB DEFAULT '[]',
    supporting_data JSONB DEFAULT '{}',
    effectiveness_score DECIMAL(5,4),
    
    -- Metadata
    created_by VARCHAR(200),
    validated_by VARCHAR(200),
    validation_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competitive Intelligence
CREATE TABLE IF NOT EXISTS competitive_intelligence (
    id SERIAL PRIMARY KEY,
    competitor_uei VARCHAR(50) NOT NULL,
    competitor_name VARCHAR(500) NOT NULL,
    
    -- Competitive Profile
    primary_naics_codes JSONB DEFAULT '[]',
    geographic_focus JSONB DEFAULT '[]',
    typical_contract_size_range VARCHAR(100),
    specializations JSONB DEFAULT '[]',
    
    -- Performance Metrics
    total_contracts_won INTEGER DEFAULT 0,
    total_contract_value DECIMAL(20,2) DEFAULT 0,
    average_contract_value DECIMAL(20,2),
    win_rate DECIMAL(5,4),
    
    -- Agency Relationships
    preferred_agencies JSONB DEFAULT '[]',
    agency_success_rates JSONB DEFAULT '{}',
    
    -- Competitive Advantages
    key_differentiators JSONB DEFAULT '[]',
    typical_teaming_partners JSONB DEFAULT '[]',
    pricing_patterns JSONB DEFAULT '{}',
    
    -- Intelligence Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_completeness_score DECIMAL(5,4),
    intelligence_confidence DECIMAL(5,4),
    
    FOREIGN KEY (competitor_uei) REFERENCES enriched_companies_full(uei)
);

-- SMB Assistance Tracking
CREATE TABLE IF NOT EXISTS smb_assistance_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(200) UNIQUE NOT NULL,
    company_uei VARCHAR(50) NOT NULL,
    
    -- Session Details
    assistance_type VARCHAR(200), -- opportunity_analysis, proposal_development, compliance_check
    session_status VARCHAR(100), -- active, completed, abandoned
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Context
    opportunity_context JSONB,
    user_goals JSONB DEFAULT '[]',
    challenges_identified JSONB DEFAULT '[]',
    
    -- Assistance Provided
    recommendations_given JSONB DEFAULT '[]',
    resources_suggested JSONB DEFAULT '[]',
    actions_completed JSONB DEFAULT '[]',
    
    -- Outcomes
    session_satisfaction INTEGER, -- 1-5 rating
    goals_achieved JSONB DEFAULT '[]',
    follow_up_needed BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (company_uei) REFERENCES enriched_companies_full(uei)
);

-- Data Ingestion Logs
CREATE TABLE IF NOT EXISTS data_ingestion_logs (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL,
    ingestion_run_id VARCHAR(200) NOT NULL,
    
    -- Run Details
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(100) NOT NULL, -- running, completed, failed, partial
    
    -- Metrics
    records_processed INTEGER DEFAULT 0,
    records_successful INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- Error Information
    error_summary TEXT,
    detailed_errors JSONB DEFAULT '[]',
    
    -- Performance
    processing_duration_seconds DECIMAL(10,2),
    records_per_second DECIMAL(10,2),
    
    FOREIGN KEY (source_id) REFERENCES procurement_data_sources(source_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_opportunities_naics ON procurement_opportunities(naics_code);
CREATE INDEX IF NOT EXISTS idx_opportunities_agency ON procurement_opportunities(department);
CREATE INDEX IF NOT EXISTS idx_opportunities_posted_date ON procurement_opportunities(posted_date);
CREATE INDEX IF NOT EXISTS idx_opportunities_deadline ON procurement_opportunities(response_deadline);

CREATE INDEX IF NOT EXISTS idx_contracts_recipient ON contract_awards(recipient_uei);
CREATE INDEX IF NOT EXISTS idx_contracts_agency ON contract_awards(awarding_agency);
CREATE INDEX IF NOT EXISTS idx_contracts_naics ON contract_awards(naics_code);
CREATE INDEX IF NOT EXISTS idx_contracts_award_date ON contract_awards(award_date);

CREATE INDEX IF NOT EXISTS idx_forecasts_agency ON budget_forecasts(agency);
CREATE INDEX IF NOT EXISTS idx_forecasts_fy ON budget_forecasts(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_forecasts_naics ON budget_forecasts(naics_code);

CREATE INDEX IF NOT EXISTS idx_intelligence_company ON intelligence_reports(company_uei);
CREATE INDEX IF NOT EXISTS idx_intelligence_generated ON intelligence_reports(generated_at);

CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base_articles(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_base_articles(article_type);

-- Update functions for maintaining search vectors
CREATE OR REPLACE FUNCTION update_opportunity_search_vector() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.department, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.sub_agency, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_knowledge_search_vector() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.category, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
DROP TRIGGER IF EXISTS opportunity_search_update ON procurement_opportunities;
CREATE TRIGGER opportunity_search_update
    BEFORE INSERT OR UPDATE ON procurement_opportunities
    FOR EACH ROW EXECUTE FUNCTION update_opportunity_search_vector();

DROP TRIGGER IF EXISTS knowledge_search_update ON knowledge_base_articles;
CREATE TRIGGER knowledge_search_update
    BEFORE INSERT OR UPDATE ON knowledge_base_articles
    FOR EACH ROW EXECUTE FUNCTION update_knowledge_search_vector();

-- Insert initial data source configurations
INSERT INTO procurement_data_sources (source_id, source_name, source_url, source_type, data_format, priority, refresh_interval_hours, requires_auth, api_key_env_var, rate_limit_per_hour) VALUES
    ('sam_gov', 'System for Award Management', 'https://sam.gov/api/prod/', 'contract_data', 'json_api', 1, 6, true, 'SAM_GOV_API_KEY', 1000),
    ('fpds_ng', 'Federal Procurement Data System - Next Generation', 'https://www.fpds.gov/', 'contract_data', 'xml_api', 1, 24, false, null, 200),
    ('usaspending', 'USAspending.gov', 'https://api.usaspending.gov/api/', 'contract_data', 'json_api', 1, 24, false, null, 500),
    ('fedconnect', 'FedConnect', 'https://www.fedconnect.net/', 'opportunity', 'html_scraping', 1, 4, false, null, 100),
    ('dsbs', 'Dynamic Small Business Search', 'https://dsbs.sba.gov/', 'small_business', 'html_scraping', 1, 24, false, null, 100),
    ('sbir_sttr', 'SBIR/STTR Portal', 'https://www.sbir.gov/', 'small_business', 'html_scraping', 1, 24, false, null, 100),
    ('far', 'Federal Acquisition Regulation', 'https://www.acquisition.gov/far/', 'regulatory', 'html_scraping', 2, 168, false, null, 20),
    ('dfars', 'Defense Federal Acquisition Regulations', 'https://www.acquisition.gov/dfars/', 'regulatory', 'html_scraping', 2, 168, false, null, 20)
ON CONFLICT (source_id) DO NOTHING;

-- Insert sample knowledge base articles
INSERT INTO knowledge_base_articles (article_id, title, content, category, subcategory, article_type, complexity_level) VALUES
    ('kb_001', 'Understanding NAICS Codes for Government Contracting', 'NAICS (North American Industry Classification System) codes are critical for government contracting...', 'Fundamentals', 'Classification Systems', 'guide', 'basic'),
    ('kb_002', 'Small Business Set-Aside Types Explained', 'Government contracting includes various set-aside programs designed to provide opportunities for small businesses...', 'Set-Asides', 'Small Business Programs', 'guide', 'basic'),
    ('kb_003', 'Writing Effective Technical Approaches', 'The technical approach is often the most critical section of your proposal...', 'Proposal Writing', 'Technical Sections', 'guide', 'intermediate'),
    ('kb_004', 'Past Performance Examples and Best Practices', 'Past performance is a key evaluation criterion in government contracting...', 'Proposal Writing', 'Past Performance', 'guide', 'intermediate')
ON CONFLICT (article_id) DO NOTHING;

-- Insert sample best practices
INSERT INTO best_practices (practice_id, title, description, practice_category, practice_type, applicability) VALUES
    ('bp_001', 'Always Respond to RFI Before RFP', 'Participating in Request for Information (RFI) processes helps you understand requirements and influence the final RFP.', 'opportunity_pursuit', 'tip', 'universal'),
    ('bp_002', 'Build Relationships Before You Need Them', 'Successful government contractors invest in relationship building during non-competitive periods.', 'business_development', 'tip', 'universal'),
    ('bp_003', 'Never Submit Without Compliance Matrix', 'Always include a compliance matrix that shows exactly where you address each requirement.', 'proposal_writing', 'do', 'universal'),
    ('bp_004', 'Avoid Generic Boilerplate Language', 'Generic, non-specific content is easily identified by evaluators and hurts your score.', 'proposal_writing', 'dont', 'universal')
ON CONFLICT (practice_id) DO NOTHING;