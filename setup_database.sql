-- Create the database and user
CREATE DATABASE kbi_enriched;
CREATE USER ubuntu WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE kbi_enriched TO ubuntu;

-- Connect to the new database
\c kbi_enriched

-- Create the master enriched companies table
CREATE TABLE enriched_companies (
    -- Core identifiers
    uei VARCHAR(50) PRIMARY KEY,
    organization_name VARCHAR(255),
    primary_naics VARCHAR(10),
    state VARCHAR(2),
    city VARCHAR(100),
    zipcode VARCHAR(10),
    website VARCHAR(255),
    phone_number VARCHAR(20),
    
    -- Enrichment tracking
    last_enriched TIMESTAMP,
    enrichment_version VARCHAR(10),
    enrichment_status JSONB,
    
    -- Government data
    sam_registration_status VARCHAR(50),
    cage_code VARCHAR(20),
    federal_contracts_count INTEGER DEFAULT 0,
    federal_contracts_value DECIMAL(15,2) DEFAULT 0,
    latest_contract_date DATE,
    set_aside_types JSONB,
    
    -- Economic indicators
    economic_indicators JSONB,
    market_fragmentation_score DECIMAL(5,2),
    industry_concentration DECIMAL(5,2),
    
    -- Innovation metrics
    patent_count INTEGER DEFAULT 0,
    patent_citations INTEGER DEFAULT 0,
    r_and_d_intensity DECIMAL(5,2),
    innovation_score DECIMAL(5,2),
    nsf_grants JSONB,
    
    -- Digital presence
    has_website BOOLEAN DEFAULT FALSE,
    website_quality_score DECIMAL(5,2),
    social_media_presence JSONB,
    online_reviews_count INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    
    -- Risk scores
    succession_risk_score DECIMAL(5,2),
    financial_risk_score DECIMAL(5,2),
    operational_risk_score DECIMAL(5,2),
    overall_risk_rating VARCHAR(20),
    
    -- Growth indicators
    growth_potential_score DECIMAL(5,2),
    acquisition_readiness DECIMAL(5,2),
    market_expansion_opportunities JSONB,
    
    -- Calculated insights
    pe_investment_score DECIMAL(5,2),
    business_health_grade VARCHAR(2),
    peer_percentile DECIMAL(5,2),
    key_recommendations JSONB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_enriched_companies_state ON enriched_companies(state);
CREATE INDEX idx_enriched_companies_naics ON enriched_companies(primary_naics);
CREATE INDEX idx_enriched_companies_pe_score ON enriched_companies(pe_investment_score);
CREATE INDEX idx_enriched_companies_health_grade ON enriched_companies(business_health_grade);

-- Grant permissions to ubuntu user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ubuntu;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ubuntu;
