#!/usr/bin/env python3
"""
Debug Census API - test without key and different formats
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "70e4e3355e1b7b1a42622ba9201157bd1b105629"

def test_census_without_key():
    """Test Census API without API key (public data)"""
    print("🧪 Testing Census API WITHOUT key (public access)")
    
    url = 'https://api.census.gov/data/2021/acs/acs5'
    params = {
        'get': 'NAME,B01001_001E',  # Name, Total Population
        'for': 'state:*'
        # No key parameter
    }
    
    try:
        response = requests.get(url, params=params, timeout=10, verify=False)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            print("✅ SUCCESS without key!")
            try:
                data = response.json()
                print(f"✅ Valid JSON with {len(data)} items")
                if data:
                    print("Sample data:")
                    for i, item in enumerate(data[:3]):
                        print(f"  [{i}]: {item}")
                return True
            except json.JSONDecodeError:
                print("❌ Still not JSON")
                print("Response:", response.text[:200])
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_different_census_datasets():
    """Test different Census datasets that might not require keys"""
    
    datasets = [
        {
            'name': 'Population Estimates',
            'url': 'https://api.census.gov/data/2021/pep/population',
            'params': {'get': 'NAME,POP', 'for': 'state:*'}
        },
        {
            'name': 'Decennial Census',
            'url': 'https://api.census.gov/data/2020/dec/pl',
            'params': {'get': 'NAME,P1_001N', 'for': 'state:*'}
        },
        {
            'name': 'ACS Subject Tables',
            'url': 'https://api.census.gov/data/2021/acs/acs5/subject',
            'params': {'get': 'NAME,S0101_C01_001E', 'for': 'state:*'}
        }
    ]
    
    working_datasets = []
    
    for dataset in datasets:
        print(f"\n🧪 Testing: {dataset['name']}")
        try:
            response = requests.get(dataset['url'], params=dataset['params'], timeout=10, verify=False)
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ {dataset['name']} works! {len(data)} records")
                    working_datasets.append(dataset)
                    if data:
                        print(f"   Sample: {data[0]}")
                except json.JSONDecodeError:
                    print(f"❌ {dataset['name']}: Not JSON")
            else:
                print(f"❌ {dataset['name']}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {dataset['name']}: {e}")
    
    return working_datasets

def test_api_key_formats():
    """Test different ways to send the API key"""
    print("\n🔑 Testing different API key formats")
    
    base_url = 'https://api.census.gov/data/2021/acs/acs5'
    base_params = {'get': 'NAME,B01001_001E', 'for': 'state:01'}  # Just Alabama
    
    key_formats = [
        {'key': API_KEY},  # Standard
        {'api_key': API_KEY},  # Alternative
        {'KEY': API_KEY},  # Uppercase
    ]
    
    headers_formats = [
        {},  # No headers
        {'X-API-Key': API_KEY},  # Header-based
        {'Authorization': f'Bearer {API_KEY}'},  # Bearer token
    ]
    
    for key_format in key_formats:
        for headers in headers_formats:
            params = {**base_params, **key_format}
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=5, verify=False)
                if response.status_code == 200 and 'Invalid Key' not in response.text:
                    try:
                        data = response.json()
                        print(f"✅ Working format: params={key_format}, headers={headers}")
                        print(f"   Data: {data}")
                        return True
                    except:
                        pass
            except:
                pass
    
    print("❌ No working key format found")
    return False

if __name__ == "__main__":
    print("🔍 COMPREHENSIVE CENSUS API DEBUGGING")
    print("=" * 60)
    
    # Test 1: No key required
    if test_census_without_key():
        print("\n🎉 Census API works without key!")
    else:
        print("\n📋 Testing different datasets...")
        working = test_different_census_datasets()
        
        if working:
            print(f"\n🎉 Found {len(working)} working datasets!")
        else:
            print("\n🔑 Testing API key formats...")
            test_api_key_formats()
    
    print("\n✅ Census debugging complete!")