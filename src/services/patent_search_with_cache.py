#!/usr/bin/env python3
import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import json
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentSearchEngine:
    def __init__(self, db_path='/app/patent_data/patents_kbi.db'):
        self.db_path = db_path
        
        # Initialize Redis cache
        try:
            import redis
            self.redis_client = redis.Redis(host='kbi_redis', port=6379, decode_responses=True)
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("Redis cache enabled for patent searches")
        except:
            self.redis_client = None
            self.cache_enabled = False
            logger.warning("Redis not available, running without cache")
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key from method and parameters"""
        params = json.dumps(kwargs, sort_keys=True)
        return f"patent:{method}:{hashlib.md5(params.encode()).hexdigest()}"
    
    def _cache_get(self, key: str) -> Any:
        """Get from cache"""
        if not self.cache_enabled:
            return None
        try:
            data = self.redis_client.get(key)
            if data:
                logger.info(f"Cache HIT for key: {key[:50]}...")
                return json.loads(data)
            logger.info(f"Cache MISS for key: {key[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def _cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Set in cache with TTL (default 1 hour)"""
        if not self.cache_enabled:
            return
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            logger.info(f"Cached result for key: {key[:50]}...")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def search_by_organization(self, org_name: str, limit: int = 100) -> pd.DataFrame:
        """Search patents by organization name with caching"""
        # Try cache first
        cache_key = self._get_cache_key('org_search', org_name=org_name, limit=limit)
        cached = self._cache_get(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        # If not cached, query database
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT DISTINCT
            p.patent_id,
            p.patent_title,
            p.patent_date,
            p.year,
            p.patent_type,
            a.organization
        FROM patents p
        JOIN patent_assignee pa ON p.patent_id = pa.patent_id
        JOIN assignees a ON pa.assignee_id = a.assignee_id
        WHERE a.org_clean LIKE ?
        ORDER BY p.patent_date DESC
        LIMIT ?
        """
        org_search = f"%{org_name.upper().strip()}%"
        results = pd.read_sql_query(query, conn, params=(org_search, limit))
        conn.close()
        
        # Cache the results
        self._cache_set(cache_key, results.to_dict('records'))
        
        return results
    
    def get_org_patent_stats(self, org_name: str) -> Dict:
        """Get patent statistics for an organization with caching"""
        # Try cache first
        cache_key = self._get_cache_key('org_stats', org_name=org_name)
        cached = self._cache_get(cache_key)
        if cached:
            return cached
        
        conn = sqlite3.connect(self.db_path)
        
        # Get total patents
        total_query = """
        SELECT COUNT(DISTINCT pa.patent_id) as total_patents
        FROM assignees a
        JOIN patent_assignee pa ON a.assignee_id = pa.assignee_id
        WHERE a.org_clean LIKE ?
        """
        org_search = f"%{org_name.upper().strip()}%"
        total = pd.read_sql_query(total_query, conn, params=(org_search,)).iloc[0]['total_patents']
        
        # Get patents by year
        yearly_query = """
        SELECT p.year, COUNT(DISTINCT p.patent_id) as patent_count
        FROM patents p
        JOIN patent_assignee pa ON p.patent_id = pa.patent_id
        JOIN assignees a ON pa.assignee_id = a.assignee_id
        WHERE a.org_clean LIKE ? AND p.year IS NOT NULL
        GROUP BY p.year
        ORDER BY p.year DESC
        LIMIT 10
        """
        yearly = pd.read_sql_query(yearly_query, conn, params=(org_search,))
        
        # Get recent patents
        recent_query = """
        SELECT p.patent_title, p.patent_date
        FROM patents p
        JOIN patent_assignee pa ON p.patent_id = pa.patent_id
        JOIN assignees a ON pa.assignee_id = a.assignee_id
        WHERE a.org_clean LIKE ?
        ORDER BY p.patent_date DESC
        LIMIT 5
        """
        recent = pd.read_sql_query(recent_query, conn, params=(org_search,))
        
        conn.close()
        
        result = {
            'organization': org_name,
            'total_patents': int(total),
            'patents_by_year': yearly.to_dict('records'),
            'recent_patents': recent.to_dict('records')
        }
        
        # Cache the results
        self._cache_set(cache_key, result)
        
        return result
    
    def search_patents_by_keyword(self, keyword: str, limit: int = 100) -> pd.DataFrame:
        """Search patents by keyword in title with caching"""
        # Try cache first
        cache_key = self._get_cache_key('keyword_search', keyword=keyword, limit=limit)
        cached = self._cache_get(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT DISTINCT
            p.patent_id,
            p.patent_title,
            p.patent_date,
            p.year,
            p.patent_type,
            GROUP_CONCAT(DISTINCT a.organization) as assignees
        FROM patents p
        LEFT JOIN patent_assignee pa ON p.patent_id = pa.patent_id
        LEFT JOIN assignees a ON pa.assignee_id = a.assignee_id
        WHERE p.patent_title LIKE ?
        GROUP BY p.patent_id
        ORDER BY p.patent_date DESC
        LIMIT ?
        """
        keyword_search = f"%{keyword}%"
        results = pd.read_sql_query(query, conn, params=(keyword_search, limit))
        conn.close()
        
        # Cache the results
        self._cache_set(cache_key, results.to_dict('records'))
        
        return results
    
    def get_top_patent_holders(self, year: Optional[int] = None, limit: int = 20) -> pd.DataFrame:
        """Get top patent holders with caching"""
        # Try cache first
        cache_key = self._get_cache_key('top_holders', year=year, limit=limit)
        cached = self._cache_get(cache_key)
        if cached:
            return pd.DataFrame(cached)
        
        conn = sqlite3.connect(self.db_path)
        
        if year:
            query = """
            SELECT a.organization, COUNT(DISTINCT pa.patent_id) as patent_count
            FROM assignees a
            JOIN patent_assignee pa ON a.assignee_id = pa.assignee_id
            JOIN patents p ON pa.patent_id = p.patent_id
            WHERE p.year = ?
            GROUP BY a.organization
            ORDER BY patent_count DESC
            LIMIT ?
            """
            results = pd.read_sql_query(query, conn, params=(year, limit))
        else:
            query = """
            SELECT a.organization, COUNT(DISTINCT pa.patent_id) as patent_count
            FROM assignees a
            JOIN patent_assignee pa ON a.assignee_id = pa.assignee_id
            GROUP BY a.organization
            ORDER BY patent_count DESC
            LIMIT ?
            """
            results = pd.read_sql_query(query, conn, params=(limit,))
        
        conn.close()
        
        # Cache the results (longer TTL for top holders)
        self._cache_set(cache_key, results.to_dict('records'), ttl=7200)
        
        return results
    
    def get_cache_stats(self) -> Dict:
        """Get Redis cache statistics"""
        if not self.cache_enabled:
            return {"status": "disabled"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "enabled",
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(info.get("keyspace_hits", 0) / 
                                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)) * 100, 2)
            }
        except:
            return {"status": "error"}

# Create instance
patent_engine = PatentSearchEngine()
