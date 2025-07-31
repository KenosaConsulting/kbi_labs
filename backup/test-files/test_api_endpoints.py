#!/usr/bin/env python3
"""Test API endpoints"""
import asyncio
import httpx
import json

async def test_endpoints():
    print("🧪 Testing API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8001"
    headers = {"Authorization": "Bearer test-token"}
    
    async with httpx.AsyncClient() as client:
        # Test health
        try:
            resp = await client.get(f"{base_url}/health/")
            print(f"✅ Health check: {resp.status_code}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # Test enrichment health
        try:
            resp = await client.get(f"{base_url}/api/v3/enrichment/health", headers=headers)
            print(f"✅ Enrichment health: {resp.status_code}")
            if resp.status_code == 200:
                print(f"   Response: {resp.json()}")
        except Exception as e:
            print(f"❌ Enrichment health failed: {e}")
        
        # Test company enrichment
        try:
            resp = await client.post(
                f"{base_url}/api/v3/enrichment/enrich",
                headers=headers,
                json={"uei": "SHKSNU48JHZ7", "force_refresh": False}
            )
            print(f"✅ Enrichment request: {resp.status_code}")
            if resp.status_code == 200:
                print(f"   Response: {resp.json()}")
        except Exception as e:
            print(f"❌ Enrichment request failed: {e}")

if __name__ == "__main__":
    print("⏳ Waiting 3 seconds for API to start...")
    import time
    time.sleep(3)
    asyncio.run(test_endpoints())
