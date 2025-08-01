#!/usr/bin/env python3
"""
KBI Labs Integrated Enrichment
Combines API calls (SAM.gov, Census, FRED) with local data files (USPTO, NSF)
"""

import os
import pandas as pd
import sqlite3
import json
import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, Optional
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedEnrichment:
    def __init__(self):
        # Load API keys
        self.sam_gov_api_key = os.getenv('SAM_GOV_API_KEY')
        self.census_api_key = os.getenv('CENSUS_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        
        # Load local data files
        self.load_patent_data()
        self.load_nsf_data()
        
        # Check what's available
        self.check_availability()
    
    def check_availability(self):
        """Check which data sources are available"""
        print("\n=== Data Source Availability ===")
        
        # APIs
        if self.sam_gov_api_key and self.sam_gov_api_key != 'your_actual_sam_gov_key_here':
            print("✓ SAM.gov API: Ready")
        else:
            print("✗ SAM.gov API: Need to add key to .env")
            
        if self.census_api_key and self.census_api_key != 'need_to_register':
            print("✓ Census API: Ready")
        else:
            print("✗ Census API: Need to register at https://api.census.gov/data/key_signup.html")
            
        if self.fred_api_key and self.fred_api_key != 'your_actual_fred_key_here':
            print("✓ FRED API: Ready")
        else:
            print("✗ FRED API: Need to add key to .env")
        
        # Local files
        if hasattr(self, 'patent_data') and len(self.patent_data) > 0:
            print(f"✓ Patent Data: {len(self.patent_data):,} records loaded")
        else:
            print("✗ Patent Data: No data loaded")
            
        if hasattr(self, 'nsf_data') and len(self.nsf_data) > 0:
            print(f"✓ NSF Data: {len(self.nsf_data):,} records loaded")
        else:
            print("✗ NSF Data: No data loaded")
    
    def load_patent_data(self):
        """Load USPTO patent data from local files"""
        patent_path = 'patent_data/'
        self.patent_data = pd.DataFrame()
        
        if os.path.exists(patent_path):
            # Load all TSV files in patent_data directory
            for file in os.listdir(patent_path):
                if file.endswith('.tsv'):
                    try:
                        df = pd.read_csv(os.path.join(patent_path, file), 
                                       sep='\t', 
                                       low_memory=False)
                        self.patent_data = pd.concat([self.patent_data, df], 
                                                   ignore_index=True)
                        logger.info(f"Loaded patent file: {file}")
                    except Exception as e:
                        logger.error(f"Error loading {file}: {e}")
            
            if len(self.patent_data) > 0:
                # Create lookup index by organization name
                self.patent_data['org_name_lower'] = self.patent_data.get('organization', '').str.lower()
                logger.info(f"Total patent records loaded: {len(self.patent_data):,}")
    
    def load_nsf_data(self):
        """Load NSF grant data from local files"""
        nsf_path = 'nsf_data/'
        self.nsf_data = pd.DataFrame()
        
        if os.path.exists(nsf_path):
            # Load NSF data files
            for file in os.listdir(nsf_path):
                if file.endswith('.csv') or file.endswith('.json'):
                    try:
                        if file.endswith('.csv'):
                            df = pd.read_csv(os.path.join(nsf_path, file))
                        else:
                            df = pd.read_json(os.path.join(nsf_path, file))
                        
                        self.nsf_data = pd.concat([self.nsf_data, df], 
                                                ignore_index=True)
                        logger.info(f"Loaded NSF file: {file}")
                    except Exception as e:
                        logger.error(f"Error loading {file}: {e}")
            
            if len(self.nsf_data) > 0:
                logger.info(f"Total NSF records loaded: {len(self.nsf_data):,}")
    
    async def enrich_with_sam_gov(self, session, uei):
        """Call SAM.gov API"""
        if not self.sam_gov_api_key or not uei:
            return {}
        
        try:
            url = f"https://api.sam.gov/entity-information/v3/entities/{uei}"
            headers = {'X-Api-Key': self.sam_gov_api_key}
            
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    entity = data.get('entityData', [{}])[0] if data.get('entityData') else {}
                    
                    return {
                        'sam_registration_status': entity.get('entityRegistration', {}).get('registrationStatus'),
                        'sam_cage_code': entity.get('cageCode'),
                        'sam_business_types': json.dumps(entity.get('businessTypes', [])),
                        'sam_registration_date': entity.get('entityRegistration', {}).get('registrationDate')
                    }
        except Exception as e:
            logger.error(f"SAM.gov API error: {e}")
        
        return {}
    
    async def enrich_with_census(self, session, state, zipcode):
        """Call Census API"""
        if not self.census_api_key or not state:
            return {}
        
        try:
            # Get state-level economic data
            url = "https://api.census.gov/data/2021/acs/acs5"
            params = {
                'get': 'B01003_001E,B19013_001E',  # Population, Median Income
                'for': f'state:{state}',
                'key': self.census_api_key
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data) > 1:
                        values = data[1]
                        return {
                            'census_state_population': int(values[0]) if values[0] else None,
                            'census_state_median_income': int(values[1]) if values[1] else None
                        }
        except Exception as e:
            logger.error(f"Census API error: {e}")
        
        return {}
    
    async def enrich_with_fred(self, session, state):
        """Call FRED API"""
        if not self.fred_api_key or not state:
            return {}
        
        try:
            # Map state to FRED series ID
            series_id = f"{state}UR"  # State unemployment rate
            
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    observations = data.get('observations', [])
                    
                    if observations:
                        latest = observations[0]
                        return {
                            'fred_unemployment_rate': float(latest.get('value')),
                            'fred_unemployment_date': latest.get('date')
                        }
        except Exception as e:
            logger.error(f"FRED API error: {e}")
        
        return {}
    
    def enrich_with_patent_data(self, org_name):
        """Look up patent data from local files"""
        if not hasattr(self, 'patent_data') or self.patent_data.empty or not org_name:
            return {}
        
        # Search for organization
        org_lower = org_name.lower()
        matches = self.patent_data[
            self.patent_data['org_name_lower'].str.contains(org_lower, na=False)
        ]
        
        if len(matches) > 0:
            return {
                'patent_count': len(matches),
                'patent_years': matches['year'].unique().tolist() if 'year' in matches.columns else [],
                'patent_titles': matches['title'].head(5).tolist() if 'title' in matches.columns else []
            }
        
        return {'patent_count': 0}
    
    def enrich_with_nsf_data(self, org_name):
        """Look up NSF grant data from local files"""
        if not hasattr(self, 'nsf_data') or self.nsf_data.empty or not org_name:
            return {}
        
        # Search for organization in NSF data
        org_lower = org_name.lower()
        
        # Try different column names that might contain organization
        org_columns = ['AwardeeOrganization', 'Institution', 'Organization', 'Awardee']
        
        matches = pd.DataFrame()
        for col in org_columns:
            if col in self.nsf_data.columns:
                temp_matches = self.nsf_data[
                    self.nsf_data[col].str.lower().str.contains(org_lower, na=False)
                ]
                matches = pd.concat([matches, temp_matches])
                break
        
        if len(matches) > 0:
            # Calculate total funding
            funding_columns = ['AwardAmount', 'AwardedAmountToDate', 'Amount']
            total_funding = 0
            
            for col in funding_columns:
                if col in matches.columns:
                    total_funding = matches[col].sum()
                    break
            
            return {
                'nsf_grant_count': len(matches),
                'nsf_total_funding': float(total_funding),
                'nsf_grant_years': matches['AwardEffectiveDate'].str[:4].unique().tolist() if 'AwardEffectiveDate' in matches.columns else []
            }
        
        return {'nsf_grant_count': 0, 'nsf_total_funding': 0}
    
    async def enrich_company(self, company_data):
        """Enrich a single company with all available sources"""
        enriched = company_data.copy()
        
        # Extract key fields
        uei = company_data.get('uei')
        org_name = company_data.get('organization_name')
        state = company_data.get('state')
        zipcode = company_data.get('zipcode')
        
        # API calls (concurrent)
        async with aiohttp.ClientSession() as session:
            api_tasks = []
            
            # SAM.gov
            api_tasks.append(self.enrich_with_sam_gov(session, uei))
            
            # Census
            api_tasks.append(self.enrich_with_census(session, state, zipcode))
            
            # FRED
            api_tasks.append(self.enrich_with_fred(session, state))
            
            # Execute API calls
            api_results = await asyncio.gather(*api_tasks)
            
            # Merge API results
            for result in api_results:
                enriched.update(result)
        
        # Local file lookups
        enriched.update(self.enrich_with_patent_data(org_name))
        enriched.update(self.enrich_with_nsf_data(org_name))
        
        # Add metadata
        enriched['enrichment_timestamp'] = datetime.now().isoformat()
        enriched['data_sources_used'] = self.get_data_sources_used(enriched)
        
        return enriched
    
    def get_data_sources_used(self, enriched_data):
        """Track which data sources were successfully used"""
        sources = []
        
        if enriched_data.get('sam_registration_status'):
            sources.append('SAM.gov')
        if enriched_data.get('census_state_population'):
            sources.append('Census')
        if enriched_data.get('fred_unemployment_rate'):
            sources.append('FRED')
        if enriched_data.get('patent_count', 0) > 0:
            sources.append('USPTO')
        if enriched_data.get('nsf_grant_count', 0) > 0:
            sources.append('NSF')
            
        return json.dumps(sources)
    
    async def process_companies(self, companies_df, output_db='kbi_fully_enriched.db'):
        """Process a dataframe of companies"""
        print(f"\nProcessing {len(companies_df)} companies...")
        
        # Create output database
        conn = sqlite3.connect(output_db)
        
        # Process in batches
        batch_size = 10
        all_enriched = []
        
        for i in range(0, len(companies_df), batch_size):
            batch = companies_df.iloc[i:i+batch_size]
            
            # Process batch
            tasks = []
            for _, company in batch.iterrows():
                tasks.append(self.enrich_company(company.to_dict()))
            
            enriched_batch = await asyncio.gather(*tasks)
            all_enriched.extend(enriched_batch)
            
            print(f"Progress: {min(i+batch_size, len(companies_df))}/{len(companies_df)}")
        
        # Save to database
        enriched_df = pd.DataFrame(all_enriched)
        enriched_df.to_sql('companies_fully_enriched', conn, if_exists='replace', index=False)
        
        conn.close()
        print(f"\n✓ Saved {len(all_enriched)} enriched companies to {output_db}")
        
        # Show summary
        self.show_enrichment_summary(enriched_df)
    
    def show_enrichment_summary(self, df):
        """Show summary of enrichment results"""
        print("\n=== Enrichment Summary ===")
        
        # Count successful enrichments
        sam_count = df['sam_registration_status'].notna().sum()
        census_count = df['census_state_population'].notna().sum()
        fred_count = df['fred_unemployment_rate'].notna().sum()
        patent_count = (df['patent_count'] > 0).sum()
        nsf_count = (df['nsf_grant_count'] > 0).sum()
        
        total = len(df)
        
        print(f"\nData Source Coverage:")
        print(f"  SAM.gov: {sam_count}/{total} ({sam_count/total*100:.1f}%)")
        print(f"  Census: {census_count}/{total} ({census_count/total*100:.1f}%)")
        print(f"  FRED: {fred_count}/{total} ({fred_count/total*100:.1f}%)")
        print(f"  Patents: {patent_count}/{total} ({patent_count/total*100:.1f}%)")
        print(f"  NSF Grants: {nsf_count}/{total} ({nsf_count/total*100:.1f}%)")
        
        # Show some enriched examples
        print("\nTop Patent Holders:")
        top_patents = df.nlargest(5, 'patent_count')[['organization_name', 'patent_count']]
        for _, row in top_patents.iterrows():
            print(f"  {row['organization_name']}: {row['patent_count']} patents")
        
        print("\nTop NSF Grant Recipients:")
        top_nsf = df.nlargest(5, 'nsf_total_funding')[['organization_name', 'nsf_grant_count', 'nsf_total_funding']]
        for _, row in top_nsf.iterrows():
            print(f"  {row['organization_name']}: {row['nsf_grant_count']} grants (${row['nsf_total_funding']:,.0f})")

# Test function
async def test_enrichment():
    """Test the enrichment with sample data"""
    enricher = IntegratedEnrichment()
    
    # Load sample companies
    sample_df = pd.read_csv('data/dsbs_raw/sample_50.csv', nrows=5)
    
    # Process them
    await enricher.process_companies(sample_df, 'test_enrichment.db')

if __name__ == "__main__":
    # First, add your actual API keys to the .env file!
    print("\nREMINDER: Add your actual API keys to .env file:")
    print("1. SAM.gov API key")
    print("2. Census API key (register at: https://api.census.gov/data/key_signup.html)")
    print("3. FRED API key")
    
    # Run test
    asyncio.run(test_enrichment())
