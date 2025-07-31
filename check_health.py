#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

def check_api_health():
    endpoints = [
        ("Health", "http://localhost:8001/health"),
        ("Detailed Health", "http://localhost:8001/api/v3/health/detailed"),
        ("Metrics", "http://localhost:8001/metrics"),
        ("Enrichment Health", "http://localhost:8001/api/v3/enrichment/health")
    ]
    
    print(f"\n🔍 API Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    for name, url in endpoints:
        try:
            start = time.time()
            response = requests.get(url, timeout=5)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                print(f"✅ {name}: OK ({elapsed:.0f}ms)")
                if "health" in url and "metrics" not in url:
                    data = response.json()
                    if "system" in data:
                        print(f"   CPU: {data['system']['cpu_percent']}%")
                        print(f"   Memory: {data['system']['memory_percent']}%")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Failed - {str(e)}")
    
    print("=" * 50)

if __name__ == "__main__":
    check_api_health()
