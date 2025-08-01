#!/usr/bin/env python3
"""Cache warming script - pre-populate cache with popular searches"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/patents"

# Popular companies to pre-cache
POPULAR_COMPANIES = [
    "Samsung", "IBM", "Apple", "Microsoft", "Google", 
    "Intel", "Amazon", "Tesla", "Oracle", "Cisco",
    "Qualcomm", "Sony", "Toyota", "General Electric", "3M"
]

# Popular keywords to pre-cache
POPULAR_KEYWORDS = [
    "artificial intelligence", "machine learning", "blockchain",
    "quantum computing", "5G", "autonomous vehicle", "drone",
    "battery", "solar", "covid", "vaccine", "semiconductor"
]

def warm_cache():
    print("🔥 Warming cache with popular searches...")
    
    # Warm organization searches
    for company in POPULAR_COMPANIES:
        try:
            url = f"{API_BASE}/search/organization?org_name={company}&limit=20"
            response = requests.get(url)
            print(f"✓ Cached {company}: {response.json()['query_time']:.3f}s")
            time.sleep(0.1)  # Be nice to the API
        except:
            print(f"✗ Failed to cache {company}")
    
    # Warm keyword searches
    for keyword in POPULAR_KEYWORDS:
        try:
            url = f"{API_BASE}/search/keyword?keyword={keyword}&limit=20"
            response = requests.get(url)
            print(f"✓ Cached '{keyword}': {response.json()['query_time']:.3f}s")
            time.sleep(0.1)
        except:
            print(f"✗ Failed to cache '{keyword}'")
    
    # Cache top holders
    for year in [None, 2024, 2023, 2022]:
        try:
            url = f"{API_BASE}/top-holders?limit=20"
            if year:
                url += f"&year={year}"
            response = requests.get(url)
            print(f"✓ Cached top holders {year or 'all-time'}")
            time.sleep(0.1)
        except:
            pass
    
    # Check final cache stats
    stats = requests.get("http://localhost:8000/api/cache/stats").json()
    print(f"\n📊 Cache Stats After Warming:")
    print(f"   Hit Rate: {stats['hit_rate']}%")
    print(f"   Memory Used: {stats['used_memory']}")
    print(f"   Total Commands: {stats['total_commands']}")

if __name__ == "__main__":
    warm_cache()
