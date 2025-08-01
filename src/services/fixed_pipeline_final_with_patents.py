#!/usr/bin/env python3
"""
KBI Labs Complete Enrichment Pipeline - Fixed Version
Handles duplicate UEIs and processes all companies smoothly
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
    Complete enrichment pipeline - handles duplicates and runs smoothly
    """
    
    def __init__(self, batch_size: int = 100, max_concurrent: int = 25):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        
        # API Keys
        self.census_api_key = os.getenv('CENSUS_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'duplicates_skipped': 0,
            'census_enriched': 0,
            'fred_enriched': 0,
            'patent_matched': 0,
            'nsf_matched': 0,
            'errors': 0
        }
        
        # Track processed UEIs to avoid duplicates
        self.processed_ueis = set()
        
        # Pre-load data
        self.nsf_data = None
        self.patent_data = None
        
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
        
    async def process_all_companies(self, csv_path: str, output_db: str, limit: Optional[int] = None):
        """
        Main entry point - processes all companies
        """
        logger.info(f"Starting complete enrichment of {csv_path}")
        start_time = time.time()
        
        # Check existing database for already processed UEIs
        self._load_existing_ueis(output_db)
        
        # Create/update database
        self._create_database(output_db)
        
        # Load all local data sources
        logger.info("Loading local data sources...")
        self._load_local_data()
        
        # Count total rows
        if limit:
            total_rows = limit
        else:
            # Count unique companies by UEI
            df_count = pd.read_csv(csv_path, usecols=['UEI (Unique Entity Identifier)'])
            unique_ueis = df_count['UEI (Unique Entity Identifier)'].nunique()
            total_rows = len(df_count)
            logger.info(f"Total rows in file: {total_rows:,}")
            logger.info(f"Unique UEIs: {unique_ueis:,}")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process in batches
        async with aiohttp.ClientSession() as session:
            chunk_iterator = pd.read_csv(csv_path, chunksize=self.batch_size)
            
            for chunk_num, chunk_df in enumerate(chunk_iterator):
                if limit and self.stats['total_processed'] >= limit:
                    break
                    
                # Remove duplicates within chunk and already processed
                chunk_df = self._filter_duplicates(chunk_df)
                
                if len(chunk_df) == 0:
                    continue
                    
                logger.info(f"Processing batch {chunk_num + 1} ({len(chunk_df)} unique companies)")
                
                # Enrich all companies in batch
                tasks = []
                for _, company in chunk_df.iterrows():
                    task = self._enrich_company_with_semaphore(
                        company, session, semaphore
                    )
                    tasks.append(task)
                
                # Wait for batch to complete
                enriched_batch = await asyncio.gather(*tasks)
                
                # Filter out None results
                enriched_batch = [e for e in enriched_batch if e is not None]
                
                # Save to database
                if enriched_batch:
                    self._save_batch_to_db(enriched_batch, output_db)
                
                # Update progress
                self.stats['total_processed'] += len(enriched_batch)
                self._log_progress(total_rows, start_time)
                
                # Add delay between batches to avoid rate limiting
                if chunk_num % 10 == 0 and chunk_num > 0:
                    logger.info("Pausing to avoid rate limits...")
                    await asyncio.sleep(5)
        
        # Final report
        self._generate_final_report(output_db, start_time)
        
    def _load_existing_ueis(self, db_path: str):
        """Load already processed UEIs from database"""
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                existing = pd.read_sql_query("SELECT uei FROM enriched_companies_full", conn)
                self.processed_ueis = set(existing['uei'].tolist())
                logger.info(f"Found {len(self.processed_ueis)} already processed companies")
                conn.close()
            except Exception as e:
                logger.debug(f"No existing data found: {e}")
                
    def _filter_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out duplicates and already processed companies"""
        # Remove duplicates within the dataframe
        df = df.drop_duplicates(subset=['UEI (Unique Entity Identifier)'])
        
        # Filter out already processed UEIs
        before_count = len(df)
        df = df[~df['UEI (Unique Entity Identifier)'].isin(self.processed_ueis)]
        
        duplicates_removed = before_count - len(df)
        if duplicates_removed > 0:
            self.stats['duplicates_skipped'] += duplicates_removed
            logger.debug(f"Skipped {duplicates_removed} already processed companies")
            
        return df
        
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
                org_name = str(row.get('Organization Name', '')).lower().strip()
                if org_name and org_name != 'nan':
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
        """Load patent data from local files - FIXED VERSION"""
        self.patent_lookup = {}
        patent_path = 'patent_data/'
        
        if os.path.exists(patent_path):
            try:
                logger.info("Loading patent data...")
                
                # Process assignee files specifically
                assignee_files = [
                    'g_assignee_disambiguated.tsv',
                    'g_assignee_not_disambiguated.tsv'
                ]
                
                total_patents = 0
                
                for filename in assignee_files:
                    filepath = os.path.join(patent_path, filename)
                    if os.path.exists(filepath):
                        try:
                            logger.info(f"Loading {filename}...")
                            
                            if 'disambiguated' in filename:
                                # For disambiguated file
                                df = pd.read_csv(filepath, sep='	', 
                                               usecols=['patent_id', 'disambig_assignee_organization'],
                                               dtype={'disambig_assignee_organization': str})
                                org_col = 'disambig_assignee_organization'
                            else:
                                # For not disambiguated file
                                df = pd.read_csv(filepath, sep='	',
                                               usecols=['patent_id', 'raw_assignee_organization'],
                                               dtype={'raw_assignee_organization': str})
                                org_col = 'raw_assignee_organization'
                            
                            # Count patents per organization
                            org_counts = df[org_col].dropna().value_counts()
                            
                            # Add to lookup
                            for org, count in org_counts.items():
                                org_clean = str(org).lower().strip()
                                if org_clean and len(org_clean) > 3 and org_clean != 'nan':
                                    if org_clean not in self.patent_lookup:
                                        self.patent_lookup[org_clean] = 0
                                    self.patent_lookup[org_clean] += count
                                    total_patents += count
                                    
                            logger.info(f"Loaded {len(org_counts)} organizations from {filename}")
                            
                        except Exception as e:
                            logger.error(f"Error loading {filename}: {e}")
                
                logger.info(f"Loaded patent data for {len(self.patent_lookup):,} unique organizations with {total_patents:,} total patents")
                
            except Exception as e:
                logger.error(f"Error loading patent data: {e}")
    def _enrich_nsf_local(self, org_name: str) -> Dict:
        """Look up NSF data from local file"""
        if not org_name or not self.nsf_lookup or pd.isna(org_name):
            return {'nsf_awards_count': 0, 'nsf_total_funding': 0}
            
        org_lower = str(org_name).lower().strip()
        
        # Direct lookup
        if org_lower in self.nsf_lookup:
            data = self.nsf_lookup[org_lower]
            return {
                'nsf_awards_count': int(data['awards_count']),
                'nsf_total_funding': float(data['total_funding']),
                'nsf_recent_awards': json.dumps(data['recent_awards']) if data['recent_awards'] else ''
            }
        
        # Fuzzy matching - check if org name contains or is contained in NSF org names
        for nsf_org, data in self.nsf_lookup.items():
            if len(org_lower) > 5 and len(nsf_org) > 5:  # Avoid short matches
                if org_lower in nsf_org or nsf_org in org_lower:
                    return {
                        'nsf_awards_count': int(data['awards_count']),
                        'nsf_total_funding': float(data['total_funding']),
                        'nsf_recent_awards': json.dumps(data['recent_awards']) if data['recent_awards'] else ''
                    }
        
        return {'nsf_awards_count': 0, 'nsf_total_funding': 0}
    
    def _enrich_patents_local(self, org_name: str) -> Dict:
        """Look up patent data from local file"""
        if not org_name or not self.patent_lookup or pd.isna(org_name):
            return {'patent_count': 0}
            
        org_lower = str(org_name).lower().strip()
        
        # Direct lookup
        if org_lower in self.patent_lookup:
            return {'patent_count': self.patent_lookup[org_lower]}
        
        # Partial matching
        patent_count = 0
        for patent_org, count in self.patent_lookup.items():
            if len(org_lower) > 5 and len(patent_org) > 5:  # Avoid short matches
                if org_lower in patent_org or patent_org in org_lower:
                    patent_count += count
                    
        return {'patent_count': patent_count}
    
    def _calculate_scores(self, company: Dict) -> Dict:
        """
        Calculate PE investment score and business health grade
        """
        score = 50.0  # Base score
        
        # Industry factors (30%)
        naics = str(company.get('primary_naics', ''))
        if naics and naics != 'nan':
            industry_info = self.naics_mapping.get(naics[:2], {})
            growth_rate = industry_info.get('growth_rate', 0)
            score += growth_rate * 3  # Max 30 points
        
        # Market location factors (25%)
        state = company.get('state')
        if state in ['California', 'Texas', 'New York', 'Florida']:
            score += 15
        elif state in ['Illinois', 'Pennsylvania', 'Ohio', 'Georgia']:
            score += 10
        elif state:
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
        website = company.get('website')
        if website and not pd.isna(website):
            score += 10
            if '.com' in str(website):
                score += 5
            if 'https' in str(website):
                score += 5
        
        # Certifications (15%)
        certs = str(company.get('active_sba_certifications', ''))
        if certs and certs != 'nan':
            if '8(a)' in certs:
                score += 8
            if 'HUBZone' in certs:
                score += 4
            if 'WOSB' in certs or 'EDWOSB' in certs:
                score += 3
        
        # Business structure (10%)
        structure = str(company.get('legal_structure', ''))
        if structure and structure != 'nan':
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
            'pe_investment_score': round(min(100, max(0, score)), 1),
            'business_health_grade': grade,
            'scoring_factors': json.dumps({
                'industry_score': naics[:2] if naics and naics != 'nan' else 'Unknown',
                'location_score': state if state else 'Unknown',
                'digital_score': bool(website and not pd.isna(website)),
                'certification_score': bool(certs and certs != 'nan'),
                'structure_score': structure if structure and structure != 'nan' else 'Unknown',
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
                address_line_1 TEXT,
                address_line_2 TEXT,
                first_name TEXT,
                last_name TEXT,
                job_title TEXT,
                
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
                
                -- Calculated scores
                pe_investment_score REAL,
                business_health_grade TEXT,
                scoring_factors TEXT,
                
                -- Metadata
                enrichment_timestamp TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def _save_batch_to_db(self, batch: List[Dict], db_path: str):
        """Save enriched batch to database - handle duplicates gracefully"""
        if not batch:
            return
            
        conn = sqlite3.connect(db_path)
        df = pd.DataFrame(batch)
        
        # Use replace to handle any duplicates
        df.to_sql('enriched_companies_full', conn, if_exists='append', index=False, method='multi')
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
            f"Patents: {self.stats['patent_matched']} | "
            f"Duplicates: {self.stats['duplicates_skipped']}"
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
        
        Total Processing Time: {elapsed/60:.1f} minutes ({elapsed/3600:.1f} hours)
        Companies Processed: {self.stats['total_processed']:,}
        Duplicates Skipped: {self.stats['duplicates_skipped']:,}
        
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
        
        # Industry breakdown
        report += f"\n\nTop Industries by Average PE Score:"
        industry_scores = df.groupby('primary_naics').agg({
            'pe_investment_score': 'mean',
            'organization_name': 'count'
        }).round(1)
        industry_scores.columns = ['avg_score', 'company_count']
        top_industries = industry_scores.nlargest(10, 'avg_score')
        
        for naics, row in top_industries.iterrows():
            if str(naics) != 'nan':
                report += f"\n        NAICS {naics}: {row['avg_score']:.1f} ({row['company_count']} companies)"
        
        report += f"""
        
        Data saved to: {db_path}
        Log saved to: kbi_enrichment_complete.log
        
        ========================================
        """
        
        logger.info(report)
        
        # Save report to file
        with open('enrichment_report_final.txt', 'w') as f:
            f.write(report)
        
        # Export summary CSV
        summary_df = df[['uei', 'organization_name', 'state', 'city', 
                        'pe_investment_score', 'business_health_grade',
                        'patent_count', 'nsf_awards_count', 'nsf_total_funding']].copy()
        summary_df.to_csv('enrichment_summary_final.csv', index=False)
        
        # Export top 1000 companies
        top_1000 = df.nlargest(1000, 'pe_investment_score')
        top_1000.to_csv('top_1000_companies.csv', index=False)
        
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
        return
    
    # Initialize pipeline
    pipeline = CompleteEnrichmentPipeline(
        batch_size=BATCH_SIZE,
        max_concurrent=MAX_CONCURRENT
    )
    
    # Ask if user wants to process all or test first
    print("\nKBI Labs Complete Enrichment Pipeline")
    print("=====================================")
    print(f"Input file: {INPUT_CSV}")
    print(f"Output database: {OUTPUT_DB}")
    print("\nOptions:")
    print("1. Test with first 1,000 companies")
    print("2. Process ALL companies (~64,799 unique)")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == "1":
        await pipeline.process_all_companies(INPUT_CSV, OUTPUT_DB, limit=1000)
    else:
        await pipeline.process_all_companies(INPUT_CSV, OUTPUT_DB)
    
    print("\n✅ Complete enrichment finished!")
    print(f"Database: {OUTPUT_DB}")
    print("Report: enrichment_report_final.txt")
    print("Summary: enrichment_summary_final.csv")
    print("Top companies: top_1000_companies.csv")


if __name__ == "__main__":
    # Run the complete pipeline
    asyncio.run(main())
