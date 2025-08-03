#!/usr/bin/env python3
"""
Debug USASpending.gov API to understand correct request format
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_usaspending_direct():
    """Test USASpending API directly with simple requests"""
    
    print("🔍 DEBUGGING USASPENDING.GOV API")
    print("=" * 50)
    
    base_url = "https://api.usaspending.gov/api/v2"
    
    # Test 1: Simple agency financial data
    print("\n1️⃣ Testing Financial Balances (Agencies)")
    try:
        url = f"{base_url}/financial_balances/agencies"
        params = {
            'fiscal_year': 2024,
            'funding_agency_id': 'all'  # Try with 'all' parameter
        }
        
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, params=params, timeout=15, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Got {len(data.get('results', []))} agencies")
            
            if data.get('results'):
                sample = data['results'][0]
                print(f"Sample agency: {sample.get('agency_name', 'N/A')}")
                print(f"Budget: ${sample.get('total_budgetary_resources', 0):,.0f}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Different agency endpoint
    print("\n2️⃣ Testing Alternative Agency Endpoint")
    try:
        url = f"{base_url}/financial_balances/agencies"
        params = {
            'fiscal_year': 2024
        }
        
        response = requests.get(url, params=params, timeout=15, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Award search with POST
    print("\n3️⃣ Testing Award Search (POST)")
    try:
        url = f"{base_url}/search/spending_by_award"
        
        # Minimal payload to test
        payload = {
            "filters": {
                "keywords": ["technology"],
                "time_period": [
                    {
                        "start_date": "2023-10-01",
                        "end_date": "2024-09-30"
                    }
                ]
            },
            "fields": ["Award ID", "Recipient Name", "Award Amount"],
            "page": 1,
            "limit": 5
        }
        
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            url, 
            json=payload, 
            timeout=30, 
            verify=False,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Response keys: {list(data.keys())}")
            
            if 'results' in data:
                print(f"Found {len(data['results'])} results")
                if data['results']:
                    sample = data['results'][0]
                    print(f"Sample award: {sample}")
        else:
            print(f"❌ Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Simpler award search
    print("\n4️⃣ Testing Simpler Award Search")
    try:
        url = f"{base_url}/search/spending_by_award"
        
        # Even simpler payload
        payload = {
            "filters": {},
            "limit": 3
        }
        
        response = requests.post(url, json=payload, timeout=15, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        
    # Test 5: Check available endpoints
    print("\n5️⃣ Testing Root API to see available endpoints")
    try:
        response = requests.get("https://api.usaspending.gov", timeout=10, verify=False)
        print(f"Root API Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API is accessible")
        
        # Try API docs endpoint
        response = requests.get("https://api.usaspending.gov/docs/", timeout=10, verify=False)
        print(f"Docs Status: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_usaspending_direct()