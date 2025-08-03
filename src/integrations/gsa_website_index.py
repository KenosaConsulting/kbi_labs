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
    """Integration with GSA Federal Website Index"""
    
    def __init__(self):
        self.csv_url = "https://github.com/GSA/federal-website-index/raw/main/data/site-scanning-target-url-list.csv"
        self.cache_duration = 3600  # 1 hour cache
        self.cached_data = None
        self.cache_timestamp = None
    
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
                        df = pd.read_csv(pd.StringIO(csv_content))
                        
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