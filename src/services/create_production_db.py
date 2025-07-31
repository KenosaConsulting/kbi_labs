#!/usr/bin/env python3
"""
KBI Labs Production Database Creator
Creates optimized production database from enriched data
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json

class ProductionDatabaseCreator:
    def __init__(self):
        self.source_db = 'kbi_complete_enriched.db'
        self.production_db = 'kbi_production.db'
        
    def create_production_database(self):
        """Create optimized production database with indexes"""
        print("Creating KBI Labs Production Database...")
        
        # Connect to source
        source_conn = sqlite3.connect(self.source_db)
        prod_conn = sqlite3.connect(self.production_db)
        
        # Copy data
        print("Copying enriched data...")
        df = pd.read_sql_query("SELECT * FROM enriched_companies_full", source_conn)
        
        # Create production schema with optimizations
        prod_conn.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                -- Core identifiers
                uei TEXT PRIMARY KEY,
                organization_name TEXT NOT NULL,
                
                -- Location
                state TEXT,
                city TEXT,
                zipcode TEXT,
                metro_area TEXT,
                
                -- Business info
                primary_naics TEXT,
                industry_sector TEXT,
                website TEXT,
                phone_number TEXT,
                email TEXT,
                
                -- Federal contracting
                sam_registration_status TEXT,
                cage_code TEXT,
                federal_contracts_count INTEGER DEFAULT 0,
                federal_contracts_value REAL DEFAULT 0,
                
                -- Scoring & Analytics
                pe_investment_score REAL,
                business_health_grade TEXT,
                growth_potential_score REAL,
                innovation_score REAL,
                market_position_score REAL,
                
                -- Enrichment data
                patent_count INTEGER DEFAULT 0,
                nsf_total_funding REAL DEFAULT 0,
                state_gdp_billions REAL,
                state_gdp_growth_rate REAL,
                
                -- Metadata
                enrichment_timestamp TIMESTAMP,
                data_quality_score REAL,
                
                -- Indexed for performance
                CHECK (pe_investment_score >= 0 AND pe_investment_score <= 100)
            )
        ''')
        
        # Insert data
        df.to_sql('companies', prod_conn, if_exists='replace', index=False)
        
        # Create indexes for fast queries
        print("Creating performance indexes...")
        indexes = [
            "CREATE INDEX idx_pe_score ON companies(pe_investment_score DESC)",
            "CREATE INDEX idx_health_grade ON companies(business_health_grade)",
            "CREATE INDEX idx_state ON companies(state)",
            "CREATE INDEX idx_naics ON companies(primary_naics)",
            "CREATE INDEX idx_city_state ON companies(city, state)",
            "CREATE INDEX idx_innovation ON companies(innovation_score DESC)",
            "CREATE INDEX idx_growth ON companies(growth_potential_score DESC)"
        ]
        
        for idx in indexes:
            prod_conn.execute(idx)
            
        # Create materialized views for common queries
        print("Creating analytics views...")
        
        # State summary view
        prod_conn.execute('''
            CREATE VIEW state_analytics AS
            SELECT 
                state,
                COUNT(*) as company_count,
                AVG(pe_investment_score) as avg_pe_score,
                COUNT(CASE WHEN business_health_grade IN ('A', 'B') THEN 1 END) as high_grade_count,
                SUM(federal_contracts_value) as total_federal_value,
                AVG(innovation_score) as avg_innovation,
                AVG(growth_potential_score) as avg_growth
            FROM companies
            GROUP BY state
        ''')
        
        # Industry summary view
        prod_conn.execute('''
            CREATE VIEW industry_analytics AS
            SELECT 
                SUBSTR(primary_naics, 1, 2) as naics_2digit,
                industry_sector,
                COUNT(*) as company_count,
                AVG(pe_investment_score) as avg_pe_score,
                AVG(patent_count) as avg_patents,
                SUM(nsf_total_funding) as total_nsf_funding
            FROM companies
            GROUP BY SUBSTR(primary_naics, 1, 2), industry_sector
        ''')
        
        # Top companies view
        prod_conn.execute('''
            CREATE VIEW top_companies AS
            SELECT 
                uei,
                organization_name,
                city,
                state,
                pe_investment_score,
                business_health_grade,
                innovation_score,
                growth_potential_score,
                federal_contracts_value,
                patent_count
            FROM companies
            WHERE pe_investment_score >= 70
            ORDER BY pe_investment_score DESC
        ''')
        
        # Commit and optimize
        prod_conn.commit()
        prod_conn.execute("VACUUM")
        prod_conn.execute("ANALYZE")
        
        # Get statistics
        stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total_companies,
                AVG(pe_investment_score) as avg_score,
                COUNT(CASE WHEN sam_registration_status = 'ACTIVE' THEN 1 END) as sam_active,
                COUNT(CASE WHEN patent_count > 0 THEN 1 END) as companies_with_patents,
                COUNT(CASE WHEN nsf_total_funding > 0 THEN 1 END) as companies_with_nsf
            FROM companies
        """, prod_conn)
        
        print("\n" + "="*60)
        print("PRODUCTION DATABASE CREATED")
        print("="*60)
        print(f"Total Companies: {stats.iloc[0]['total_companies']:,}")
        print(f"Average PE Score: {stats.iloc[0]['avg_score']:.1f}")
        print(f"SAM.gov Active: {stats.iloc[0]['sam_active']:,}")
        print(f"Companies with Patents: {stats.iloc[0]['companies_with_patents']:,}")
        print(f"Companies with NSF Grants: {stats.iloc[0]['companies_with_nsf']:,}")
        print(f"\nDatabase: {self.production_db}")
        print("Ready for UI/UX development!")
        
        source_conn.close()
        prod_conn.close()

if __name__ == "__main__":
    creator = ProductionDatabaseCreator()
    creator.create_production_database()
