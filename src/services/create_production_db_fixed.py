#!/usr/bin/env python3
"""
KBI Labs Production Database Creator - Fixed Version
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
        
        # First, let's see what columns we actually have
        cursor = source_conn.execute("SELECT * FROM enriched_companies_full LIMIT 1")
        columns = [description[0] for description in cursor.description]
        print(f"Found {len(columns)} columns in source database")
        
        # Get all data
        print("Reading enriched data...")
        df = pd.read_sql_query("SELECT * FROM enriched_companies_full", source_conn)
        print(f"Loaded {len(df)} companies")
        
        # Create production database
        prod_conn = sqlite3.connect(self.production_db)
        
        # Write data to production database (keep same structure)
        print("Writing to production database...")
        df.to_sql('companies', prod_conn, if_exists='replace', index=False)
        
        # Create indexes for fast queries based on available columns
        print("Creating performance indexes...")
        
        # Check which columns exist and create appropriate indexes
        available_indexes = []
        
        if 'pe_investment_score' in columns:
            available_indexes.append("CREATE INDEX idx_pe_score ON companies(pe_investment_score DESC)")
        if 'business_health_grade' in columns:
            available_indexes.append("CREATE INDEX idx_health_grade ON companies(business_health_grade)")
        if 'state' in columns:
            available_indexes.append("CREATE INDEX idx_state ON companies(state)")
        if 'primary_naics' in columns:
            available_indexes.append("CREATE INDEX idx_naics ON companies(primary_naics)")
        if 'city' in columns and 'state' in columns:
            available_indexes.append("CREATE INDEX idx_city_state ON companies(city, state)")
        
        for idx in available_indexes:
            try:
                prod_conn.execute(idx)
                print(f"  ✓ Created index: {idx.split(' ')[2]}")
            except Exception as e:
                print(f"  ✗ Failed to create index: {e}")
        
        # Create views based on available columns
        print("Creating analytics views...")
        
        # State analytics view
        if 'state' in columns and 'pe_investment_score' in columns:
            try:
                prod_conn.execute('''
                    CREATE VIEW state_analytics AS
                    SELECT 
                        state,
                        COUNT(*) as company_count,
                        AVG(pe_investment_score) as avg_pe_score,
                        COUNT(CASE WHEN business_health_grade IN ('A', 'B') THEN 1 END) as high_grade_count
                    FROM companies
                    WHERE state IS NOT NULL
                    GROUP BY state
                ''')
                print("  ✓ Created state_analytics view")
            except Exception as e:
                print(f"  ✗ Failed to create state_analytics view: {e}")
        
        # Top companies view
        if 'pe_investment_score' in columns:
            try:
                prod_conn.execute('''
                    CREATE VIEW top_companies AS
                    SELECT 
                        uei,
                        organization_name,
                        city,
                        state,
                        pe_investment_score,
                        business_health_grade
                    FROM companies
                    WHERE pe_investment_score >= 70
                    ORDER BY pe_investment_score DESC
                ''')
                print("  ✓ Created top_companies view")
            except Exception as e:
                print(f"  ✗ Failed to create top_companies view: {e}")
        
        # Commit and optimize
        prod_conn.commit()
        print("Optimizing database...")
        prod_conn.execute("VACUUM")
        prod_conn.execute("ANALYZE")
        
        # Get statistics
        stats_query = "SELECT COUNT(*) as total_companies"
        if 'pe_investment_score' in columns:
            stats_query += ", AVG(pe_investment_score) as avg_score"
        if 'sam_registration_status' in columns:
            stats_query += ", COUNT(CASE WHEN sam_registration_status = 'ACTIVE' THEN 1 END) as sam_active"
        stats_query += " FROM companies"
        
        stats = pd.read_sql_query(stats_query, prod_conn)
        
        print("\n" + "="*60)
        print("PRODUCTION DATABASE CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Total Companies: {stats.iloc[0]['total_companies']:,}")
        if 'avg_score' in stats.columns:
            print(f"Average PE Score: {stats.iloc[0]['avg_score']:.1f}")
        if 'sam_active' in stats.columns:
            print(f"SAM.gov Active: {stats.iloc[0]['sam_active']:,}")
        print(f"\nDatabase: {self.production_db}")
        print(f"Available columns: {len(columns)}")
        print("Ready for API integration!")
        
        source_conn.close()
        prod_conn.close()

if __name__ == "__main__":
    creator = ProductionDatabaseCreator()
    creator.create_production_database()
