#!/usr/bin/env python3
import requests
import json

API_BASE = "http://localhost:8000"

print("🧪 Testing KBI Labs API Integration\n")

# Test health
print("1. Testing health endpoint...")
resp = requests.get(f"{API_BASE}/health")
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}\n")

# Test detailed health
print("2. Testing detailed health...")
resp = requests.get(f"{API_BASE}/health/detailed")
health_data = resp.json()
print(f"   Overall Status: {health_data['status']}")
print(f"   Services: {json.dumps(health_data['services'], indent=2)}\n")

# Test service connections
print("3. Testing service connections...")
resp = requests.get(f"{API_BASE}/api/test/services")
services = resp.json()
for service, status in services.items():
    print(f"   {service}: {status}")
print()

# Test company endpoints
print("4. Testing company endpoints...")
resp = requests.get(f"{API_BASE}/api/v3/companies")
companies = resp.json()
print(f"   Found {len(companies)} companies")
if companies:
    print(f"   First company: {companies[0]['organization_name']}")
print()

# Test enrichment
print("5. Testing enrichment...")
resp = requests.post(
    f"{API_BASE}/api/v3/enrichment/enrich",
    json={"uei": "TEST123", "company_name": "Test Company"}
)
print(f"   Response: {resp.json()}\n")

print("✅ API Integration Test Complete!")
