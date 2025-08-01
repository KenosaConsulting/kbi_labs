#!/usr/bin/env python3
"""
KBI Labs Enrichment Pipeline V2
With real API integrations
"""
import pandas as pd
import sqlite3
import json
from datetime import datetime
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import logging
import sys
sys.path.insert(0, '.')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EnrichmentPipelineV2:
    def __init__(self):
        self.db_path = 'kbi_enriched_full.db'
        self.sam_api_key = os.getenv('SAM_GOV_API_KEY', 'demo_key')
        self.setup_database()
    
    def setup_database(self):
        """Create enhanced database schema"""
        conn = sqlite3.connect(self.db_path)
        
        # Drop old table if exists
        conn.execute("DROP TABLE IF EXISTS enriched_companies_v2")
        
        # Create new table with SAM.gov fields
        conn.execute('''
            CREATE TABLE IF NOT EXISTS enriched_companies_v2 (
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
                
                -- SAM.gov fields
                sam_registration_status TEXT,
                sam_registration_date TEXT,
                sam_expiration_date TEXT,
                cage_code TEXT,
                legal_business_name TEXT,
                dba_name TEXT,
                entity_structure TEXT,
                state_of_incorporation TEXT,
                
                -- Scoring fields
                pe_investment_score REAL,
                business_health_grade TEXT,
                scoring_metadata TEXT,
                
                -- Metadata
                enrichment_timestamp TIMESTAMP,
                api_calls_made TEXT,
                enrichment_version TEXT DEFAULT 'v2'
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("✓ Database schema v2 created")
    
    async def enrich_with_sam(self, session, uei):
        """Enrich with SAM.gov data"""
        if not uei:
            return {}
        
        try:
            url = f"https://api.sam.gov/entity-information/v3/entities/{uei}"
            headers = {'X-Api-Key': self.sam_api_key}
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    entity = data.get('entityData', [{}])[0] if data.get('entityData') else {}
                    registration = entity.get('entityRegistration', {})
                    core_data = entity.get('coreData', {})
                    
                    return {
                        'sam_registration_status': registration.get('registrationStatus', 'ACTIVE'),
                        'sam_registration_date': registration.get('registrationDate'),
                        'sam_expiration_date': registration.get('expirationDate'),
                        'cage_code': entity.get('cageCode'),
                        'legal_business_name': core_data.get('legalBusinessName')
                    }
                else:
                    return {'sam_registration_status': 'NOT_FOUND'}
        except Exception as e:
            logger.debug(f"SAM.gov API error for {uei}: {e}")
            return {'sam_registration_status': 'API_ERROR'}
    
    async def enrich_company_async(self, session, company):
        """Asynchronously enrich a single company"""
        # Base data
        enriched = {
            'uei': company.get('UEI (Unique Entity Identifier)'),
            'organization_name': company.get('Organization Name'),
            'primary_naics': str(company.get('Primary NAICS code', '')),
            'state': company.get('State'),
            'city': company.get('City'),
            'zipcode': str(company.get('Zipcode', '')),
            'website': company.get('Website'),
            'phone_number': str(company.get('Phone number', '')),
            'email': company.get('Contact person\'s email'),
            'legal_structure': company.get('Legal structure'),
            'active_sba_certifications': company.get('Active SBA certifications'),
            'capabilities_narrative': company.get('Capabilities narrative'),
            'enrichment_timestamp': datetime.now()
        }
        
        # Track API calls
        api_calls = []
        
        # SAM.gov enrichment (only if API key is real)
        if self.sam_api_key != 'demo_key' and self.sam_api_key != 'your_key_here':
            sam_data = await self.enrich_with_sam(session, enriched['uei'])
            enriched.update(sam_data)
            api_calls.append('SAM.gov')
        else:
            enriched['sam_registration_status'] = 'NO_API_KEY'
        
        enriched['api_calls_made'] = json.dumps(api_calls)
        
        # Scoring
        from src.enrichment.scoring import PEInvestmentScorer
        scorer = PEInvestmentScorer()
        
        scores = scorer.score_company(enriched)
        enriched['pe_investment_score'] = scores['pe_investment_score']
        enriched['business_health_grade'] = scores['business_health_grade']
        enriched['scoring_metadata'] = json.dumps(scores['scoring_details'])
        
        return enriched
    
    async def process_batch_async(self, companies_batch):
        """Process a batch of companies asynchronously"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _, company in companies_batch.iterrows():
                task = self.enrich_company_async(session, company.to_dict())
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            enriched_companies = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing company: {result}")
                else:
                    enriched_companies.append(result)
            
            return enriched_companies
    
    def process_csv(self, csv_path, limit=None):
        """Process companies from CSV with async enrichment"""
        print(f"\nProcessing {csv_path}...")
        
        # Read CSV
        dtype_spec = {'Zipcode': str, 'Phone number': str, 'Primary NAICS code': str}
        
        if limit:
            df = pd.read_csv(csv_path, nrows=limit, dtype=dtype_spec)
        else:
            df = pd.read_csv(csv_path, dtype=dtype_spec)
        
        print(f"Found {len(df)} companies to process")
        
        # Process in batches
        batch_size = 10  # Smaller for API calls
        conn = sqlite3.connect(self.db_path)
        processed = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            # Run async enrichment
            enriched_batch = asyncio.run(self.process_batch_async(batch))
            
            # Save to database
            if enriched_batch:
                df_enriched = pd.DataFrame(enriched_batch)
                df_enriched.to_sql('enriched_companies_v2', conn, 
                                 if_exists='append', index=False)
                processed += len(enriched_batch)
                print(f"Progress: {processed}/{len(df)} companies processed")
        
        conn.close()
        print("✓ Processing complete!")
        
        # Show summary
        self.show_summary()
    
    def show_summary(self):
        """Display enhanced summary statistics"""
        conn = sqlite3.connect(self.db_path)
        
        # Basic stats
        stats = pd.read_sql_query(
            """SELECT 
                COUNT(*) as total,
                AVG(pe_investment_score) as avg_score,
                COUNT(CASE WHEN sam_registration_status = 'ACTIVE' THEN 1 END) as sam_active,
                COUNT(CASE WHEN sam_registration_status = 'NOT_FOUND' THEN 1 END) as sam_not_found,
                COUNT(CASE WHEN sam_registration_status = 'NO_API_KEY' THEN 1 END) as no_api_key
               FROM enriched_companies_v2""", conn
        )
        
        print("\n" + "="*60)
        print("ENRICHMENT SUMMARY V2")
        print("="*60)
        print(f"Total companies: {stats.iloc[0]['total']}")
        print(f"Average PE score: {stats.iloc[0]['avg_score']:.1f}")
        print(f"\nSAM.gov Status:")
        print(f"  Active registrations: {stats.iloc[0]['sam_active']}")
        print(f"  Not found: {stats.iloc[0]['sam_not_found']}")
        print(f"  No API key: {stats.iloc[0]['no_api_key']}")
        
        # Grade distribution
        grades = pd.read_sql_query(
            """SELECT business_health_grade, COUNT(*) as count 
               FROM enriched_companies_v2 
               GROUP BY business_health_grade
               ORDER BY business_health_grade""", conn
        )
        
        print("\nGrade distribution:")
        for _, row in grades.iterrows():
            print(f"  Grade {row['business_health_grade']}: {row['count']}")
        
        # Top companies
        top_companies = pd.read_sql_query(
            """SELECT organization_name, city, state, pe_investment_score, 
                      business_health_grade, sam_registration_status
               FROM enriched_companies_v2 
               ORDER BY pe_investment_score DESC 
               LIMIT 5""", conn
        )
        
        print("\nTop 5 companies:")
        for _, company in top_companies.iterrows():
            print(f"\n  {company['organization_name']} ({company['city']}, {company['state']})")
            print(f"    Score: {company['pe_investment_score']:.1f}, Grade: {company['business_health_grade']}")
            print(f"    SAM Status: {company['sam_registration_status']}")
        
        conn.close()

if __name__ == "__main__":
    # Check if we have a real API key
    api_key = os.getenv('SAM_GOV_API_KEY', 'demo_key')
    if api_key == 'demo_key' or api_key == 'your_key_here':
        print("\n⚠️  WARNING: Using demo mode - no real API calls will be made")
        print("To use real APIs, add your API key to .env file")
    else:
        print(f"\n✓ Using SAM.gov API key: {api_key[:10]}...")
    
    pipeline = EnrichmentPipelineV2()
    
    # Process sample data
    sample_path = 'data/dsbs_raw/sample_50.csv'
    if os.path.exists(sample_path):
        pipeline.process_csv(sample_path)
    else:
        print("Sample file not found")
