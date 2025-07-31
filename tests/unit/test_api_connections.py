#!/usr/bin/env python3
"""Test all API connections"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_apis():
    print("\n=== Testing API Connections ===\n")
    
    # Load API keys
    sam_key = os.getenv('SAM_GOV_API_KEY')
    census_key = os.getenv('CENSUS_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')
    
    async with aiohttp.ClientSession() as session:
        # Test SAM.gov
        print("Testing SAM.gov API...")
        try:
            url = "https://api.sam.gov/entity-information/v3/entities/ZQGGHJH74DW7"
            headers = {'X-Api-Key': sam_key}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    print("✓ SAM.gov API: Working")
                else:
                    print(f"✗ SAM.gov API: Error {response.status}")
        except Exception as e:
            print(f"✗ SAM.gov API: {e}")
        
        # Test Census API
        print("\nTesting Census API...")
        try:
            url = "https://api.census.gov/data/2021/acs/acs5"
            params = {
                'get': 'B01003_001E',
                'for': 'state:01',
                'key': census_key
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    print("✓ Census API: Working")
                else:
                    print(f"✗ Census API: Error {response.status}")
        except Exception as e:
            print(f"✗ Census API: {e}")
        
        # Test FRED API
        print("\nTesting FRED API...")
        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': 'UNRATE',
                'api_key': fred_key,
                'file_type': 'json',
                'limit': 1
            }
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    print("✓ FRED API: Working")
                else:
                    print(f"✗ FRED API: Error {response.status}")
        except Exception as e:
            print(f"✗ FRED API: {e}")

asyncio.run(test_apis())
