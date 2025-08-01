import psycopg2
import sys

print("Testing database connections...")

# Test different connection methods
tests = [
    {
        "name": "Unix socket port 5433",
        "params": {
            "database": "kbi_enriched",
            "user": "postgres",
            "host": "/var/run/postgresql",
            "port": "5433"
        }
    },
    {
        "name": "Localhost port 5433",
        "params": {
            "database": "kbi_enriched",
            "user": "postgres",
            "host": "localhost",
            "port": "5433"
        }
    },
    {
        "name": "Unix socket default",
        "params": {
            "database": "kbi_enriched",
            "user": "postgres",
            "host": "/var/run/postgresql"
        }
    }
]

for test in tests:
    print(f"\nTrying: {test['name']}")
    try:
        conn = psycopg2.connect(**test['params'])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM enriched_companies")
        count = cur.fetchone()[0]
        print(f"✓ SUCCESS! Connected using {test['name']}. Found {count} companies.")
        
        # Get sample data
        cur.execute("SELECT organization_name, federal_contracts_value FROM enriched_companies LIMIT 3")
        for row in cur.fetchall():
            print(f"  - {row[0]}: ${row[1]:,.2f}")
        
        conn.close()
        break
    except Exception as e:
        print(f"✗ Failed: {e}")

