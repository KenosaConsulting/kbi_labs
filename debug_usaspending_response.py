#!/usr/bin/env python3
"""
Debug USASpending response structure
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_response_structure():
    """Debug the actual response structure from USASpending"""
    
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award"
    
    payload = {
        "filters": {
            "keywords": ["artificial intelligence"],
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [
                {
                    "start_date": "2023-10-01",
                    "end_date": "2024-09-30"
                }
            ]
        },
        "fields": [
            "Award ID",
            "Recipient Name", 
            "Award Amount",
            "Awarding Agency",
            "Award Description"
        ],
        "page": 1,
        "limit": 3
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Print full response structure
            print(f"Full response: {json.dumps(data, indent=2)}")
            
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

def test_agency_endpoints():
    """Test different agency endpoints"""
    
    base_url = "https://api.usaspending.gov/api/v2"
    
    # Try different agency endpoints
    endpoints = [
        "/financial_balances/agencies?fiscal_year=2023",
        "/financial_balances/agencies?fiscal_year=2023&funding_agency_id=all",
        "/financial_balances/agencies?fiscal_year=2022",
        "/agencies",
        "/agencies/overview",
    ]
    
    for endpoint in endpoints:
        print(f"\n🧪 Testing: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10, verify=False)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ SUCCESS!")
                data = response.json()
                print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
            else:
                print(f"Error: {response.text[:200]}...")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    print("🔍 DEBUGGING USASPENDING RESPONSE STRUCTURE")
    print("=" * 60)
    
    debug_response_structure()
    test_agency_endpoints()