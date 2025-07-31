# src/data_processors/usaspending_processor.py
"""
USASpending.gov API integration for DSBS enhancement
FIXED VERSION - Updated API endpoints and parameters
"""

import asyncio
import aiohttp
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USASpendingProcessor:
    """
    Integrates USASpending.gov API data with DSBS companies
    Rate limit: ~1000 requests/hour (no API key required)
    """
    
    def __init__(self, base_url: str = "https://api.usaspending.gov/api/v2/"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 3.6  # seconds between requests (1000/hour)
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'KBI-Labs-Business-Intelligence/1.0',
                'Accept': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_recipients_by_uei(self, uei: str) -> Optional[Dict[str, Any]]:
        """
        Search for government contracts by UEI using search endpoint
        Updated to work with current USASpending API
        """
        endpoint = "search/spending_by_award/"
        url = f"{self.base_url}{endpoint}"
        
        # Search for any awards by this UEI (last 3 years for better coverage)
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')
        
        payload = {
            "filters": {
                "recipient_search_text": [uei]
            },
            "fields": [
                "Recipient Name",
                "Award Amount", 
                "Award Type",
                "Awarding Agency",
                "Start Date"
            ],
            "sort": "Award Amount",
            "order": "desc",
            "limit": 50  # Get more results for better analysis
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    if results:
                        # Calculate total contract value
                        total_amount = sum(
                            float(r.get('Award Amount', 0)) 
                            for r in results 
                            if r.get('Award Amount')
                        )
                        
                        return {
                            'recipient_name': results[0].get('Recipient Name', ''),
                            'total_amount': total_amount,
                            'award_count': len(results),
                            'awards': results,
                            'found_via_search': True
                        }
                    return None
                elif response.status == 404:
                    logger.debug(f"No USASpending data found for UEI: {uei}")
                    return None
                else:
                    logger.debug(f"USASpending API status {response.status} for UEI {uei}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching USASpending data for UEI {uei}: {e}")
            return None

    async def get_awards_by_recipient(self, uei: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent awards/contracts for a specific recipient
        Returns contract values, dates, and awarding agencies
        """
        endpoint = "search/spending_by_award/"
        url = f"{self.base_url}{endpoint}"
        
        # Search for last 2 years of data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        payload = {
            "filters": {
                "recipient_search_text": [uei],
                "time_period": [
                    {
                        "start_date": start_date,
                        "end_date": end_date
                    }
                ]
            },
            "fields": [
                "Award ID",
                "Award Amount",
                "Award Type", 
                "Awarding Agency",
                "Awarding Sub Agency",
                "Start Date",
                "End Date",
                "Description",
                "Recipient Name"
            ],
            "sort": "Award Amount",
            "order": "desc",
            "limit": limit
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logger.debug(f"Awards search status {response.status} for UEI {uei}")
                    return []
                    
        except Exception as e:
            logger.debug(f"Error fetching awards for UEI {uei}: {e}")
            return []

    async def enrich_dsbs_company(self, company_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single DSBS company with USASpending data
        Returns enhanced company data with government contracting info
        """
        uei = company_row.get('UEI (Unique Entity Identifier)')
        if not uei or pd.isna(uei):
            return {**company_row, 'gov_contracts_found': False}
        
        # Clean UEI (remove any whitespace, ensure proper format)
        uei = str(uei).strip().upper()
        if len(uei) != 12:  # UEI should be 12 characters
            return {**company_row, 'gov_contracts_found': False}
        
        logger.info(f"Enriching {company_row.get('Organization Name', 'Unknown')} with UEI: {uei}")
        
        # Get recipient info
        recipient_data = await self.search_recipients_by_uei(uei)
        
        # Enhance the company data
        enhanced_data = company_row.copy()
        
        if recipient_data and recipient_data.get('awards'):
            enhanced_data['gov_contracts_found'] = True
            enhanced_data['total_contract_value'] = recipient_data.get('total_amount', 0)
            enhanced_data['contract_count'] = len(recipient_data.get('awards', []))
            enhanced_data['last_contract_date'] = None
            enhanced_data['primary_agencies'] = []
            
            awards = recipient_data.get('awards', [])
            
            # Get most recent contract date
            dates = [award.get('Start Date') for award in awards if award.get('Start Date')]
            if dates:
                enhanced_data['last_contract_date'] = max(dates)
            
            # Get top agencies
            agencies = [award.get('Awarding Agency') for award in awards if award.get('Awarding Agency')]
            enhanced_data['primary_agencies'] = list(set(agencies))[:3]  # Top 3 unique agencies
            
            # Calculate recent contract value (last 2 years from awards)
            recent_awards = await self.get_awards_by_recipient(uei)
            recent_value = sum(
                float(award.get('Award Amount', 0)) 
                for award in recent_awards 
                if award.get('Award Amount')
            )
            enhanced_data['recent_contract_value_2yr'] = recent_value
            
            logger.info(f"✅ Found {enhanced_data['contract_count']} contracts worth ${enhanced_data['total_contract_value']:,.2f}")
        else:
            enhanced_data['gov_contracts_found'] = False
            enhanced_data['total_contract_value'] = 0
            enhanced_data['contract_count'] = 0
            enhanced_data['recent_contract_value_2yr'] = 0
        
        return enhanced_data

    async def process_dsbs_batch(self, csv_file_path: str, output_file_path: str, batch_size: int = 50):
        """
        Process a DSBS CSV file and enrich with USASpending data
        Processes in batches to manage rate limits and memory
        """
        logger.info(f"Processing DSBS file: {csv_file_path}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file_path, low_memory=False)
        total_companies = len(df)
        logger.info(f"Found {total_companies} companies to process")
        
        # Process in batches
        enriched_companies = []
        for i in range(0, total_companies, batch_size):
            batch = df.iloc[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: companies {i+1}-{min(i+batch_size, total_companies)}")
            
            # Process each company in the batch
            batch_tasks = []
            for _, company in batch.iterrows():
                task = self.enrich_dsbs_company(company.to_dict())
                batch_tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Filter out exceptions and add successful results
            for result in batch_results:
                if not isinstance(result, Exception):
                    enriched_companies.append(result)
                else:
                    logger.error(f"Error processing company: {result}")
            
            logger.info(f"Completed batch {i//batch_size + 1}. Total processed: {len(enriched_companies)}")
        
        # Save enriched data
        enriched_df = pd.DataFrame(enriched_companies)
        enriched_df.to_csv(output_file_path, index=False)
        logger.info(f"Enriched data saved to: {output_file_path}")
        
        # Print summary statistics
        gov_contractors = enriched_df[enriched_df['gov_contracts_found'] == True]
        logger.info(f"\n🎯 ENRICHMENT SUMMARY:")
        logger.info(f"Total companies processed: {len(enriched_df):,}")
        logger.info(f"Government contractors found: {len(gov_contractors):,}")
        if len(gov_contractors) > 0:
            logger.info(f"Total contract value: ${enriched_df['total_contract_value'].sum():,.2f}")
            logger.info(f"Average contracts per contractor: {gov_contractors['contract_count'].mean():.1f}")
            logger.info(f"Success rate: {len(gov_contractors)/len(enriched_df)*100:.1f}%")
        
        return enriched_df

# CLI interface for running the processor
async def main():
    """
    Main execution function for USASpending integration
    """
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description='Enrich DSBS data with USASpending.gov contracts')
    parser.add_argument('--input', '-i', default='/app/data/dsbs_raw/*.csv', 
                       help='Input CSV file(s) or pattern')
    parser.add_argument('--output-dir', '-o', default='/app/data/enriched/', 
                       help='Output directory for enriched files')
    parser.add_argument('--batch-size', '-b', type=int, default=10,
                       help='Batch size for processing (default: 10)')
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find input files
    input_files = glob.glob(args.input)
    if not input_files:
        logger.error(f"No files found matching pattern: {args.input}")
        return
    
    logger.info(f"Found {len(input_files)} files to process")
    
    # Process each file
    async with USASpendingProcessor() as processor:
        for input_file in input_files:
            file_name = Path(input_file).stem
            output_file = Path(args.output_dir) / f"{file_name}_enriched_usaspending.csv"
            
            logger.info(f"Processing: {input_file} -> {output_file}")
            await processor.process_dsbs_batch(
                csv_file_path=input_file,
                output_file_path=str(output_file),
                batch_size=args.batch_size
            )
    
    logger.info("🚀 USASpending enrichment complete!")

if __name__ == "__main__":
    asyncio.run(main())
