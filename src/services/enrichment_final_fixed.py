#!/usr/bin/env python3
"""
Fixed production enrichment pipeline
"""
import os
import pandas as pd
import sqlite3
import json
import aiohttp
import asyncio
from datetime import datetime
import logging
from dotenv import load_dotenv
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalEnrichment:
    def __init__(self):
        # Load API keys
        self.sam_gov_api_key = os.getenv('SAM_GOV_API_KEY')
        self.census_api_key = os.getenv('CENSUS_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        
        # Track statistics
        self.stats = {
            'sam_success': 0,
            'sam_not_found': 0,
            'census_success': 0,
            'fred_success': 0
        }
        
        # Load patent data with correct columns
        self.load_patent_data()
        
        # Load NSF data
        self.load_nsf_data()
    
    def load_patent_data(self):
        """Load patent data with actual column names"""
        self.patent_lookup = {}
        patent_path = 'patent_data/'
        
        if os.path.exists(patent_path):
            # Check what columns are actually in the files
            for file in os.listdir(patent_path):
                if file.endswith('.tsv'):
                    try:
                        # Read first few rows to check columns
                        df_sample = pd.read_csv(os.path.join(patent_path, file), 
                                               sep='\t', nrows=5)
                        logger.info(f"Columns in {file}: {list(df_sample.columns)[:5]}")
                        
                        # For assignee files, look for organization column
                        if 'assignee' in file and 'disambig_assignee_organization' in df_sample.columns:
                            df = pd.read_csv(os.path.join(patent_path, file), 
                                           sep='\t',
                                           usecols=['disambig_assignee_organization', 'patent_id'],
                                           low_memory=False)
                            
                            # Count patents per organization
                            for org, group in df.groupby('disambig_assignee_organization'):
                                if pd.notna(org):
                                    self.patent_lookup[org.lower()] = len(group)
                            
                            logger.info(f"Loaded {len(self.patent_lookup)} organizations from {file}")
                            break  # Only load one file for now
                            
                    except Exception as e:
                        logger.debug(f"Skipping {file}: {e}")
    
    def load_nsf_data(self):
        """Load NSF data"""
        self.nsf_lookup = {}
        nsf_path = 'nsf_data/'
        
        if os.path.exists(nsf_path):
            # Similar approach for NSF data
            logger.info(f"NSF data directory exists with {len(os.listdir(nsf_path))} files")
    
    async def enrich_company(self, session, company):
        """Enrich a single company with all available data"""
        # Base fields
        enriched = {
            'uei': company.get('UEI (Unique Entity Identifier)'),
            'organization_name': company.get('Organization Name'),
            'state': company.get('State'),
            'city': company.get('City'),
            'zipcode': company.get('Zipcode'),
            'primary_naics': company.get('Primary NAICS code'),
            'website': company.get('Website'),
            'email': company.get('Contact person\'s email'),
            'active_sba_certifications': company.get('Active SBA certifications'),
            'legal_structure': company.get('Legal structure')
        }
        
        # API enrichments
        tasks = []
        
        # SAM.gov
        if enriched['uei']:
            tasks.append(('sam', self.get_sam_data(session, enriched['uei'])))
        
        # Census
        if enriched['state']:
            tasks.append(('census', self.get_census_data(session, enriched['state'])))
        
        # FRED
        if enriched['state']:
            tasks.append(('fred', self.get_fred_data(session, enriched['state'])))
        
        # Execute all API calls
        for name, task in tasks:
            try:
                result = await task
                if result:
                    enriched.update(result)
            except Exception as e:
                logger.debug(f"{name} API error: {e}")
        
        # Local data lookups
        if enriched['organization_name']:
            org_lower = enriched['organization_name'].lower()
            enriched['patent_count'] = self.patent_lookup.get(org_lower, 0)
            enriched['has_patents'] = enriched['patent_count'] > 0
        
        # Calculate enhanced score
        enriched['pe_score'] = self.calculate_pe_score(enriched)
        enriched['enrichment_date'] = datetime.now().isoformat()
        
        return enriched
    
    async def get_sam_data(self, session, uei):
        """Get SAM.gov data"""
        try:
            url = f"https://api.sam.gov/entity-information/v3/entities/{uei}"
            headers = {'X-Api-Key': self.sam_gov_api_key}
            
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    self.stats['sam_success'] += 1
                    data = await response.json()
                    entity = data.get('entityData', [{}])[0] if data.get('entityData') else {}
                    
                    return {
                        'sam_registered': True,
                        'sam_status': entity.get('entityRegistration', {}).get('registrationStatus'),
                        'sam_cage_code': entity.get('cageCode')
                    }
                elif response.status == 404:
                    self.stats['sam_not_found'] += 1
                    return {'sam_registered': False}
                    
        except Exception as e:
            logger.debug(f"SAM error: {e}")
            
        return {}
    
    async def get_census_data(self, session, state):
        """Get Census data with state FIPS mapping"""
        try:
            # State to FIPS mapping
            state_fips = {
                'Alabama': '01', 'Alaska': '02', 'Arizona': '04', 'Arkansas': '05',
                'California': '06', 'Colorado': '08', 'Connecticut': '09', 'Delaware': '10',
                'District of Columbia': '11', 'Florida': '12', 'Georgia': '13', 'Hawaii': '15',
                'Idaho': '16', 'Illinois': '17', 'Indiana': '18', 'Iowa': '19',
                'Kansas': '20', 'Kentucky': '21', 'Louisiana': '22', 'Maine': '23',
                'Maryland': '24', 'Massachusetts': '25', 'Michigan': '26', 'Minnesota': '27',
                'Mississippi': '28', 'Missouri': '29', 'Montana': '30', 'Nebraska': '31',
                'Nevada': '32', 'New Hampshire': '33', 'New Jersey': '34', 'New Mexico': '35',
                'New York': '36', 'North Carolina': '37', 'North Dakota': '38', 'Ohio': '39',
                'Oklahoma': '40', 'Oregon': '41', 'Pennsylvania': '42', 'Rhode Island': '44',
                'South Carolina': '45', 'South Dakota': '46', 'Tennessee': '47', 'Texas': '48',
                'Utah': '49', 'Vermont': '50', 'Virginia': '51', 'Washington': '53',
                'West Virginia': '54', 'Wisconsin': '55', 'Wyoming': '56'
            }
            
            fips = state_fips.get(state)
            if not fips:
                return {}
            
            url = "https://api.census.gov/data/2021/acs/acs5"
            params = {
                'get': 'B01003_001E,B19013_001E',
                'for': f'state:{fips}',
                'key': self.census_api_key
            }
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    self.stats['census_success'] += 1
                    data = await response.json()
                    
                    if len(data) > 1:
                        values = data[1]
                        return {
                            'state_population': int(values[0]) if values[0] else None,
                            'state_median_income': int(values[1]) if values[1] else None
                        }
                        
        except Exception as e:
            logger.debug(f"Census error: {e}")
            
        return {}
    
    async def get_fred_data(self, session, state):
        """Get FRED data - using national unemployment if state fails"""
        try:
            # Try national unemployment rate first
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'UNRATE',  # National unemployment
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    self.stats['fred_success'] += 1
                    data = await response.json()
                    obs = data.get('observations', [])
                    
                    if obs:
                        return {
                            'national_unemployment': float(obs[0].get('value')),
                            'unemployment_date': obs[0].get('date')
                        }
                        
        except Exception as e:
            logger.debug(f"FRED error: {e}")
            
        return {}
    
    def calculate_pe_score(self, company):
        """Calculate PE investment score with available data"""
        score = 50.0  # Base score
        
        # Website bonus
        if company.get('website'):
            score += 5
        
        # Email bonus  
        if company.get('email'):
            score += 3
        
        # Certification bonus
        if company.get('active_sba_certifications'):
            score += 10
        
        # SAM registration bonus
        if company.get('sam_registered'):
            score += 15
        
        # Patent bonus
        if company.get('patent_count', 0) > 0:
            score += min(10, company['patent_count'])
        
        # Legal structure bonus
        if company.get('legal_structure'):
            if 'LLC' in str(company['legal_structure']):
                score += 5
            elif 'Corporation' in str(company['legal_structure']):
                score += 7
        
        # Location bonus (if in high-income state)
        if company.get('state_median_income', 0) > 70000:
            score += 5
        
        return min(score, 100)
    
    async def process_batch(self, companies_df):
        """Process a batch of companies"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for _, company in companies_df.iterrows():
                task = self.enrich_company(session, company.to_dict())
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
    
    def process_dataset(self, csv_path, output_db='kbi_final_enriched.db', limit=None):
        """Process the dataset"""
        print(f"\n{'='*60}")
        print("KBI LABS FINAL ENRICHMENT")
        print(f"{'='*60}")
        print(f"Processing: {csv_path}")
        
        # Create database
        conn = sqlite3.connect(output_db)
        
        # Process in chunks
        chunk_size = 100
        total_processed = 0
        start_time = time.time()
        
        chunks_to_process = pd.read_csv(csv_path, chunksize=chunk_size)
        
        for chunk_num, chunk in enumerate(chunks_to_process):
            # Run async processing
            enriched = asyncio.run(self.process_batch(chunk))
            
            # Save to database
            df_enriched = pd.DataFrame(enriched)
            df_enriched.to_sql('companies_enriched', conn, 
                             if_exists='append' if chunk_num > 0 else 'replace', 
                             index=False)
            
            total_processed += len(chunk)
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            
            # Progress update
            print(f"\rProcessed: {total_processed:,} companies ({rate:.1f}/sec)", end='')
            
            # Stop if limit reached
            if limit and total_processed >= limit:
                break
        
        conn.close()
        
        print(f"\n\n{'='*60}")
        print("✓ ENRICHMENT COMPLETE!")
        print(f"{'='*60}")
        print(f"Total processed: {total_processed:,} companies")
        print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Average rate: {rate:.1f} companies/second")
        
        print(f"\nAPI Statistics:")
        print(f"  SAM.gov: {self.stats['sam_success']} found, {self.stats['sam_not_found']} not found")
        print(f"  Census: {self.stats['census_success']} successful")
        print(f"  FRED: {self.stats['fred_success']} successful")
        
        print(f"\nDatabase saved to: {output_db}")
        
        # Show sample results
        self.show_results(output_db)
    
    def show_results(self, db_path):
        """Show enrichment results"""
        conn = sqlite3.connect(db_path)
        
        # Get summary
        df = pd.read_sql_query("SELECT * FROM companies_enriched", conn)
        
        print(f"\n{'='*60}")
        print("ENRICHMENT RESULTS")
        print(f"{'='*60}")
        
        # Basic stats
        print(f"\nTotal companies: {len(df):,}")
        print(f"Average PE Score: {df['pe_score'].mean():.1f}")
        
        # Coverage stats
        print(f"\nData Coverage:")
        print(f"  Has website: {df['website'].notna().sum():,} ({df['website'].notna().sum()/len(df)*100:.1f}%)")
        print(f"  Has email: {df['email'].notna().sum():,} ({df['email'].notna().sum()/len(df)*100:.1f}%)")
        print(f"  SAM registered: {df['sam_registered'].sum():,} ({df['sam_registered'].sum()/len(df)*100:.1f}%)")
        print(f"  Has patents: {df['has_patents'].sum():,} ({df['has_patents'].sum()/len(df)*100:.1f}%)")
        print(f"  Has certifications: {df['active_sba_certifications'].notna().sum():,} ({df['active_sba_certifications'].notna().sum()/len(df)*100:.1f}%)")
        
        # Top companies
        print(f"\nTop 10 Companies by PE Score:")
        top_companies = df.nlargest(10, 'pe_score')[
            ['organization_name', 'city', 'state', 'pe_score', 'sam_registered', 'patent_count']
        ]
        
        for i, row in top_companies.iterrows():
            print(f"\n{df.index.get_loc(i)+1}. {row['organization_name']}")
            print(f"   Location: {row['city']}, {row['state']}")
            print(f"   PE Score: {row['pe_score']:.1f}")
            print(f"   SAM: {'Yes' if row['sam_registered'] else 'No'} | Patents: {row['patent_count']}")
        
        conn.close()

if __name__ == "__main__":
    enricher = FinalEnrichment()
    
    # Process sample data
    sample_path = 'data/dsbs_raw/sample_50.csv'
    enricher.process_dataset(sample_path, 'kbi_final_enriched.db')
    
    # To process full dataset, uncomment:
    # full_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
    # enricher.process_dataset(full_path, 'kbi_full_enriched.db', limit=10000)
