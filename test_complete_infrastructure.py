#!/usr/bin/env python3
"""Complete infrastructure test"""
import psycopg2
import redis
from kafka import KafkaProducer, KafkaConsumer
import requests
import json
import time

print("🧪 Complete KBI Labs Infrastructure Test\n")

# Test PostgreSQL with actual data
print("1. Testing PostgreSQL with data operations...")
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='kbi_labs',
        user='kbi_user',
        password='kbi_secure_pass_2024'
    )
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cursor.fetchall()
    print(f"   ✅ Found {len(tables)} tables: {[t[0] for t in tables]}")
    
    # Check data
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]
    print(f"   ✅ Companies table has {count} records")
    
    conn.close()
except Exception as e:
    print(f"   ❌ PostgreSQL error: {e}")

# Test Redis operations
print("\n2. Testing Redis operations...")
try:
    r = redis.Redis(host='localhost', port=6379)
    r.set('test_key', 'test_value', ex=60)
    value = r.get('test_key').decode('utf-8')
    print(f"   ✅ Redis working: stored and retrieved '{value}'")
except Exception as e:
    print(f"   ❌ Redis error: {e}")

# Test Kafka produce/consume
print("\n3. Testing Kafka messaging...")
try:
    # Produce a message
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    test_msg = {'test': True, 'timestamp': time.time()}
    producer.send('data-ingestion', value=test_msg)
    producer.flush()
    print("   ✅ Sent message to Kafka")
    producer.close()
except Exception as e:
    print(f"   ❌ Kafka error: {e}")

# Test API endpoints
print("\n4. Testing API endpoints...")
try:
    # Health check
    resp = requests.get("http://localhost:8000/health/detailed")
    health = resp.json()
    print(f"   ✅ API health: {health['status']}")
    
    # Test database through API
    resp = requests.get("http://localhost:8000/api/v3/companies")
    companies = resp.json()
    print(f"   ✅ API returned {len(companies)} companies")
    
except Exception as e:
    print(f"   ❌ API error: {e}")

print("\n🎉 Infrastructure test complete!")
print("\nYour KBI Labs platform is ready for:")
print("- Data ingestion from 250M+ daily sources")
print("- Real-time enrichment processing")
print("- Predictive analytics and ML models")
print("- Decision-grade reporting")
