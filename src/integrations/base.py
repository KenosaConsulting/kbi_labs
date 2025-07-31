"""Base class for all external API integrations"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

class BaseAPIIntegration(ABC):
    """Base class for external API integrations"""
    
    def __init__(self, name: str, base_url: str, api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            headers=self._get_default_headers()
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        headers = {"User-Agent": "KBI-Labs/2.0"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in {self.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {self.name}: {e}")
            raise
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate API connection"""
        pass
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
