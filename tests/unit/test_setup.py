#!/usr/bin/env python3
import sys
import os

print("Testing KBI Labs setup...")

# Test imports
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from src.enrichment.config import EnrichmentConfig
    from src.enrichment.models import EnrichedCompany
    from src.enrichment.engine import EnrichmentEngine
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test database connection
try:
    from src.database.connection import engine
    conn = engine.connect()
    conn.close()
    print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection error: {e}")
    print("  Make sure PostgreSQL is installed and database is created")

# Test Redis
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("✓ Redis connection successful")
except Exception as e:
    print(f"✗ Redis connection error: {e}")
    print("  Make sure Redis is installed and running")

print("\nSetup test complete!")
