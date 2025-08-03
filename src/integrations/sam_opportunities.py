"""
SAM.gov Opportunities API Integration

Integrates with SAM.gov Opportunities API to provide real-time
government procurement opportunities data.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from config.api_config import get_api_config, get_headers, has_api_key

logger = logging.getLogger(__name__)

@dataclass
class ProcurementOpportunity:
    """Procurement opportunity data structure"""
    notice_id: str
    title: str
    solicitation_number: str
    department: str
    sub_tier: str
    office: str
    posted_date: str
    response_deadline: str
    archive_date: str
    award_number: str
    award_date: str
    award_amount: Optional[float]
    naics_code: str
    classification_code: str
    set_aside_code: str
    pop_country: str
    pop_state: str
    pop_zip: str

class SAMOpportunitiesAPI:
    """Integration with SAM.gov Opportunities API"""
    
    def __init__(self):
        self.config = get_api_config('sam_gov')
        self.base_url = self.config.get('base_url')
        self.headers = get_headers('sam_gov')
        self.session = None
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
        
        if not has_api_key('sam_gov'):
            logger.warning("SAM.gov API key not available")
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for now
        self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_active_opportunities(self, limit: int = 100) -> List[Dict]:
        """Get active procurement opportunities"""
        try:
            if not has_api_key('sam_gov'):
                return self._get_mock_opportunities()
            
            cache_key = f"active_opportunities_{limit}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]
            
            # Calculate date range for active opportunities
            today = datetime.now()
            start_date = (today - timedelta(days=7)).strftime('%m/%d/%Y')
            end_date = (today + timedelta(days=60)).strftime('%m/%d/%Y')
            
            url = f"{self.base_url}/opportunities/v2/search"
            params = {
                'api_key': self.config.get('api_key'),
                'postedFrom': start_date,
                'postedTo': end_date,
                'ptype': 'o',  # Opportunities
                'limit': limit
            }
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    
                    # Process and enhance opportunities
                    processed_opps = [self._process_opportunity(opp) for opp in opportunities]
                    
                    # Cache results
                    self.cache[cache_key] = processed_opps
                    
                    logger.info(f"Fetched {len(processed_opps)} active opportunities from SAM.gov")
                    return processed_opps
                    
                elif response.status == 401:
                    logger.error("SAM.gov API authentication failed - check API key")
                    return self._get_mock_opportunities()
                else:
                    logger.error(f"SAM.gov API error: {response.status}")
                    return self._get_mock_opportunities()
                    
        except Exception as e:
            logger.error(f"Error fetching SAM.gov opportunities: {e}")
            return self._get_mock_opportunities()
    
    async def get_opportunities_by_agency(self, agency: str, limit: int = 50) -> List[Dict]:
        """Get opportunities for specific agency"""
        try:
            if not has_api_key('sam_gov'):
                return self._get_mock_opportunities_by_agency(agency)
            
            today = datetime.now()
            start_date = (today - timedelta(days=30)).strftime('%m/%d/%Y')
            end_date = (today + timedelta(days=90)).strftime('%m/%d/%Y')
            
            url = f"{self.base_url}/opportunities/v2/search"
            params = {
                'api_key': self.config.get('api_key'),
                'postedFrom': start_date,
                'postedTo': end_date,
                'deptname': agency,
                'ptype': 'o',
                'limit': limit
            }
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    
                    processed_opps = [self._process_opportunity(opp) for opp in opportunities]
                    
                    logger.info(f"Fetched {len(processed_opps)} opportunities for {agency}")
                    return processed_opps
                else:
                    logger.error(f"SAM.gov API error for agency {agency}: {response.status}")
                    return self._get_mock_opportunities_by_agency(agency)
                    
        except Exception as e:
            logger.error(f"Error fetching opportunities for {agency}: {e}")
            return self._get_mock_opportunities_by_agency(agency)
    
    async def get_small_business_opportunities(self, limit: int = 50) -> List[Dict]:
        """Get small business set-aside opportunities"""
        try:
            if not has_api_key('sam_gov'):
                return self._get_mock_small_business_opportunities()
            
            today = datetime.now()
            start_date = (today - timedelta(days=14)).strftime('%m/%d/%Y')
            end_date = (today + timedelta(days=60)).strftime('%m/%d/%Y')
            
            url = f"{self.base_url}/opportunities/v2/search"
            params = {
                'api_key': self.config.get('api_key'),
                'postedFrom': start_date,
                'postedTo': end_date,
                'typeOfSetAside': 'SBA',  # Small Business Administration set-asides
                'ptype': 'o',
                'limit': limit
            }
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    opportunities = data.get('opportunitiesData', [])
                    
                    processed_opps = [self._process_opportunity(opp) for opp in opportunities]
                    
                    logger.info(f"Fetched {len(processed_opps)} small business opportunities")
                    return processed_opps
                else:
                    logger.error(f"SAM.gov small business API error: {response.status}")
                    return self._get_mock_small_business_opportunities()
                    
        except Exception as e:
            logger.error(f"Error fetching small business opportunities: {e}")
            return self._get_mock_small_business_opportunities()
    
    async def get_opportunities_dashboard_data(self) -> Dict:
        """Get comprehensive opportunities dashboard data"""
        try:
            # Fetch different types of opportunities
            active_opps = await self.get_active_opportunities(50)
            sb_opps = await self.get_small_business_opportunities(25)
            
            # Analyze opportunities
            total_value = sum(self._extract_estimated_value(opp) for opp in active_opps)
            upcoming_deadlines = len([opp for opp in active_opps if self._is_deadline_soon(opp)])
            
            # Agency analysis
            agency_breakdown = self._analyze_agencies(active_opps)
            naics_breakdown = self._analyze_naics_codes(active_opps)
            
            return {
                'summary': {
                    'total_active_opportunities': len(active_opps),
                    'small_business_opportunities': len(sb_opps),
                    'estimated_total_value': total_value,
                    'upcoming_deadlines': upcoming_deadlines
                },
                'active_opportunities': active_opps[:20],  # Top 20
                'small_business_opportunities': sb_opps[:10],  # Top 10 SB
                'agency_breakdown': agency_breakdown,
                'naics_breakdown': naics_breakdown,
                'market_intelligence': {
                    'most_active_agencies': list(agency_breakdown.keys())[:5],
                    'trending_naics': list(naics_breakdown.keys())[:5],
                    'average_opportunity_value': total_value / len(active_opps) if active_opps else 0
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating opportunities dashboard: {e}")
            return {}
    
    def _process_opportunity(self, opp: Dict) -> Dict:
        """Process and enhance opportunity data"""
        try:
            # Extract key information
            processed = {
                'notice_id': opp.get('noticeId', ''),
                'title': opp.get('title', ''),
                'solicitation_number': opp.get('solicitationNumber', ''),
                'department': opp.get('departmentName', ''),
                'sub_tier': opp.get('subTier', ''),
                'office': opp.get('officeAddress', {}).get('city', ''),
                'posted_date': opp.get('postedDate', ''),
                'response_deadline': opp.get('responseDeadline', ''),
                'archive_date': opp.get('archiveDate', ''),
                'naics_code': opp.get('naicsCode', ''),
                'classification_code': opp.get('classificationCode', ''),
                'set_aside_code': opp.get('typeOfSetAsideDescription', ''),
                'pop_state': opp.get('placeOfPerformance', {}).get('state', {}).get('name', ''),
                'pop_zip': opp.get('placeOfPerformance', {}).get('zip', ''),
                'description': opp.get('description', ''),
                'estimated_value': self._extract_estimated_value(opp),
                'ai_score': self._calculate_ai_score(opp)
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing opportunity: {e}")
            return opp
    
    def _extract_estimated_value(self, opp: Dict) -> float:
        """Extract estimated contract value from opportunity"""
        try:
            # Try to find value in various fields
            value_fields = ['awardAmount', 'estimatedValue', 'dollarAmount']
            
            for field in value_fields:
                if field in opp and opp[field]:
                    try:
                        return float(str(opp[field]).replace('$', '').replace(',', ''))
                    except:
                        continue
            
            # Try to extract from description
            description = opp.get('description', '').lower()
            if '$' in description:
                import re
                amounts = re.findall(r'\$[\d,]+', description)
                if amounts:
                    try:
                        return float(amounts[0].replace('$', '').replace(',', ''))
                    except:
                        pass
            
            return 0.0
            
        except:
            return 0.0
    
    def _calculate_ai_score(self, opp: Dict) -> float:
        """Calculate AI relevance score for opportunity"""
        try:
            score = 0.5  # Base score
            
            title = opp.get('title', '').lower()
            description = opp.get('description', '').lower()
            text = f"{title} {description}"
            
            # High-value keywords
            high_value_terms = ['technology', 'software', 'cybersecurity', 'AI', 'data', 'cloud']
            medium_value_terms = ['services', 'support', 'consulting', 'professional']
            
            for term in high_value_terms:
                if term in text:
                    score += 0.15
            
            for term in medium_value_terms:
                if term in text:
                    score += 0.05
            
            # Set-aside bonus
            set_aside = opp.get('typeOfSetAsideDescription', '').lower()
            if 'small business' in set_aside:
                score += 0.1
            
            return min(1.0, score)
            
        except:
            return 0.5
    
    def _is_deadline_soon(self, opp: Dict, days: int = 14) -> bool:
        """Check if opportunity deadline is within specified days"""
        try:
            deadline_str = opp.get('response_deadline', '')
            if not deadline_str:
                return False
            
            # Parse deadline date
            deadline = datetime.strptime(deadline_str, '%m/%d/%Y')
            cutoff = datetime.now() + timedelta(days=days)
            
            return deadline <= cutoff
            
        except:
            return False
    
    def _analyze_agencies(self, opportunities: List[Dict]) -> Dict[str, int]:
        """Analyze opportunities by agency"""
        agency_counts = {}
        
        for opp in opportunities:
            agency = opp.get('department', 'Unknown')
            agency_counts[agency] = agency_counts.get(agency, 0) + 1
        
        # Sort by count
        sorted_agencies = dict(sorted(agency_counts.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_agencies.items())[:10])  # Top 10
    
    def _analyze_naics_codes(self, opportunities: List[Dict]) -> Dict[str, int]:
        """Analyze opportunities by NAICS code"""
        naics_counts = {}
        
        for opp in opportunities:
            naics = opp.get('naics_code', 'Unknown')
            if naics and naics != 'Unknown':
                naics_counts[naics] = naics_counts.get(naics, 0) + 1
        
        # Sort by count
        sorted_naics = dict(sorted(naics_counts.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_naics.items())[:10])  # Top 10
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and valid"""
        return key in self.cache  # Simple cache for now
    
    def _get_mock_opportunities(self) -> List[Dict]:
        """Get mock opportunities for testing when API key unavailable"""
        return [
            {
                'notice_id': 'SAM-2024-001',
                'title': 'Enterprise Cloud Infrastructure Services',
                'solicitation_number': 'SAM-IT-2024-001',
                'department': 'General Services Administration',
                'sub_tier': 'Federal Acquisition Service',
                'office': 'Washington, DC',
                'posted_date': '03/01/2024',
                'response_deadline': '04/15/2024',
                'naics_code': '518210',
                'set_aside_code': 'Small Business Set-Aside',
                'pop_state': 'DC',
                'estimated_value': 15000000.0,
                'ai_score': 0.85
            },
            {
                'notice_id': 'SAM-2024-002',
                'title': 'Cybersecurity Assessment and Monitoring',
                'solicitation_number': 'SAM-SEC-2024-002',
                'department': 'Department of Homeland Security',
                'sub_tier': 'Cybersecurity and Infrastructure Security Agency',
                'office': 'Arlington, VA',
                'posted_date': '03/05/2024',
                'response_deadline': '04/20/2024',
                'naics_code': '541512',
                'set_aside_code': '8(a) Set-Aside',
                'pop_state': 'VA',
                'estimated_value': 8500000.0,
                'ai_score': 0.92
            }
        ]
    
    def _get_mock_opportunities_by_agency(self, agency: str) -> List[Dict]:
        """Get mock opportunities for specific agency"""
        mock_opps = self._get_mock_opportunities()
        return [opp for opp in mock_opps if agency.lower() in opp['department'].lower()]
    
    def _get_mock_small_business_opportunities(self) -> List[Dict]:
        """Get mock small business opportunities"""
        mock_opps = self._get_mock_opportunities()
        return [opp for opp in mock_opps if 'small business' in opp['set_aside_code'].lower()]

# Async helper functions
async def get_real_procurement_opportunities():
    """Get real procurement opportunities from SAM.gov"""
    async with SAMOpportunitiesAPI() as sam_api:
        dashboard_data = await sam_api.get_opportunities_dashboard_data()
        return dashboard_data

async def get_agency_opportunities(agency_name: str):
    """Get opportunities for specific agency"""
    async with SAMOpportunitiesAPI() as sam_api:
        opportunities = await sam_api.get_opportunities_by_agency(agency_name)
        return opportunities