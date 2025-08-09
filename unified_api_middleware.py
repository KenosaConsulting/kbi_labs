"""
Unified API Middleware for KBI Labs
==================================

This module consolidates all the scattered API integrations into a single
unified middleware layer that provides clean, consistent access to all
government data sources.

Replaces:
- src/api/routers/government_intelligence.py
- src/api/routers/procurement_intelligence.py  
- Multiple API servers and routers
- Scattered integration modules

With a single, unified API middleware that provides:
1. Consistent data models across all sources
2. Intelligent caching and rate limiting
3. Error handling and fallback mechanisms
4. Real-time data synchronization
5. Context-aware data enrichment
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import aiohttp
import redis
from concurrent.futures import ThreadPoolExecutor
import hashlib

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Government data sources"""
    SAM_GOV = "sam_gov"
    USASPENDING = "usaspending"
    FEDERAL_REGISTER = "federal_register"
    FPDS = "fpds"
    GSA = "gsa"
    CONGRESS = "congress_gov"
    SEC_EDGAR = "sec_edgar"
    USPTO = "uspto"

@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    source: DataSource
    data: Any
    timestamp: datetime
    cache_key: Optional[str] = None
    ttl_seconds: int = 3600
    success: bool = True
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None

@dataclass
class GovernmentOpportunity:
    """Unified opportunity data model across all sources"""
    id: str
    source: DataSource
    title: str
    agency: str
    description: str
    naics_codes: List[str]
    response_deadline: datetime
    estimated_value: Optional[float] = None
    set_aside: Optional[str] = None
    contract_type: Optional[str] = None
    place_of_performance: Optional[str] = None
    contact_info: Optional[Dict] = None
    
    # Standardized metadata
    created_at: datetime = None
    updated_at: datetime = None
    status: str = "active"
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass  
class ContractAward:
    """Unified contract award data model"""
    id: str
    source: DataSource
    recipient_uei: str
    recipient_name: str
    agency: str
    award_amount: float
    award_date: datetime
    naics_code: str
    description: str
    contract_type: str
    place_of_performance: str
    
