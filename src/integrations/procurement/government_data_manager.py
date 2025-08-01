"""
Government Data Manager

Central orchestrator for managing data ingestion from 70+ government sources.
Extends existing KBI Labs patterns for SAM.gov integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import redis
import json
from dataclasses import asdict

from ..base import BaseAPIIntegration
from .source_registry import ProcurementSourceRegistry, ProcurementSource, SourceType
from .scrapers import ScraperFactory

logger = logging.getLogger(__name__)

class GovernmentDataManager:
    """
    Manages comprehensive data ingestion from government procurement sources.
    Leverages existing KBI Labs Redis caching and error handling patterns.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.source_registry = ProcurementSourceRegistry()
        self.scraper_factory = ScraperFactory()
        self.redis_client = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            decode_responses=True
        )
        self.active_scrapers: Dict[str, BaseAPIIntegration] = {}
        self.processing_stats: Dict[str, Dict] = {}
        
        # Cache TTL settings (following existing KBI patterns)
        self.cache_ttl = {
            SourceType.CONTRACT_DATA: 21600,      # 6 hours
            SourceType.OPPORTUNITY: 14400,        # 4 hours  
            SourceType.BUDGET_FORECAST: 604800,   # 1 week
            SourceType.AGENCY_INFO: 86400,        # 24 hours
            SourceType.SMALL_BUSINESS: 86400,     # 24 hours
            SourceType.REGULATORY: 604800         # 1 week
        }
    
    async def initialize(self):
        """Initialize all active data sources"""
        logger.info("Initializing Government Data Manager...")
        
        active_sources = self.source_registry.get_all_active_sources()
        logger.info(f"Found {len(active_sources)} active sources")
        
        # Initialize scrapers for each source
        for source in active_sources:
            try:
                scraper = await self.scraper_factory.create_scraper(source)
                if await scraper.validate_connection():
                    self.active_scrapers[source.id] = scraper
                    logger.info(f"Initialized scraper for {source.name}")
                else:
                    logger.warning(f"Failed to validate connection for {source.name}")
            except Exception as e:
                logger.error(f"Failed to initialize {source.name}: {e}")
        
        logger.info(f"Successfully initialized {len(self.active_scrapers)} scrapers")
    
    async def refresh_all_sources(self) -> Dict[str, Any]:
        """Refresh data from all active sources"""
        logger.info("Starting comprehensive data refresh...")
        
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'sources_processed': 0,
            'sources_successful': 0,
            'sources_failed': 0,
            'errors': [],
            'data_summary': {}
        }
        
        # Process high priority sources first
        high_priority = self.source_registry.get_high_priority_sources()
        await self._process_sources_batch(high_priority, results)
        
        # Process remaining sources
        remaining_sources = [
            s for s in self.source_registry.get_all_active_sources() 
            if s.priority > 1
        ]
        await self._process_sources_batch(remaining_sources, results)
        
        results['completed_at'] = datetime.utcnow().isoformat()
        logger.info(f"Data refresh completed: {results['sources_successful']}/{results['sources_processed']} successful")
        
        return results
    
    async def _process_sources_batch(self, sources: List[ProcurementSource], results: Dict):
        """Process a batch of sources with rate limiting"""
        
        # Process in smaller batches to respect rate limits
        batch_size = 5
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self._process_single_source(source, results) for source in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Brief pause between batches
            await asyncio.sleep(1)
    
    async def _process_single_source(self, source: ProcurementSource, results: Dict):
        """Process data from a single source"""
        results['sources_processed'] += 1
        
        try:
            # Check if data is cached and fresh
            cache_key = f"procurement_data:{source.id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data and not self._is_cache_expired(source, cache_key):
                logger.debug(f"Using cached data for {source.name}")
                results['sources_successful'] += 1
                return json.loads(cached_data)
            
            # Fetch fresh data
            scraper = self.active_scrapers.get(source.id)
            if not scraper:
                raise Exception(f"No scraper available for {source.id}")
            
            logger.info(f"Fetching fresh data from {source.name}")
            data = await scraper.fetch_data()
            
            if data:
                # Cache the data
                ttl = self.cache_ttl.get(source.source_type, 86400)
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(data, default=str)
                )
                
                # Update processing stats
                self._update_processing_stats(source.id, len(data) if isinstance(data, list) else 1)
                
                results['sources_successful'] += 1
                results['data_summary'][source.id] = {
                    'records': len(data) if isinstance(data, list) else 1,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                logger.info(f"Successfully processed {source.name}")
                return data
            else:
                raise Exception(f"No data returned from {source.name}")
                
        except Exception as e:
            results['sources_failed'] += 1
            results['errors'].append({
                'source_id': source.id,
                'source_name': source.name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.error(f"Failed to process {source.name}: {e}")
            return None
    
    def _is_cache_expired(self, source: ProcurementSource, cache_key: str) -> bool:
        """Check if cached data has expired"""
        ttl = self.redis_client.ttl(cache_key)
        return ttl <= 0
    
    def _update_processing_stats(self, source_id: str, record_count: int):
        """Update processing statistics"""
        if source_id not in self.processing_stats:
            self.processing_stats[source_id] = {
                'total_records': 0,
                'total_runs': 0,
                'last_run': None,
                'avg_records_per_run': 0
            }
        
        stats = self.processing_stats[source_id]
        stats['total_records'] += record_count
        stats['total_runs'] += 1
        stats['last_run'] = datetime.utcnow().isoformat()
        stats['avg_records_per_run'] = stats['total_records'] / stats['total_runs']
    
    async def get_opportunity_data(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get procurement opportunities with optional filtering"""
        opportunity_sources = self.source_registry.get_sources_by_type(SourceType.OPPORTUNITY)
        
        all_opportunities = []
        for source in opportunity_sources:
            cache_key = f"procurement_data:{source.id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                if isinstance(data, list):
                    all_opportunities.extend(data)
                else:
                    all_opportunities.append(data)
        
        # Apply filters if provided
        if filters:
            all_opportunities = self._apply_filters(all_opportunities, filters)
        
        return all_opportunities
    
    async def get_contract_data(self, company_uei: str) -> Dict[str, Any]:
        """Get contract history for a specific company"""
        contract_sources = self.source_registry.get_sources_by_type(SourceType.CONTRACT_DATA)
        
        contract_data = {
            'uei': company_uei,
            'contracts': [],
            'summary': {
                'total_contracts': 0,
                'total_value': 0,
                'latest_contract_date': None
            }
        }
        
        for source in contract_sources:
            try:
                scraper = self.active_scrapers.get(source.id)
                if scraper and hasattr(scraper, 'get_company_contracts'):
                    company_contracts = await scraper.get_company_contracts(company_uei)
                    if company_contracts:
                        contract_data['contracts'].extend(company_contracts)
            except Exception as e:
                logger.error(f"Error fetching contract data from {source.name}: {e}")
        
        # Calculate summary statistics
        if contract_data['contracts']:
            contract_data['summary']['total_contracts'] = len(contract_data['contracts'])
            contract_data['summary']['total_value'] = sum(
                float(c.get('value', 0)) for c in contract_data['contracts']
            )
            
            dates = [c.get('award_date') for c in contract_data['contracts'] if c.get('award_date')]
            if dates:
                contract_data['summary']['latest_contract_date'] = max(dates)
        
        return contract_data
    
    async def get_budget_forecasts(self, agency: Optional[str] = None) -> List[Dict]:
        """Get budget and procurement forecasts"""
        budget_sources = self.source_registry.get_sources_by_type(SourceType.BUDGET_FORECAST)
        
        forecasts = []
        for source in budget_sources:
            cache_key = f"procurement_data:{source.id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                if isinstance(data, list):
                    forecasts.extend(data)
                else:
                    forecasts.append(data)
        
        # Filter by agency if specified
        if agency:
            forecasts = [f for f in forecasts if f.get('agency', '').lower() == agency.lower()]
        
        return forecasts
    
    def _apply_filters(self, data: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to procurement data"""
        filtered_data = data
        
        for filter_key, filter_value in filters.items():
            if filter_key == 'agency':
                filtered_data = [
                    item for item in filtered_data 
                    if item.get('agency', '').lower() == filter_value.lower()
                ]
            elif filter_key == 'naics':
                filtered_data = [
                    item for item in filtered_data 
                    if item.get('naics_code', '').startswith(str(filter_value))
                ]
            elif filter_key == 'set_aside':
                filtered_data = [
                    item for item in filtered_data 
                    if filter_value.lower() in item.get('set_aside_type', '').lower()
                ]
            elif filter_key == 'min_value':
                filtered_data = [
                    item for item in filtered_data 
                    if float(item.get('estimated_value', 0)) >= float(filter_value)
                ]
        
        return filtered_data
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics"""
        return {
            'active_sources': len(self.active_scrapers),
            'total_sources': len(self.source_registry.get_all_active_sources()),
            'processing_stats': self.processing_stats,
            'cache_status': self._get_cache_status(),
            'last_refresh': self._get_last_refresh_time()
        }
    
    def _get_cache_status(self) -> Dict[str, int]:
        """Get cache statistics"""
        cache_stats = {'total_keys': 0, 'expired_keys': 0}
        
        for source_id in self.source_registry.sources.keys():
            cache_key = f"procurement_data:{source_id}"
            if self.redis_client.exists(cache_key):
                cache_stats['total_keys'] += 1
                if self.redis_client.ttl(cache_key) <= 0:
                    cache_stats['expired_keys'] += 1
        
        return cache_stats
    
    def _get_last_refresh_time(self) -> Optional[str]:
        """Get timestamp of last successful refresh"""
        last_refresh = self.redis_client.get("procurement_data:last_refresh")
        return last_refresh
    
    async def shutdown(self):
        """Clean shutdown of all scrapers"""
        logger.info("Shutting down Government Data Manager...")
        
        for scraper in self.active_scrapers.values():
            try:
                await scraper.close()
            except Exception as e:
                logger.error(f"Error closing scraper: {e}")
        
        self.active_scrapers.clear()
        logger.info("Shutdown complete")