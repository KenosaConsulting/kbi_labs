#!/usr/bin/env python3
"""Test enrichment API"""
import requests
import json

base_url = "http://localhost:8001"

print("🧪 Testing Enrichment API")
print("=" * 40)

# Test without auth (should work now)
print("\n1. Testing health (no auth):")
resp = requests.get(f"{base_url}/api/v3/enrichment/health")
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")

# Test the test endpoint
print("\n2. Testing test endpoint:")
resp = requests.get(f"{base_url}/api/v3/enrichment/test")
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")

# Test with auth
print("\n3. Testing enrichment with auth:")
headers = {"Authorization": "Bearer test-token"}
data = {"uei": "SHKSNU48JHZ7", "force_refresh": False}
resp = requests.post(
    f"{base_url}/api/v3/enrichment/enrich",
    headers=headers,
    json=data
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")

# Test without auth (should also work for testing)
print("\n4. Testing enrichment without auth:")
resp = requests.post(
    f"{base_url}/api/v3/enrichment/enrich",
    json=data
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")

# Test status endpoint
print("\n5. Testing status endpoint:")
resp = requests.get(
    f"{base_url}/api/v3/enrichment/status/SHKSNU48JHZ7",
    headers=headers
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")
