"""Database connection tests"""
import pytest
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database_manager import db_manager

@pytest.mark.asyncio
async def test_database_connection():
    """Test database can connect"""
    try:
        await db_manager.initialize()
        assert db_manager.database_url is not None
        
        # Test a simple query
        result = await db_manager.execute_one("SELECT COUNT(*) as count FROM companies")
        assert result is not None
        assert result["count"] > 0
        
        await db_manager.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

@pytest.mark.asyncio
async def test_company_query():
    """Test company queries work"""
    await db_manager.initialize()
    
    # Test getting companies
    companies = await db_manager.execute_all(
        "SELECT * FROM companies LIMIT 5"
    )
    assert len(companies) <= 5
    
    if companies:
        assert "uei" in companies[0]
        assert "organization_name" in companies[0]
    
    await db_manager.close()
