"""
Federal Register API Integration

Integrates with the Federal Register API to track regulatory changes,
rulemaking activities, and policy updates affecting government contractors.
"""

import requests
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class RegulatoryDocument:
    """Regulatory document data structure"""
    document_number: str
    title: str
    abstract: str
    publication_date: str
    agency_names: List[str]
    document_type: str
    action: str
    significant: bool
    contractor_relevance_score: float

class FederalRegisterAPI:
    """Integration with Federal Register API"""
    
    def __init__(self):
        self.base_url = "https://www.federalregister.gov/api/v1"
        self.session = None
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for now
        self.session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_recent_contractor_regulations(self, days: int = 30) -> List[Dict]:
        """Get recent regulations affecting government contractors"""
        try:
            cache_key = f"contractor_regs_{days}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]
            
            # Search for contractor-relevant regulations
            search_terms = [
                "federal acquisition",
                "procurement",
                "contractor",
                "contracting",
                "small business",
                "SBIR",
                "GSA",
                "defense contractor"
            ]
            
            all_docs = []
            
            for term in search_terms:
                docs = await self._search_documents(
                    term=term,
                    days=days,
                    document_types=['RULE', 'PRORULE', 'NOTICE']
                )
                all_docs.extend(docs)
            
            # Remove duplicates and score relevance
            unique_docs = self._deduplicate_documents(all_docs)
            scored_docs = [self._score_contractor_relevance(doc) for doc in unique_docs]
            
            # Sort by relevance and recency
            scored_docs.sort(key=lambda x: (x['contractor_relevance_score'], x['publication_date']), reverse=True)
            
            # Cache results
            self.cache[cache_key] = scored_docs[:50]  # Top 50 results
            
            logger.info(f"Found {len(scored_docs)} contractor-relevant regulations")
            return scored_docs[:50]
            
        except Exception as e:
            logger.error(f"Error fetching contractor regulations: {e}")
            return []
    
    async def get_agency_regulatory_activity(self, agency: str, days: int = 90) -> Dict:
        """Get regulatory activity summary for specific agency"""
        try:
            cache_key = f"agency_activity_{agency}_{days}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]
            
            # Search for agency documents
            docs = await self._search_documents(
                agency=agency,
                days=days,
                document_types=['RULE', 'PRORULE', 'NOTICE']
            )
            
            # Analyze activity patterns
            activity_summary = self._analyze_agency_activity(docs, agency)
            
            # Cache results
            self.cache[cache_key] = activity_summary
            
            return activity_summary
            
        except Exception as e:
            logger.error(f"Error getting agency regulatory activity: {e}")
            return {}
    
    async def get_procurement_policy_changes(self, days: int = 60) -> List[Dict]:
        """Get recent procurement policy changes"""
        try:
            # Focus on procurement-specific terms
            procurement_terms = [
                "Federal Acquisition Regulation",
                "FAR",
                "DFARS", 
                "procurement policy",
                "acquisition regulation",
                "contract administration"
            ]
            
            policy_docs = []
            
            for term in procurement_terms:
                docs = await self._search_documents(
                    term=term,
                    days=days,
                    document_types=['RULE', 'PRORULE'],
                    significant_only=True
                )
                policy_docs.extend(docs)
            
            # Remove duplicates and add policy impact analysis
            unique_docs = self._deduplicate_documents(policy_docs)
            analyzed_docs = [self._analyze_policy_impact(doc) for doc in unique_docs]
            
            # Sort by impact score
            analyzed_docs.sort(key=lambda x: x.get('policy_impact_score', 0), reverse=True)
            
            return analyzed_docs[:25]  # Top 25 policy changes
            
        except Exception as e:
            logger.error(f"Error getting procurement policy changes: {e}")
            return []
    
    async def _search_documents(self, term: str = None, agency: str = None, 
                              days: int = 30, document_types: List[str] = None,
                              significant_only: bool = False) -> List[Dict]:
        """Search Federal Register documents"""
        try:
            url = f"{self.base_url}/articles"
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                'per_page': 100,
                'order': 'newest',
                'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
                'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d'),
                'fields[]': [
                    'document_number', 'title', 'abstract', 'publication_date',
                    'agency_names', 'type', 'action', 'significant'
                ]
            }
            
            # Add search conditions
            if term:
                params['conditions[term]'] = term
            
            if agency:
                params['conditions[agencies][]'] = agency
            
            if document_types:
                params['conditions[type][]'] = document_types
            
            if significant_only:
                params['conditions[significant]'] = 1
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for now
                self.session = aiohttp.ClientSession(connector=connector)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logger.error(f"Federal Register API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching Federal Register: {e}")
            return []
    
    def _score_contractor_relevance(self, doc: Dict) -> Dict:
        """Score document relevance to government contractors"""
        try:
            score = 0.0
            title = doc.get('title') or ''
            abstract = doc.get('abstract') or ''
            title = title.lower() if title else ''
            abstract = abstract.lower() if abstract else ''
            text = f"{title} {abstract}"
            
            # High-value keywords
            high_value_terms = [
                'federal acquisition', 'procurement', 'contractor', 'contracting',
                'small business', 'sbir', 'sttr', 'gsa', 'far', 'dfars'
            ]
            
            # Medium-value keywords  
            medium_value_terms = [
                'acquisition', 'solicitation', 'award', 'proposal', 'bid',
                'competition', 'contract', 'vendor', 'supplier'
            ]
            
            # Score based on keyword presence
            for term in high_value_terms:
                if term in text:
                    score += 3.0
            
            for term in medium_value_terms:
                if term in text:
                    score += 1.0
            
            # Bonus for significant regulations
            if doc.get('significant'):
                score += 2.0
            
            # Bonus for certain agencies
            agency_names = doc.get('agency_names', [])
            high_impact_agencies = ['General Services Administration', 'Department of Defense', 
                                  'Small Business Administration', 'Office of Management and Budget']
            
            for agency in agency_names:
                if any(impact_agency in agency for impact_agency in high_impact_agencies):
                    score += 1.5
            
            # Normalize score (0-10 scale)
            normalized_score = min(10.0, score)
            
            doc['contractor_relevance_score'] = normalized_score
            return doc
            
        except Exception as e:
            logger.error(f"Error scoring contractor relevance: {e}")
            doc['contractor_relevance_score'] = 0.0
            return doc
    
    def _analyze_policy_impact(self, doc: Dict) -> Dict:
        """Analyze potential policy impact on contractors"""
        try:
            impact_score = 0.0
            title = doc.get('title') or ''
            abstract = doc.get('abstract') or ''
            title = title.lower() if title else ''
            abstract = abstract.lower() if abstract else ''
            
            # High-impact policy indicators
            high_impact_indicators = [
                'final rule', 'interim final rule', 'emergency rule',
                'compliance required', 'mandatory', 'shall comply'
            ]
            
            # Implementation timeline indicators
            timeline_indicators = [
                'effective immediately', 'effective date', 'compliance date',
                'implementation', 'transition period'
            ]
            
            # Score impact level
            text = f"{title} {abstract}"
            
            for indicator in high_impact_indicators:
                if indicator in text:
                    impact_score += 2.0
            
            for indicator in timeline_indicators:
                if indicator in text:
                    impact_score += 1.0
            
            # Extract key dates
            dates = self._extract_key_dates(text)
            
            doc['policy_impact_score'] = min(10.0, impact_score)
            doc['key_dates'] = dates
            doc['impact_level'] = self._classify_impact_level(impact_score)
            
            return doc
            
        except Exception as e:
            logger.error(f"Error analyzing policy impact: {e}")
            return doc
    
    def _extract_key_dates(self, text: str) -> List[str]:
        """Extract important dates from regulatory text"""
        try:
            # Simple date pattern matching
            date_patterns = [
                r'effective (\w+ \d{1,2}, \d{4})',
                r'compliance (\w+ \d{1,2}, \d{4})',
                r'implementation (\w+ \d{1,2}, \d{4})'
            ]
            
            dates = []
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                dates.extend(matches)
            
            return dates[:5]  # Limit to 5 dates
            
        except:
            return []
    
    def _classify_impact_level(self, score: float) -> str:
        """Classify policy impact level"""
        if score >= 6.0:
            return "HIGH"
        elif score >= 3.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _analyze_agency_activity(self, docs: List[Dict], agency: str) -> Dict:
        """Analyze regulatory activity patterns for agency"""
        try:
            if not docs:
                return {}
            
            # Activity metrics
            total_docs = len(docs)
            significant_docs = len([d for d in docs if d.get('significant')])
            rule_types = {}
            
            for doc in docs:
                doc_type = doc.get('type', 'Unknown')
                rule_types[doc_type] = rule_types.get(doc_type, 0) + 1
            
            # Recent activity trend
            recent_docs = [d for d in docs if self._is_recent_doc(d, days=30)]
            activity_trend = "increasing" if len(recent_docs) > total_docs * 0.4 else "stable"
            
            return {
                'agency': agency,
                'total_documents': total_docs,
                'significant_documents': significant_docs,
                'document_types': rule_types,
                'activity_trend': activity_trend,
                'avg_contractor_relevance': sum(d.get('contractor_relevance_score', 0) for d in docs) / total_docs if total_docs > 0 else 0,
                'recent_activity': len(recent_docs)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing agency activity: {e}")
            return {}
    
    def _is_recent_doc(self, doc: Dict, days: int = 30) -> bool:
        """Check if document is from recent period"""
        try:
            pub_date = datetime.strptime(doc.get('publication_date', ''), '%Y-%m-%d')
            cutoff_date = datetime.now() - timedelta(days=days)
            return pub_date >= cutoff_date
        except:
            return False
    
    def _deduplicate_documents(self, docs: List[Dict]) -> List[Dict]:
        """Remove duplicate documents"""
        seen = set()
        unique_docs = []
        
        for doc in docs:
            doc_id = doc.get('document_number')
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and valid"""
        if key not in self.cache:
            return False
        
        # Simple time-based cache invalidation
        return True  # For now, assume cache is valid

# Async helper functions for API integration
async def get_contractor_regulatory_intelligence():
    """Get comprehensive regulatory intelligence for contractors"""
    async with FederalRegisterAPI() as fr_api:
        recent_regs = await fr_api.get_recent_contractor_regulations()
        policy_changes = await fr_api.get_procurement_policy_changes()
        
        return {
            'recent_regulations': recent_regs,
            'policy_changes': policy_changes,
            'summary': {
                'total_regulations': len(recent_regs),
                'high_relevance_count': len([r for r in recent_regs if r.get('contractor_relevance_score', 0) > 7]),
                'policy_changes_count': len(policy_changes),
                'high_impact_policies': len([p for p in policy_changes if p.get('impact_level') == 'HIGH'])
            },
            'last_updated': datetime.now().isoformat()
        }

async def get_agency_regulatory_profile(agency_name: str):
    """Get regulatory activity profile for specific agency"""
    async with FederalRegisterAPI() as fr_api:
        activity = await fr_api.get_agency_regulatory_activity(agency_name)
        recent_regs = await fr_api.get_recent_contractor_regulations(days=60)
        
        # Filter regulations by agency
        agency_regs = [
            reg for reg in recent_regs 
            if any(agency_name.lower() in (agency or '').lower() 
                  for agency in reg.get('agency_names', [])
                  if agency is not None)
        ]
        
        return {
            'agency': agency_name,
            'activity_summary': activity,
            'recent_regulations': agency_regs[:10],
            'regulatory_intensity': len(agency_regs) / 60 if agency_regs else 0  # Regs per day
        }