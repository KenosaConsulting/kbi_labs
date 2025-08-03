"""
Congress.gov API Integration

Integrates with Congress.gov API to track bills, votes, and congressional
activities that affect government contractors.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import re

from config.api_config import get_api_config, get_headers, has_api_key

logger = logging.getLogger(__name__)

@dataclass
class CongressionalBill:
    """Congressional bill data structure"""
    bill_id: str
    title: str
    number: str
    congress: int
    bill_type: str
    introduced_date: str
    latest_action: str
    sponsor: str
    contractor_relevance_score: float
    policy_areas: List[str]

class CongressAPI:
    """Integration with Congress.gov API"""
    
    def __init__(self):
        self.config = get_api_config('congress_gov')
        self.base_url = self.config.get('base_url')
        self.headers = get_headers('congress_gov')
        self.session = None
        self.cache = {}
        self.cache_duration = 3600  # 1 hour
        
        if not has_api_key('congress_gov'):
            logger.warning("Congress.gov API key not available")
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for now
        self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_contractor_relevant_bills(self, congress: int = 118, limit: int = 50) -> List[Dict]:
        """Get bills relevant to government contractors"""
        try:
            if not has_api_key('congress_gov'):
                return self._get_mock_bills()
            
            cache_key = f"contractor_bills_{congress}_{limit}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]
            
            # Search for contractor-relevant bills
            contractor_terms = [
                "federal acquisition",
                "procurement", 
                "contractor",
                "small business",
                "SBIR",
                "government contract",
                "acquisition reform"
            ]
            
            all_bills = []
            
            for term in contractor_terms:
                bills = await self._search_bills(congress, term, limit=20)
                all_bills.extend(bills)
            
            # Remove duplicates and score relevance
            unique_bills = self._deduplicate_bills(all_bills)
            scored_bills = [self._score_contractor_relevance(bill) for bill in unique_bills]
            
            # Sort by relevance score
            scored_bills.sort(key=lambda x: x.get('contractor_relevance_score', 0), reverse=True)
            
            # Cache results
            result = scored_bills[:limit]
            self.cache[cache_key] = result
            
            logger.info(f"Found {len(result)} contractor-relevant bills in Congress {congress}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching contractor bills: {e}")
            return self._get_mock_bills()
    
    async def get_procurement_policy_bills(self, congress: int = 118) -> List[Dict]:
        """Get bills specifically related to procurement policy"""
        try:
            if not has_api_key('congress_gov'):
                return self._get_mock_policy_bills()
            
            policy_terms = [
                "Federal Acquisition Regulation",
                "FAR",
                "procurement policy",
                "acquisition modernization", 
                "government contracting reform"
            ]
            
            policy_bills = []
            
            for term in policy_terms:
                bills = await self._search_bills(congress, term, limit=10)
                policy_bills.extend(bills)
            
            # Remove duplicates and add policy impact analysis
            unique_bills = self._deduplicate_bills(policy_bills)
            analyzed_bills = [self._analyze_policy_impact(bill) for bill in unique_bills]
            
            # Sort by policy impact score
            analyzed_bills.sort(key=lambda x: x.get('policy_impact_score', 0), reverse=True)
            
            return analyzed_bills[:25]
            
        except Exception as e:
            logger.error(f"Error fetching procurement policy bills: {e}")
            return self._get_mock_policy_bills()
    
    async def get_congressional_intelligence_summary(self, congress: int = 118) -> Dict:
        """Get summary of congressional activity affecting contractors"""
        try:
            contractor_bills = await self.get_contractor_relevant_bills(congress)
            policy_bills = await self.get_procurement_policy_bills(congress)
            
            # Analyze activity patterns
            high_relevance_bills = [b for b in contractor_bills if b.get('contractor_relevance_score', 0) >= 7.0]
            recent_activity = [b for b in contractor_bills if self._is_recent_activity(b)]
            
            return {
                'congress': congress,
                'summary': {
                    'total_contractor_bills': len(contractor_bills),
                    'high_relevance_bills': len(high_relevance_bills),
                    'policy_bills': len(policy_bills),
                    'recent_activity': len(recent_activity)
                },
                'top_contractor_bills': contractor_bills[:10],
                'top_policy_bills': policy_bills[:5],
                'activity_trend': self._analyze_activity_trend(contractor_bills),
                'policy_areas': self._extract_policy_areas(contractor_bills),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating congressional intelligence summary: {e}")
            return {}
    
    async def _search_bills(self, congress: int, search_term: str, limit: int = 20) -> List[Dict]:
        """Search for bills by term"""
        try:
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
            
            url = f"{self.base_url}/bill/{congress}"
            params = {
                'format': 'json',
                'limit': limit,
                'offset': 0
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    bills = data.get('bills', [])
                    
                    # Filter bills by search term
                    relevant_bills = []
                    for bill in bills:
                        title = bill.get('title', '').lower()
                        if search_term.lower() in title:
                            relevant_bills.append(bill)
                    
                    return relevant_bills
                else:
                    logger.error(f"Congress API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching bills: {e}")
            return []
    
    def _score_contractor_relevance(self, bill: Dict) -> Dict:
        """Score bill relevance to government contractors"""
        try:
            score = 0.0
            title = bill.get('title', '').lower()
            
            # High-value keywords
            high_value_terms = [
                'federal acquisition', 'procurement', 'contractor', 'contracting',
                'small business', 'sbir', 'sttr', 'government contract'
            ]
            
            # Medium-value keywords
            medium_value_terms = [
                'acquisition', 'competition', 'bid', 'proposal', 'award',
                'vendor', 'supplier', 'federal spending'
            ]
            
            # Score based on keyword presence
            for term in high_value_terms:
                if term in title:
                    score += 3.0
            
            for term in medium_value_terms:
                if term in title:
                    score += 1.0
            
            # Bonus for specific bill types
            bill_type = bill.get('type', '').lower()
            if bill_type in ['hr', 's']:  # House/Senate bills (not resolutions)
                score += 1.0
            
            # Normalize score (0-10 scale)
            normalized_score = min(10.0, score)
            
            bill['contractor_relevance_score'] = normalized_score
            return bill
            
        except Exception as e:
            logger.error(f"Error scoring contractor relevance: {e}")
            bill['contractor_relevance_score'] = 0.0
            return bill
    
    def _analyze_policy_impact(self, bill: Dict) -> Dict:
        """Analyze potential policy impact of bill"""
        try:
            impact_score = 0.0
            title = bill.get('title', '').lower()
            
            # High-impact policy indicators
            high_impact_indicators = [
                'reform', 'modernization', 'act', 'amendment',
                'compliance', 'requirement', 'mandate'
            ]
            
            # Implementation scope indicators
            scope_indicators = [
                'federal', 'government-wide', 'department', 'agency',
                'small business', 'all contractors'
            ]
            
            # Score impact level
            for indicator in high_impact_indicators:
                if indicator in title:
                    impact_score += 2.0
            
            for indicator in scope_indicators:
                if indicator in title:
                    impact_score += 1.0
            
            bill['policy_impact_score'] = min(10.0, impact_score)
            bill['impact_level'] = self._classify_impact_level(impact_score)
            
            return bill
            
        except Exception as e:
            logger.error(f"Error analyzing policy impact: {e}")
            return bill
    
    def _classify_impact_level(self, score: float) -> str:
        """Classify policy impact level"""
        if score >= 6.0:
            return "HIGH"
        elif score >= 3.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _deduplicate_bills(self, bills: List[Dict]) -> List[Dict]:
        """Remove duplicate bills"""
        seen = set()
        unique_bills = []
        
        for bill in bills:
            bill_id = f"{bill.get('congress', 0)}_{bill.get('type', '')}_{bill.get('number', '')}"
            if bill_id not in seen:
                seen.add(bill_id)
                unique_bills.append(bill)
        
        return unique_bills
    
    def _is_recent_activity(self, bill: Dict, days: int = 30) -> bool:
        """Check if bill has recent activity"""
        try:
            # For now, assume bills from current congress are recent
            current_congress = 118
            return bill.get('congress', 0) == current_congress
        except:
            return False
    
    def _analyze_activity_trend(self, bills: List[Dict]) -> str:
        """Analyze congressional activity trend"""
        if not bills:
            return "stable"
        
        high_relevance_count = len([b for b in bills if b.get('contractor_relevance_score', 0) >= 7.0])
        
        if high_relevance_count > len(bills) * 0.3:
            return "increasing"
        elif high_relevance_count > len(bills) * 0.1:
            return "active"
        else:
            return "stable"
    
    def _extract_policy_areas(self, bills: List[Dict]) -> List[str]:
        """Extract policy areas from bills"""
        policy_areas = []
        
        for bill in bills:
            title = bill.get('title', '').lower()
            
            if 'small business' in title:
                policy_areas.append('Small Business')
            if 'cybersecurity' in title or 'security' in title:
                policy_areas.append('Cybersecurity')
            if 'acquisition' in title or 'procurement' in title:
                policy_areas.append('Acquisition Reform')
            if 'technology' in title or 'innovation' in title:
                policy_areas.append('Technology Innovation')
        
        # Return unique policy areas
        return list(set(policy_areas))
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and valid"""
        return key in self.cache  # Simple cache for now
    
    def _get_mock_bills(self) -> List[Dict]:
        """Get mock contractor-relevant bills for testing"""
        return [
            {
                'congress': 118,
                'type': 'hr',
                'number': '1234',
                'title': 'Federal Acquisition Modernization Act of 2024',
                'introducedDate': '2024-01-15',
                'latestAction': 'Referred to Committee on Oversight and Reform',
                'sponsor': 'Rep. Smith, John',
                'contractor_relevance_score': 9.0,
                'policy_areas': ['Acquisition Reform']
            },
            {
                'congress': 118,
                'type': 's',
                'number': '567',
                'title': 'Small Business Contracting Enhancement Act',
                'introducedDate': '2024-02-01',
                'latestAction': 'Passed Senate, referred to House',
                'sponsor': 'Sen. Johnson, Mary',
                'contractor_relevance_score': 8.5,
                'policy_areas': ['Small Business']
            }
        ]
    
    def _get_mock_policy_bills(self) -> List[Dict]:
        """Get mock policy bills for testing"""
        return [
            {
                'congress': 118,
                'type': 'hr',
                'number': '2468',
                'title': 'Procurement Transparency and Efficiency Act',
                'introducedDate': '2024-01-20',
                'latestAction': 'Committee markup scheduled',
                'sponsor': 'Rep. Williams, Sarah',
                'policy_impact_score': 8.0,
                'impact_level': 'HIGH'
            }
        ]

# Async helper functions
async def get_congressional_contractor_intelligence():
    """Get comprehensive congressional intelligence for contractors"""
    async with CongressAPI() as congress_api:
        summary = await congress_api.get_congressional_intelligence_summary()
        return summary

async def get_contractor_bills(congress: int = 118):
    """Get contractor-relevant bills"""
    async with CongressAPI() as congress_api:
        bills = await congress_api.get_contractor_relevant_bills(congress)
        return bills