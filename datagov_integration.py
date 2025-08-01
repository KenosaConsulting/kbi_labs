#!/usr/bin/env python3
"""
Data.gov CKAN API Integration
Provides access to 200,000+ federal datasets for comprehensive agency intelligence
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatasetIntelligence:
    """Dataset intelligence data structure"""
    id: str
    title: str
    name: str
    agency: str
    description: str
    resource_count: int
    last_updated: str
    tags: List[str]
    formats: List[str]
    procurement_relevance_score: float
    intelligence_value: str
    url: str

class DataGovProcessor:
    """
    Data.gov CKAN API Integration
    
    Provides:
    - Access to federal datasets
    - Agency data intelligence
    - Procurement-related dataset discovery
    - Data freshness analysis
    """
    
    def __init__(self):
        self.base_url = "https://catalog.data.gov/api/3"
        self.session = None
        self.rate_limit = 0.5  # 0.5 seconds between requests
        
        # Keywords that indicate procurement relevance
        self.procurement_keywords = [
            'contract', 'procurement', 'acquisition', 'spending', 'award', 'vendor',
            'supplier', 'competition', 'solicitation', 'federal', 'government',
            'budget', 'financial', 'grant', 'funding', 'performance'
        ]
        
        # High-value data categories for procurement intelligence
        self.high_value_categories = [
            'Federal Government Contractors',
            'Federal Spending',
            'Government Performance',
            'Budget and Financial Data',
            'Agency Operations',
            'Small Business Programs',
            'Economic Development',
            'Grant and Funding Data'
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
    
    async def search_datasets(self, query: str, limit: int = 100, agency: str = None) -> List[Dict[str, Any]]:
        """Search for datasets using CKAN API"""
        logger.info(f"Searching for datasets: '{query}' (limit: {limit})")
        
        endpoint = f"{self.base_url}/action/package_search"
        
        # Build search query
        search_query = query
        if agency:
            search_query += f" organization:{agency}"
        
        params = {
            'q': search_query,
            'rows': limit,
            'sort': 'metadata_modified desc',
            'facet.field': ['organization', 'tags', 'res_format']
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('result', {}).get('results', [])
                    logger.info(f"Found {len(results)} datasets for query: '{query}'")
                    return results
                else:
                    logger.error(f"Data.gov API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching datasets: {e}")
            return []
    
    async def get_procurement_datasets(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Get datasets specifically related to procurement"""
        logger.info("Fetching procurement-related datasets")
        
        all_datasets = []
        
        # Search for multiple procurement-related terms
        search_terms = [
            'federal procurement', 'government contracts', 'federal spending',
            'contract awards', 'vendor data', 'acquisition', 'small business contracting'
        ]
        
        for term in search_terms:
            datasets = await self.search_datasets(term, limit=limit//len(search_terms))
            all_datasets.extend(datasets)
            await asyncio.sleep(self.rate_limit)
        
        # Remove duplicates based on dataset ID
        seen_ids = set()
        unique_datasets = []
        for dataset in all_datasets:
            dataset_id = dataset.get('id', '')
            if dataset_id not in seen_ids:
                seen_ids.add(dataset_id)
                unique_datasets.append(dataset)
        
        logger.info(f"Found {len(unique_datasets)} unique procurement-related datasets")
        return unique_datasets
    
    async def get_agency_datasets(self, agency_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get datasets from a specific agency"""
        logger.info(f"Fetching datasets from agency: {agency_name}")
        
        # First, get organization info
        org_endpoint = f"{self.base_url}/action/organization_list"
        
        try:
            async with self.session.get(org_endpoint, params={'all_fields': True}) as response:
                if response.status == 200:
                    data = await response.json()
                    organizations = data.get('result', [])
                    
                    # Find matching organization
                    target_org = None
                    for org in organizations:
                        if agency_name.lower() in org.get('display_name', '').lower():
                            target_org = org.get('name')
                            break
                    
                    if target_org:
                        # Get datasets from this organization
                        datasets = await self.search_datasets('*', limit=limit, agency=target_org)
                        return datasets
                    else:
                        logger.warning(f"Agency '{agency_name}' not found in organizations")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching agency datasets: {e}")
            return []
    
    async def get_recent_datasets(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recently updated datasets"""
        logger.info(f"Fetching datasets updated in last {days} days")
        
        endpoint = f"{self.base_url}/action/package_search"
        
        # Calculate date threshold
        date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        params = {
            'q': f'metadata_modified:[{date_threshold}T00:00:00Z TO NOW]',
            'rows': limit,
            'sort': 'metadata_modified desc'
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('result', {}).get('results', [])
                    logger.info(f"Found {len(results)} recently updated datasets")
                    return results
                else:
                    logger.error(f"Data.gov API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching recent datasets: {e}")
            return []
    
    def calculate_procurement_relevance_score(self, dataset: Dict[str, Any]) -> float:
        """Calculate how relevant a dataset is to procurement intelligence"""
        score = 0.0
        
        title = dataset.get('title', '').lower()
        description = dataset.get('notes', '').lower()
        tags = [tag.get('display_name', '').lower() for tag in dataset.get('tags', [])]
        organization = dataset.get('organization', {}).get('title', '').lower()
        
        # Combine all text for analysis
        all_text = f"{title} {description} {' '.join(tags)} {organization}"
        
        # High-value keyword scoring
        high_value_keywords = [
            'federal procurement', 'government contract', 'federal spending',
            'contract award', 'usaspending', 'fpds', 'sam.gov'
        ]
        
        for keyword in high_value_keywords:
            if keyword in all_text:
                score += 3.0
        
        # Medium-value keyword scoring
        medium_value_keywords = [
            'procurement', 'contract', 'acquisition', 'spending', 'vendor',
            'supplier', 'award', 'competition', 'small business'
        ]
        
        for keyword in medium_value_keywords:
            if keyword in all_text:
                score += 1.5
        
        # Low-value keyword scoring
        low_value_keywords = [
            'financial', 'budget', 'performance', 'grant', 'funding'
        ]
        
        for keyword in low_value_keywords:
            if keyword in all_text:
                score += 0.5
        
        # Organization scoring (key agencies)
        key_agencies = [
            'general services administration', 'department of defense',
            'small business administration', 'office of management and budget'
        ]
        
        for agency in key_agencies:
            if agency in organization:
                score += 2.0
        
        # Resource count bonus (more resources = more valuable)
        resource_count = len(dataset.get('resources', []))
        if resource_count > 5:
            score += 1.0
        elif resource_count > 2:
            score += 0.5
        
        # Freshness bonus (recently updated datasets are more valuable)
        last_updated = dataset.get('metadata_modified', '')
        if last_updated:
            try:
                update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_old = (datetime.now().replace(tzinfo=update_date.tzinfo) - update_date).days
                if days_old < 30:
                    score += 1.0
                elif days_old < 90:
                    score += 0.5
            except:
                pass
        
        return min(score, 10.0)  # Cap at 10.0
    
    def determine_intelligence_value(self, dataset: Dict[str, Any], score: float) -> str:
        """Determine the intelligence value of a dataset"""
        if score >= 7.0:
            return "CRITICAL - High-value procurement intelligence"
        elif score >= 5.0:
            return "HIGH - Significant procurement insights available"
        elif score >= 3.0:
            return "MEDIUM - Useful supporting data"
        elif score >= 1.0:
            return "LOW - Limited procurement relevance"
        else:
            return "MINIMAL - Indirect relevance only"
    
    async def analyze_dataset_intelligence(self, datasets: List[Dict[str, Any]]) -> List[DatasetIntelligence]:
        """Analyze datasets for procurement intelligence value"""
        logger.info(f"Analyzing {len(datasets)} datasets for intelligence value")
        
        intelligence = []
        
        for dataset in datasets:
            try:
                # Calculate relevance score
                relevance_score = self.calculate_procurement_relevance_score(dataset)
                
                # Skip datasets with very low relevance
                if relevance_score < 0.5:
                    continue
                
                # Extract dataset information
                resources = dataset.get('resources', [])
                formats = list(set([res.get('format', '').upper() for res in resources if res.get('format')]))
                
                tags = [tag.get('display_name', '') for tag in dataset.get('tags', [])]
                
                intelligence_value = self.determine_intelligence_value(dataset, relevance_score)
                
                agency = dataset.get('organization', {}).get('title', 'Unknown Agency')
                
                intelligence.append(DatasetIntelligence(
                    id=dataset.get('id', ''),
                    title=dataset.get('title', ''),
                    name=dataset.get('name', ''),
                    agency=agency,
                    description=dataset.get('notes', '')[:200] + '...' if len(dataset.get('notes', '')) > 200 else dataset.get('notes', ''),
                    resource_count=len(resources),
                    last_updated=dataset.get('metadata_modified', ''),
                    tags=tags[:10],  # Limit to top 10 tags
                    formats=formats,
                    procurement_relevance_score=relevance_score,
                    intelligence_value=intelligence_value,
                    url=f"https://catalog.data.gov/dataset/{dataset.get('name', '')}"
                ))
                
            except Exception as e:
                logger.error(f"Error analyzing dataset {dataset.get('id', 'Unknown')}: {e}")
                continue
        
        # Sort by relevance score (highest first)
        intelligence.sort(key=lambda x: x.procurement_relevance_score, reverse=True)
        
        logger.info(f"Generated intelligence analysis for {len(intelligence)} datasets")
        return intelligence
    
    async def get_dataset_intelligence_summary(self, limit: int = 200) -> Dict[str, Any]:
        """Get comprehensive dataset intelligence summary"""
        logger.info("Generating comprehensive dataset intelligence summary")
        
        # Get procurement-related datasets
        datasets = await self.get_procurement_datasets(limit=limit)
        
        if not datasets:
            return {'error': 'No datasets available for analysis'}
        
        # Analyze for intelligence value
        intelligence = await self.analyze_dataset_intelligence(datasets)
        
        # Categorize by intelligence value
        critical_datasets = [d for d in intelligence if d.procurement_relevance_score >= 7.0]
        high_value_datasets = [d for d in intelligence if 5.0 <= d.procurement_relevance_score < 7.0]
        medium_value_datasets = [d for d in intelligence if 3.0 <= d.procurement_relevance_score < 5.0]
        
        # Agency analysis
        agency_counts = {}
        for item in intelligence:
            agency = item.agency
            agency_counts[agency] = agency_counts.get(agency, 0) + 1
        
        top_agencies = sorted(agency_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Format analysis
        all_formats = []
        for item in intelligence:
            all_formats.extend(item.formats)
        
        format_counts = {}
        for fmt in all_formats:
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        top_formats = sorted(format_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'total_datasets_analyzed': len(intelligence),
            'critical_intelligence_datasets': len(critical_datasets),
            'high_value_datasets': len(high_value_datasets),
            'medium_value_datasets': len(medium_value_datasets),
            'top_agencies': [{'agency': agency, 'dataset_count': count} for agency, count in top_agencies],
            'top_data_formats': [{'format': fmt, 'count': count} for fmt, count in top_formats],
            'critical_datasets': [
                {
                    'title': item.title,
                    'agency': item.agency,
                    'relevance_score': item.procurement_relevance_score,
                    'intelligence_value': item.intelligence_value,
                    'resource_count': item.resource_count,
                    'formats': item.formats,
                    'url': item.url
                }
                for item in critical_datasets[:10]  # Top 10 critical datasets
            ],
            'recommendations': {
                'immediate_integration': [item.title for item in critical_datasets[:5]],
                'high_priority_datasets': [item.title for item in high_value_datasets[:5]],
                'data_richness_trend': f"Average {sum(item.resource_count for item in intelligence) / len(intelligence):.1f} resources per dataset",
                'top_intelligence_agencies': [agency for agency, _ in top_agencies[:3]]
            }
        }

async def test_datagov_integration():
    """Test Data.gov integration"""
    print("📊 Testing Data.gov CKAN API Integration...")
    
    async with DataGovProcessor() as datagov:
        # Test basic dataset search
        datasets = await datagov.search_datasets('federal contracts', limit=20)
        print(f"✅ Found {len(datasets)} datasets for 'federal contracts'")
        
        # Test procurement dataset discovery
        procurement_datasets = await datagov.get_procurement_datasets(limit=50)
        print(f"✅ Discovered {len(procurement_datasets)} procurement-related datasets")
        
        # Test intelligence summary
        intelligence_summary = await datagov.get_dataset_intelligence_summary(limit=100)
        print(f"✅ Generated intelligence summary for {intelligence_summary.get('total_datasets_analyzed', 0)} datasets")
        
        # Display critical datasets
        critical_datasets = intelligence_summary.get('critical_datasets', [])
        if critical_datasets:
            print("\n🎯 Critical Intelligence Datasets:")
            for i, dataset in enumerate(critical_datasets[:5], 1):
                print(f"{i}. {dataset['title'][:60]}...")
                print(f"   Agency: {dataset['agency']}")
                print(f"   Relevance Score: {dataset['relevance_score']:.1f}")
                print(f"   Resources: {dataset['resource_count']} files")
                print(f"   Formats: {', '.join(dataset['formats'][:3])}")
                print()
        
        # Display recommendations
        recommendations = intelligence_summary.get('recommendations', {})
        if recommendations:
            print("📋 Dataset Intelligence Recommendations:")
            print(f"   Immediate Integration: {len(recommendations.get('immediate_integration', []))} datasets")
            print(f"   High Priority: {len(recommendations.get('high_priority_datasets', []))} datasets")
            print(f"   Data Richness: {recommendations.get('data_richness_trend', 'N/A')}")
            print(f"   Top Agencies: {', '.join(recommendations.get('top_intelligence_agencies', []))}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_datagov_integration())