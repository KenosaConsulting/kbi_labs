#!/usr/bin/env python3
"""
KBI Labs Master Enrichment Script - Fixed Version
"""
import pandas as pd
import sqlite3
import json
from datetime import datetime
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

class MasterEnrichmentFixed:
    def __init__(self):
        self.db_path = 'kbi_enriched_master.db'
        self.setup_database()
        self.start_time = time.time()
        
    def setup_database(self):
        """Create master database with all fields"""
        conn = sqlite3.connect(self.db_path)
        
        # Don't drop existing table - just create if not exists
        conn.execute('''
            CREATE TABLE IF NOT EXISTS companies_master (
                -- Primary fields
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
                address_line_1 TEXT,
                address_line_2 TEXT,
                first_name TEXT,
                last_name TEXT,
                job_title TEXT,
                capabilities_statement_link TEXT,
                
                -- Scoring
                pe_investment_score REAL,
                business_health_grade TEXT,
                
                -- Industry analysis
                industry_sector TEXT,
                industry_growth_score REAL,
                market_position_score REAL,
                
                -- Location analysis
                location_score REAL,
                state_business_climate TEXT,
                metro_area TEXT,
                
                -- Digital presence
                has_website INTEGER,
                website_quality_score REAL,
                digital_maturity_score REAL,
                
                -- Certification analysis
                certification_count INTEGER,
                certification_value_score REAL,
                federal_contractor_potential REAL,
                
                -- Size and scale
                estimated_employees TEXT,
                estimated_revenue TEXT,
                business_age_estimate INTEGER,
                
                -- Risk assessment
                overall_risk_score REAL,
                data_completeness_score REAL,
                
                -- Metadata
                enrichment_timestamp TIMESTAMP,
                processing_time_seconds REAL,
                data_sources TEXT,
                enrichment_version TEXT DEFAULT '3.0'
            )
        ''')
        
        # Create indexes for performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_pe_score ON companies_master(pe_investment_score DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_state ON companies_master(state)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_naics ON companies_master(primary_naics)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_grade ON companies_master(business_health_grade)')
        
        conn.commit()
        conn.close()
        print("✓ Master database ready")
    
    def process_full_dataset(self):
        """Process the full 64,799 company dataset"""
        csv_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
        
        if not os.path.exists(csv_path):
            print(f"Error: Full dataset not found at {csv_path}")
            return
        
        print(f"\n{'='*60}")
        print("KBI LABS MASTER ENRICHMENT - FULL DATASET")
        print(f"{'='*60}")
        
        # Count total rows
        print("Counting total companies...")
        total_rows = sum(1 for _ in open(csv_path)) - 1
        print(f"Total companies to process: {total_rows:,}")
        
        response = input(f"\nThis will process all {total_rows:,} companies. Continue? (y/n): ")
        if response.lower() != 'y':
            print("Processing cancelled.")
            return
        
        # Import enrichment logic from original script
        from master_enrichment import MasterEnrichment
        original_enricher = MasterEnrichment()
        
        # Read and process in chunks
        chunk_size = 5000
        conn = sqlite3.connect(self.db_path)
        processed = 0
        skipped = 0
        
        # Check existing UEIs
        existing_ueis = set(pd.read_sql_query(
            "SELECT uei FROM companies_master", conn
        )['uei'].values)
        
        print(f"Found {len(existing_ueis):,} existing companies in database")
        
        dtype_spec = {
            'Zipcode': str, 'Phone number': str, 
            'Primary NAICS code': str, 'First Name': str,
            'Last Name': str
        }
        
        for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size, dtype=dtype_spec):
            chunk_start = time.time()
            enriched_batch = []
            
            for _, company in chunk_df.iterrows():
                uei = company.get('UEI (Unique Entity Identifier)')
                
                # Skip if already processed
                if uei in existing_ueis:
                    skipped += 1
                    continue
                
                try:
                    enriched = original_enricher.enrich_company(company.to_dict())
                    enriched_batch.append(enriched)
                    existing_ueis.add(uei)  # Add to set to avoid duplicates in same run
                except Exception as e:
                    print(f"Error processing {company.get('Organization Name')}: {e}")
            
            # Save batch
            if enriched_batch:
                df_enriched = pd.DataFrame(enriched_batch)
                df_enriched.to_sql('companies_master', conn, 
                                 if_exists='append', index=False)
                processed += len(enriched_batch)
            
            # Progress update
            total_handled = processed + skipped
            chunk_time = time.time() - chunk_start
            
            if processed > 0:
                rate = len(enriched_batch) / chunk_time
                remaining = total_rows - total_handled
                eta = remaining / rate / 60 if rate > 0 else 0
                
                print(f"Progress: {total_handled:,}/{total_rows:,} "
                      f"({total_handled/total_rows*100:.1f}%) - "
                      f"Processed: {processed:,} - Skipped: {skipped:,} - "
                      f"Rate: {rate:.1f}/sec - ETA: {eta:.1f} min")
        
        conn.close()
        
        total_time = (time.time() - self.start_time) / 60
        
        print(f"\n{'='*60}")
        print(f"✓ ENRICHMENT COMPLETE!")
        print(f"{'='*60}")
        print(f"Total companies processed: {processed:,}")
        print(f"Companies skipped (already in DB): {skipped:,}")
        print(f"Total time: {total_time:.1f} minutes")
        print(f"Average rate: {processed/total_time:.1f} companies/minute" if total_time > 0 else "N/A")
        
        # Generate summary
        self.generate_final_summary()
    
    def generate_final_summary(self):
        """Generate final summary of all data"""
        conn = sqlite3.connect(self.db_path)
        
        # Get total count
        total = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM companies_master", conn
        ).iloc[0]['count']
        
        print(f"\n{'='*60}")
        print("FINAL DATABASE SUMMARY")
        print(f"{'='*60}")
        print(f"\nTotal companies in database: {total:,}")
        
        # PE Score distribution
        score_dist = pd.read_sql_query("""
            SELECT 
                COUNT(CASE WHEN pe_investment_score >= 90 THEN 1 END) as score_90_100,
                COUNT(CASE WHEN pe_investment_score >= 80 AND pe_investment_score < 90 THEN 1 END) as score_80_90,
                COUNT(CASE WHEN pe_investment_score >= 70 AND pe_investment_score < 80 THEN 1 END) as score_70_80,
                COUNT(CASE WHEN pe_investment_score >= 60 AND pe_investment_score < 70 THEN 1 END) as score_60_70,
                COUNT(CASE WHEN pe_investment_score >= 50 AND pe_investment_score < 60 THEN 1 END) as score_50_60,
                COUNT(CASE WHEN pe_investment_score < 50 THEN 1 END) as score_below_50
            FROM companies_master
        """, conn).iloc[0]
        
        print("\nPE Investment Score Distribution:")
        print(f"  90-100: {score_dist['score_90_100']:,} companies")
        print(f"  80-90:  {score_dist['score_80_90']:,} companies")
        print(f"  70-80:  {score_dist['score_70_80']:,} companies")
        print(f"  60-70:  {score_dist['score_60_70']:,} companies")
        print(f"  50-60:  {score_dist['score_50_60']:,} companies")
        print(f"  <50:    {score_dist['score_below_50']:,} companies")
        
        # Top opportunities
        print("\nTop 10 Investment Opportunities:")
        top_opps = pd.read_sql_query("""
            SELECT organization_name, city, state, pe_investment_score, 
                   business_health_grade, industry_sector
            FROM companies_master
            ORDER BY pe_investment_score DESC
            LIMIT 10
        """, conn)
        
        for i, row in top_opps.iterrows():
            print(f"\n  {i+1}. {row['organization_name']}")
            print(f"     {row['city']}, {row['state']} | {row['industry_sector']}")
            print(f"     Score: {row['pe_investment_score']:.1f} | Grade: {row['business_health_grade']}")
        
        conn.close()

if __name__ == "__main__":
    enricher = MasterEnrichmentFixed()
    enricher.process_full_dataset()
