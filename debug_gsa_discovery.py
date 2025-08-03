#!/usr/bin/env python3
"""
GSA API Discovery - find the current API structure
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY"

def test_gsa_base_discovery():
    """Test GSA API discovery endpoints"""
    
    discovery_urls = [
        'https://api.gsa.gov',
        'https://api.gsa.gov/',
        'https://api.gsa.gov/v1',
        'https://api.gsa.gov/discovery',
        'https://api.gsa.gov/api',
        'https://open.gsa.gov/api',
        'https://developers.gsa.gov'
    ]
    
    for url in discovery_urls:
        print(f"\n🔍 Testing discovery: {url}")
        try:
            response = requests.get(url, timeout=10, verify=False)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print("✅ JSON Response:")
                        print(json.dumps(data, indent=2)[:500])
                    except:
                        print("❌ Invalid JSON")
                elif 'html' in content_type:
                    # Look for API documentation links
                    text = response.text.lower()
                    if 'api' in text:
                        print("✅ HTML with API references found")
                        # Extract potential API paths
                        import re
                        api_paths = re.findall(r'/api/[^"\s<>]+', text)
                        if api_paths:
                            print(f"   Found API paths: {api_paths[:5]}")
                    else:
                        print("❌ HTML but no API references")
                else:
                    print(f"❌ Content type: {content_type}")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_known_gsa_api_patterns():
    """Test different API URL patterns that GSA might use"""
    
    # Different base patterns GSA might use
    base_patterns = [
        'https://api.data.gov/gsa',
        'https://gsa-apis.data.gov',
        'https://open.gsa.gov/api',
        'https://api.gsa.gov/technology/digitalanalytics',
        'https://api.gsa.gov/systems',
        'https://api.gsa.gov/travel/perdiem',
        'https://api.gsa.gov/acquisition'
    ]
    
    for base in base_patterns:
        print(f"\n🧪 Testing pattern: {base}")
        
        # Test with and without API key
        for with_key in [True, False]:
            try:
                params = {'api_key': API_KEY} if with_key else {}
                response = requests.get(base, params=params, timeout=8, verify=False)
                
                key_str = "with key" if with_key else "no key"
                print(f"   {key_str}: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ JSON data available ({len(str(data))} chars)")
                        return base, with_key  # Found working endpoint
                    except:
                        if len(response.text) < 1000:
                            print(f"   Text response: {response.text[:100]}...")
                
            except Exception as e:
                pass  # Ignore connection errors for discovery

def test_specific_data_endpoints():
    """Test specific data endpoints that might work"""
    
    # Test specific endpoints that are likely to exist
    specific_tests = [
        {
            'name': 'Per Diem Rates (2024)',
            'url': 'https://api.gsa.gov/travel/perdiem/v2/rates/state/DC/city/Washington/year/2024',
            'params': {'api_key': API_KEY}
        },
        {
            'name': 'Digital Analytics (current)',
            'url': 'https://api.gsa.gov/analytics/dap/v1.1/domain/gsa.gov',
            'params': {'api_key': API_KEY}
        },
        {
            'name': 'Systems Data',
            'url': 'https://api.gsa.gov/systems/v1/systems',
            'params': {'api_key': API_KEY}
        }
    ]
    
    for test in specific_tests:
        print(f"\n🎯 Testing specific: {test['name']}")
        try:
            response = requests.get(test['url'], params=test['params'], timeout=10, verify=False)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"Data type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                    elif isinstance(data, list):
                        print(f"Array length: {len(data)}")
                    return test['url'], test['params']
                except:
                    print("Non-JSON response but 200 OK")
            elif response.status_code == 404:
                print("❌ Not Found") 
            elif response.status_code == 403:
                print("❌ Forbidden (bad API key?)")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return None, None

if __name__ == "__main__":
    print("🔍 GSA API DISCOVERY")
    print("=" * 50)
    
    print("Phase 1: Base API Discovery")
    test_gsa_base_discovery()
    
    print("\n" + "=" * 50)
    print("Phase 2: API Pattern Testing")
    pattern_result = test_known_gsa_api_patterns()
    
    print("\n" + "=" * 50) 
    print("Phase 3: Specific Endpoint Testing")
    endpoint_result = test_specific_data_endpoints()
    
    print("\n" + "=" * 50)
    print("🏁 DISCOVERY SUMMARY")
    
    if pattern_result[0]:
        print(f"✅ Working pattern found: {pattern_result[0]}")
    if endpoint_result[0]:
        print(f"✅ Working endpoint found: {endpoint_result[0]}")
    
    if not pattern_result[0] and not endpoint_result[0]:
        print("❌ No working GSA API endpoints found")
        print("   Possible issues:")
        print("   - API key expired or invalid")
        print("   - GSA API structure changed")
        print("   - APIs moved to different domain")
        print("   - Need different authentication method")
    
    print("\n✅ GSA discovery complete!")