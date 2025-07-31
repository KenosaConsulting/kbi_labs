"""Database connection module with lazy initialization"""
from typing import Optional
import os
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self._connection = None
        self._engine = None
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./kbi_labs.db")
        
    async def connect(self):
        """Initialize database connection when needed"""
        if self._connection is None:
            try:
                if self.database_url.startswith("sqlite"):
                    # SQLite connection
                    import aiosqlite
                    self._connection = await aiosqlite.connect(
                        self.database_url.replace("sqlite:///", "")
                    )
                else:
                    # PostgreSQL connection
                    import asyncpg
                    self._connection = await asyncpg.connect(self.database_url)
                logger.info(f"Connected to database: {self.database_url}")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._connection
    
    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None

# Global instance (but not connected yet)
db = DatabaseConnection()

@asynccontextmanager
async def get_db_connection():
    """Get database connection context manager"""
    conn = await db.connect()
    try:
        yield conn
    finally:
        # Don't close the connection here, let the app manage it
        pass

# For backward compatibility
def get_db():
    """Legacy sync function - DO NOT USE IN NEW CODE"""
    logger.warning("Using legacy get_db() - please migrate to get_db_connection()")
    return None
