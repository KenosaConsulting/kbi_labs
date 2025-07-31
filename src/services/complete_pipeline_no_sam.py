#!/usr/bin/env python3
"""
KBI Labs Complete Enrichment Pipeline
Works with rate-limited SAM.gov API and uses your existing NSF data
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import sqlite3
import json
import os
import time
from datetime import datetime
import logging
from dotenv import load_dotenv
import glob

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kbi_enrichment_complete.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteEnrichmentPipeline:
    """
    Complete enrichment pipeline that handles rate limiting and uses local data
    """
    
    def __init__(self, batch_size: int = 100, max_concurrent: int = 25):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        
        # API Keys
        self.sam_gov_api_key = os.getenv('SAM_GOV_API_KEY')
        self.census_api_key = os.getenv('CENSUS_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'census_enriched': 0,
            'fred_enriched': 0,
            'patent_matched': 0,
            'nsf_matched': 0,
            'sam_attempts': 0,
            'sam_success': 0,
            'errors': 0
        }
        
        # Pre-load data
        self.nsf_data = None
        self.patent_data = None
        self.sam_cache = {}  # Cache SAM.gov results to avoid repeated calls
        
        # State name to FIPS code mapping
        self.state_fips = {
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
        
        # NAICS industry mapping
        self.naics_mapping = self._load_naics_mapping()
        
    async def process_all_companies(self, csv_path: str, output_db: str):
        """
        Main entry point - processes all companies
        """
        logger.info(f"Starting complete enrichment of {csv_path}")
        start_time = time.time()
        
        # Create database
        self._create_database(output_db)
        
        # Load all local data sources
        logger.info("Loading local data sources...")
        self._load_local_data()
        
        # Count total rows
        total_rows = sum(1 for _ in open(csv_path)) - 1
        logger.info(f"Total companies to process: {total_rows:,}")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process in batches
        async with aiohttp.ClientSession() as session:
            for chunk_num, chunk_df in enumerate(pd.read_csv(csv_path, chunksize=self.batch_size)):
                logger.info(f"Processing batch {chunk_num + 1} ({len(chunk_df)} companies)")
                
                # Enrich all companies in batch
                tasks = []
                for _, company in chunk_df.iterrows():
                    task = self._enrich_company_with_semaphore(
                        company, session, semaphore
                    )
                    tasks.append(task)
                
                # Wait for batch to complete
                enriched_batch = await asyncio.gather(*tasks)
                
                # Save to database
                self._save_batch_to_db(enriched_batch, output_db)
                
                # Update progress
                self.stats['total_processed'] += len(chunk_df)
                self._log_progress(total_rows, start_time)
                
                # Add delay between batches to avoid rate limiting
                if chunk_num % 10 == 0 and chunk_num > 0:
                    logger.info("Pausing to avoid rate limits...")
                    await asyncio.sleep(5)
        
        # Final report
        self._generate_final_report(output_db, start_time)
        
    def _load_local_data(self):
        """Load NSF and patent data from local files"""
        
        # Load NSF data from your existing file
        try:
            logger.info("Loading NSF data from dsbs_with_nsf_innovation.csv...")
            self.nsf_data = pd.read_csv('dsbs_with_nsf_innovation.csv')
            logger.info(f"Loaded {len(self.nsf_data)} companies with NSF data")
            
            # Index by organization name for fast lookup
            self.nsf_lookup = {}
            for _, row in self.nsf_data.iterrows():
                org_name = str(row.get('Organization Name', '')).lower()
                if org_name:
                    self.nsf_lookup[org_name] = {
                        'awards_count': row.get('nsf_awards_count', 0),
                        'total_funding': row.get('nsf_total_funding', 0),
                        'recent_awards': row.get('nsf_recent_awards', [])
                    }
        except Exception as e:
            logger.error(f"Error loading NSF data: {e}")
            self.nsf_lookup = {}
            
        # Load patent data if available
        self._load_patent_data()
        
    def _load_patent_data(self):
        """Load patent data from local files"""
        self.patent_lookup = {}
        patent_path = 'patent_data/'
        
        if os.path.exists(patent_path):
            try:
                logger.info("Loading patent data...")
                patent_files = glob.glob(os.path.join(patent_path, '*.tsv'))
                
                for file in patent_files[:5]:  # Limit to first 5 files for memory
                    try:
                        df = pd.read_csv(file, sep='\t', nrows=100000)  # Limit rows
                        
                        # Look for organization columns
                        org_cols = [col for col in df.columns if 'org' in col.lower()]
                        if org_cols:
                            org_col = org_cols[0]
                            for _, row in df.iterrows():
                                org = str(row.get(org_col, '')).lower()
                                if org and org != 'nan':
                                    if org not in self.patent_lookup:
                                        self.patent_lookup[org] = 0
                                    self.patent_lookup[org] += 1
                                    
                    except Exception as e:
                        logger.debug(f"Error loading {file}: {e}")
                        
                logger.info(f"Loaded patent data for {len(self.patent_lookup)} organizations")
                
            except Exception as e:
                logger.error(f"Error loading patent data: {e}")
                
    async def _enrich_company_with_semaphore(self, company: pd.Series, 
                                           session: aiohttp.ClientSession,
                                           semaphore: asyncio.Semaphore) -> Dict:
        """Rate-limited company enrichment"""
        async with semaphore:
            return await self._enrich_single_company(company, session)
            
    async def _enrich_single_company(self, company: pd.Series, 
                                    session: aiohttp.ClientSession) -> Dict:
        """
        Enriches a single company with all available data sources
        """
        try:
            # Start with basic info
            enriched = {
                'uei': company.get('UEI (Unique Entity Identifier)'),
                'organization_name': company.get('Organization Name'),
                'primary_naics': str(company.get('Primary NAICS code', '')),
                'state': company.get('State'),
                'city': company.get('City'),
                'zipcode': company.get('Zipcode'),
                'website': company.get('Website'),
                'phone_number': company.get('Phone number'),
                'email': company.get('Email'),
                'legal_structure': company.get('Legal structure'),
                'active_sba_certifications': company.get('Active SBA certifications'),
                'capabilities_narrative': company.get('Capabilities narrative'),
                'enrichment_timestamp': datetime.now().isoformat()
            }
            
            # API enrichments (only Census and FRED due to SAM.gov rate limits)
            census_task = self._enrich_census(enriched['state'], session)
            fred_task = self._enrich_fred(enriched['state'], session)
            
            # Execute API calls
            census_data, fred_data = await asyncio.gather(
                census_task, fred_task,
                return_exceptions=True
            )
            
            # Merge API results
            if isinstance(census_data, dict):
                enriched.update(census_data)
                self.stats['census_enriched'] += 1
                
            if isinstance(fred_data, dict):
                enriched.update(fred_data)
                self.stats['fred_enriched'] += 1
            
            # Local data enrichment
            # NSF data
            nsf_data = self._enrich_nsf_local(enriched['organization_name'])
            enriched.update(nsf_data)
            if nsf_data.get('nsf_awards_count', 0) > 0:
                self.stats['nsf_matched'] += 1
            
            # Patent data
            patent_data = self._enrich_patents_local(enriched['organization_name'])
            enriched.update(patent_data)
            if patent_data.get('patent_count', 0) > 0:
                self.stats['patent_matched'] += 1
            
            # SAM.gov registration estimate (based on business characteristics)
            sam_estimate = self._estimate_sam_registration(enriched)
            enriched.update(sam_estimate)
            
            # Calculate scores
            scores = self._calculate_scores(enriched)
            enriched.update(scores)
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error enriching {company.get('Organization Name')}: {e}")
            self.stats['errors'] += 1
            return {
                'uei': company.get('UEI (Unique Entity Identifier)'),
                'organization_name': company.get('Organization Name'),
                'error': str(e)
            }
    
    async def _enrich_census(self, state: str, session: aiohttp.ClientSession) -> Dict:
        """Get Census economic data"""
        if not state or not self.census_api_key:
            return {}
            
        try:
            # Get state FIPS code
            fips = self.state_fips.get(state)
            if not fips:
                return {}
                
            # Get economic indicators
            url = "https://api.census.gov/data/2022/acs/acs5"
            params = {
                'get': 'B01003_001E,B19013_001E,B15003_022E,B15003_023E,B15003_024E,B15003_025E',
                'for': f'state:{fips}',
                'key': self.census_api_key
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if len(data) > 1:
                        values = data[1]
                        return {
                            'census_state_population': int(values[0]) if values[0] else 0,
                            'census_median_income': int(values[1]) if values[1] else 0,
                            'census_bachelors_degree': int(values[2]) if values[2] else 0,
                            'census_masters_degree': int(values[3]) if values[3] else 0,
                            'census_professional_degree': int(values[4]) if values[4] else 0,
                            'census_doctorate_degree': int(values[5]) if values[5] else 0
                        }
        except Exception as e:
            logger.debug(f"Census API error for {state}: {e}")
            
        return {}
    
    async def _enrich_fred(self, state: str, session: aiohttp.ClientSession) -> Dict:
        """Get FRED economic indicators"""
        if not state or not self.fred_api_key:
            return {}
            
        try:
            # Use national unemployment rate
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'UNRATE',
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
            logger.debug(f"FRED API error: {e}")
            
        return {}
    
    def _enrich_nsf_local(self, org_name: str) -> Dict:
        """Look up NSF data from local file"""
        if not org_name or not self.nsf_lookup:
            return {'nsf_awards_count': 0, 'nsf_total_funding': 0}
            
        org_lower = org_name.lower()
        
        # Direct lookup
        if org_lower in self.nsf_lookup:
            data = self.nsf_lookup[org_lower]
            return {
                'nsf_awards_count': data['awards_count'],
                'nsf_total_funding': data['total_funding'],
                'nsf_recent_awards': json.dumps(data['recent_awards'])
            }
        
        # Fuzzy matching
        for nsf_org, data in self.nsf_lookup.items():
            if org_lower in nsf_org or nsf_org in org_lower:
                return {
                    'nsf_awards_count': data['awards_count'],
                    'nsf_total_funding': data['total_funding'],
                    'nsf_recent_awards': json.dumps(data['recent_awards'])
                }
        
        return {'nsf_awards_count': 0, 'nsf_total_funding': 0}
    
    def _enrich_patents_local(self, org_name: str) -> Dict:
        """Look up patent data from local file"""
        if not org_name or not self.patent_lookup:
            return {'patent_count': 0}
            
        org_lower = org_name.lower()
        
        # Direct lookup
        if org_lower in self.patent_lookup:
            return {'patent_count': self.patent_lookup[org_lower]}
        
        # Partial matching
        patent_count = 0
        for patent_org, count in self.patent_lookup.items():
            if org_lower in patent_org or patent_org in org_lower:
                patent_count += count
                
        return {'patent_count': patent_count}
    
    def _estimate_sam_registration(self, company: Dict) -> Dict:
        """
        Estimate SAM.gov registration likelihood based on company characteristics
        """
        # Factors that indicate likely SAM registration
        score = 0
        
        # Has government-related certifications
        certs = str(company.get('active_sba_certifications', ''))
        if any(cert in certs for cert in ['8(a)', 'HUBZone', 'WOSB', 'EDWOSB', 'VOSB', 'SDVOSB']):
            score += 80  # Very likely registered
            
        # Professional services or IT (common government contractors)
        naics = str(company.get('primary_naics', ''))[:2]
        if naics in ['54', '51', '23', '33']:  # Professional, IT, Construction, Manufacturing
            score += 20
            
        # Has formal business structure
        structure = str(company.get('legal_structure', ''))
        if any(s in structure for s in ['Corporation', 'LLC', 'Partnership']):
            score += 10
            
        # Has website (professional presence)
        if company.get('website'):
            score += 10
            
        # Location near federal facilities
        fed_states = ['Virginia', 'Maryland', 'District of Columbia', 'California', 'Texas']
        if company.get('state') in fed_states:
            score += 10
            
        return {
            'sam_registration_likelihood': min(100, score),
            'sam_registration_estimated': 'Likely' if score >= 50 else 'Unlikely'
        }
    
    def _calculate_scores(self, company: Dict) -> Dict:
        """
        Calculate PE investment score and business health grade
        """
        score = 50.0  # Base score
        
        # Industry factors (30%)
        naics = str(company.get('primary_naics', ''))
        if naics:
            industry_info = self.naics_mapping.get(naics[:2], {})
            growth_rate = industry_info.get('growth_rate', 0)
            score += growth_rate * 3  # Max 30 points
        
        # Market location factors (25%)
        if company.get('state') in ['California', 'Texas', 'New York', 'Florida']:
            score += 15
        elif company.get('state') in ['Illinois', 'Pennsylvania', 'Ohio', 'Georgia']:
            score += 10
        else:
            score += 5
            
        # Add population density bonus
        population = company.get('census_state_population', 0)
        if population > 20000000:
            score += 10
        elif population > 10000000:
            score += 7
        elif population > 5000000:
            score += 5
        
        # Digital presence (20%)
        if company.get('website'):
            score += 10
            if '.com' in str(company.get('website', '')):
                score += 5
            if 'https' in str(company.get('website', '')):
                score += 5
        
        # Certifications (15%)
        certs = str(company.get('active_sba_certifications', ''))
        if '8(a)' in certs:
            score += 8
        if 'HUBZone' in certs:
            score += 4
        if 'WOSB' in certs or 'EDWOSB' in certs:
            score += 3
        
        # Business structure (10%)
        structure = str(company.get('legal_structure', ''))
        if 'Corporation' in structure:
            score += 10
        elif 'LLC' in structure:
            score += 8
        else:
            score += 3
        
        # Innovation bonus
        if company.get('patent_count', 0) > 0:
            score += min(10, company.get('patent_count', 0))
        
        if company.get('nsf_awards_count', 0) > 0:
            score += min(10, company.get('nsf_awards_count', 0) * 2)
        
        # Federal contracting potential
        if company.get('sam_registration_likelihood', 0) >= 50:
            score += 5
        
        # Calculate grade
        if score >= 85:
            grade = 'A'
        elif score >= 75:
            grade = 'B'
        elif score >= 65:
            grade = 'C'
        elif score >= 55:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'pe_investment_score': min(100, max(0, score)),
            'business_health_grade': grade,
            'scoring_factors': json.dumps({
                'industry_score': naics[:2] if naics else 'Unknown',
                'location_score': company.get('state', 'Unknown'),
                'digital_score': bool(company.get('website')),
                'certification_score': bool(certs),
                'structure_score': structure,
                'innovation_score': company.get('patent_count', 0) + company.get('nsf_awards_count', 0)
            })
        }
    
    def _load_naics_mapping(self) -> Dict:
        """Load NAICS industry mapping with growth rates"""
        return {
            '11': {'name': 'Agriculture', 'growth_rate': 2},
            '21': {'name': 'Mining', 'growth_rate': 1},
            '22': {'name': 'Utilities', 'growth_rate': 3},
            '23': {'name': 'Construction', 'growth_rate': 4},
            '31': {'name': 'Manufacturing', 'growth_rate': 3},
            '32': {'name': 'Manufacturing', 'growth_rate': 3},
            '33': {'name': 'Manufacturing', 'growth_rate': 3},
            '42': {'name': 'Wholesale Trade', 'growth_rate': 3},
            '44': {'name': 'Retail Trade', 'growth_rate': 2},
            '45': {'name': 'Retail Trade', 'growth_rate': 2},
            '48': {'name': 'Transportation', 'growth_rate': 4},
            '49': {'name': 'Transportation', 'growth_rate': 4},
            '51': {'name': 'Information', 'growth_rate': 6},
            '52': {'name': 'Finance', 'growth_rate': 5},
            '53': {'name': 'Real Estate', 'growth_rate': 4},
            '54': {'name': 'Professional Services', 'growth_rate': 7},
            '55': {'name': 'Management', 'growth_rate': 5},
            '56': {'name': 'Administrative', 'growth_rate': 4},
            '61': {'name': 'Educational', 'growth_rate': 3},
            '62': {'name': 'Health Care', 'growth_rate': 6},
            '71': {'name': 'Arts', 'growth_rate': 2},
            '72': {'name': 'Accommodation', 'growth_rate': 3},
            '81': {'name': 'Other Services', 'growth_rate': 3},
            '92': {'name': 'Public Admin', 'growth_rate': 2}
        }
    
    def _create_database(self, db_path: str):
        """Create the enriched companies database"""
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS enriched_companies_full (
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
                
                -- Census data
                census_state_population INTEGER,
                census_median_income INTEGER,
                census_bachelors_degree INTEGER,
                census_masters_degree INTEGER,
                census_professional_degree INTEGER,
                census_doctorate_degree INTEGER,
                
                -- FRED data
                fred_unemployment_rate REAL,
                fred_unemployment_date TEXT,
                
                -- Patent data
                patent_count INTEGER,
                
                -- NSF data
                nsf_awards_count INTEGER,
                nsf_total_funding REAL,
                nsf_recent_awards TEXT,
                
                -- SAM.gov estimation
                sam_registration_likelihood INTEGER,
                sam_registration_estimated TEXT,
                
                -- Calculated scores
                pe_investment_score REAL,
                business_health_grade TEXT,
                scoring_factors TEXT,
                
                -- Metadata
                enrichment_timestamp TEXT,
                processing_error TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _save_batch_to_db(self, batch: List[Dict], db_path: str):
        """Save enriched batch to database"""
        conn = sqlite3.connect(db_path)
        df = pd.DataFrame(batch)
        df.to_sql('enriched_companies_full', conn, if_exists='append', index=False)
        conn.close()
    
    def _log_progress(self, total: int, start_time: float):
        """Log enrichment progress"""
        elapsed = time.time() - start_time
        rate = self.stats['total_processed'] / elapsed if elapsed > 0 else 0
        remaining = (total - self.stats['total_processed']) / rate if rate > 0 else 0
        
        logger.info(
            f"Progress: {self.stats['total_processed']:,}/{total:,} "
            f"({self.stats['total_processed']/total*100:.1f}%) | "
            f"Rate: {rate:.1f}/sec | "
            f"ETA: {remaining/60:.1f} min | "
            f"NSF: {self.stats['nsf_matched']} | "
            f"Patents: {self.stats['patent_matched']}"
        )
    
    def _generate_final_report(self, db_path: str, start_time: float):
        """Generate comprehensive final report"""
        elapsed = time.time() - start_time
        
        # Load results
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM enriched_companies_full", conn)
        
        report = f"""
        ========================================
        KBI LABS ENRICHMENT COMPLETE
        ========================================
        
        Total Processing Time: {elapsed/60:.1f} minutes
        Companies Processed: {self.stats['total_processed']:,}
        
        API Enrichment Coverage:
        - Census: {self.stats['census_enriched']:,} ({self.stats['census_enriched']/self.stats['total_processed']*100:.1f}%)  
        - FRED: {self.stats['fred_enriched']:,} ({self.stats['fred_enriched']/self.stats['total_processed']*100:.1f}%)
        
        Local Data Matching:
        - NSF Awards: {self.stats['nsf_matched']:,} ({self.stats['nsf_matched']/self.stats['total_processed']*100:.1f}%)
        - Patents: {self.stats['patent_matched']:,} ({self.stats['patent_matched']/self.stats['total_processed']*100:.1f}%)
        
        Errors: {self.stats['errors']:,}
        
        PE Investment Scores:
        - Average: {df['pe_investment_score'].mean():.1f}
        - Highest: {df['pe_investment_score'].max():.1f}
        - Lowest: {df['pe_investment_score'].min():.1f}
        
        Business Health Distribution:
        """
        
        # Grade distribution
        grades = df['business_health_grade'].value_counts()
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grades.get(grade, 0)
            pct = count / len(df) * 100 if len(df) > 0 else 0
            report += f"- Grade {grade}: {count:,} ({pct:.1f}%)\n        "
        
        report += f"""
        
        Top 10 Investment Opportunities:
        """
        
        # Top companies
        top_companies = df.nlargest(10, 'pe_investment_score')
        for i, (_, company) in enumerate(top_companies.iterrows(), 1):
            report += f"""
        {i}. {company['organization_name']}
           Location: {company['city']}, {company['state']}
           PE Score: {company['pe_investment_score']:.1f}
           Grade: {company['business_health_grade']}
           NSF Awards: {company.get('nsf_awards_count', 0)}
           Patents: {company.get('patent_count', 0)}
        """
        
        report += f"""
        
        SAM.gov Registration Estimates:
        - Likely Registered: {len(df[df['sam_registration_estimated'] == 'Likely']):,}
        - Unlikely Registered: {len(df[df['sam_registration_estimated'] == 'Unlikely']):,}
        
        Data saved to: {db_path}
        Log saved to: kbi_enrichment_complete.log
        
        ========================================
        """
        
        logger.info(report)
        
        # Save report to file
        with open('enrichment_report_complete.txt', 'w') as f:
            f.write(report)
        
        # Export summary CSV
        summary_df = df[['uei', 'organization_name', 'state', 'city', 
                        'pe_investment_score', 'business_health_grade',
                        'patent_count', 'nsf_awards_count', 'nsf_total_funding']].copy()
        summary_df.to_csv('enrichment_summary_complete.csv', index=False)
        
        conn.close()


async def main():
    """
    Main entry point to process all companies
    """
    # Configuration
    INPUT_CSV = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
    OUTPUT_DB = 'kbi_complete_enriched.db'
    BATCH_SIZE = 100
    MAX_CONCURRENT = 25  # Reduced to avoid rate limits
    
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        logger.error(f"Input file not found: {INPUT_CSV}")
        # Try alternative paths
        alt_paths = [
            'All_DSBS_processed_chunk_full_20250728.csv',
            'data/All_DSBS_processed_chunk_full_20250728.csv'
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                INPUT_CSV = alt
                logger.info(f"Found input file at: {INPUT_CSV}")
                break
        else:
            logger.error("Could not find input CSV file")
            return
    
    # Initialize pipeline
    pipeline = CompleteEnrichmentPipeline(
        batch_size=BATCH_SIZE,
        max_concurrent=MAX_CONCURRENT
    )
    
    # Process all companies
    await pipeline.process_all_companies(INPUT_CSV, OUTPUT_DB)
    
    print("\n✅ Complete enrichment finished!")
    print(f"Database: {OUTPUT_DB}")
    print("Report: enrichment_report_complete.txt")
    print("Summary: enrichment_summary_complete.csv")


if __name__ == "__main__":
    # Run the complete pipeline
    asyncio.run(main())
