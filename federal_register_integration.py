#!/usr/bin/env python3
"""
Federal Register API Integration
Provides regulatory intelligence and policy change monitoring for procurement impact
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RegulatoryIntelligence:
    """Regulatory intelligence data structure"""
    document_number: str
    title: str
    agency: str
    document_type: str
    publication_date: str
    effective_date: Optional[str]
    procurement_impact_score: float
    impact_summary: str
    relevant_keywords: List[str]
    url: str

class FederalRegisterProcessor:
    """
    Federal Register API Integration
    
    Provides:
    - Regulatory changes affecting procurement
    - Policy impact analysis
    - Procurement rule monitoring
    - Agency regulation tracking
    """
    
    def __init__(self):
        self.base_url = "https://www.federalregister.gov/api/v1"
        self.session = None
        self.rate_limit = 0.5  # 0.5 seconds between requests
        
        # Keywords that indicate procurement relevance
        self.procurement_keywords = [
            'acquisition', 'procurement', 'contract', 'contracting', 'solicitation',
            'rfp', 'rfq', 'proposal', 'bid', 'vendor', 'supplier', 'federal acquisition regulation',
            'far', 'dfars', 'government contract', 'small business', 'set-aside',
            'competition', 'award', 'evaluation', 'requirement', 'specification'
        ]
        
        # High-impact agencies for procurement
        self.key_agencies = [
            'General Services Administration', 'Department of Defense', 'Department of Homeland Security',
            'Department of Health and Human Services', 'Department of Veterans Affairs',
            'National Aeronautics and Space Administration', 'Department of Energy',
            'Department of Transportation', 'Environmental Protection Agency',
            'Office of Management and Budget', 'Small Business Administration'
        ]
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'KBI-Labs-Procurement-Intelligence/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_recent_documents(self, days: int = 30, document_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get recent Federal Register documents"""
        if document_types is None:
            document_types = ['RULE', 'PRORULE', 'NOTICE']
        
        logger.info(f"Fetching Federal Register documents from last {days} days")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        endpoint = f"{self.base_url}/documents.json"
        
        params = {
            'fields[]': ['document_number', 'title', 'agency_names', 'type', 'publication_date', 
                        'effective_on', 'abstract', 'html_url', 'body_html_url'],
            'conditions[publication_date][gte]': start_date.strftime('%Y-%m-%d'),
            'conditions[publication_date][lte]': end_date.strftime('%Y-%m-%d'),
            'conditions[type][]': document_types,
            'per_page': 1000,
            'order': 'newest'
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    logger.info(f"Retrieved {len(results)} Federal Register documents")
                    return results
                else:
                    logger.error(f"Federal Register API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching Federal Register data: {e}")
            return []
    
    async def get_procurement_related_documents(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get documents specifically related to procurement"""
        logger.info(f"Fetching procurement-related documents from last {days} days")
        
        # Get all recent documents first
        all_documents = await self.get_recent_documents(days=days)
        
        # Filter for procurement relevance
        procurement_docs = []
        for doc in all_documents:
            title = doc.get('title', '').lower()
            abstract = doc.get('abstract', '').lower()
            
            # Check for procurement keywords
            text_to_search = f"{title} {abstract}"
            if any(keyword in text_to_search for keyword in self.procurement_keywords):
                procurement_docs.append(doc)
            
            # Check for key agencies
            agency_names = doc.get('agency_names', [])
            if any(agency in str(agency_names) for agency in self.key_agencies):
                if doc not in procurement_docs:  # Avoid duplicates
                    procurement_docs.append(doc)
        
        logger.info(f"Found {len(procurement_docs)} procurement-related documents")
        return procurement_docs
    
    async def get_agency_documents(self, agency_slugs: List[str], days: int = 30) -> List[Dict[str, Any]]:
        """Get documents from specific agencies"""
        logger.info(f"Fetching documents from agencies: {agency_slugs}")
        
        documents = []
        for agency_slug in agency_slugs:
            endpoint = f"{self.base_url}/documents.json"
            
            params = {
                'fields[]': ['document_number', 'title', 'agency_names', 'type', 'publication_date', 
                            'effective_on', 'abstract', 'html_url'],
                'conditions[agencies][]': agency_slug,
                'conditions[publication_date][gte]': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'per_page': 100,
                'order': 'newest'
            }
            
            try:
                async with self.session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        agency_docs = data.get('results', [])
                        documents.extend(agency_docs)
                        logger.info(f"Retrieved {len(agency_docs)} documents from {agency_slug}")
                        
                        # Rate limiting
                        await asyncio.sleep(self.rate_limit)
                        
            except Exception as e:
                logger.error(f"Error fetching documents from {agency_slug}: {e}")
                continue
        
        return documents
    
    def calculate_procurement_impact_score(self, document: Dict[str, Any]) -> float:
        """Calculate how much a document impacts procurement"""
        score = 0.0
        
        title = document.get('title', '').lower()
        abstract = document.get('abstract', '').lower()
        doc_type = document.get('type', '')
        
        # Base score by document type
        type_scores = {
            'RULE': 3.0,  # Final rules have high impact
            'PRORULE': 2.0,  # Proposed rules have medium impact
            'NOTICE': 1.0  # Notices have lower impact
        }
        score += type_scores.get(doc_type, 0.5)
        
        # Keyword scoring
        high_impact_keywords = ['federal acquisition regulation', 'far', 'dfars', 'acquisition reform']
        medium_impact_keywords = ['contract', 'procurement', 'acquisition', 'solicitation']
        low_impact_keywords = ['small business', 'competition', 'evaluation']
        
        text_to_analyze = f"{title} {abstract}"
        
        for keyword in high_impact_keywords:
            if keyword in text_to_analyze:
                score += 2.0
        
        for keyword in medium_impact_keywords:
            if keyword in text_to_analyze:
                score += 1.0
        
        for keyword in low_impact_keywords:
            if keyword in text_to_analyze:
                score += 0.5
        
        # Agency scoring
        agency_names = str(document.get('agency_names', [])).lower()
        high_impact_agencies = ['general services administration', 'office of management and budget']
        medium_impact_agencies = ['defense', 'homeland security', 'veterans affairs']
        
        for agency in high_impact_agencies:
            if agency in agency_names:
                score += 2.0
        
        for agency in medium_impact_agencies:
            if agency in agency_names:
                score += 1.0
        
        return min(score, 10.0)  # Cap at 10.0
    
    def extract_relevant_keywords(self, document: Dict[str, Any]) -> List[str]:
        """Extract procurement-relevant keywords from document"""
        title = document.get('title', '').lower()
        abstract = document.get('abstract', '').lower()
        text = f"{title} {abstract}"
        
        found_keywords = []
        for keyword in self.procurement_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def generate_impact_summary(self, document: Dict[str, Any], score: float) -> str:
        """Generate a summary of the document's procurement impact"""
        doc_type = document.get('type', '')
        agency = document.get('agency_names', ['Unknown Agency'])[0] if document.get('agency_names') else 'Unknown Agency'
        
        if score >= 7.0:
            impact_level = "HIGH IMPACT"
        elif score >= 4.0:
            impact_level = "MODERATE IMPACT"
        elif score >= 2.0:
            impact_level = "LOW IMPACT"
        else:
            impact_level = "MINIMAL IMPACT"
        
        type_description = {
            'RULE': 'final regulation',
            'PRORULE': 'proposed regulation',
            'NOTICE': 'notice or announcement'
        }.get(doc_type, 'document')
        
        return f"{impact_level}: {agency} {type_description} affecting federal procurement"
    
    async def analyze_regulatory_intelligence(self, days: int = 30) -> List[RegulatoryIntelligence]:
        """Analyze recent documents for regulatory intelligence"""
        logger.info("Analyzing regulatory intelligence for procurement impact")
        
        # Get procurement-related documents
        documents = await self.get_procurement_related_documents(days=days)
        
        intelligence = []
        for doc in documents:
            try:
                # Calculate impact score
                impact_score = self.calculate_procurement_impact_score(doc)
                
                # Skip low-impact documents
                if impact_score < 1.0:
                    continue
                
                # Extract relevant information
                keywords = self.extract_relevant_keywords(doc)
                impact_summary = self.generate_impact_summary(doc, impact_score)
                
                intelligence.append(RegulatoryIntelligence(
                    document_number=doc.get('document_number', ''),
                    title=doc.get('title', ''),
                    agency=doc.get('agency_names', ['Unknown'])[0] if doc.get('agency_names') else 'Unknown',
                    document_type=doc.get('type', ''),
                    publication_date=doc.get('publication_date', ''),
                    effective_date=doc.get('effective_on'),
                    procurement_impact_score=impact_score,
                    impact_summary=impact_summary,
                    relevant_keywords=keywords,
                    url=doc.get('html_url', '')
                ))
                
            except Exception as e:
                logger.error(f"Error analyzing document {doc.get('document_number', 'Unknown')}: {e}")
                continue
        
        # Sort by impact score (highest first)
        intelligence.sort(key=lambda x: x.procurement_impact_score, reverse=True)
        
        logger.info(f"Generated regulatory intelligence for {len(intelligence)} documents")
        return intelligence
    
    async def get_regulatory_intelligence_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive regulatory intelligence summary"""
        logger.info("Generating comprehensive regulatory intelligence summary")
        
        intelligence = await self.analyze_regulatory_intelligence(days=days)
        
        if not intelligence:
            return {'error': 'No regulatory intelligence available'}
        
        # Categorize by impact level
        high_impact = [i for i in intelligence if i.procurement_impact_score >= 7.0]
        moderate_impact = [i for i in intelligence if 4.0 <= i.procurement_impact_score < 7.0]
        low_impact = [i for i in intelligence if 2.0 <= i.procurement_impact_score < 4.0]
        
        # Agency analysis
        agency_counts = {}
        for item in intelligence:
            agency = item.agency
            agency_counts[agency] = agency_counts.get(agency, 0) + 1
        
        # Top agencies by document volume
        top_agencies = sorted(agency_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days,
            'total_documents_analyzed': len(intelligence),
            'high_impact_documents': len(high_impact),
            'moderate_impact_documents': len(moderate_impact),
            'low_impact_documents': len(low_impact),
            'top_agencies': [{'agency': agency, 'document_count': count} for agency, count in top_agencies],
            'high_impact_alerts': [
                {
                    'title': item.title,
                    'agency': item.agency,
                    'impact_score': item.procurement_impact_score,
                    'summary': item.impact_summary,
                    'publication_date': item.publication_date,
                    'url': item.url
                }
                for item in high_impact[:5]  # Top 5 high-impact items
            ],
            'keyword_trends': list(set([keyword for item in intelligence for keyword in item.relevant_keywords]))[:10],
            'recommendations': {
                'immediate_attention': [item.title for item in high_impact[:3]],
                'monitor_closely': [item.title for item in moderate_impact[:3]],
                'regulatory_trend': 'Increased procurement regulation activity' if len(intelligence) > 10 else 'Normal regulatory activity'
            }
        }

async def test_federal_register_integration():
    """Test Federal Register integration"""
    print("📋 Testing Federal Register API Integration...")
    
    async with FederalRegisterProcessor() as fed_reg:
        # Test basic document retrieval
        recent_docs = await fed_reg.get_recent_documents(days=7)
        print(f"✅ Retrieved {len(recent_docs)} recent documents")
        
        # Test procurement-specific documents
        procurement_docs = await fed_reg.get_procurement_related_documents(days=14)
        print(f"✅ Found {len(procurement_docs)} procurement-related documents")
        
        # Test regulatory intelligence
        intelligence_summary = await fed_reg.get_regulatory_intelligence_summary(days=14)
        print(f"✅ Generated regulatory intelligence summary with {intelligence_summary.get('total_documents_analyzed', 0)} documents")
        
        # Display high-impact alerts
        high_impact_alerts = intelligence_summary.get('high_impact_alerts', [])
        if high_impact_alerts:
            print("\n🚨 High-Impact Regulatory Alerts:")
            for i, alert in enumerate(high_impact_alerts[:3], 1):
                print(f"{i}. {alert['title'][:80]}...")
                print(f"   Agency: {alert['agency']}")
                print(f"   Impact Score: {alert['impact_score']:.1f}")
                print(f"   Date: {alert['publication_date']}")
                print()
        
        # Display recommendations
        recommendations = intelligence_summary.get('recommendations', {})
        if recommendations:
            print("📋 Regulatory Intelligence Recommendations:")
            print(f"   Immediate Attention: {len(recommendations.get('immediate_attention', []))} items")
            print(f"   Monitor Closely: {len(recommendations.get('monitor_closely', []))} items")
            print(f"   Trend: {recommendations.get('regulatory_trend', 'N/A')}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_federal_register_integration())