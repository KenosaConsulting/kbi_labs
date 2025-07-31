"""Database connection helpers"""
import sqlite3
import aiosqlite
from contextlib import asynccontextmanager
import os

DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///./kbi_production.db").replace("sqlite:///", "")

@asynccontextmanager
async def get_db_connection():
    """Get async database connection"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
