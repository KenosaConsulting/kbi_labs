#!/usr/bin/env python3
"""
KBI Labs Complete Enrichment Pipeline
Processes all 64,799 companies with all data sources in one seamless operation
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import os
from sqlalchemy import create_engine, text
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnrichmentConfig:
    """Configuration for all API endpoints and data sources"""
    
    # API Keys (from environment variables)
    SAM_GOV_API_KEY: str = os.getenv('SAM_GOV_API_KEY')
    CENSUS_API_KEY: str = os.getenv('CENSUS_API_KEY')
    USPTO_API_KEY: str = os.getenv('USPTO_API_KEY')
    NSF_API_KEY: str = os.getenv('NSF_API_KEY')
    FRED_API_KEY: str = os.getenv('FRED_API_KEY')
    
    # API Endpoints
    SAM_GOV_BASE_URL: str = "https://api.sam.gov/entity-information/v3"
    CENSUS_BASE_URL: str = "https://api.census.gov/data"
    USPTO_BASE_URL: str = "https://developer.uspto.gov/api/v1"
    NSF_BASE_URL: str = "https://www.research.gov/awardapi-service/v1"
    FRED_BASE_URL: str = "https://api.stlouisfed.org/fred"
    
    # Processing configuration
    BATCH_SIZE: int = 100
    MAX_CONCURRENT_REQUESTS: int = 50
    REQUEST_TIMEOUT: int = 30
    RETRY_ATTEMPTS: int = 3
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///kbi_enriched_full.db')

class DataEnricher:
    """Base class for all data enrichment sources"""
    
    def __init__(self, config: EnrichmentConfig):
        self.config = config
        self.session = None
    
    async def setup(self):
        """Initialize aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch(self, url: str, headers: Dict = None) -> Dict:
        """Fetch data with retry logic"""
        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.warning(f"API request failed: {url} - Status: {response.status}")
                return {}

class SAMGovEnricher(DataEnricher):
    """Enriches with SAM.gov federal contracting data"""
    
    async def enrich(self, company: Dict) -> Dict:
        """Get federal contracting history and registration status"""
        uei = company.get('uei')
        if not uei:
            return {}
        
        try:
            # Entity registration endpoint
            url = f"{self.config.SAM_GOV_BASE_URL}/entities/{uei}"
            headers = {'X-Api-Key': self.config.SAM_GOV_API_KEY}
            
            data = await self.fetch(url, headers)
            
            if data:
                # Extract key information
                registration = data.get('entityRegistration', {})
                core_data = registration.get('coreData', {})
                assertions = registration.get('assertions', {})
                
                return {
                    'sam_registration_status': registration.get('registrationStatus'),
                    'sam_registration_date': registration.get('registrationDate'),
                    'sam_expiration_date': registration.get('expirationDate'),
                    'cage_code': core_data.get('cageCode'),
                    'duns_number': core_data.get('dunsNumber'),
                    'naics_codes': core_data.get('naicsCode', []),
                    'business_types': core_data.get('businessTypes', []),
                    'socio_economic_types': assertions.get('socioEconomicCategories', {}),
                    'federal_contract_vehicles': assertions.get('contractVehicles', []),
                    'past_performance_rating': assertions.get('pastPerformance', {})
                }
        except Exception as e:
            logger.error(f"SAM.gov enrichment failed for {uei}: {e}")
            return {}
        
        return {}