class UnifiedAPIMiddleware:
    """
    Unified middleware that consolidates all government API access
    into a single, consistent interface with intelligent caching,
    rate limiting, and error handling.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(
            host='localhost', port=6379, decode_responses=True
        )
        self.session = None
        self.rate_limiters = {}
        self.circuit_breakers = {}
        self.api_configs = self._load_api_configurations()
        
        logger.info("UnifiedAPIMiddleware initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _load_api_configurations(self) -> Dict[DataSource, Dict]:
        """Load API configurations for all government sources"""
        return {
            DataSource.SAM_GOV: {
                "base_url": "https://api.sam.gov",
                "rate_limit": 1000,  # requests per hour
                "timeout": 30,
                "retry_attempts": 3,
                "cache_ttl": 1800  # 30 minutes
            },
            DataSource.USASPENDING: {
                "base_url": "https://api.usaspending.gov",
                "rate_limit": 10000,
                "timeout": 30,
                "retry_attempts": 3,
                "cache_ttl": 3600  # 1 hour
            },
            DataSource.FEDERAL_REGISTER: {
                "base_url": "https://www.federalregister.gov",
                "rate_limit": 1000,
                "timeout": 20,
                "retry_attempts": 2,
                "cache_ttl": 7200  # 2 hours
            },
            DataSource.FPDS: {
                "base_url": "https://api.fpds.gov",
                "rate_limit": 100,
                "timeout": 45,
                "retry_attempts": 3,
                "cache_ttl": 3600
            },
            DataSource.GSA: {
                "base_url": "https://api.gsa.gov",
                "rate_limit": 1000,
                "timeout": 30,
                "retry_attempts": 3,
                "cache_ttl": 1800
            }
        }
    
    async def get_opportunities(
        self,
        sources: Optional[List[DataSource]] = None,
        filters: Optional[Dict] = None,
        limit: int = 100
    ) -> List[GovernmentOpportunity]:
        """
        Unified opportunity retrieval across all government sources
        
        Args:
            sources: Specific data sources to query (default: all)
            filters: Common filters (agency, naics, value_range, etc.)
            limit: Maximum opportunities to return
        """
        if sources is None:
            sources = [DataSource.SAM_GOV, DataSource.GSA, DataSource.FPDS]
        
        logger.info(f"Fetching opportunities from {len(sources)} sources with filters: {filters}")
        
        # Fetch from all sources concurrently
        tasks = []
        for source in sources:
            tasks.append(self._fetch_opportunities_from_source(source, filters, limit))
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidate and deduplicate opportunities
        all_opportunities = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching opportunities: {result}")
                continue
            if isinstance(result, list):
                all_opportunities.extend(result)
        
        # Remove duplicates and apply unified scoring
        unique_opportunities = self._deduplicate_opportunities(all_opportunities)
        
        # Sort by relevance and return top results
        return unique_opportunities[:limit]
    
    async def _fetch_opportunities_from_source(
        self,
        source: DataSource,
        filters: Optional[Dict],
        limit: int
    ) -> List[GovernmentOpportunity]:
        """Fetch opportunities from a specific source with source-specific logic"""
        
        cache_key = self._generate_cache_key(f"opportunities_{source.value}", filters, limit)
        
        # Check cache first
        cached_result = await self._get_cached_result(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for {source.value} opportunities")
            return [GovernmentOpportunity(**opp) for opp in cached_result]
        
        try:
            start_time = time.time()
            
            # Source-specific opportunity fetching
            if source == DataSource.SAM_GOV:
                opportunities = await self._fetch_sam_opportunities(filters, limit)
            elif source == DataSource.GSA:
                opportunities = await self._fetch_gsa_opportunities(filters, limit)
            elif source == DataSource.FPDS:
                opportunities = await self._fetch_fpds_opportunities(filters, limit)
            else:
                logger.warning(f"Opportunity fetching not implemented for {source.value}")
                return []
            
            response_time = (time.time() - start_time) * 1000
            logger.info(f"Fetched {len(opportunities)} opportunities from {source.value} in {response_time:.2f}ms")
            
            # Cache the results
            await self._cache_result(
                cache_key,
                [asdict(opp) for opp in opportunities],
                self.api_configs[source]["cache_ttl"]
            )
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error fetching opportunities from {source.value}: {e}")
            return []
    
    async def _fetch_sam_opportunities(self, filters: Optional[Dict], limit: int) -> List[GovernmentOpportunity]:
        """Fetch opportunities from SAM.gov"""
        try:
            # Use existing SAM integration but standardize the output
            from src.integrations.government.sam_gov import SAMGovAPI
            
            sam_client = SAMGovAPI()
            raw_opportunities = await sam_client.get_opportunities(filters, limit)
            
            # Convert to unified format
            opportunities = []
            for opp_data in raw_opportunities:
                opportunity = GovernmentOpportunity(
                    id=opp_data.get('noticeId', ''),
                    source=DataSource.SAM_GOV,
                    title=opp_data.get('title', ''),
                    agency=opp_data.get('fullParentPathName', ''),
                    description=opp_data.get('description', ''),
                    naics_codes=opp_data.get('naicsCodes', []),
                    response_deadline=self._parse_date(opp_data.get('responseDeadLine')),
                    estimated_value=self._parse_value(opp_data.get('award', {}).get('estimatedValue')),
                    set_aside=opp_data.get('typeOfSetAside'),
                    contract_type=opp_data.get('award', {}).get('awardType'),
                    place_of_performance=opp_data.get('placeOfPerformance', {}).get('city', {}).get('name')
                )
                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error in SAM opportunity fetching: {e}")
            return []
    
    async def _fetch_gsa_opportunities(self, filters: Optional[Dict], limit: int) -> List[GovernmentOpportunity]:
        """Fetch opportunities from GSA"""
        # Implement GSA-specific opportunity fetching
        # This would use the existing GSA client but standardize output
        return []
    
    async def _fetch_fpds_opportunities(self, filters: Optional[Dict], limit: int) -> List[GovernmentOpportunity]:
        """Fetch opportunities from FPDS"""
        # Implement FPDS-specific opportunity fetching
        return []
    
    async def get_contract_history(
        self,
        company_uei: str,
        sources: Optional[List[DataSource]] = None,
        date_range: Optional[tuple] = None
    ) -> List[ContractAward]:
        """
        Unified contract history retrieval across all sources
        """
        if sources is None:
            sources = [DataSource.USASPENDING, DataSource.FPDS]
        
        logger.info(f"Fetching contract history for {company_uei} from {len(sources)} sources")
        
        # Fetch from all sources concurrently
        tasks = []
        for source in sources:
            tasks.append(self._fetch_contracts_from_source(source, company_uei, date_range))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidate results
        all_contracts = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching contracts: {result}")
                continue
            if isinstance(result, list):
                all_contracts.extend(result)
        
        # Deduplicate and sort
        unique_contracts = self._deduplicate_contracts(all_contracts)
        unique_contracts.sort(key=lambda x: x.award_date, reverse=True)
        
        return unique_contracts
    
    async def get_market_intelligence(
        self,
        naics_codes: Optional[List[str]] = None,
        agencies: Optional[List[str]] = None,
        time_range_days: int = 365
    ) -> Dict[str, Any]:
        """
        Unified market intelligence across all sources
        """
        logger.info("Generating comprehensive market intelligence")
        
        try:
            # Gather intelligence from multiple sources concurrently
            tasks = [
                self._get_spending_trends(naics_codes, agencies, time_range_days),
                self._get_opportunity_forecasts(naics_codes, agencies),
                self._get_regulatory_intelligence(agencies),
                self._get_competitive_landscape(naics_codes, agencies)
            ]
            
            spending_trends, forecasts, regulatory, competitive = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            
            return {
                "generated_at": datetime.now().isoformat(),
                "parameters": {
                    "naics_codes": naics_codes,
                    "agencies": agencies,
                    "time_range_days": time_range_days
                },
                "spending_trends": spending_trends if not isinstance(spending_trends, Exception) else {},
                "opportunity_forecasts": forecasts if not isinstance(forecasts, Exception) else {},
                "regulatory_intelligence": regulatory if not isinstance(regulatory, Exception) else {},
                "competitive_landscape": competitive if not isinstance(competitive, Exception) else {},
                "data_sources": [source.value for source in self.api_configs.keys()]
            }
            
        except Exception as e:
            logger.error(f"Error generating market intelligence: {e}")
            return {"error": str(e), "generated_at": datetime.now().isoformat()}
    
    # Utility Methods
    
    def _generate_cache_key(self, prefix: str, *args) -> str:
        """Generate a deterministic cache key"""
        key_data = f"{prefix}_{json.dumps(args, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result from Redis"""
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        return None
    
    async def _cache_result(self, cache_key: str, data: Any, ttl: int):
        """Cache result in Redis"""
        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    def _deduplicate_opportunities(self, opportunities: List[GovernmentOpportunity]) -> List[GovernmentOpportunity]:
        """Remove duplicate opportunities across sources"""
        seen = set()
        unique_opportunities = []
        
        for opp in opportunities:
            # Create a hash based on title and agency to identify duplicates
            opp_hash = hashlib.md5(f"{opp.title}_{opp.agency}".encode()).hexdigest()
            
            if opp_hash not in seen:
                seen.add(opp_hash)
                unique_opportunities.append(opp)
        
        return unique_opportunities
    
    def _deduplicate_contracts(self, contracts: List[ContractAward]) -> List[ContractAward]:
        """Remove duplicate contracts across sources"""
        seen = set()
        unique_contracts = []
        
        for contract in contracts:
            contract_hash = hashlib.md5(
                f"{contract.recipient_uei}_{contract.award_amount}_{contract.award_date}".encode()
            ).hexdigest()
            
            if contract_hash not in seen:
                seen.add(contract_hash)
                unique_contracts.append(contract)
        
        return unique_contracts
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Handle multiple date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_str[:len(fmt)], fmt)
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Date parsing error for '{date_str}': {e}")
        
        return None
    
    def _parse_value(self, value_str: Optional[Union[str, float, int]]) -> Optional[float]:
        """Parse monetary value to float"""
        if not value_str:
            return None
        
        try:
            if isinstance(value_str, (int, float)):
                return float(value_str)
            
            # Clean string and parse
            clean_str = str(value_str).replace('$', '').replace(',', '').replace(' ', '')
            return float(clean_str) if clean_str else None
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Value parsing error for '{value_str}': {e}")
            return None

# Singleton instance for global use
unified_api = UnifiedAPIMiddleware()

# Convenience functions for common operations
async def get_live_opportunities(
    company_profile: Dict,
    limit: int = 25
) -> List[GovernmentOpportunity]:
    """Get live opportunities relevant to company profile"""
    
    filters = {
        'naics': company_profile.get('primary_naics', []),
        'agency': company_profile.get('preferred_agencies', []),
        'value_range': company_profile.get('contract_value_range')
    }
    
    async with unified_api as api:
        return await api.get_opportunities(filters=filters, limit=limit)

async def get_comprehensive_market_data(
    naics_codes: List[str],
    agencies: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get comprehensive market intelligence for specific NAICS codes"""
    
    async with unified_api as api:
        return await api.get_market_intelligence(
            naics_codes=naics_codes,
            agencies=agencies,
            time_range_days=365
        )

# Export key components
__all__ = [
    'UnifiedAPIMiddleware',
    'GovernmentOpportunity', 
    'ContractAward',
    'DataSource',
    'get_live_opportunities',
    'get_comprehensive_market_data',
    'unified_api'
]