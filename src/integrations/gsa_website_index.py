"""
GSA Federal Website Index Integration

Integrates with GSA's comprehensive federal website index to provide
agency digital presence and capability intelligence.
"""

import requests
import pandas as pd
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from dataclasses import dataclass
from io import StringIO

from config.api_config import get_api_config, get_headers, has_api_key

logger = logging.getLogger(__name__)

@dataclass
class FederalWebsite:
    """Federal website data structure"""
    url: str
    domain: str
    agency: str
    bureau: str = None
    branch: str = None
    agencyCode: str = None
    bureauCode: str = None

class GSAWebsiteIndex:
    """Integration with GSA Federal Website Index and Site Scanning API"""
    
    def __init__(self):
        self.csv_url = "https://github.com/GSA/federal-website-index/raw/main/data/site-scanning-target-url-list.csv"
        self.api_config = get_api_config('gsa')
        self.api_headers = get_headers('gsa')
        self.site_scanning_base_url = "https://api.gsa.gov/technology/site-scanning/v1"
        self.cache_duration = 3600  # 1 hour cache
        self.cached_data = None
        self.cache_timestamp = None
        
        if not has_api_key('gsa'):
            logger.warning("GSA API key not available - using public data only")
    
    async def fetch_federal_websites(self) -> Dict:
        """Fetch latest federal website index with caching"""
        try:
            # Check cache
            if self._is_cache_valid():
                logger.info("Using cached federal website data")
                return self.cached_data
            
            logger.info("Fetching federal website index from GSA")
            
            # Fetch CSV data
            connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for now
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(self.csv_url) as response:
                    if response.status == 200:
                        csv_content = await response.text()
                        df = pd.read_csv(StringIO(csv_content))
                        
                        # Process and cache data
                        processed_data = self._process_website_data(df)
                        self.cached_data = processed_data
                        self.cache_timestamp = datetime.now()
                        
                        logger.info(f"Successfully fetched {len(df)} federal websites")
                        return processed_data
                    else:
                        logger.error(f"Failed to fetch website index: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error fetching federal website index: {e}")
            return {}
    
    def _process_website_data(self, df: pd.DataFrame) -> Dict:
        """Process website data for agency intelligence"""
        try:
            # Clean and standardize data
            df = df.dropna(subset=['Target URL'])
            df['domain'] = df['Target URL'].apply(self._extract_domain)
            
            # Agency analysis
            agency_stats = self._analyze_agencies(df)
            domain_stats = self._analyze_domains(df)
            digital_presence = self._analyze_digital_presence(df)
            
            return {
                'metadata': {
                    'total_websites': len(df),
                    'unique_domains': df['domain'].nunique(),
                    'unique_agencies': df.get('agency', pd.Series()).nunique() if 'agency' in df.columns else 0,
                    'last_updated': datetime.now().isoformat(),
                    'source': 'GSA Federal Website Index'
                },
                'agency_stats': agency_stats,
                'domain_stats': domain_stats,
                'digital_presence': digital_presence,
                'websites': df.to_dict('records')[:1000]  # Limit for performance
            }
            
        except Exception as e:
            logger.error(f"Error processing website data: {e}")
            return {}
    
    def _analyze_agencies(self, df: pd.DataFrame) -> Dict:
        """Analyze agency digital presence"""
        try:
            if 'agency' not in df.columns:
                return {}
                
            agency_counts = df['agency'].value_counts().to_dict()
            
            # Top agencies by web presence
            top_agencies = dict(list(agency_counts.items())[:20])
            
            return {
                'total_agencies': len(agency_counts),
                'top_agencies': top_agencies,
                'agency_distribution': {
                    'large_presence': len([a for a in agency_counts.values() if a > 50]),
                    'medium_presence': len([a for a in agency_counts.values() if 10 <= a <= 50]),
                    'small_presence': len([a for a in agency_counts.values() if a < 10])
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing agencies: {e}")
            return {}
    
    def _analyze_domains(self, df: pd.DataFrame) -> Dict:
        """Analyze domain patterns and infrastructure"""
        try:
            domain_counts = df['domain'].value_counts()
            
            # Domain type analysis
            gov_domains = domain_counts[domain_counts.index.str.endswith('.gov')]
            mil_domains = domain_counts[domain_counts.index.str.endswith('.mil')]
            
            return {
                'total_domains': len(domain_counts),
                'gov_domains': len(gov_domains),
                'mil_domains': len(mil_domains),
                'top_domains': domain_counts.head(20).to_dict(),
                'domain_types': {
                    '.gov': len(gov_domains),
                    '.mil': len(mil_domains),
                    'other': len(domain_counts) - len(gov_domains) - len(mil_domains)
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing domains: {e}")
            return {}
    
    def _analyze_digital_presence(self, df: pd.DataFrame) -> Dict:
        """Analyze overall digital presence patterns"""
        try:
            # URL pattern analysis
            https_sites = len(df[df['Target URL'].str.startswith('https://')])
            subdomain_sites = len(df[df['Target URL'].str.count(r'\.') > 2])
            
            return {
                'security': {
                    'https_adoption': https_sites / len(df) if len(df) > 0 else 0,
                    'total_secure_sites': https_sites
                },
                'infrastructure': {
                    'subdomain_usage': subdomain_sites / len(df) if len(df) > 0 else 0,
                    'total_subdomains': subdomain_sites
                },
                'digital_maturity_score': self._calculate_digital_maturity(df)
            }
        except Exception as e:
            logger.error(f"Error analyzing digital presence: {e}")
            return {}
    
    def _calculate_digital_maturity(self, df: pd.DataFrame) -> float:
        """Calculate overall federal digital maturity score"""
        try:
            https_score = len(df[df['Target URL'].str.startswith('https://')]) / len(df)
            domain_diversity = df['domain'].nunique() / len(df)
            
            # Simple maturity score (0-100)
            maturity_score = (https_score * 60 + domain_diversity * 40) * 100
            return round(maturity_score, 2)
        except:
            return 0.0
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.cached_data or not self.cache_timestamp:
            return False
        
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < self.cache_duration
    
    async def get_agency_websites(self, agency_name: str) -> List[Dict]:
        """Get websites for a specific agency"""
        try:
            data = await self.fetch_federal_websites()
            websites = data.get('websites', [])
            
            # Filter by agency (case-insensitive)
            agency_websites = [
                site for site in websites 
                if agency_name.lower() in site.get('agency', '').lower()
            ]
            
            return agency_websites[:50]  # Limit results
            
        except Exception as e:
            logger.error(f"Error getting agency websites: {e}")
            return []
    
    async def get_digital_capabilities_summary(self) -> Dict:
        """Get summary of government digital capabilities"""
        try:
            data = await self.fetch_federal_websites()
            
            return {
                'overview': data.get('metadata', {}),
                'top_agencies': data.get('agency_stats', {}).get('top_agencies', {}),
                'security_posture': data.get('digital_presence', {}).get('security', {}),
                'infrastructure_insights': data.get('digital_presence', {}).get('infrastructure', {}),
                'maturity_score': data.get('digital_presence', {}).get('digital_maturity_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting digital capabilities summary: {e}")
            return {}
    
    async def fetch_site_scanning_data(self, limit: int = 100) -> Dict:
        """Fetch enhanced site scanning data using GSA Site Scanning API"""
        try:
            if not has_api_key('gsa'):
                logger.info("GSA API key not available - skipping enhanced site scanning")
                return {}
            
            logger.info("Fetching enhanced site scanning data from GSA API")
            
            # Fetch scanned sites data
            url = f"{self.site_scanning_base_url}/scans"
            params = {
                'api_key': self.api_config.get('api_key'),
                'limit': limit,
                'format': 'json'
            }
            
            headers = self.api_headers.copy()
            
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        scans = data.get('data', [])
                        
                        # Process scanning results
                        enhanced_intelligence = self._process_scanning_results(scans)
                        
                        logger.info(f"Processed {len(scans)} site scanning results")
                        return enhanced_intelligence
                        
                    elif response.status == 401:
                        logger.error("GSA Site Scanning API authentication failed - check API key")
                        return {}
                    else:
                        logger.error(f"GSA Site Scanning API error: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Error fetching GSA site scanning data: {e}")
            return {}
    
    def _process_scanning_results(self, scans: List[Dict]) -> Dict:
        """Process site scanning results for intelligence insights"""
        try:
            total_sites = len(scans)
            if total_sites == 0:
                return {}
            
            # Analyze security metrics
            https_enabled = sum(1 for scan in scans if scan.get('https', False))
            secure_sites_percentage = (https_enabled / total_sites) * 100
            
            # Analyze performance metrics
            mobile_friendly = sum(1 for scan in scans if scan.get('mobile_friendly', False))
            mobile_percentage = (mobile_friendly / total_sites) * 100
            
            # Agency breakdown
            agency_performance = {}
            for scan in scans:
                agency = scan.get('agency', 'Unknown')
                if agency not in agency_performance:
                    agency_performance[agency] = {
                        'total_sites': 0,
                        'https_sites': 0,
                        'mobile_friendly': 0
                    }
                
                agency_performance[agency]['total_sites'] += 1
                if scan.get('https', False):
                    agency_performance[agency]['https_sites'] += 1
                if scan.get('mobile_friendly', False):
                    agency_performance[agency]['mobile_friendly'] += 1
            
            # Calculate maturity scores for each agency
            for agency in agency_performance:
                metrics = agency_performance[agency]
                total = metrics['total_sites']
                if total > 0:
                    https_score = (metrics['https_sites'] / total) * 50
                    mobile_score = (metrics['mobile_friendly'] / total) * 50
                    agency_performance[agency]['digital_maturity_score'] = https_score + mobile_score
                else:
                    agency_performance[agency]['digital_maturity_score'] = 0
            
            return {
                'scanning_summary': {
                    'total_sites_scanned': total_sites,
                    'https_adoption_percentage': secure_sites_percentage,
                    'mobile_friendly_percentage': mobile_percentage
                },
                'agency_digital_performance': dict(sorted(
                    agency_performance.items(), 
                    key=lambda x: x[1]['digital_maturity_score'], 
                    reverse=True
                )[:15]),
                'security_intelligence': {
                    'https_leaders': [agency for agency, metrics in agency_performance.items() 
                                    if metrics['total_sites'] > 5 and (metrics['https_sites'] / metrics['total_sites']) > 0.9],
                    'improvement_needed': [agency for agency, metrics in agency_performance.items() 
                                         if metrics['total_sites'] > 5 and (metrics['https_sites'] / metrics['total_sites']) < 0.5]
                },
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing scanning results: {e}")
            return {}

# Async helper functions for API integration
async def get_federal_website_intelligence():
    """Get comprehensive federal website intelligence"""
    gsa_index = GSAWebsiteIndex()
    return await gsa_index.fetch_federal_websites()

async def get_agency_digital_profile(agency_name: str):
    """Get digital profile for specific agency"""
    gsa_index = GSAWebsiteIndex()
    websites = await gsa_index.get_agency_websites(agency_name)
    capabilities = await gsa_index.get_digital_capabilities_summary()
    
    return {
        'agency': agency_name,
        'websites': websites,
        'digital_capabilities': capabilities,
        'website_count': len(websites)
    }

async def get_enhanced_gsa_intelligence():
    """Get enhanced GSA Site Scanning intelligence with API data"""
    gsa_index = GSAWebsiteIndex()
    
    # Get both public data and enhanced API data
    website_data = await gsa_index.fetch_federal_websites()
    scanning_data = await gsa_index.fetch_site_scanning_data()
    
    # Combine insights
    combined_intelligence = {
        'federal_websites': website_data,
        'site_scanning': scanning_data,
        'enhanced_analysis': {
            'api_enabled': has_api_key('gsa'),
            'data_sources': ['GSA Federal Website Index', 'GSA Site Scanning API'] if has_api_key('gsa') else ['GSA Federal Website Index'],
            'combined_insights': _merge_intelligence_sources(website_data, scanning_data)
        }
    }
    
    return combined_intelligence

def _merge_intelligence_sources(website_data: Dict, scanning_data: Dict) -> Dict:
    """Merge website index and scanning data for enhanced insights"""
    try:
        merged = {
            'total_federal_websites': website_data.get('metadata', {}).get('total_websites', 0),
            'top_agencies': website_data.get('agency_stats', {}).get('top_agencies', {}),
            'digital_maturity_overview': website_data.get('digital_presence', {}).get('digital_maturity_score', 0)
        }
        
        # Add scanning insights if available
        if scanning_data:
            merged.update({
                'security_posture': scanning_data.get('scanning_summary', {}),
                'agency_performance_rankings': scanning_data.get('agency_digital_performance', {}),
                'security_leaders': scanning_data.get('security_intelligence', {}).get('https_leaders', []),
                'improvement_opportunities': scanning_data.get('security_intelligence', {}).get('improvement_needed', [])
            })
        
        return merged
        
    except Exception as e:
        logger.error(f"Error merging intelligence sources: {e}")
        return {}