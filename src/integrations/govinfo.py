"""
GovInfo API Integration

Integrates with GovInfo API to provide congressional documents,
federal publications, and government information resources.
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
class GovInfoDocument:
    """Government document data structure"""
    package_id: str
    title: str
    doc_class: str
    collection_code: str
    date_issued: str
    government_author: str
    pages: int
    download_url: str
    congress: Optional[int]
    session: Optional[int]
    bill_number: Optional[str]
    bill_type: Optional[str]

class GovInfoAPI:
    """Integration with GovInfo API"""
    
    def __init__(self):
        self.config = get_api_config('govinfo')
        self.base_url = self.config.get('base_url', 'https://api.govinfo.gov')
        self.headers = get_headers('govinfo')
        self.session = None
        self.cache = {}
        self.cache_duration = 3600  # 1 hour
        
        if not has_api_key('govinfo'):
            logger.warning("GovInfo API key not available")
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for now
        self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_congressional_documents(self, congress: int = 118, limit: int = 50) -> List[Dict]:
        """Get congressional documents for contractor analysis"""
        try:
            if not has_api_key('govinfo'):
                return self._get_mock_congressional_documents()
            
            cache_key = f"congressional_docs_{congress}_{limit}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]
            
            # Query for congressional bills and reports
            url = f"{self.base_url}/collections"
            params = {
                'api_key': self.config.get('api_key'),
                'congress': congress,
                'docClass': 'hr,s,hjres,sjres',  # House/Senate bills and joint resolutions
                'limit': limit,
                'offset': 0
            }
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    documents = data.get('packages', [])
                    
                    # Process and enhance documents
                    processed_docs = [self._process_document(doc) for doc in documents]
                    
                    # Filter for contractor-relevant documents
                    contractor_docs = [doc for doc in processed_docs if self._is_contractor_relevant(doc)]
                    
                    # Cache results
                    self.cache[cache_key] = contractor_docs
                    
                    logger.info(f"Fetched {len(contractor_docs)} contractor-relevant documents from GovInfo")
                    return contractor_docs
                    
                elif response.status == 401:
                    logger.error("GovInfo API authentication failed - check API key")
                    return self._get_mock_congressional_documents()
                else:
                    logger.error(f"GovInfo API error: {response.status}")
                    return self._get_mock_congressional_documents()
                    
        except Exception as e:
            logger.error(f"Error fetching GovInfo documents: {e}")
            return self._get_mock_congressional_documents()
    
    async def get_federal_register_documents(self, days_back: int = 30, limit: int = 25) -> List[Dict]:
        """Get Federal Register documents related to contracting"""
        try:
            if not has_api_key('govinfo'):
                return self._get_mock_federal_register_docs()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            url = f"{self.base_url}/collections/FR"
            params = {
                'api_key': self.config.get('api_key'),
                'publishedDate': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
                'limit': limit
            }
            
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                self.session = aiohttp.ClientSession(connector=connector, headers=self.headers)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    documents = data.get('packages', [])
                    
                    processed_docs = [self._process_document(doc) for doc in documents]
                    contractor_docs = [doc for doc in processed_docs if self._is_contractor_relevant(doc)]
                    
                    logger.info(f"Fetched {len(contractor_docs)} contractor-relevant FR documents")
                    return contractor_docs
                else:
                    logger.error(f"GovInfo Federal Register API error: {response.status}")
                    return self._get_mock_federal_register_docs()
                    
        except Exception as e:
            logger.error(f"Error fetching Federal Register documents: {e}")
            return self._get_mock_federal_register_docs()
    
    async def get_govinfo_intelligence_dashboard(self) -> Dict:
        """Get comprehensive GovInfo intelligence dashboard data"""
        try:
            # Fetch different types of documents
            congressional_docs = await self.get_congressional_documents(118, 30)
            fr_docs = await self.get_federal_register_documents(30, 20)
            
            # Analyze document trends
            doc_categories = self._analyze_document_categories(congressional_docs + fr_docs)
            recent_activity = self._analyze_recent_activity(congressional_docs + fr_docs)
            
            return {
                'summary': {
                    'total_congressional_documents': len(congressional_docs),
                    'total_federal_register_docs': len(fr_docs),
                    'contractor_relevant_docs': len([d for d in congressional_docs + fr_docs if d.get('contractor_relevance_score', 0) > 0.5]),
                    'recent_activity_trend': recent_activity.get('trend', 'stable')
                },
                'congressional_documents': congressional_docs[:10],  # Top 10
                'federal_register_documents': fr_docs[:10],  # Top 10
                'document_categories': doc_categories,
                'recent_activity': recent_activity,
                'intelligence_insights': {
                    'most_active_congress_areas': self._get_active_areas(congressional_docs),
                    'trending_regulatory_topics': self._get_trending_topics(fr_docs),
                    'contractor_impact_assessment': self._assess_contractor_impact(congressional_docs + fr_docs)
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating GovInfo dashboard: {e}")
            return {}
    
    def _process_document(self, doc: Dict) -> Dict:
        """Process and enhance document data"""
        try:
            processed = {
                'package_id': doc.get('packageId', ''),
                'title': doc.get('title', ''),
                'doc_class': doc.get('docClass', ''),
                'collection_code': doc.get('collectionCode', ''),
                'date_issued': doc.get('dateIssued', ''),
                'government_author': doc.get('governmentAuthor1', ''),
                'pages': doc.get('pages', 0),
                'download_url': doc.get('download', {}).get('pdfLink', ''),
                'congress': doc.get('congress'),
                'session': doc.get('session'),
                'bill_number': doc.get('billNumber'),
                'bill_type': doc.get('billType'),
                'contractor_relevance_score': self._calculate_contractor_relevance(doc),
                'summary': doc.get('summary', '')[:500]  # Truncate summary
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return doc
    
    def _calculate_contractor_relevance(self, doc: Dict) -> float:
        """Calculate contractor relevance score for document"""
        try:
            score = 0.0
            
            title = doc.get('title', '').lower()
            summary = doc.get('summary', '').lower()
            text = f"{title} {summary}"
            
            # High-relevance terms for contractors
            high_relevance_terms = [
                'contract', 'contractor', 'procurement', 'acquisition',
                'small business', 'sbir', 'sttr', 'federal acquisition',
                'competitive bidding', 'sole source', 'gsa schedule'
            ]
            
            medium_relevance_terms = [
                'federal', 'government', 'agency', 'department',
                'regulation', 'compliance', 'certification',
                'cybersecurity', 'technology', 'services'
            ]
            
            for term in high_relevance_terms:
                if term in text:
                    score += 0.2
            
            for term in medium_relevance_terms:
                if term in text:
                    score += 0.05
            
            # Doc class bonus
            if doc.get('docClass') in ['hr', 's', 'hjres', 'sjres']:
                score += 0.1
            
            return min(1.0, score)
            
        except:
            return 0.3
    
    def _is_contractor_relevant(self, doc: Dict) -> bool:
        """Check if document is relevant to contractors"""
        return doc.get('contractor_relevance_score', 0) > 0.3
    
    def _analyze_document_categories(self, documents: List[Dict]) -> Dict[str, int]:
        """Analyze documents by category"""
        categories = {}
        
        for doc in documents:
            doc_class = doc.get('doc_class', 'Unknown')
            categories[doc_class] = categories.get(doc_class, 0) + 1
        
        # Sort by count
        sorted_categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_categories.items())[:10])  # Top 10
    
    def _analyze_recent_activity(self, documents: List[Dict]) -> Dict:
        """Analyze recent document activity"""
        try:
            if not documents:
                return {'trend': 'stable', 'recent_count': 0}
            
            # Count documents by date
            today = datetime.now()
            last_week = today - timedelta(days=7)
            last_month = today - timedelta(days=30)
            
            recent_docs = []
            for doc in documents:
                try:
                    doc_date = datetime.fromisoformat(doc.get('date_issued', '').replace('Z', '+00:00'))
                    if doc_date >= last_week:
                        recent_docs.append(doc)
                except:
                    continue
            
            trend = 'increasing' if len(recent_docs) > len(documents) * 0.3 else 'stable'
            
            return {
                'trend': trend,
                'recent_count': len(recent_docs),
                'total_analyzed': len(documents)
            }
            
        except:
            return {'trend': 'stable', 'recent_count': 0}
    
    def _get_active_areas(self, congressional_docs: List[Dict]) -> List[str]:
        """Get most active congressional areas"""
        areas = []
        for doc in congressional_docs[:5]:
            if doc.get('government_author'):
                areas.append(doc['government_author'])
        return list(set(areas))[:5]
    
    def _get_trending_topics(self, fr_docs: List[Dict]) -> List[str]:
        """Get trending regulatory topics"""
        topics = []
        for doc in fr_docs[:5]:
            title = doc.get('title', '')
            if len(title) > 20:
                topics.append(title[:50] + '...' if len(title) > 50 else title)
        return topics[:5]
    
    def _assess_contractor_impact(self, documents: List[Dict]) -> Dict:
        """Assess overall contractor impact"""
        high_impact = len([d for d in documents if d.get('contractor_relevance_score', 0) > 0.7])
        medium_impact = len([d for d in documents if 0.4 <= d.get('contractor_relevance_score', 0) <= 0.7])
        
        return {
            'high_impact_documents': high_impact,
            'medium_impact_documents': medium_impact,
            'total_analyzed': len(documents),
            'overall_impact_level': 'high' if high_impact > 5 else 'medium' if medium_impact > 10 else 'low'
        }
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and valid"""
        return key in self.cache  # Simple cache for now
    
    def _get_mock_congressional_documents(self) -> List[Dict]:
        """Get mock congressional documents for testing"""
        return [
            {
                'package_id': 'BILLS-118hr1234ih',
                'title': 'Small Business Innovation Research Enhancement Act of 2024',
                'doc_class': 'hr',
                'collection_code': 'BILLS',
                'date_issued': '2024-01-15T00:00:00Z',
                'government_author': 'House Committee on Small Business',
                'pages': 45,
                'download_url': 'https://www.govinfo.gov/content/pkg/BILLS-118hr1234ih/pdf/BILLS-118hr1234ih.pdf',
                'congress': 118,
                'session': 1,
                'bill_number': 'H.R.1234',
                'bill_type': 'hr',
                'contractor_relevance_score': 0.95,
                'summary': 'Enhances the Small Business Innovation Research (SBIR) program to increase contractor participation and funding opportunities.'
            },
            {
                'package_id': 'BILLS-118s567is',
                'title': 'Federal Acquisition Regulation Modernization Act',
                'doc_class': 's',
                'collection_code': 'BILLS',
                'date_issued': '2024-02-01T00:00:00Z',
                'government_author': 'Senate Committee on Homeland Security and Governmental Affairs',
                'pages': 67,
                'download_url': 'https://www.govinfo.gov/content/pkg/BILLS-118s567is/pdf/BILLS-118s567is.pdf',
                'congress': 118,
                'session': 1,
                'bill_number': 'S.567',
                'bill_type': 's',
                'contractor_relevance_score': 0.88,
                'summary': 'Modernizes the Federal Acquisition Regulation to streamline procurement processes and increase small business participation.'
            }
        ]
    
    def _get_mock_federal_register_docs(self) -> List[Dict]:
        """Get mock Federal Register documents for testing"""
        return [
            {
                'package_id': 'FR-2024-01234',
                'title': 'Cybersecurity Maturity Model Certification Requirements',
                'doc_class': 'fr',
                'collection_code': 'FR',
                'date_issued': '2024-01-20T00:00:00Z',
                'government_author': 'Department of Defense',
                'pages': 23,
                'download_url': 'https://www.govinfo.gov/content/pkg/FR-2024-01234/pdf/FR-2024-01234.pdf',
                'contractor_relevance_score': 0.92,
                'summary': 'New cybersecurity certification requirements for defense contractors under CMMC 2.0 framework.'
            }
        ]

# Async helper functions
async def get_govinfo_congressional_intelligence():
    """Get congressional intelligence from GovInfo"""
    async with GovInfoAPI() as govinfo_api:
        dashboard_data = await govinfo_api.get_govinfo_intelligence_dashboard()
        return dashboard_data

async def get_govinfo_documents(doc_type: str = 'congressional'):
    """Get GovInfo documents by type"""
    async with GovInfoAPI() as govinfo_api:
        if doc_type == 'congressional':
            documents = await govinfo_api.get_congressional_documents()
        elif doc_type == 'federal_register':
            documents = await govinfo_api.get_federal_register_documents()
        else:
            documents = []
        return documents