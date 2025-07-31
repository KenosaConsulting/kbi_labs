#!/usr/bin/env python3
"""
Simplified enrichment for KBI Labs
Focuses on core functionality
"""
import pandas as pd
import sqlite3
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
sys.path.insert(0, '.')

# Load environment variables
load_dotenv()

class SimpleEnrichmentPipeline:
    def __init__(self):
        self.db_path = 'kbi_enriched_full.db'
        self.setup_database()
    
    def setup_database(self):
        """Create basic database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS enriched_companies (
                uei TEXT PRIMARY KEY,
                organization_name TEXT,
                primary_naics TEXT,
                state TEXT,
                city TEXT,
                zipcode TEXT,
                website TEXT,
                phone_number TEXT,
                email TEXT,
                legal_structure TEXT,
                active_sba_certifications TEXT,
                capabilities_narrative TEXT,
                pe_investment_score REAL,
                business_health_grade TEXT,
                enrichment_timestamp TIMESTAMP,
                sam_registration_status TEXT,
                patent_count INTEGER DEFAULT 0,
                nsf_grant_count INTEGER DEFAULT 0,
                federal_contracts_count INTEGER DEFAULT 0,
                scoring_metadata TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✓ Database schema created")
    
    def enrich_company(self, company):
        """Basic enrichment with placeholder for API calls"""
        enriched = {
            'uei': company.get('UEI (Unique Entity Identifier)'),
            'organization_name': company.get('Organization Name'),
            'primary_naics': str(company.get('Primary NAICS code', '')),
            'state': company.get('State'),
            'city': company.get('City'),
            'zipcode': str(company.get('Zipcode', '')),
            'website': company.get('Website'),
            'phone_number': str(company.get('Phone number', '')),
            'email': company.get('Contact person\'s email') or company.get('Email'),
            'legal_structure': company.get('Legal structure'),
            'active_sba_certifications': company.get('Active SBA certifications'),
            'capabilities_narrative': company.get('Capabilities narrative'),
            'enrichment_timestamp': datetime.now()
        }
        
        # Placeholder for API enrichments
        # In full version, these would make actual API calls
        enriched['sam_registration_status'] = 'ACTIVE' if enriched['website'] else 'UNKNOWN'
        enriched['patent_count'] = 0
        enriched['nsf_grant_count'] = 0
        enriched['federal_contracts_count'] = 0
        
        # Use existing scoring
        from src.enrichment.scoring import PEInvestmentScorer
        scorer = PEInvestmentScorer()
        scores = scorer.score_company(enriched)
        
        enriched['pe_investment_score'] = scores['pe_investment_score']
        enriched['business_health_grade'] = scores['business_health_grade']
        enriched['scoring_metadata'] = json.dumps(scores['scoring_details'])
        
        return enriched
    
    def process_csv(self, csv_path, limit=None):
        """Process companies from CSV"""
        print(f"Processing {csv_path}...")
        
        # Read CSV with proper dtypes
        dtype_spec = {
            'Zipcode': str,
            'Phone number': str,
            'Primary NAICS code': str
        }
        
        # Read CSV
        if limit:
            df = pd.read_csv(csv_path, nrows=limit, dtype=dtype_spec)
        else:
            df = pd.read_csv(csv_path, dtype=dtype_spec)
        
        print(f"Found {len(df)} companies to process")
        
        # Connect to database
        conn = sqlite3.connect(self.db_path)
        
        # Process in batches
        batch_size = 100
        processed = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            enriched_batch = []
            
            for _, company in batch.iterrows():
                try:
                    enriched = self.enrich_company(company.to_dict())
                    enriched_batch.append(enriched)
                    processed += 1
                except Exception as e:
                    print(f"Error processing {company.get('Organization Name')}: {e}")
            
            # Save batch to database
            if enriched_batch:
                df_enriched = pd.DataFrame(enriched_batch)
                df_enriched.to_sql('enriched_companies', conn, 
                                 if_exists='append', index=False)
                print(f"Progress: {processed}/{len(df)} companies processed")
        
        conn.close()
        print("✓ Processing complete!")
        
        # Show summary
        self.show_summary()
    
    def show_summary(self):
        """Display summary statistics"""
        conn = sqlite3.connect(self.db_path)
        
        # Get statistics
        total = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM enriched_companies", conn
        ).iloc[0]['count']
        
        avg_score = pd.read_sql_query(
            "SELECT AVG(pe_investment_score) as avg FROM enriched_companies", conn
        ).iloc[0]['avg']
        
        grades = pd.read_sql_query(
            """SELECT business_health_grade, COUNT(*) as count 
               FROM enriched_companies 
               GROUP BY business_health_grade
               ORDER BY business_health_grade""", conn
        )
        
        print("\n" + "="*50)
        print("ENRICHMENT SUMMARY")
        print("="*50)
        print(f"Total companies: {total}")
        print(f"Average PE score: {avg_score:.1f}")
        print("\nGrade distribution:")
        for _, row in grades.iterrows():
            print(f"  Grade {row['business_health_grade']}: {row['count']}")
        
        # Top companies
        top_companies = pd.read_sql_query(
            """SELECT organization_name, city, state, pe_investment_score, business_health_grade
               FROM enriched_companies 
               ORDER BY pe_investment_score DESC 
               LIMIT 5""", conn
        )
        
        print("\nTop 5 companies:")
        for _, company in top_companies.iterrows():
            print(f"  {company['organization_name']} ({company['city']}, {company['state']})")
            print(f"    Score: {company['pe_investment_score']:.1f}, Grade: {company['business_health_grade']}")
        
        conn.close()

# Test function
def test_enrichment():
    pipeline = SimpleEnrichmentPipeline()
    
    # Test with sample data
    sample_path = 'data/dsbs_raw/sample_50.csv'
    if os.path.exists(sample_path):
        pipeline.process_csv(sample_path)
    else:
        print(f"Sample file not found: {sample_path}")
        print("Processing main file with limit...")
        main_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
        if os.path.exists(main_path):
            pipeline.process_csv(main_path, limit=100)
        else:
            print(f"Main file not found: {main_path}")

if __name__ == "__main__":
    test_enrichment()
