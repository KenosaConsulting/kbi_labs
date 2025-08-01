#!/usr/bin/env python3
"""
GSA CALC API Integration for Procurement Labor Rate Analysis
No API key required - Public access
"""

import asyncio
import aiohttp
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GSACALCProcessor:
    """
    Integrates GSA CALC API for labor rate and procurement pricing intelligence
    Rate limit: No authentication required, reasonable rate limiting recommended
    """
    
    def __init__(self, base_url: str = "https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 1.0  # Conservative 1 second delay
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'KBI-Labs-Procurement-Intelligence/1.0',
                'Accept': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_labor_rates_by_category(self, labor_category: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Search labor rates by category (e.g., 'Software Engineer', 'Project Manager')
        Returns competitive rate analysis for procurement decisions
        """
        params = {
            'search': f'labor_category:{labor_category}',
            'page': 1,
            'page_size': min(limit, 100)  # API max is 100
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    if results:
                        return {
                            'labor_category': labor_category,
                            'total_records': data.get('count', 0),
                            'rates': results,
                            'rate_analysis': self._analyze_rates(results),
                            'searched_at': datetime.now().isoformat()
                        }
                    return None
                else:
                    logger.debug(f"GSA CALC API status {response.status} for category: {labor_category}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching CALC data for category {labor_category}: {e}")
            return None

    async def search_vendor_rates(self, vendor_name: str, limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Search labor rates by vendor name for competitive analysis
        """
        params = {
            'search': f'vendor_name:{vendor_name}',
            'page': 1,
            'page_size': min(limit, 100)
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    if results:
                        return {
                            'vendor_name': vendor_name,
                            'total_records': data.get('count', 0),
                            'rates': results,
                            'vendor_analysis': self._analyze_vendor_rates(results),
                            'searched_at': datetime.now().isoformat()
                        }
                    return None
                else:
                    logger.debug(f"GSA CALC API status {response.status} for vendor: {vendor_name}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching CALC data for vendor {vendor_name}: {e}")
            return None

    async def get_rate_suggestions(self, search_term: str) -> List[str]:
        """
        Get suggestions for labor categories or vendor names
        Useful for building search interfaces
        """
        params = {
            'suggest': f'labor_category:{search_term}'
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('suggestions', [])
                else:
                    return []
                    
        except Exception as e:
            logger.debug(f"Error fetching suggestions for {search_term}: {e}")
            return []

    async def get_filtered_rates(self, filters: Dict[str, Any], limit: int = 100) -> Optional[Dict[str, Any]]:
        """
        Get rates with specific filters
        
        Available filters:
        - education_level: BA, MA, PhD
        - experience_range: 0-2, 3-4, 5-7, 8-10, 11-15, 16-20, 20+
        - business_size: s (small), o (other than small)
        - price_including_iff: price range
        """
        params = {
            'page': 1,
            'page_size': min(limit, 100)
        }
        
        # Add filters
        for key, value in filters.items():
            params[f'filter'] = f"{key}:{value}"
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    if results:
                        return {
                            'filters_applied': filters,
                            'total_records': data.get('count', 0),
                            'rates': results,
                            'filtered_analysis': self._analyze_rates(results),
                            'searched_at': datetime.now().isoformat()
                        }
                    return None
                else:
                    logger.debug(f"GSA CALC API status {response.status} for filters: {filters}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching filtered CALC data: {e}")
            return None

    def _analyze_rates(self, rates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze rate data to provide procurement intelligence
        """
        if not rates:
            return {}
        
        # Extract pricing data
        prices = []
        for rate in rates:
            price = rate.get('price_including_iff')
            if price and isinstance(price, (int, float)):
                prices.append(float(price))
        
        if not prices:
            return {}
        
        # Calculate statistics
        prices.sort()
        n = len(prices)
        
        analysis = {
            'total_rates': len(rates),
            'price_count': len(prices),
            'min_rate': min(prices),
            'max_rate': max(prices),
            'avg_rate': sum(prices) / len(prices),
            'median_rate': prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2,
            'percentile_25': prices[int(n * 0.25)],
            'percentile_75': prices[int(n * 0.75)],
        }
        
        # Business insights
        analysis['competitive_range'] = {
            'low_competitive': analysis['percentile_25'],
            'mid_competitive': analysis['median_rate'], 
            'high_competitive': analysis['percentile_75']
        }
        
        # Education level breakdown
        education_breakdown = {}
        for rate in rates:
            edu = rate.get('education_level', 'Unknown')
            if edu not in education_breakdown:
                education_breakdown[edu] = []
            price = rate.get('price_including_iff')
            if price:
                education_breakdown[edu].append(float(price))
        
        analysis['education_rates'] = {}
        for edu, prices in education_breakdown.items():
            if prices:
                analysis['education_rates'][edu] = {
                    'count': len(prices),
                    'avg_rate': sum(prices) / len(prices)
                }
        
        return analysis

    def _analyze_vendor_rates(self, rates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze vendor-specific rate data
        """
        analysis = self._analyze_rates(rates)
        
        # Add vendor-specific insights
        if rates:
            # Contract vehicles
            vehicles = [rate.get('schedule') for rate in rates if rate.get('schedule')]
            analysis['contract_vehicles'] = list(set(vehicles))
            
            # Labor categories offered
            categories = [rate.get('labor_category') for rate in rates if rate.get('labor_category')]
            analysis['labor_categories'] = list(set(categories))
            
            # Sin numbers (Special Item Numbers)
            sins = [rate.get('sin') for rate in rates if rate.get('sin')]
            analysis['sin_numbers'] = list(set(sins))
        
        return analysis

    async def enrich_company_with_calc_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich company data with GSA CALC pricing intelligence
        Useful for procurement readiness assessment
        """
        company_name = company_data.get('Organization Name', '')
        enhanced_data = company_data.copy()
        
        if not company_name:
            return enhanced_data
        
        logger.info(f"Enriching {company_name} with GSA CALC pricing data")
        
        # Search for vendor in CALC system
        vendor_data = await self.search_vendor_rates(company_name)
        
        if vendor_data and vendor_data.get('rates'):
            enhanced_data['gsa_calc_found'] = True
            enhanced_data['gsa_schedule_rates'] = len(vendor_data['rates'])
            
            analysis = vendor_data.get('vendor_analysis', {})
            enhanced_data['gsa_avg_rate'] = analysis.get('avg_rate', 0)
            enhanced_data['gsa_min_rate'] = analysis.get('min_rate', 0)
            enhanced_data['gsa_max_rate'] = analysis.get('max_rate', 0)
            enhanced_data['gsa_contract_vehicles'] = analysis.get('contract_vehicles', [])
            enhanced_data['gsa_labor_categories'] = analysis.get('labor_categories', [])
            enhanced_data['gsa_competitive_position'] = self._assess_competitive_position(analysis)
            
            logger.info(f"✅ Found {enhanced_data['gsa_schedule_rates']} GSA rates for {company_name}")
        else:
            enhanced_data['gsa_calc_found'] = False
            enhanced_data['gsa_schedule_rates'] = 0
            enhanced_data['gsa_competitive_position'] = 'Unknown'
        
        return enhanced_data

    def _assess_competitive_position(self, analysis: Dict[str, Any]) -> str:
        """
        Assess competitive position based on rate analysis
        """
        avg_rate = analysis.get('avg_rate', 0)
        competitive_range = analysis.get('competitive_range', {})
        
        if not avg_rate or not competitive_range:
            return 'Unknown'
        
        low_comp = competitive_range.get('low_competitive', 0)
        mid_comp = competitive_range.get('mid_competitive', 0)
        
        if avg_rate <= low_comp:
            return 'Highly Competitive (Low Cost)'
        elif avg_rate <= mid_comp:
            return 'Competitive (Mid Range)'
        else:
            return 'Premium Provider (High Cost)'

    async def generate_procurement_intelligence_report(self, output_file: str):
        """
        Generate a comprehensive procurement intelligence report
        """
        logger.info("Generating GSA CALC procurement intelligence report...")
        
        # Key labor categories for analysis
        key_categories = [
            'Software Engineer',
            'Project Manager', 
            'Business Analyst',
            'Data Scientist',
            'Cybersecurity Specialist',
            'Program Manager',
            'Systems Administrator',
            'Database Administrator'
        ]
        
        report_data = []
        
        for category in key_categories:
            logger.info(f"Analyzing rates for: {category}")
            rate_data = await self.search_labor_rates_by_category(category, limit=100)
            
            if rate_data:
                analysis = rate_data.get('rate_analysis', {})
                report_data.append({
                    'Labor Category': category,
                    'Total Records': rate_data.get('total_records', 0),
                    'Average Rate': analysis.get('avg_rate', 0),
                    'Median Rate': analysis.get('median_rate', 0),
                    'Min Rate': analysis.get('min_rate', 0),
                    'Max Rate': analysis.get('max_rate', 0),
                    'Competitive Low': analysis.get('competitive_range', {}).get('low_competitive', 0),
                    'Competitive High': analysis.get('competitive_range', {}).get('high_competitive', 0)
                })
        
        # Save report
        df = pd.DataFrame(report_data)
        df.to_csv(output_file, index=False)
        logger.info(f"Procurement intelligence report saved to: {output_file}")
        
        return df

# CLI interface
async def main():
    """
    Main execution function for GSA CALC integration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='GSA CALC API Integration for Procurement Intelligence')
    parser.add_argument('--mode', choices=['search', 'vendor', 'report'], default='report',
                       help='Operation mode')
    parser.add_argument('--query', '-q', help='Search query (labor category or vendor name)')
    parser.add_argument('--output', '-o', default='gsa_calc_report.csv',
                       help='Output file path')
    
    args = parser.parse_args()
    
    async with GSACALCProcessor() as processor:
        if args.mode == 'search' and args.query:
            result = await processor.search_labor_rates_by_category(args.query)
            if result:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"No data found for: {args.query}")
                
        elif args.mode == 'vendor' and args.query:
            result = await processor.search_vendor_rates(args.query)
            if result:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"No vendor data found for: {args.query}")
                
        elif args.mode == 'report':
            await processor.generate_procurement_intelligence_report(args.output)
            print(f"Report generated: {args.output}")

if __name__ == "__main__":
    asyncio.run(main())