"""
Base Procurement Scraper

Base class for all procurement data scrapers, extending KBI Labs integration patterns.
Provides common functionality for data extraction, caching, and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from abc import abstractmethod
import httpx
from datetime import datetime

from ...base import BaseAPIIntegration
from ..source_registry import ProcurementSource

logger = logging.getLogger(__name__)

class BaseProcurementScraper(BaseAPIIntegration):
    """Base class for procurement data scrapers"""
    
    def __init__(self, source: ProcurementSource):
        self.source = source
        
        # Initialize with source configuration
        api_key = None
        if source.requires_auth and source.api_key_env_var:
            import os
            api_key = os.getenv(source.api_key_env_var)
        
        super().__init__(
            name=source.name,
            base_url=source.url,
            api_key=api_key
        )
        
        # Rate limiting
        self.rate_limit = source.rate_limit_per_hour
        self.request_timestamps: List[datetime] = []
        
        # Extraction configuration
        self.extraction_config = source.extraction_config
    
    async def validate_connection(self) -> bool:
        """Validate connection to the data source"""
        try:
            # For API sources, try a simple health check
            if hasattr(self, '_health_check_endpoint'):
                response = await self._make_request('GET', self._health_check_endpoint)
                return response is not None
            
            # For web scraping sources, try to fetch the main page
            response = await self.client.get(self.base_url)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Connection validation failed for {self.name}: {e}")
            return False
    
    async def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data from the source - to be implemented by subclasses"""
        logger.info(f"Fetching data from {self.name}")
        
        # Check rate limiting
        if not await self._check_rate_limit():
            logger.warning(f"Rate limit exceeded for {self.name}")
            return []
        
        try:
            # Call the specific implementation
            data = await self._fetch_source_data()
            
            # Post-process the data
            processed_data = await self._process_data(data)
            
            logger.info(f"Successfully fetched {len(processed_data)} records from {self.name}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error fetching data from {self.name}: {e}")
            return []
    
    @abstractmethod
    async def _fetch_source_data(self) -> List[Dict[str, Any]]:
        """Fetch raw data from the specific source - must be implemented by subclasses"""
        pass
    
    async def _process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and standardize raw data"""
        processed_data = []
        
        for item in raw_data:
            try:
                # Apply source-specific processing
                processed_item = await self._process_single_item(item)
                
                if processed_item:
                    # Add metadata
                    processed_item['_source'] = self.source.id
                    processed_item['_source_name'] = self.source.name
                    processed_item['_extracted_at'] = datetime.utcnow().isoformat()
                    
                    processed_data.append(processed_item)
                    
            except Exception as e:
                logger.error(f"Error processing item from {self.name}: {e}")
                continue
        
        return processed_data
    
    async def _process_single_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single data item - can be overridden by subclasses"""
        return item
    
    async def _check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        now = datetime.utcnow()
        
        # Remove timestamps older than 1 hour
        hour_ago = now.timestamp() - 3600
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if ts.timestamp() > hour_ago
        ]
        
        # Check if we're within the rate limit
        if len(self.request_timestamps) >= self.rate_limit:
            return False
        
        # Add current timestamp
        self.request_timestamps.append(now)
        return True
    
    async def get_company_contracts(self, uei: str) -> List[Dict[str, Any]]:
        """Get contracts for a specific company - can be overridden by subclasses"""
        logger.warning(f"get_company_contracts not implemented for {self.name}")
        return []
    
    async def search_opportunities(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for procurement opportunities - can be overridden by subclasses"""
        logger.warning(f"search_opportunities not implemented for {self.name}")
        return []
    
    def _extract_standard_fields(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standard fields based on source type"""
        standard_item = {}
        
        # Map common fields based on source type
        field_mappings = self.extraction_config.get('field_mappings', {})
        
        for standard_field, source_field in field_mappings.items():
            if source_field in item:
                standard_item[standard_field] = item[source_field]
        
        return standard_item
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded"""
        if not await self._check_rate_limit():
            # Calculate wait time until oldest request expires
            if self.request_timestamps:
                oldest_request = min(self.request_timestamps)
                wait_time = 3600 - (datetime.utcnow().timestamp() - oldest_request.timestamp())
                
                if wait_time > 0:
                    logger.info(f"Rate limit exceeded, waiting {wait_time:.0f} seconds")
                    await asyncio.sleep(wait_time)
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about this data source"""
        return {
            'id': self.source.id,
            'name': self.source.name,
            'url': self.source.url,
            'type': self.source.source_type.value,
            'format': self.source.data_format.value,
            'priority': self.source.priority,
            'refresh_interval_hours': self.source.refresh_interval_hours,
            'rate_limit_per_hour': self.rate_limit,
            'active': self.source.active
        }