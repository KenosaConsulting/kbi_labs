#!/usr/bin/env python3
"""Test database connection"""
import psycopg2
import asyncpg
import asyncio

def test_sync_connection():
    """Test synchronous connection"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='kbi_labs',
            user='kbi_user',
            password='kbi_secure_pass_2024'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()
        print(f"✅ PostgreSQL connected (sync): {version[0].split(',')[0]}")
        
        # Check tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"\n📊 Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Sync connection failed: {e}")
        return False

async def test_async_connection():
    """Test asynchronous connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            database='kbi_labs',
            user='kbi_user',
            password='kbi_secure_pass_2024'
        )
        
        version = await conn.fetchval('SELECT version()')
        print(f"\n✅ PostgreSQL connected (async): {version.split(',')[0]}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Async connection failed: {e}")
        return False

async def main():
    print("🔧 Testing PostgreSQL connections...\n")
    sync_ok = test_sync_connection()
    async_ok = await test_async_connection()
    
    if sync_ok and async_ok:
        print("\n✅ All database tests passed!")
    else:
        print("\n❌ Some database tests failed")

if __name__ == "__main__":
    asyncio.run(main())
