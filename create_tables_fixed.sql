-- Create companies table
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2),
    pe_investment_score FLOAT,
    business_health_grade VARCHAR(2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create other tables
CREATE TABLE IF NOT EXISTS enrichment_history (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12),
    prediction_type VARCHAR(50),
    prediction_value JSONB,
    confidence FLOAT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    entity_id VARCHAR(50),
    user_id VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test data
INSERT INTO companies (uei, organization_name, city, state, pe_investment_score, business_health_grade)
VALUES 
    ('TEST123456789', 'Test Corp Alpha', 'San Francisco', 'CA', 85.5, 'A'),
    ('TEST987654321', 'Test Corp Beta', 'New York', 'NY', 92.3, 'A+')
ON CONFLICT (uei) DO NOTHING;
