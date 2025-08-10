#!/usr/bin/env python3
"""
Database Connection Management
Handles PostgreSQL connection pooling for the KBI Labs platform
"""

import asyncpg
import logging
from typing import Optional
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global connection pool
_connection_pool: Optional[asyncpg.Pool] = None

async def create_database_pool() -> asyncpg.Pool:
    """
    Create and configure database connection pool
    
    Returns:
        Configured asyncpg connection pool
    """
    
    global _connection_pool
    
    if _connection_pool is not None:
        return _connection_pool
    
    # Get database configuration from environment - require all credentials
    required_env_vars = ['DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER', 'DATABASE_PASSWORD']
    for var in required_env_vars:
        if not os.getenv(var):
            raise ValueError(f"Required environment variable {var} not set for database connection")
    
    database_config = {
        'host': os.getenv('DATABASE_HOST'),
        'port': int(os.getenv('DATABASE_PORT', '5432')),
        'database': os.getenv('DATABASE_NAME'),
        'user': os.getenv('DATABASE_USER'),
        'password': os.getenv('DATABASE_PASSWORD'),
    }
    
    # Connection pool configuration
    pool_config = {
        'min_size': int(os.getenv('DATABASE_POOL_MIN_SIZE', '5')),
        'max_size': int(os.getenv('DATABASE_POOL_MAX_SIZE', '20')),
        'command_timeout': int(os.getenv('DATABASE_COMMAND_TIMEOUT', '60')),
    }
    
    try:
        logger.info(f"Creating database connection pool to {database_config['host']}:{database_config['port']}")
        
        _connection_pool = await asyncpg.create_pool(
            **database_config,
            **pool_config
        )
        
        # Test the connection
        async with _connection_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("Database connection pool created successfully")
        return _connection_pool
        
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {str(e)}")
        raise

async def get_database_pool() -> asyncpg.Pool:
    """
    Get the database connection pool (dependency injection for FastAPI)
    
    Returns:
        Database connection pool
    """
    
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = await create_database_pool()
    
    return _connection_pool

@asynccontextmanager
async def get_database_connection():
    """
    Context manager for getting a database connection from the pool
    
    Usage:
        async with get_database_connection() as conn:
            result = await conn.fetch("SELECT * FROM table")
    """
    
    pool = await get_database_pool()
    
    async with pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise

async def close_database_pool():
    """Close the database connection pool"""
    
    global _connection_pool
    
    if _connection_pool is not None:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("Database connection pool closed")

async def execute_migration(migration_file: str):
    """
    Execute a database migration file
    
    Args:
        migration_file: Path to SQL migration file
    """
    
    try:
        # Read migration file
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        async with get_database_connection() as conn:
            await conn.execute(migration_sql)
        
        logger.info(f"Migration executed successfully: {migration_file}")
        
    except Exception as e:
        logger.error(f"Migration failed: {migration_file}: {str(e)}")
        raise

# Database health check
async def check_database_health() -> dict:
    """
    Check database health and return status information
    
    Returns:
        Dictionary with health status information
    """
    
    try:
        pool = await get_database_pool()
        
        async with pool.acquire() as conn:
            # Test basic connectivity
            result = await conn.fetchval("SELECT 1")
            
            # Get pool statistics
            pool_stats = {
                'size': pool.get_size(),
                'min_size': pool.get_min_size(),
                'max_size': pool.get_max_size(),
                'idle_size': pool.get_idle_size()
            }
            
            # Get database version
            db_version = await conn.fetchval("SELECT version()")
            
            return {
                'status': 'healthy',
                'connection_test': result == 1,
                'pool_stats': pool_stats,
                'database_version': db_version,
                'timestamp': 'now()'
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': 'now()'
        }