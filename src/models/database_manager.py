"""Database Manager with connection pooling"""
import os
import asyncio
from typing import Optional, Any, List, Dict
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./kbi_production.db")
        self.is_sqlite = self.database_url.startswith("sqlite")
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            if self.is_sqlite:
                import aiosqlite
                # For SQLite, we'll manage connections differently
                db_path = self.database_url.replace("sqlite:///", "")
                logger.info(f"Using SQLite database: {db_path}")
                
                # Test connection
                async with aiosqlite.connect(db_path) as conn:
                    cursor = await conn.execute("SELECT COUNT(*) FROM companies")
                    count = await cursor.fetchone()
                    logger.info(f"Database connected. Companies found: {count[0]}")
            else:
                import asyncpg
                # PostgreSQL connection pool
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                    timeout=60,
                    command_timeout=60
                )
                logger.info(f"Connected to PostgreSQL: {self.database_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.pool and not self.is_sqlite:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if self.is_sqlite:
            import aiosqlite
            db_path = self.database_url.replace("sqlite:///", "")
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = aiosqlite.Row
                yield conn
        else:
            async with self.pool.acquire() as conn:
                yield conn
    
    async def execute_one(self, query: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single row"""
        async with self.get_connection() as conn:
            if self.is_sqlite:
                cursor = await conn.execute(query, params or [])
                row = await cursor.fetchone()
                return dict(row) if row else None
            else:
                row = await conn.fetchrow(query, *(params or []))
                return dict(row) if row else None
    
    async def execute_all(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute query and return all rows"""
        async with self.get_connection() as conn:
            if self.is_sqlite:
                cursor = await conn.execute(query, params or [])
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                rows = await conn.fetch(query, *(params or []))
                return [dict(row) for row in rows]
    
    async def execute(self, query: str, params: Optional[List[Any]] = None) -> None:
        """Execute query without returning results"""
        async with self.get_connection() as conn:
            if self.is_sqlite:
                await conn.execute(query, params or [])
                await conn.commit()
            else:
                await conn.execute(query, *(params or []))

# Create singleton instance
db_manager = DatabaseManager()
