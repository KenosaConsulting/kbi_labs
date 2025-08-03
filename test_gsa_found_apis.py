#!/usr/bin/env python3
"""
Test the GSA API paths we discovered
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY"

def test_discovered_gsa_apis():
    """Test the API paths we found"""
    
    discovered_apis = [
        {
            'name': 'Digital Analytics Program',
            'base_url': 'https://api.gsa.gov/api/dap',
            'endpoints': [
                '/reports/today',
                '/reports/yesterday', 
                '/reports/7-days',
                '/reports/30-days',
                '/reports/90-days',
                '/reports/site/gsa.gov',
                '/agencies'
            ]
        },
        {
            'name': 'Agriculture API',
            'base_url': 'https://api.gsa.gov/api/ag-api',
            'endpoints': [
                '/v1/products',
                '/v1/categories',
                '/v1/search'
            ]
        },
        {
            'name': 'API Data Gov',
            'base_url': 'https://api.gsa.gov/api/apidatagov',
            'endpoints': [
                '/metrics',
                '/status',
                '/v1/apis'
            ]
        }
    ]
    
    working_endpoints = []
    
    for api in discovered_apis:
        print(f"\n🧪 Testing {api['name']}")
        print(f"Base URL: {api['base_url']}")
        
        for endpoint in api['endpoints']:
            full_url = api['base_url'] + endpoint
            print(f"\n   Testing: {endpoint}")
            
            # Test with API key
            try:
                params = {'api_key': API_KEY}
                response = requests.get(full_url, params=params, timeout=10, verify=False)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ SUCCESS with API key!")
                    try:
                        data = response.json()
                        print(f"   ✅ Valid JSON ({len(str(data))} chars)")
                        
                        # Show structure
                        if isinstance(data, dict):
                            keys = list(data.keys())[:5]
                            print(f"   Keys: {keys}")
                            
                            # Show sample data
                            for key in keys[:2]:
                                value = data[key]
                                if isinstance(value, (list, dict)):
                                    print(f"   {key}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
                                else:
                                    print(f"   {key}: {str(value)[:50]}...")
                                    
                        elif isinstance(data, list):
                            print(f"   Array with {len(data)} items")
                            if data:
                                print(f"   Sample item: {str(data[0])[:100]}...")
                        
                        working_endpoints.append({
                            'name': f"{api['name']} - {endpoint}",
                            'url': full_url,
                            'params': params,
                            'data_preview': data
                        })
                        
                    except json.JSONDecodeError:
                        print("   ⚠️ Not JSON, but 200 OK")
                        print(f"   Content: {response.text[:100]}...")
                        
                elif response.status_code == 404:
                    print("   ❌ Not Found")
                elif response.status_code == 403:
                    print("   ❌ Forbidden")
                elif response.status_code == 429:
                    print("   ⚠️ Rate Limited")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}...")
    
    return working_endpoints

def test_without_paths():
    """Test base URLs directly"""
    print("\n🔍 Testing base URLs directly")
    
    base_urls = [
        'https://api.gsa.gov/api/dap',
        'https://api.gsa.gov/api/ag-api', 
        'https://api.gsa.gov/api/apidatagov'
    ]
    
    for url in base_urls:
        print(f"\n   Testing: {url}")
        try:
            params = {'api_key': API_KEY}
            response = requests.get(url, params=params, timeout=10, verify=False)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON data available")
                    return url, data
                except:
                    print(f"   Text: {response.text[:100]}...")
                    
        except Exception as e:
            print(f"   Error: {e}")
    
    return None, None

if __name__ == "__main__":
    print("🔍 TESTING DISCOVERED GSA APIS")
    print("=" * 60)
    
    working = test_discovered_gsa_apis()
    
    if not working:
        print("\nTrying base URLs...")
        base_result = test_without_paths()
    
    print(f"\n📊 RESULTS")
    print("=" * 30)
    print(f"Working endpoints found: {len(working)}")
    
    for endpoint in working:
        print(f"✅ {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        if isinstance(endpoint['data_preview'], dict):
            keys = list(endpoint['data_preview'].keys())[:3]
            print(f"   Data keys: {keys}")
        print()
    
    if working:
        print("🎉 GSA API endpoints found and working!")
    else:
        print("❌ No working GSA endpoints found")
    
    print("✅ GSA API testing complete!")