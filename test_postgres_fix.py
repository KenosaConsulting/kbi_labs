#!/usr/bin/env python3
import psycopg2
import os

print("Testing PostgreSQL connections...")

# Test configurations
configs = [
    {
        "name": "Standard",
        "host": "localhost",
        "port": 5432,
        "database": "kbi_labs",
        "user": "kbi_user",
        "password": "kbi_secure_pass_2024"
    },
    {
        "name": "With postgres DB",
        "host": "localhost",
        "port": 5432,
        "database": "postgres",
        "user": "kbi_user",
        "password": "kbi_secure_pass_2024"
    },
    {
        "name": "As postgres user",
        "host": "localhost",
        "port": 5432,
        "database": "kbi_labs",
        "user": "postgres",
        "password": "postgres"
    }
]

for config in configs:
    print(f"\nTrying {config['name']}...")
    try:
        conn = psycopg2.connect(**{k: v for k, v in config.items() if k != 'name'})
        print(f"✅ SUCCESS with {config['name']}")
        conn.close()
    except Exception as e:
        print(f"❌ FAILED: {e}")

# Try with environment variable
print("\nTrying with PGPASSWORD env variable...")
os.environ['PGPASSWORD'] = 'kbi_secure_pass_2024'
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="kbi_labs",
        user="kbi_user"
    )
    print("✅ SUCCESS with env variable")
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")
