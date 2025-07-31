"""Enhanced base class for external API integrations"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class RateLimiter:
    """Simple rate limiter"""
    max_requests: int
    window_seconds: int
    requests: List[datetime] = None
    
    def __post_init__(self):
        self.requests = []
    
    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        now = datetime.now()
        # Remove old requests outside window
        self.requests = [
            req for req in self.requests 
            if (now - req).total_seconds() < self.window_seconds
        ]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest = min(self.requests)
            wait_time = self.window_seconds - (now - oldest).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                await self.acquire()  # Recursive call after wait
        
        self.requests.append(now)


class CircuitBreaker:
    """Simple circuit breaker implementation"""
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def __aenter__(self):
        if self.state == "open":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception(f"Circuit breaker is open")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success
            self.failure_count = 0
            self.state = "closed"
        elif issubclass(exc_type, self.expected_exception):
            # Expected failure
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        return False  # Don't suppress exceptions


class EnhancedAPIIntegration(ABC):
    """Enhanced base class for external API integrations"""
    
    def __init__(
        self, 
        name: str, 
        base_url: str, 
        api_key: Optional[str] = None,
        rate_limit: int = 60,  # requests per minute
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=httpx.HTTPError
        )
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit,
            window_seconds=60
        )
        
        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=self._get_default_headers()
        )
        
        # Status tracking
        self.last_error: Optional[str] = None
        self.last_success: Optional[datetime] = None
        self.status = APIStatus.INACTIVE
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        headers = {
            "User-Agent": "KBI-Labs/3.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """Make HTTP request with circuit breaker, rate limiting"""
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Make request with circuit breaker
        try:
            async with self.circuit_breaker:
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    **kwargs
                )
                response.raise_for_status()
                
                # Update status
                self.status = APIStatus.ACTIVE
                self.last_success = datetime.now()
                
                # Return appropriate response type
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return response.json()
                elif "application/xml" in content_type or "text/xml" in content_type:
                    return response.text
                else:
                    return response.content
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.status = APIStatus.RATE_LIMITED
            else:
                self.status = APIStatus.ERROR
            self.last_error = str(e)
            raise
        except Exception as e:
            self.status = APIStatus.ERROR
            self.last_error = str(e)
            raise
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate API connection"""
        pass
    
    @abstractmethod
    async def get_enrichment_data(self, **kwargs) -> Dict[str, Any]:
        """Get enrichment data - must be implemented by subclasses"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "circuit_breaker_state": self.circuit_breaker.state
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
