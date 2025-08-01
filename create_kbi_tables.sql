-- Companies table with all fields
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    dba_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    country VARCHAR(100) DEFAULT 'USA',
    
    -- Contact information
    website VARCHAR(500),
    phone_number VARCHAR(50),
    email VARCHAR(255),
    
    -- Financial metrics
    annual_revenue DECIMAL(15,2),
    federal_contracts_value DECIMAL(15,2),
    grants_received DECIMAL(15,2),
    
    -- Scores
    pe_investment_score FLOAT,
    business_health_grade VARCHAR(2),
    innovation_score FLOAT,
    growth_potential_score FLOAT,
    market_position_score FLOAT,
    
    -- Certifications
    cage_code VARCHAR(10),
    sam_status VARCHAR(20),
    active_sba_certifications TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_enriched_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_companies_state ON companies(state);
CREATE INDEX idx_companies_pe_score ON companies(pe_investment_score);
CREATE INDEX idx_companies_uei ON companies(uei);

-- Enrichment history table
CREATE TABLE IF NOT EXISTS enrichment_history (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (uei) REFERENCES companies(uei)
);

-- ML predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) REFERENCES companies(uei),
    prediction_type VARCHAR(50),
    prediction_value JSONB,
    confidence FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    entity_id VARCHAR(50),
    user_id VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create a view for company analytics
CREATE OR REPLACE VIEW company_analytics AS
SELECT 
    c.*,
    COUNT(DISTINCT p.id) as prediction_count,
    COUNT(DISTINCT eh.id) as enrichment_count,
    MAX(eh.created_at) as last_enrichment_date
FROM companies c
LEFT JOIN predictions p ON c.uei = p.uei
LEFT JOIN enrichment_history eh ON c.uei = eh.uei
GROUP BY c.id;

-- Insert some test data
INSERT INTO companies (uei, organization_name, city, state, pe_investment_score, business_health_grade)
VALUES 
    ('TEST123456789', 'Test Corp Alpha', 'San Francisco', 'CA', 85.5, 'A'),
    ('TEST987654321', 'Test Corp Beta', 'New York', 'NY', 92.3, 'A+')
ON CONFLICT (uei) DO NOTHING;
