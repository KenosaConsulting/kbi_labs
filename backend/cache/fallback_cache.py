#!/usr/bin/env python3
"""
Fallback Cache Client - In-memory cache when Redis is not available
Compatible with Python 3.13+
"""

import json
import logging
import os
import time
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class FallbackCache:
    """
    In-memory cache client for when Redis is not available
    """
    
    def __init__(self):
        self.cache_data: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
        self.ml_cache_ttl = int(os.getenv("ML_CACHE_TTL_SECONDS", "86400"))  # 24 hours
        self._lock = threading.RLock()
        self.connected = False
    
    async def connect(self) -> None:
        """Initialize cache connection"""
        try:
            logger.info("Using in-memory fallback cache (Redis not available)")
            self.connected = True
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
    
    async def disconnect(self) -> None:
        """Close cache connection"""
        with self._lock:
            self.cache_data.clear()
            self.connected = False
            logger.info("Fallback cache disconnected")
    
    def _generate_cache_key(self, prefix: str, identifier: Union[str, Dict[str, Any]]) -> str:
        """Generate consistent cache key"""
        if isinstance(identifier, dict):
            sorted_items = sorted(identifier.items())
            identifier_str = json.dumps(sorted_items, sort_keys=True)
        else:
            identifier_str = str(identifier)
        
        key_hash = hashlib.md5(identifier_str.encode()).hexdigest()
        return f"kbi:{prefix}:{key_hash}"
    
    def _is_expired(self, expiry_time: float) -> bool:
        """Check if cache entry has expired"""
        return time.time() > expiry_time
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache_data.items():
            if current_time > entry['expires_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache_data[key]
    
    async def get(self, key: str, prefix: str = "general") -> Optional[Any]:
        """Get cached value"""
        if not self.connected:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            
            with self._lock:
                # Clean up expired entries periodically
                if len(self.cache_data) % 100 == 0:
                    self._cleanup_expired()
                
                entry = self.cache_data.get(cache_key)
                if entry and not self._is_expired(entry['expires_at']):
                    return entry['value']
                elif entry:
                    # Remove expired entry
                    del self.cache_data[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        prefix: str = "general"
    ) -> bool:
        """Set cached value"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            
            with self._lock:
                self.cache_data[cache_key] = {
                    'value': value,
                    'expires_at': expires_at,
                    'created_at': time.time()
                }
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "general") -> bool:
        """Delete cached value"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            
            with self._lock:
                if cache_key in self.cache_data:
                    del self.cache_data[cache_key]
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "general") -> bool:
        """Check if key exists in cache"""
        if not self.connected:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            
            with self._lock:
                entry = self.cache_data.get(cache_key)
                return entry is not None and not self._is_expired(entry['expires_at'])
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str, prefix: str = "general") -> Optional[int]:
        """Get remaining TTL for key"""
        if not self.connected:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            
            with self._lock:
                entry = self.cache_data.get(cache_key)
                if entry and not self._is_expired(entry['expires_at']):
                    remaining = int(entry['expires_at'] - time.time())
                    return remaining if remaining > 0 else 0
            
            return None
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None
    
    async def clear_pattern(self, pattern: str, prefix: str = "general") -> int:
        """Clear all keys matching pattern"""
        if not self.connected:
            return 0
        
        try:
            search_prefix = f"kbi:{prefix}:"
            matching_keys = []
            
            with self._lock:
                for key in self.cache_data.keys():
                    if key.startswith(search_prefix) and pattern in key:
                        matching_keys.append(key)
                
                for key in matching_keys:
                    del self.cache_data[key]
            
            logger.info(f"Cleared {len(matching_keys)} cache keys matching pattern: {pattern}")
            return len(matching_keys)
            
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.connected:
            return {"status": "disconnected"}
        
        try:
            with self._lock:
                total_entries = len(self.cache_data)
                expired_count = 0
                current_time = time.time()
                
                for entry in self.cache_data.values():
                    if current_time > entry['expires_at']:
                        expired_count += 1
            
            return {
                "status": "connected",
                "cache_type": "in-memory",
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "active_entries": total_entries - expired_count,
                "memory_usage": "N/A (in-memory)",
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    # Specialized caching methods
    
    async def cache_agency_data(
        self, 
        agency_code: str, 
        data_type: str, 
        data: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Cache agency enrichment data"""
        key = f"{agency_code}:{data_type}"
        return await self.set(key, data, ttl or self.default_ttl, "agency_data")
    
    async def get_agency_data(self, agency_code: str, data_type: str) -> Optional[Any]:
        """Get cached agency enrichment data"""
        key = f"{agency_code}:{data_type}"
        return await self.get(key, "agency_data")
    
    async def cache_ml_model_result(
        self, 
        model_name: str, 
        input_hash: str, 
        result: Any
    ) -> bool:
        """Cache ML model prediction results"""
        key = f"{model_name}:{input_hash}"
        return await self.set(key, result, self.ml_cache_ttl, "ml_results")
    
    async def get_ml_model_result(self, model_name: str, input_hash: str) -> Optional[Any]:
        """Get cached ML model prediction results"""
        key = f"{model_name}:{input_hash}"
        return await self.get(key, "ml_results")
    
    async def cache_api_response(
        self, 
        endpoint: str, 
        params: Dict[str, Any], 
        response: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache external API responses"""
        key = f"{endpoint}:{params}"
        return await self.set(key, response, ttl or 1800, "api_responses")  # 30 min default
    
    async def get_api_response(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached API response"""
        key = f"{endpoint}:{params}"
        return await self.get(key, "api_responses")

# Global cache instance
cache = FallbackCache()

# Decorator for automatic caching
def cached(ttl: int = 3600, prefix: str = "general"):
    """Decorator for automatic function result caching"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            args_str = json.dumps([str(arg) for arg in args], sort_keys=True)
            kwargs_str = json.dumps(kwargs, sort_keys=True)
            key_data = f"{func.__name__}:{args_str}:{kwargs_str}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key, prefix)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl, prefix)
            
            return result
        return wrapper
    return decorator