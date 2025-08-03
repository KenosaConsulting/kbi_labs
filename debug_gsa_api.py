#!/usr/bin/env python3
"""
Debug GSA API to find correct endpoints
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY"

def test_gsa_endpoints():
    """Test different GSA API endpoints"""
    
    # Known GSA API endpoints from documentation
    endpoints_to_test = [
        {
            'name': 'GSA Analytics - Domain',
            'url': 'https://api.gsa.gov/analytics/dap/v1.1/domain',
            'params': {'api_key': API_KEY}
        },
        {
            'name': 'GSA Analytics - Agencies',
            'url': 'https://api.gsa.gov/analytics/dap/v1.1/agencies',
            'params': {'api_key': API_KEY}
        },
        {
            'name': 'GSA Analytics - Reports',
            'url': 'https://api.gsa.gov/analytics/dap/v1.1/reports',
            'params': {'api_key': API_KEY}
        },
        {
            'name': 'GSA FSRS (Federal Sub-awards)',
            'url': 'https://api.gsa.gov/acquisition/federal-sub-awards/v1',
            'params': {'api_key': API_KEY, 'limit': 5}
        },
        {
            'name': 'GSA SAM Entity Management',
            'url': 'https://api.gsa.gov/entity-information/v1/entities',
            'params': {'api_key': API_KEY, 'limit': 5}
        },
        {
            'name': 'GSA Multiple Awards Schedule',
            'url': 'https://api.gsa.gov/acquisition/schedules-pss/v1/schedules',
            'params': {'api_key': API_KEY, 'limit': 5}
        },
        {
            'name': 'GSA Per Diem API',
            'url': 'https://api.gsa.gov/travel/perdiem/v2/rates/city/Washington/DC/20190901',
            'params': {'api_key': API_KEY}
        },
        {
            'name': 'GSA Auctions API',
            'url': 'https://api.gsa.gov/auctions/v0/auctions',
            'params': {'api_key': API_KEY, 'limit': 5}
        }
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing: {endpoint['name']}")
        print(f"URL: {endpoint['url']}")
        
        try:
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=15, verify=False)
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"✅ Valid JSON response")
                    
                    # Show structure
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                        if 'data' in data:
                            print(f"   Data count: {len(data['data']) if isinstance(data['data'], list) else 'Not a list'}")
                        if 'results' in data:
                            print(f"   Results count: {len(data['results']) if isinstance(data['results'], list) else 'Not a list'}")
                    elif isinstance(data, list):
                        print(f"   Array with {len(data)} items")
                    
                    # Show sample
                    if isinstance(data, dict) and data:
                        sample_key = list(data.keys())[0]
                        print(f"   Sample key '{sample_key}': {str(data[sample_key])[:100]}...")
                    elif isinstance(data, list) and data:
                        print(f"   Sample item: {str(data[0])[:100]}...")
                    
                    working_endpoints.append(endpoint)
                    
                except json.JSONDecodeError:
                    print("❌ Not valid JSON")
                    print("Response content:", response.text[:200])
                except Exception as e:
                    print(f"❌ JSON processing error: {e}")
                    
            elif response.status_code == 403:
                print("❌ 403 Forbidden - API key might be invalid or endpoint restricted")
            elif response.status_code == 404:
                print("❌ 404 Not Found - endpoint doesn't exist")
            elif response.status_code == 429:
                print("⚠️ 429 Rate Limited - try again later")
            else:
                print(f"❌ HTTP {response.status_code}")
                print("Response:", response.text[:200])
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
        except Exception as e:
            print(f"❌ Request exception: {e}")
    
    return working_endpoints

def test_without_api_key():
    """Test GSA endpoints that might work without API key"""
    print("\n🔓 Testing GSA endpoints WITHOUT API key")
    
    public_endpoints = [
        'https://api.gsa.gov/travel/perdiem/v2/rates/city/Washington/DC/20190901',
        'https://api.gsa.gov/auctions/v0/auctions?limit=5',
    ]
    
    for url in public_endpoints:
        print(f"\n🧪 Testing: {url}")
        try:
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                print("✅ Works without key!")
                try:
                    data = response.json()
                    print(f"   Data type: {type(data)}")
                    if isinstance(data, list):
                        print(f"   Items: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
                except:
                    print("   Non-JSON response")
            else:
                print(f"❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 GSA API DEBUGGING")
    print("=" * 50)
    
    working = test_gsa_endpoints()
    test_without_api_key()
    
    print(f"\n📊 SUMMARY")
    print(f"Working endpoints: {len(working)}")
    for endpoint in working:
        print(f"✅ {endpoint['name']}")
    
    print("\n✅ GSA debugging complete!")