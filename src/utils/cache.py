"""Simple in-memory cache service"""
from typing import Any, Optional
from datetime import datetime, timedelta
import asyncio

class CacheService:
    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > datetime.now():
                    return value
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set a value with TTL in seconds"""
        async with self._lock:
            expiry = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = (value, expiry)
    
    async def delete(self, key: str):
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()

# Global cache instance
cache_service = CacheService()
