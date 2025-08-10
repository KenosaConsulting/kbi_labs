#!/usr/bin/env python3
"""
Redis Cache Client
High-performance caching layer with automatic serialization and compression
"""

import json
import gzip
import logging
import os
from typing import Any, Optional, Dict, List, Union
from datetime import timedelta
import aioredis
import pickle
import hashlib

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Redis cache client with intelligent caching strategies
    """
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.default_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
        self.ml_cache_ttl = int(os.getenv("ML_CACHE_TTL_SECONDS", "86400"))  # 24 hours
        self.compression_enabled = True
        self.compression_threshold = 1024  # Compress data larger than 1KB
    
    async def connect(self) -> None:
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
            # Parse Redis URL for connection parameters
            self.redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle encoding ourselves for compression
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache connected successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to in-memory cache")
            self.redis_client = None
    
    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, identifier: Union[str, Dict[str, Any]]) -> str:
        """Generate consistent cache key"""
        if isinstance(identifier, dict):
            # Create consistent hash from dictionary
            sorted_items = sorted(identifier.items())
            identifier_str = json.dumps(sorted_items, sort_keys=True)
        else:
            identifier_str = str(identifier)
        
        # Generate hash for long keys
        key_hash = hashlib.md5(identifier_str.encode()).hexdigest()
        return f"kbi:{prefix}:{key_hash}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data with optional compression"""
        try:
            # Use pickle for complex Python objects, JSON for simple types
            if isinstance(data, (dict, list, str, int, float, bool, type(None))):
                serialized = json.dumps(data).encode('utf-8')
            else:
                serialized = pickle.dumps(data)
            
            # Compress if data is large enough
            if self.compression_enabled and len(serialized) > self.compression_threshold:
                compressed = gzip.compress(serialized)
                # Add compression marker
                return b"GZIP:" + compressed
            
            return serialized
            
        except Exception as e:
            logger.error(f"Data serialization error: {e}")
            return pickle.dumps(data)  # Fallback to pickle
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data with optional decompression"""
        try:
            # Check for compression marker
            if data.startswith(b"GZIP:"):
                compressed_data = data[5:]  # Remove "GZIP:" prefix
                decompressed = gzip.decompress(compressed_data)
                data = decompressed
            
            # Try JSON first (more common and faster)
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fallback to pickle
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Data deserialization error: {e}")
            return None
    
    async def get(self, key: str, prefix: str = "general") -> Optional[Any]:
        """Get cached value"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return self._deserialize_data(cached_data)
            
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
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            serialized_value = self._serialize_data(value)
            
            ttl = ttl or self.default_ttl
            
            await self.redis_client.setex(cache_key, ttl, serialized_value)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "general") -> bool:
        """Delete cached value"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            result = await self.redis_client.delete(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "general") -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            result = await self.redis_client.exists(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str, prefix: str = "general") -> Optional[int]:
        """Get remaining TTL for key"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prefix, key)
            ttl = await self.redis_client.ttl(cache_key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None
    
    async def clear_pattern(self, pattern: str, prefix: str = "general") -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            search_pattern = f"kbi:{prefix}:{pattern}"
            keys = await self.redis_client.keys(search_pattern)
            
            if keys:
                result = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {result} cache keys matching pattern: {pattern}")
                return result
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            
            return {
                "status": "connected",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
    
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
cache = RedisCache()

# Decorator for automatic caching
def cached(ttl: int = 3600, prefix: str = "general"):
    """Decorator for automatic function result caching"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            import hashlib
            import json
            
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