#!/usr/bin/env python3
"""
SAM.gov Opportunities API Integration
Enhanced procurement opportunity intelligence and matching
Requires SAM.gov API key
"""

import asyncio
import aiohttp
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SAMOpportunitiesProcessor:
    """
    Enhanced SAM.gov Opportunities API integration for procurement intelligence
    Provides real-time contract opportunities and vendor matching
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.sam.gov/opportunities/v2/search"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 1.0  # SAM.gov rate limits
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=45)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'X-Api-Key': self.api_key,
                'User-Agent': 'KBI-Labs-Opportunities-Intelligence/1.0',
                'Accept': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_opportunities_by_naics(self, naics_code: str, limit: int = 100, 
                                          days_ahead: int = 90) -> Optional[Dict[str, Any]]:
        """
        Search opportunities by NAICS code
        """
        # Calculate date range for opportunities
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        params = {
            'naics': naics_code,
            'postedFrom': start_date.strftime('%m/%d/%Y'),
            'postedTo': end_date.strftime('%m/%d/%Y'),
            'ptype': 'o',  # Opportunities (not awards)
            'limit': min(limit, 100)  # API max
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    
                    if opportunities:
                        return {
                            'naics_code': naics_code,
                            'total_opportunities': len(opportunities),
                            'opportunities': opportunities,
                            'analysis': self._analyze_opportunities(opportunities),
                            'searched_at': datetime.now().isoformat()
                        }
                    return None
                elif response.status == 429:
                    logger.warning("SAM.gov rate limit hit")
                    await asyncio.sleep(5)
                    return None
                else:
                    logger.debug(f"SAM Opportunities API status {response.status} for NAICS: {naics_code}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching opportunities for NAICS {naics_code}: {e}")
            return None

    async def search_opportunities_by_keywords(self, keywords: List[str], limit: int = 100,
                                             days_ahead: int = 90, set_aside_code: str = None) -> Optional[Dict[str, Any]]:
        """
        Search opportunities by keywords with optional set-aside filtering
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        params = {
            'q': ' '.join(keywords),
            'postedFrom': start_date.strftime('%m/%d/%Y'),
            'postedTo': end_date.strftime('%m/%d/%Y'),
            'ptype': 'o',
            'limit': min(limit, 100)
        }
        
        # Add set-aside filter if specified
        if set_aside_code:
            params['typeOfSetAside'] = set_aside_code
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    
                    if opportunities:
                        return {
                            'keywords': keywords,
                            'set_aside_code': set_aside_code,
                            'total_opportunities': len(opportunities),
                            'opportunities': opportunities,
                            'analysis': self._analyze_opportunities(opportunities),
                            'searched_at': datetime.now().isoformat()
                        }
                    return None
                else:
                    logger.debug(f"SAM Opportunities API status {response.status} for keywords: {keywords}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching opportunities for keywords {keywords}: {e}")
            return None

    async def get_opportunity_details(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific opportunity
        """
        detail_url = f"https://api.sam.gov/opportunities/v2/search?opportunityId={opportunity_id}"
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(detail_url) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    if opportunities:
                        return opportunities[0]
                    return None
                else:
                    logger.debug(f"SAM Opportunities detail API status {response.status} for ID: {opportunity_id}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching opportunity details for {opportunity_id}: {e}")
            return None

    async def search_small_business_opportunities(self, limit: int = 100, days_ahead: int = 90) -> Optional[Dict[str, Any]]:
        """
        Search specifically for small business set-aside opportunities
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        # Common small business set-aside codes
        set_aside_codes = ['SBA', 'SBP', 'WOSB', 'EDWOSB', 'SDVOSB', 'HZ']
        
        all_opportunities = []
        
        for code in set_aside_codes:
            params = {
                'typeOfSetAside': code,
                'postedFrom': start_date.strftime('%m/%d/%Y'),
                'postedTo': end_date.strftime('%m/%d/%Y'),
                'ptype': 'o',
                'limit': min(limit // len(set_aside_codes), 100)
            }
            
            try:
                await asyncio.sleep(self.rate_limit_delay)
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        opportunities = data.get('opportunitiesData', [])
                        
                        # Tag opportunities with set-aside type
                        for opp in opportunities:
                            opp['matched_set_aside'] = code
                        
                        all_opportunities.extend(opportunities)
                        
            except Exception as e:
                logger.debug(f"Error fetching {code} opportunities: {e}")
                continue
        
        if all_opportunities:
            return {
                'search_type': 'small_business_setasides',
                'total_opportunities': len(all_opportunities),
                'opportunities': all_opportunities,
                'analysis': self._analyze_small_business_opportunities(all_opportunities),
                'searched_at': datetime.now().isoformat()
            }
        
        return None

    async def get_agency_opportunities(self, agency_code: str, limit: int = 100, days_ahead: int = 90) -> Optional[Dict[str, Any]]:
        """
        Get opportunities from a specific agency
        """
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        params = {
            'deptname': agency_code,
            'postedFrom': start_date.strftime('%m/%d/%Y'), 
            'postedTo': end_date.strftime('%m/%d/%Y'),
            'ptype': 'o',
            'limit': min(limit, 100)
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    
                    if opportunities:
                        return {
                            'agency_code': agency_code,
                            'total_opportunities': len(opportunities),
                            'opportunities': opportunities,
                            'analysis': self._analyze_agency_opportunities(opportunities, agency_code),
                            'searched_at': datetime.now().isoformat()
                        }
                    return None
                else:
                    logger.debug(f"SAM Opportunities API status {response.status} for agency: {agency_code}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching opportunities for agency {agency_code}: {e}")
            return None

    def _analyze_opportunities(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze opportunity data for business intelligence
        """
        if not opportunities:
            return {}
        
        analysis = {
            'total_count': len(opportunities),
            'active_opportunities': 0,
            'total_estimated_value': 0,
            'avg_estimated_value': 0
        }
        
        # Collect values and analyze
        values = []
        agencies = {}
        naics_codes = {}
        set_aside_types = {}
        response_deadlines = []
        
        for opp in opportunities:
            # Status analysis
            if opp.get('active') == 'Yes':
                analysis['active_opportunities'] += 1
            
            # Value analysis
            award_value = opp.get('awardValue')
            if award_value:
                try:
                    value = float(str(award_value).replace('$', '').replace(',', ''))
                    values.append(value)
                    analysis['total_estimated_value'] += value
                except:
                    pass
            
            # Agency breakdown
            agency = opp.get('department', 'Unknown')
            agencies[agency] = agencies.get(agency, 0) + 1
            
            # NAICS analysis
            naics = opp.get('naicsCode', 'Unknown')
            naics_codes[naics] = naics_codes.get(naics, 0) + 1
            
            # Set-aside analysis
            set_aside = opp.get('typeOfSetAsideDescription', 'None')
            set_aside_types[set_aside] = set_aside_types.get(set_aside, 0) + 1
            
            # Response deadline analysis
            response_date = opp.get('responseDeadLine')
            if response_date:
                try:
                    deadline = datetime.strptime(response_date, '%m/%d/%Y %I:%M:%S %p')
                    days_until = (deadline - datetime.now()).days
                    response_deadlines.append(days_until)
                except:
                    pass
        
        # Calculate averages
        if values:
            analysis['avg_estimated_value'] = analysis['total_estimated_value'] / len(values)
            analysis['median_estimated_value'] = sorted(values)[len(values) // 2]
        
        # Top categories
        analysis['top_agencies'] = sorted(agencies.items(), key=lambda x: x[1], reverse=True)[:5]
        analysis['top_naics'] = sorted(naics_codes.items(), key=lambda x: x[1], reverse=True)[:5]
        analysis['set_aside_breakdown'] = dict(sorted(set_aside_types.items(), key=lambda x: x[1], reverse=True))
        
        # Timing analysis
        if response_deadlines:
            analysis['avg_response_time'] = sum(response_deadlines) / len(response_deadlines)
            analysis['urgent_opportunities'] = len([d for d in response_deadlines if d <= 7])  # Due within 7 days
        
        return analysis

    def _analyze_small_business_opportunities(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Specialized analysis for small business opportunities
        """
        base_analysis = self._analyze_opportunities(opportunities)
        
        # Set-aside type distribution
        set_aside_distribution = {}
        for opp in opportunities:
            sa_type = opp.get('matched_set_aside', 'Unknown')
            set_aside_distribution[sa_type] = set_aside_distribution.get(sa_type, 0) + 1
        
        base_analysis['set_aside_distribution'] = set_aside_distribution
        
        # Size standard analysis
        size_standards = {}
        for opp in opportunities:
            size_std = opp.get('sizeStandard', 'Unknown')
            size_standards[size_std] = size_standards.get(size_std, 0) + 1
        
        base_analysis['size_standards'] = dict(sorted(size_standards.items(), key=lambda x: x[1], reverse=True))
        
        return base_analysis

    def _analyze_agency_opportunities(self, opportunities: List[Dict[str, Any]], agency_code: str) -> Dict[str, Any]:
        """
        Agency-specific opportunity analysis
        """
        base_analysis = self._analyze_opportunities(opportunities) 
        
        # Sub-agency/office breakdown
        offices = {}
        for opp in opportunities:
            office = opp.get('officeAddress', {}).get('state', 'Unknown')
            offices[office] = offices.get(office, 0) + 1
        
        base_analysis['geographic_distribution'] = dict(sorted(offices.items(), key=lambda x: x[1], reverse=True))
        
        # Competition analysis
        competition_types = {}
        for opp in opportunities:
            comp_type = opp.get('typeOfSetAsideDescription', 'Full and Open Competition')
            competition_types[comp_type] = competition_types.get(comp_type, 0) + 1
        
        base_analysis['competition_breakdown'] = competition_types
        
        return base_analysis

    async def match_company_to_opportunities(self, company_data: Dict[str, Any], 
                                           max_opportunities: int = 20) -> Dict[str, Any]:
        """
        Match a company to relevant opportunities based on NAICS, capabilities, and size
        """
        company_name = company_data.get('Organization Name', '')
        naics_codes = []
        
        # Extract NAICS codes
        primary_naics = company_data.get('Primary NAICS Code')
        if primary_naics:
            naics_codes.append(str(primary_naics))
        
        # Get additional NAICS from other fields
        for i in range(2, 6):  # NAICS Code 2 through 5
            naics = company_data.get(f'NAICS Code {i}')
            if naics:
                naics_codes.append(str(naics))
        
        if not naics_codes:
            return {'company_name': company_name, 'matched_opportunities': [], 'message': 'No NAICS codes found'}
        
        logger.info(f"Matching opportunities for {company_name} with NAICS: {naics_codes}")
        
        all_matches = []
        
        # Search by each NAICS code
        for naics in naics_codes[:3]:  # Limit to top 3 NAICS to manage API calls
            naics_opportunities = await self.search_opportunities_by_naics(naics, limit=max_opportunities // len(naics_codes))
            
            if naics_opportunities and naics_opportunities.get('opportunities'):
                opportunities = naics_opportunities['opportunities']
                
                # Score and rank opportunities
                for opp in opportunities:
                    score = self._calculate_opportunity_match_score(opp, company_data)
                    opp['match_score'] = score
                    opp['matched_naics'] = naics
                
                all_matches.extend(opportunities)
        
        # Sort by match score and deduplicate
        unique_matches = {}
        for opp in all_matches:
            opp_id = opp.get('noticeId', opp.get('solicitationNumber', ''))
            if opp_id and (opp_id not in unique_matches or opp['match_score'] > unique_matches[opp_id]['match_score']):
                unique_matches[opp_id] = opp
        
        # Get top matches
        top_matches = sorted(unique_matches.values(), key=lambda x: x.get('match_score', 0), reverse=True)[:max_opportunities]
        
        return {
            'company_name': company_name,
            'matched_naics_codes': naics_codes,
            'total_matches': len(top_matches),
            'matched_opportunities': top_matches,
            'match_summary': self._summarize_matches(top_matches),
            'matched_at': datetime.now().isoformat()
        }

    def _calculate_opportunity_match_score(self, opportunity: Dict[str, Any], company_data: Dict[str, Any]) -> int:
        """
        Calculate how well an opportunity matches a company
        Score range: 0-100
        """
        score = 0
        
        # Base score for NAICS match (30 points)
        score += 30
        
        # Small business bonus (20 points)
        set_aside = opportunity.get('typeOfSetAsideDescription', '').lower()
        company_size = company_data.get('Business Size', '').lower()
        
        if 'small' in set_aside and 'small' in company_size:
            score += 20
        elif 'small' in company_size:
            score += 10  # Small business competing in full & open
        
        # Location bonus (15 points)
        opp_state = opportunity.get('officeAddress', {}).get('state', '')
        company_state = company_data.get('Physical Address State', '')
        
        if opp_state and company_state and opp_state.upper() == company_state.upper():
            score += 15
        
        # Value range match (15 points)
        award_value = opportunity.get('awardValue', '')
        if award_value:
            try:
                value = float(str(award_value).replace('$', '').replace(',', ''))
                # Score based on reasonable contract size for company
                if 10000 <= value <= 10000000:  # $10K - $10M range
                    score += 15
                elif value <= 50000000:  # Up to $50M
                    score += 10
            except:
                pass
        
        # Response time bonus (10 points)
        response_date = opportunity.get('responseDeadLine', '')
        if response_date:
            try:
                deadline = datetime.strptime(response_date, '%m/%d/%Y %I:%M:%S %p')
                days_until = (deadline - datetime.now()).days
                
                if 14 <= days_until <= 60:  # Sweet spot for response time
                    score += 10
                elif 7 <= days_until <= 90:
                    score += 5
            except:
                pass
        
        # Active opportunity bonus (10 points)
        if opportunity.get('active') == 'Yes':
            score += 10
        
        return min(score, 100)

    def _summarize_matches(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize matching opportunities
        """
        if not matches:
            return {}
        
        total_value = 0
        high_score_matches = 0
        urgent_matches = 0
        
        for match in matches:
            # Value analysis
            award_value = match.get('awardValue', '')
            if award_value:
                try:
                    value = float(str(award_value).replace('$', '').replace(',', ''))
                    total_value += value
                except:
                    pass
            
            # High-score matches (80+)
            if match.get('match_score', 0) >= 80:
                high_score_matches += 1
            
            # Urgent matches (due within 14 days)
            response_date = match.get('responseDeadLine', '')
            if response_date:
                try:
                    deadline = datetime.strptime(response_date, '%m/%d/%Y %I:%M:%S %p')
                    days_until = (deadline - datetime.now()).days
                    if days_until <= 14:
                        urgent_matches += 1
                except:
                    pass
        
        return {
            'total_opportunities': len(matches),
            'high_score_matches': high_score_matches,
            'urgent_matches': urgent_matches,
            'total_estimated_value': total_value,
            'avg_match_score': sum(m.get('match_score', 0) for m in matches) / len(matches) if matches else 0
        }

    async def enrich_company_with_opportunities(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich company data with relevant procurement opportunities
        """
        enhanced_data = company_data.copy()
        
        # Get opportunity matches
        matches = await self.match_company_to_opportunities(company_data)
        
        if matches and matches.get('matched_opportunities'):
            enhanced_data['sam_opportunities_found'] = True
            enhanced_data['sam_total_matches'] = matches['total_matches']
            
            summary = matches.get('match_summary', {})
            enhanced_data['sam_high_score_matches'] = summary.get('high_score_matches', 0)
            enhanced_data['sam_urgent_matches'] = summary.get('urgent_matches', 0)
            enhanced_data['sam_total_opp_value'] = summary.get('total_estimated_value', 0)
            enhanced_data['sam_avg_match_score'] = summary.get('avg_match_score', 0)
            
            # Store top 5 opportunities
            top_opps = matches['matched_opportunities'][:5]
            enhanced_data['sam_top_opportunities'] = [
                {
                    'title': opp.get('title', ''),
                    'agency': opp.get('department', ''),
                    'value': opp.get('awardValue', ''),
                    'deadline': opp.get('responseDeadLine', ''),
                    'match_score': opp.get('match_score', 0)
                }
                for opp in top_opps
            ]
            
            logger.info(f"✅ Found {enhanced_data['sam_total_matches']} opportunities for {company_data.get('Organization Name', 'Company')}")
        else:
            enhanced_data['sam_opportunities_found'] = False
            enhanced_data['sam_total_matches'] = 0
            enhanced_data['sam_high_score_matches'] = 0
            enhanced_data['sam_urgent_matches'] = 0
        
        return enhanced_data

# CLI interface
async def main():
    """
    Main execution function for SAM Opportunities integration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='SAM.gov Opportunities API Integration')
    parser.add_argument('--api-key', required=True, help='SAM.gov API key')
    parser.add_argument('--mode', choices=['naics', 'keywords', 'smallbiz', 'agency', 'match'], 
                       default='smallbiz', help='Search mode')
    parser.add_argument('--query', '-q', help='Search query (NAICS code, keywords, agency)')
    parser.add_argument('--company-file', help='CSV file with company data for matching')
    parser.add_argument('--days', '-d', type=int, default=90, help='Days ahead to search')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    async with SAMOpportunitiesProcessor(args.api_key) as processor:
        result = None
        
        if args.mode == 'naics' and args.query:
            result = await processor.search_opportunities_by_naics(args.query, days_ahead=args.days)
        elif args.mode == 'keywords' and args.query:
            keywords = args.query.split(',')
            result = await processor.search_opportunities_by_keywords(keywords, days_ahead=args.days)
        elif args.mode == 'agency' and args.query:
            result = await processor.get_agency_opportunities(args.query, days_ahead=args.days)
        elif args.mode == 'smallbiz':
            result = await processor.search_small_business_opportunities(days_ahead=args.days)
        elif args.mode == 'match' and args.company_file:
            # Match companies from CSV to opportunities
            df = pd.read_csv(args.company_file)
            matches = []
            
            for _, company in df.head(10).iterrows():  # Limit to 10 for demo
                match = await processor.match_company_to_opportunities(company.to_dict())
                matches.append(match)
            
            result = {'company_matches': matches}
        
        if result:
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"Results saved to: {args.output}")
            else:
                print(json.dumps(result, indent=2, default=str))
        else:
            print(f"No opportunities found for query: {args.query}")

if __name__ == "__main__":
    asyncio.run(main())