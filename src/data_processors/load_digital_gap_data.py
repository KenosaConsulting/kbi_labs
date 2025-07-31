# src/data_processors/load_digital_gap_data.py
"""
Load Digital Gap Analysis data into PostgreSQL database
Creates new tables for the opportunity intelligence platform
"""

import pandas as pd
import asyncpg
import asyncio
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DigitalGapLoader:
    def __init__(self, db_url: str = "postgresql://kbi_user:secure_password@localhost/kbi_labs"):
        self.db_url = db_url
        
    async def create_tables(self):
        """Create tables for digital gap analysis data"""
        conn = await asyncpg.connect(self.db_url)
        
        # Create digital_gap_companies table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS digital_gap_companies (
                id SERIAL PRIMARY KEY,
                organization_name VARCHAR(500) NOT NULL,
                city VARCHAR(100),
                state VARCHAR(50),
                zipcode VARCHAR(20),
                email VARCHAR(255),
                phone_number VARCHAR(50),
                website VARCHAR(500),
                uei VARCHAR(50),
                primary_naics_code INTEGER,
                legal_structure VARCHAR(100),
                active_sba_certifications TEXT,
                
                -- Digital Gap Analysis Fields
                has_website BOOLEAN DEFAULT FALSE,
                website_opportunity BOOLEAN DEFAULT FALSE,
                opportunity_score INTEGER DEFAULT 0,
                opportunity_level VARCHAR(20),
                
                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # Create indexes for fast queries
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_state ON digital_gap_companies(state);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_city ON digital_gap_companies(city);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_opportunity_level ON digital_gap_companies(opportunity_level);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_website_opportunity ON digital_gap_companies(website_opportunity);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_opportunity_score ON digital_gap_companies(opportunity_score);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_naics ON digital_gap_companies(primary_naics_code);')
        
        # Create summary statistics table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS digital_gap_stats (
                id SERIAL PRIMARY KEY,
                stat_type VARCHAR(50) NOT NULL,
                stat_key VARCHAR(100) NOT NULL,
                stat_value INTEGER NOT NULL,
                percentage DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stat_type, stat_key)
            );
        ''')
        
        await conn.close()
        logger.info("✅ Database tables created successfully")
    
    async def load_companies_data(self, csv_file_path: str):
        """Load companies data from CSV into database"""
        logger.info(f"Loading data from {csv_file_path}")
        
        # Read CSV with proper data types
        df = pd.read_csv(csv_file_path, low_memory=False)
        
        # Clean and prepare data
        df = df.fillna('')  # Replace NaN with empty strings
        
        # Convert phone numbers to strings
        df['Phone number'] = df['Phone number'].astype(str).replace('nan', '')
        
        # Clean zipcode
        df['Zipcode'] = df['Zipcode'].astype(str).replace('nan', '')
        
        # Ensure boolean fields
        df['has_website'] = df['has_website'].astype(bool)
        df['website_opportunity'] = df['website_opportunity'].astype(bool)
        
        logger.info(f"Prepared {len(df):,} companies for database insertion")
        
        conn = await asyncpg.connect(self.db_url)
        
        # Clear existing data
        await conn.execute('DELETE FROM digital_gap_companies;')
        logger.info("Cleared existing data")
        
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            record = (
                row['Organization Name'][:500],  # Truncate if too long
                row['City'][:100] if row['City'] else '',
                row['State'][:50] if row['State'] else '',
                row['Zipcode'][:20] if row['Zipcode'] else '',
                row['Email'][:255] if row['Email'] else '',
                row['Phone number'][:50] if row['Phone number'] else '',
                row['Website'][:500] if row['Website'] else '',
                row['UEI (Unique Entity Identifier)'][:50] if row['UEI (Unique Entity Identifier)'] else '',
                int(row['Primary NAICS code']) if pd.notna(row['Primary NAICS code']) else None,
                row['Legal structure'][:100] if row['Legal structure'] else '',
                row['Active SBA certifications'] if row['Active SBA certifications'] else '',
                bool(row['has_website']),
                bool(row['website_opportunity']),
                int(row['opportunity_score']),
                row['opportunity_level'][:20] if row['opportunity_level'] else 'NONE'
            )
            records.append(record)
        
        # Batch insert
        insert_query = '''
            INSERT INTO digital_gap_companies (
                organization_name, city, state, zipcode, email, phone_number,
                website, uei, primary_naics_code, legal_structure, 
                active_sba_certifications, has_website, website_opportunity,
                opportunity_score, opportunity_level
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        '''
        
        await conn.executemany(insert_query, records)
        await conn.close()
        
        logger.info(f"✅ Successfully loaded {len(records):,} companies into database")
    
    async def generate_statistics(self):
        """Generate summary statistics for the dashboard"""
        conn = await asyncpg.connect(self.db_url)
        
        # Clear existing stats
        await conn.execute('DELETE FROM digital_gap_stats;')
        
        # Generate various statistics
        stats_queries = [
            # Overall stats
            ("total", "companies", "SELECT COUNT(*) FROM digital_gap_companies"),
            ("total", "without_websites", "SELECT COUNT(*) FROM digital_gap_companies WHERE website_opportunity = true"),
            
            # Opportunity level breakdown
            ("opportunity", "high", "SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'HIGH'"),
            ("opportunity", "medium", "SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'MEDIUM'"),
            ("opportunity", "low", "SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'LOW'"),
            
            # Top states
            ("state", "texas", "SELECT COUNT(*) FROM digital_gap_companies WHERE state = 'Texas' AND website_opportunity = true"),
            ("state", "florida", "SELECT COUNT(*) FROM digital_gap_companies WHERE state = 'Florida' AND website_opportunity = true"),
            ("state", "california", "SELECT COUNT(*) FROM digital_gap_companies WHERE state = 'California' AND website_opportunity = true"),
            ("state", "virginia", "SELECT COUNT(*) FROM digital_gap_companies WHERE state = 'Virginia' AND website_opportunity = true"),
            ("state", "georgia", "SELECT COUNT(*) FROM digital_gap_companies WHERE state = 'Georgia' AND website_opportunity = true"),
            
            # Business intelligence
            ("business", "sba_certified", "SELECT COUNT(*) FROM digital_gap_companies WHERE active_sba_certifications != '' AND website_opportunity = true"),
            ("business", "govt_ready", "SELECT COUNT(*) FROM digital_gap_companies WHERE uei != '' AND website_opportunity = true"),
        ]
        
        total_companies = await conn.fetchval("SELECT COUNT(*) FROM digital_gap_companies")
        
        for stat_type, stat_key, query in stats_queries:
            value = await conn.fetchval(query)
            percentage = (value / total_companies * 100) if total_companies > 0 else 0
            
            await conn.execute('''
                INSERT INTO digital_gap_stats (stat_type, stat_key, stat_value, percentage)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (stat_type, stat_key) 
                DO UPDATE SET stat_value = $3, percentage = $4, created_at = CURRENT_TIMESTAMP
            ''', stat_type, stat_key, value, percentage)
        
        await conn.close()
        logger.info("✅ Statistics generated successfully")

# CLI interface
async def main():
    """Load digital gap data into database"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Load Digital Gap Analysis data into database')
    parser.add_argument('--csv-file', '-f', 
                       default='/app/data/enriched/full_digital_gap_analysis.csv',
                       help='Path to the digital gap analysis CSV file')
    parser.add_argument('--db-url', '-d',
                       default='postgresql://kbi_user:secure_password@postgres/kbi_labs',
                       help='Database connection URL')
    
    args = parser.parse_args()
    
    loader = DigitalGapLoader(db_url=args.db_url)
    
    try:
        # Create tables
        await loader.create_tables()
        
        # Load data
        await loader.load_companies_data(args.csv_file)
        
        # Generate statistics
        await loader.generate_statistics()
        
        logger.info("🚀 Digital Gap Analyzer data loaded successfully!")
        logger.info("Ready to power your dashboard and API endpoints!")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
