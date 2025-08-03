#!/usr/bin/env python3
"""Test current infrastructure"""
import time

print("🧪 Testing infrastructure components...\n")

# Test Redis
print("Testing Redis...")
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
    r.ping()
    print("✅ Redis is working!")
except Exception as e:
    print(f"❌ Redis error: {e}")

# Test PostgreSQL
print("\nTesting PostgreSQL...")
try:
    import psycopg2
    # Try with the new credentials
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='kbi_labs',
        user='kbi_user',
        password='kbi_secure_pass_2024',
        connect_timeout=5
    )
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print(f"✅ PostgreSQL is working! Test query returned: {result}")
    
    # Create tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id SERIAL PRIMARY KEY,
            uei VARCHAR(12) UNIQUE NOT NULL,
            organization_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL error: {e}")

# Test Kafka
print("\nTesting Kafka...")
try:
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable
    
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        request_timeout_ms=5000,
        api_version_auto_timeout_ms=5000
    )
    print("✅ Kafka is working!")
    producer.close()
except NoBrokersAvailable:
    print("❌ Kafka error: No brokers available. Kafka might not be running.")
except Exception as e:
    print(f"❌ Kafka error: {e}")

print("\n📊 Summary:")
print("- Redis: Check port 6379")
print("- PostgreSQL: Check port 5432") 
print("- Kafka: Check port 9092")
print("\nIf services aren't running, use: docker-compose up -d")
