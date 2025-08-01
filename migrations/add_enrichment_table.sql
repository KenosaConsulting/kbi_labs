-- Add company enrichment table
CREATE TABLE IF NOT EXISTS company_enrichment (
    uei TEXT PRIMARY KEY,
    enrichment_data JSON NOT NULL,
    enrichment_score REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uei) REFERENCES companies(uei)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enrichment_score 
ON company_enrichment(enrichment_score DESC);

CREATE INDEX IF NOT EXISTS idx_enrichment_updated 
ON company_enrichment(last_updated DESC);

-- Add enrichment tracking to companies table (if columns don't exist)
-- Note: SQLite doesn't support IF NOT EXISTS for columns, so these might fail if already exist
-- That's okay, the error will be ignored
ALTER TABLE companies ADD COLUMN enrichment_status TEXT DEFAULT 'pending';
ALTER TABLE companies ADD COLUMN last_enriched TIMESTAMP;
