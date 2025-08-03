#!/usr/bin/env python3
"""
Debug Census API to see exact response format
"""

import requests
import json

API_KEY = "70e4e3355e1b7b1a42622ba9201157bd1b105629"

def test_census_endpoints():
    """Test different Census API endpoints to see what works"""
    
    endpoints_to_test = [
        {
            'name': 'ACS 5-Year Population Data',
            'url': 'https://api.census.gov/data/2021/acs/acs5',
            'params': {
                'get': 'NAME,B01001_001E',  # Name, Total Population
                'for': 'state:*',
                'key': API_KEY
            }
        },
        {
            'name': 'County Business Patterns',
            'url': 'https://api.census.gov/data/2021/cbp',
            'params': {
                'get': 'NAME,EMP,ESTAB',  # Name, Employees, Establishments
                'for': 'state:*',
                'NAICS2017': '54',  # Professional services
                'key': API_KEY
            }
        },
        {
            'name': 'Economic Census',
            'url': 'https://api.census.gov/data/2017/ecnbasic',
            'params': {
                'get': 'NAME,EMP,PAYANN',  # Name, Employees, Annual Payroll
                'for': 'state:*',
                'NAICS2017': '541',  # Professional services
                'key': API_KEY
            }
        }
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        print(f"Params: {endpoint['params']}")
        
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=10, verify=False)
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Response Length: {len(response.text)} characters")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                print("Raw Response (first 500 chars):")
                print(response.text[:500])
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"✅ Valid JSON with {len(data)} items")
                    if data:
                        print("Sample data:")
                        for i, item in enumerate(data[:3]):
                            print(f"  [{i}]: {item}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Parse Error: {e}")
                    print("Trying to parse as other formats...")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print("Error Response:", response.text[:300])
                
        except Exception as e:
            print(f"❌ Request Exception: {e}")

if __name__ == "__main__":
    print("🔍 CENSUS API DEBUGGING")
    print("=" * 50)
    test_census_endpoints()