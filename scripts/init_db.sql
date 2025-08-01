-- KBI Labs PostgreSQL Initialization Script

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS ml_features;

-- Create main companies table
CREATE TABLE IF NOT EXISTS public.companies (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    dba_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    country VARCHAR(100) DEFAULT 'USA',
    
    -- Financial metrics
    annual_revenue DECIMAL(15,2),
    federal_contracts_value DECIMAL(15,2),
    grants_received DECIMAL(15,2),
    
    -- Scores
    pe_investment_score FLOAT,
    business_health_grade VARCHAR(2),
    innovation_score FLOAT,
    growth_potential_score FLOAT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_enriched_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_companies_state ON companies(state);
CREATE INDEX IF NOT EXISTS idx_companies_pe_score ON companies(pe_investment_score);
CREATE INDEX IF NOT EXISTS idx_companies_health_grade ON companies(business_health_grade);

-- Create enrichment tracking table
CREATE TABLE IF NOT EXISTS public.enrichment_history (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (uei) REFERENCES companies(uei)
);

CREATE INDEX IF NOT EXISTS idx_enrichment_uei_source ON enrichment_history(uei, source);
CREATE INDEX IF NOT EXISTS idx_enrichment_created_at ON enrichment_history(created_at);

-- Create enriched companies table for streaming pipeline
CREATE TABLE IF NOT EXISTS public.enriched_companies (
    uei VARCHAR(12) PRIMARY KEY,
    data JSONB NOT NULL,
    enrichment_timestamp TIMESTAMP NOT NULL,
    data_quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO kbi_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO kbi_user;
GRANT ALL ON SCHEMA analytics TO kbi_user;
GRANT ALL ON SCHEMA staging TO kbi_user;
GRANT ALL ON SCHEMA ml_features TO kbi_user;