class CensusEnricher(DataEnricher):
    """Enriches with Census economic and demographic data"""
    
    async def enrich(self, company: Dict) -> Dict:
        """Get economic indicators for company location"""
        state = company.get('state')
        zipcode = company.get('zipcode')
        naics = company.get('primary_naics')
        
        if not state:
            return {}
        
        try:
            enriched = {}
            
            # County Business Patterns API
            if naics:
                url = f"{self.config.CENSUS_BASE_URL}/2021/cbp"
                params = {
                    'get': 'EMP,PAYANN,ESTAB',
                    'for': f'state:{state}',
                    'NAICS2017': str(naics)[:2],
                    'key': self.config.CENSUS_API_KEY
                }
                
                data = await self.fetch(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
                
                if data and len(data) > 1:
                    headers = data[0]
                    values = data[1]
                    result = dict(zip(headers, values))
                    
                    enriched.update({
                        'industry_employment_state': int(result.get('EMP', 0)),
                        'industry_payroll_state': int(result.get('PAYANN', 0)),
                        'industry_establishments_state': int(result.get('ESTAB', 0))
                    })
            
            # Economic indicators
            if zipcode:
                # Add ZIP code level demographics
                enriched.update({
                    'zip_population': 0,  # Would fetch from appropriate endpoint
                    'zip_median_income': 0,
                    'zip_business_density': 0
                })
            
            return enriched
            
        except Exception as e:
            logger.error(f"Census enrichment failed for {company.get('uei')}: {e}")
            return {}

class PatentEnricher(DataEnricher):
    """Enriches with USPTO patent data"""
    
    async def enrich(self, company: Dict) -> Dict:
        """Search for patents by company name"""
        org_name = company.get('organization_name')
        if not org_name:
            return {}
        
        try:
            # Patent search API
            url = f"{self.config.USPTO_BASE_URL}/patents/search"
            params = {
                'query': f'assignee:"{org_name}"',
                'fields': 'patent_number,patent_date,patent_title,inventors'
            }
            
            data = await self.fetch(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
            
            if data:
                patents = data.get('patents', [])
                
                return {
                    'patent_count': len(patents),
                    'patents': patents[:10],  # First 10 patents
                    'latest_patent_date': max([p.get('patent_date', '') for p in patents]) if patents else None,
                    'patent_categories': list(set([p.get('category', '') for p in patents if p.get('category')]))
                }
        
        except Exception as e:
            logger.error(f"Patent enrichment failed for {org_name}: {e}")
            
        return {
            'patent_count': 0,
            'patents': []
        }

class NSFGrantEnricher(DataEnricher):
    """Enriches with NSF grant data"""
    
    async def enrich(self, company: Dict) -> Dict:
        """Search for NSF grants and awards"""
        org_name = company.get('organization_name')
        if not org_name:
            return {}
        
        try:
            # NSF Award Search API
            url = f"{self.config.NSF_BASE_URL}/award/search"
            params = {
                'awardeeOrganization': org_name,
                'printFields': 'id,title,date,awardeeName,fundsObligatedAmt,piFirstName,piLastName'
            }
            
            data = await self.fetch(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
            
            if data:
                awards = data.get('response', {}).get('award', [])
                
                if awards:
                    total_funding = sum([float(a.get('fundsObligatedAmt', 0)) for a in awards])
                    
                    return {
                        'nsf_grant_count': len(awards),
                        'nsf_total_funding': total_funding,
                        'nsf_grants': awards[:5],  # First 5 grants
                        'nsf_latest_grant_date': max([a.get('date', '') for a in awards]) if awards else None,
                        'nsf_research_areas': list(set([a.get('primaryProgram', '') for a in awards if a.get('primaryProgram')]))
                    }
        
        except Exception as e:
            logger.error(f"NSF enrichment failed for {org_name}: {e}")
        
        return {
            'nsf_grant_count': 0,
            'nsf_total_funding': 0
        }

class FREDEconomicEnricher(DataEnricher):
    """Enriches with FRED economic indicators"""
    
    async def enrich(self, company: Dict) -> Dict:
        """Get regional economic indicators"""
        state = company.get('state')
        if not state:
            return {}
        
        try:
            enriched = {}
            
            # State unemployment rate
            series_id = f"UR{state}"  # Unemployment rate series
            url = f"{self.config.FRED_BASE_URL}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.config.FRED_API_KEY,
                'limit': 1,
                'sort_order': 'desc',
                'file_type': 'json'
            }
            
            data = await self.fetch(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
            
            if data and data.get('observations'):
                latest = data['observations'][0]
                enriched['state_unemployment_rate'] = float(latest.get('value', 0))
                enriched['state_unemployment_date'] = latest.get('date')
            
            # Add more economic indicators as needed
            # - GDP by state
            # - Personal income
            # - Business formation rates
            
            return enriched
            
        except Exception as e:
            logger.error(f"FRED enrichment failed for state {state}: {e}")
            return {}

class CompleteEnrichmentPipeline:
    """Main pipeline that orchestrates all enrichment sources"""
    
    def __init__(self, config: EnrichmentConfig = None):
        self.config = config or EnrichmentConfig()
        
        # Initialize all enrichers
        self.enrichers = {
            'sam_gov': SAMGovEnricher(self.config),
            'census': CensusEnricher(self.config),
            'patents': PatentEnricher(self.config),
            'nsf_grants': NSFGrantEnricher(self.config),
            'fred_economic': FREDEconomicEnricher(self.config)
        }
        
        # Database connection
        self.engine = create_engine(self.config.DATABASE_URL)
        
        # Scoring engine
        from src.enrichment.scoring import PEInvestmentScorer
        self.scorer = PEInvestmentScorer()
    
    async def enrich_company(self, company: Dict) -> Dict:
        """Enrich a single company with all data sources"""
        uei = company.get('UEI (Unique Entity Identifier)')
        logger.info(f"Enriching company: {company.get('Organization Name')} ({uei})")
        
        # Prepare base data
        enriched = {
            'uei': uei,
            'organization_name': company.get('Organization Name'),
            'primary_naics': company.get('Primary NAICS code'),
            'state': company.get('State'),
            'city': company.get('City'),
            'zipcode': company.get('Zipcode'),
            'website': company.get('Website'),
            'phone_number': company.get('Phone number'),
            'email': company.get('Contact person\'s email'),
            'legal_structure': company.get('Legal structure'),
            'active_sba_certifications': company.get('Active SBA certifications'),
            'capabilities_narrative': company.get('Capabilities narrative'),
            'address_line_1': company.get('Address line 1'),
            'address_line_2': company.get('Address line 2'),
            'first_name': company.get('First Name'),
            'last_name': company.get('Last Name'),
            'job_title': company.get('Job Title'),
            'enrichment_timestamp': datetime.utcnow().isoformat()
        }
        
        # Run all enrichers concurrently
        enrichment_tasks = []
        for name, enricher in self.enrichers.items():
            task = enricher.enrich(enriched)
            enrichment_tasks.append((name, task))
        
        # Gather all enrichment results
        for name, task in enrichment_tasks:
            try:
                result = await task
                enriched.update(result)
            except Exception as e:
                logger.error(f"{name} enrichment failed for {uei}: {e}")
        
        # Calculate investment scores
        scoring_results = self.scorer.score_company(enriched)
        enriched.update({
            'pe_investment_score': scoring_results['pe_investment_score'],
            'business_health_grade': scoring_results['business_health_grade'],
            'scoring_metadata': json.dumps(scoring_results['scoring_details'])
        })
        
        return enriched
    
    async def process_batch(self, companies: List[Dict]) -> List[Dict]:
        """Process a batch of companies concurrently"""
        tasks = []
        
        # Limit concurrent processing
        semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_REQUESTS)
        
        async def process_with_semaphore(company):
            async with semaphore:
                return await self.enrich_company(company)
        
        for company in companies:
            task = process_with_semaphore(company)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        enriched_companies = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to enrich company {companies[i].get('Organization Name')}: {result}")
            else:
                enriched_companies.append(result)
        
        return enriched_companies
    
    def save_to_database(self, enriched_companies: List[Dict]):
        """Save enriched data to database"""
        df = pd.DataFrame(enriched_companies)
        
        # Save to database
        df.to_sql('enriched_companies_full', self.engine, if_exists='append', index=False)
        logger.info(f"Saved {len(enriched_companies)} companies to database")
    
    async def process_all_companies(self, csv_path: str):
        """Main entry point - process all 64,799 companies"""
        start_time = datetime.now()
        
        logger.info(f"Starting complete enrichment pipeline for {csv_path}")
        
        # Setup all enrichers
        for enricher in self.enrichers.values():
            await enricher.setup()
        
        try:
            # Read the CSV in chunks
            total_processed = 0
            
            for chunk in pd.read_csv(csv_path, chunksize=self.config.BATCH_SIZE):
                companies = chunk.to_dict('records')
                
                # Process batch
                enriched = await self.process_batch(companies)
                
                # Save to database
                self.save_to_database(enriched)
                
                total_processed += len(enriched)
                logger.info(f"Progress: {total_processed} companies processed")
                
                # Calculate and log statistics
                if total_processed % 1000 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = total_processed / elapsed
                    logger.info(f"Processing rate: {rate:.1f} companies/second")
        
        finally:
            # Cleanup all enrichers
            for enricher in self.enrichers.values():
                await enricher.cleanup()
        
        # Final statistics
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Complete enrichment finished!")
        logger.info(f"Total companies processed: {total_processed}")
        logger.info(f"Total time: {elapsed/60:.1f} minutes")
        logger.info(f"Average rate: {total_processed/elapsed:.1f} companies/second")
        
        # Generate summary report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate summary statistics after processing"""
        with self.engine.connect() as conn:
            # Get statistics
            stats = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_companies,
                    AVG(pe_investment_score) as avg_score,
                    MAX(pe_investment_score) as max_score,
                    MIN(pe_investment_score) as min_score,
                    COUNT(CASE WHEN business_health_grade = 'A' THEN 1 END) as grade_a,
                    COUNT(CASE WHEN business_health_grade = 'B' THEN 1 END) as grade_b,
                    COUNT(CASE WHEN business_health_grade = 'C' THEN 1 END) as grade_c,
                    COUNT(CASE WHEN business_health_grade = 'D' THEN 1 END) as grade_d,
                    COUNT(CASE WHEN business_health_grade = 'F' THEN 1 END) as grade_f,
                    COUNT(CASE WHEN sam_registration_status IS NOT NULL THEN 1 END) as sam_registered,
                    SUM(patent_count) as total_patents,
                    SUM(nsf_grant_count) as total_nsf_grants,
                    SUM(nsf_total_funding) as total_nsf_funding
                FROM enriched_companies_full
            """)).fetchone()
            
            print("\n" + "="*60)
            print("KBI LABS COMPLETE ENRICHMENT SUMMARY")
            print("="*60)
            print(f"Total Companies Processed: {stats['total_companies']:,}")
            print(f"\nPE Investment Scores:")
            print(f"  Average: {stats['avg_score']:.1f}")
            print(f"  Maximum: {stats['max_score']:.1f}")
            print(f"  Minimum: {stats['min_score']:.1f}")
            print(f"\nBusiness Health Grades:")
            print(f"  Grade A: {stats['grade_a']:,} ({stats['grade_a']/stats['total_companies']*100:.1f}%)")
            print(f"  Grade B: {stats['grade_b']:,} ({stats['grade_b']/stats['total_companies']*100:.1f}%)")
            print(f"  Grade C: {stats['grade_c']:,} ({stats['grade_c']/stats['total_companies']*100:.1f}%)")
            print(f"  Grade D: {stats['grade_d']:,} ({stats['grade_d']/stats['total_companies']*100:.1f}%)")
            print(f"  Grade F: {stats['grade_f']:,} ({stats['grade_f']/stats['total_companies']*100:.1f}%)")
            print(f"\nEnrichment Statistics:")
            print(f"  SAM.gov Registered: {stats['sam_registered']:,}")
            print(f"  Total Patents Found: {stats['total_patents']:,}")
            print(f"  Total NSF Grants: {stats['total_nsf_grants']:,}")
            print(f"  Total NSF Funding: ${stats['total_nsf_funding']:,.2f}")
            print("="*60)

def run_complete_enrichment():
    """Main function to run the complete enrichment pipeline"""
    
    # Check for required environment variables
    required_vars = ['SAM_GOV_API_KEY', 'CENSUS_API_KEY', 'USPTO_API_KEY', 'NSF_API_KEY', 'FRED_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("Missing required API keys:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these environment variables before running.")
        return
    
    # Create pipeline
    pipeline = CompleteEnrichmentPipeline()
    
    # Run the complete enrichment
    csv_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
    
    print("="*60)
    print("KBI LABS COMPLETE ENRICHMENT PIPELINE")
    print("="*60)
    print(f"Processing file: {csv_path}")
    print(f"This will enrich all companies with:")
    print("  - SAM.gov federal contracting data")
    print("  - US Census economic indicators")
    print("  - USPTO patent information")
    print("  - NSF grant history")
    print("  - FRED economic data")
    print("  - PE investment scoring")
    print("  - Business health grading")
    print("\nEstimated time: 2-3 hours")
    print("="*60)
    
    response = input("\nProceed with complete enrichment? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(pipeline.process_all_companies(csv_path))
    else:
        print("Enrichment cancelled.")

if __name__ == "__main__":
    run_complete_enrichment()
# (The file is too large to paste here, but copy everything from the artifact)
