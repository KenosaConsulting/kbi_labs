#!/usr/bin/env python3
"""
Production enrichment pipeline
Handles SAM.gov 404s gracefully and continues with other sources
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

class ProductionEnrichment:
    def __init__(self):
        # Load API keys
        self.sam_gov_api_key = os.getenv('SAM_GOV_API_KEY')
        self.census_api_key = os.getenv('CENSUS_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        
        # Track API statistics
        self.api_stats = {
            'sam_gov': {'success': 0, 'failed': 0},
            'census': {'success': 0, 'failed': 0},
            'fred': {'success': 0, 'failed': 0}
        }
        
        # Load local data files
        self.load_local_data()
    
    def load_local_data(self):
        """Load patent and NSF data"""
        # Patent data
        self.patent_lookup = {}
        patent_files = ['patent_data/' + f for f in os.listdir('patent_data/') if f.endswith('.tsv')]
        
        for file in patent_files[:3]:  # Limit for memory
            try:
                df = pd.read_csv(file, sep='\t', usecols=['organization', 'patent_id'], low_memory=False)
                for org in df['organization'].dropna().unique():
                    self.patent_lookup[org.lower()] = len(df[df['organization'] == org])
                logger.info(f"Loaded {file}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        # NSF data - similar approach
        self.nsf_lookup = {}
        # Add NSF loading logic here
    
    async def enrich_company(self, session, company):
        """Enrich a single company"""
        enriched = {
            'uei': company.get('UEI (Unique Entity Identifier)'),
            'organization_name': company.get('Organization Name'),
            'state': company.get('State'),
            'city': company.get('City'),
            'primary_naics': company.get('Primary NAICS code')
        }
        
        # Concurrent API calls
        tasks = []
        
        # SAM.gov (skip if no UEI)
        if enriched['uei']:
            tasks.append(self.get_sam_data(session, enriched['uei']))
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))  # Placeholder
        
        # Census (if state exists)
        if enriched['state']:
            tasks.append(self.get_census_data(session, enriched['state']))
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
        
        # FRED (if state exists)
        if enriched['state']:
            tasks.append(self.get_fred_data(session, enriched['state']))
        else:
            tasks.append(asyncio.create_task(asyncio.sleep(0)))
        
        # Execute all API calls
        sam_data, census_data, fred_data = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        if isinstance(sam_data, dict):
            enriched.update(sam_data)
        if isinstance(census_data, dict):
            enriched.update(census_data)
        if isinstance(fred_data, dict):
            enriched.update(fred_data)
        
        # Add local data lookups
        org_name = enriched.get('organization_name', '').lower()
        enriched['patent_count'] = self.patent_lookup.get(org_name, 0)
        enriched['nsf_grant_count'] = self.nsf_lookup.get(org_name, 0)
        
        # Add metadata
        enriched['enrichment_timestamp'] = datetime.now().isoformat()
        
        return enriched
    
    async def get_sam_data(self, session, uei):
        """Get SAM.gov data"""
        try:
            url = f"https://api.sam.gov/entity-information/v3/entities/{uei}"
            headers = {'X-Api-Key': self.sam_gov_api_key}
            
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    self.api_stats['sam_gov']['success'] += 1
                    data = await response.json()
                    entity = data.get('entityData', [{}])[0] if data.get('entityData') else {}
                    
                    return {
                        'sam_status': 'ACTIVE',
                        'sam_cage_code': entity.get('cageCode'),
                        'sam_registration_date': entity.get('entityRegistration', {}).get('registrationDate')
                    }
                elif response.status == 404:
                    self.api_stats['sam_gov']['failed'] += 1
                    return {'sam_status': 'NOT_FOUND'}
                else:
                    self.api_stats['sam_gov']['failed'] += 1
                    return {'sam_status': f'ERROR_{response.status}'}
                    
        except Exception as e:
            self.api_stats['sam_gov']['failed'] += 1
            return {'sam_status': 'ERROR'}
    
    async def get_census_data(self, session, state):
        """Get Census data"""
        try:
            # Map state names to FIPS codes if needed
            state_fips = {
                'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
                'CO': '08', 'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13',
                'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19',
                'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24',
                'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29',
                'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
                'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
                'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45',
                'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50',
                'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56'
            }
            
            state_code = state_fips.get(state, state)
            
            url = "https://api.census.gov/data/2021/acs/acs5"
            params = {
                'get': 'B01003_001E,B19013_001E',
                'for': f'state:{state_code}',
                'key': self.census_api_key
            }
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    self.api_stats['census']['success'] += 1
                    data = await response.json()
                    if len(data) > 1:
                        values = data[1]
                        return {
                            'census_population': int(values[0]) if values[0] else None,
                            'census_median_income': int(values[1]) if values[1] else None
                        }
                else:
                    self.api_stats['census']['failed'] += 1
                    
        except Exception as e:
            self.api_stats['census']['failed'] += 1
            
        return {}
    
    async def get_fred_data(self, session, state):
        """Get FRED data"""
        try:
            # Construct series ID for state unemployment
            series_id = f"{state}UR"
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    self.api_stats['fred']['success'] += 1
                    data = await response.json()
                    obs = data.get('observations', [])
                    
                    if obs:
                        return {
                            'fred_unemployment': float(obs[0].get('value')),
                            'fred_date': obs[0].get('date')
                        }
                else:
                    self.api_stats['fred']['failed'] += 1
                    
        except Exception as e:
            self.api_stats['fred']['failed'] += 1
            
        return {}
    
    async def process_batch(self, companies_df):
        """Process a batch of companies"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for _, company in companies_df.iterrows():
                task = self.enrich_company(session, company.to_dict())
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
    
    def process_dataset(self, csv_path, output_db='kbi_production_enriched.db'):
        """Process the entire dataset"""
        print(f"\nProcessing {csv_path}...")
        
        # Create database
        conn = sqlite3.connect(output_db)
        
        # Process in chunks
        chunk_size = 100
        total_processed = 0
        start_time = time.time()
        
        for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            # Run async processing
            enriched = asyncio.run(self.process_batch(chunk))
            
            # Save to database
            df_enriched = pd.DataFrame(enriched)
            df_enriched.to_sql('enriched_companies', conn, 
                             if_exists='append' if chunk_num > 0 else 'replace', 
                             index=False)
            
            total_processed += len(chunk)
            
            # Progress update
            elapsed = time.time() - start_time
            rate = total_processed / elapsed
            
            print(f"\rProcessed: {total_processed:,} companies ({rate:.1f}/sec) - "
                  f"SAM: {self.api_stats['sam_gov']['success']}/{self.api_stats['sam_gov']['failed']} "
                  f"Census: {self.api_stats['census']['success']}/{self.api_stats['census']['failed']} "
                  f"FRED: {self.api_stats['fred']['success']}/{self.api_stats['fred']['failed']}", 
                  end='')
            
            # Break after a few chunks for testing
            if chunk_num >= 2:  # Remove this for full processing
                break
        
        conn.close()
        
        print(f"\n\nEnrichment complete!")
        print(f"Total time: {(time.time() - start_time)/60:.1f} minutes")
        print(f"Output saved to: {output_db}")
        
        # Show summary
        self.show_summary(output_db)
    
    def show_summary(self, db_path):
        """Show enrichment summary"""
        conn = sqlite3.connect(db_path)
        
        # Get counts
        df = pd.read_sql_query("SELECT * FROM enriched_companies", conn)
        
        print(f"\n=== Enrichment Summary ===")
        print(f"Total companies: {len(df):,}")
        
        # SAM.gov coverage
        sam_found = (df['sam_status'] == 'ACTIVE').sum()
        print(f"\nSAM.gov: {sam_found:,} active registrations ({sam_found/len(df)*100:.1f}%)")
        
        # Census coverage
        census_found = df['census_population'].notna().sum()
        print(f"Census: {census_found:,} with data ({census_found/len(df)*100:.1f}%)")
        
        # FRED coverage
        fred_found = df['fred_unemployment'].notna().sum()
        print(f"FRED: {fred_found:,} with data ({fred_found/len(df)*100:.1f}%)")
        
        # Patent coverage
        patent_found = (df['patent_count'] > 0).sum()
        print(f"Patents: {patent_found:,} with patents ({patent_found/len(df)*100:.1f}%)")
        
        conn.close()

if __name__ == "__main__":
    enricher = ProductionEnrichment()
    
    # Test with sample first
    sample_path = 'data/dsbs_raw/sample_50.csv'
    enricher.process_dataset(sample_path, 'test_production_enriched.db')
    
    # If successful, uncomment to run full dataset:
    # full_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
    # enricher.process_dataset(full_path, 'kbi_full_production_enriched.db')
