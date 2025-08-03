#!/usr/bin/env python3
"""
Test the enhanced government API client
This will verify all 7 APIs are working correctly
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.government_apis.enhanced_api_client import EnhancedGovernmentAPIClient, search_government_opportunities
from datetime import datetime

# API Keys
API_KEYS = {
    "SAM_API_KEY": "Ec4gRnGckZjZmwbCtTiCyCsELua6nREcoyysaXqk",
    "CONGRESS_API_KEY": "Lt9hyLPZ5yBFUreIFDHvrMljeplEviWoHkAshNq9",
    "CENSUS_API_KEY": "70e4e3355e1b7b1a42622ba9201157bd1b105629",
    "REGULATIONS_API_KEY": "eOaulCdds6asIkvxR54otUJIC6badoeSynDJN68w",
    "GSA_API_KEY": "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY",
    "GOVINFO_API_KEY": "2y76olvQevGbWUkoWgFNAJSa1KBabOFU1FBrhWsF"
}

async def test_individual_apis():
    """Test each API individually"""
    print("🧪 Testing Individual Government APIs")
    print("=" * 50)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Test SAM.gov
        print("\n🏛️ Testing SAM.gov Opportunities...")
        sam_result = await client.search_sam_gov_opportunities("cloud computing", 5)
        if sam_result.success:
            print(f"✅ SAM.gov: Found {sam_result.count} opportunities ({sam_result.response_time_ms:.0f}ms)")
            if sam_result.data:
                sample = sam_result.data[0]
                print(f"   Sample: {sample.get('title', 'N/A')[:60]}...")
        else:
            print(f"⚠️ SAM.gov: {sam_result.error}")
        
        # Test Congress.gov
        print("\n🏛️ Testing Congress.gov Bills...")
        congress_result = await client.search_congress_bills("artificial intelligence", 5)
        if congress_result.success:
            print(f"✅ Congress.gov: Found {congress_result.count} bills ({congress_result.response_time_ms:.0f}ms)")
            if congress_result.data:
                sample = congress_result.data[0]
                print(f"   Sample: {sample.get('title', 'N/A')[:60]}...")
        else:
            print(f"❌ Congress.gov: {congress_result.error}")
        
        # Test Federal Register
        print("\n📋 Testing Federal Register...")
        fr_result = await client.search_federal_register("technology", 5)
        if fr_result.success:
            print(f"✅ Federal Register: Found {fr_result.count} articles ({fr_result.response_time_ms:.0f}ms)")
            if fr_result.data:
                sample = fr_result.data[0]
                print(f"   Sample: {sample.get('title', 'N/A')[:60]}...")
                agencies = sample.get('agency_names', [])
                print(f"   Agencies: {', '.join(agencies[:2])}")
        else:
            print(f"❌ Federal Register: {fr_result.error}")
        
        # Test Census
        print("\n📊 Testing Census Bureau...")
        census_result = await client.get_census_data("business_patterns")
        if census_result.success:
            print(f"✅ Census: Found {census_result.count} records ({census_result.response_time_ms:.0f}ms)")
            if census_result.data:
                sample = census_result.data[0]
                print(f"   Sample: {sample.get('NAME', 'N/A')} - {sample.get('EMP', 'N/A')} employees")
        else:
            print(f"❌ Census: {census_result.error}")
        
        # Test Government Analytics (GSA replacement)
        print("\n🏢 Testing Government Analytics...")
        analytics_result = await client.get_government_analytics_data("agencies")
        if analytics_result.success:
            print(f"✅ Government Analytics: Found {analytics_result.count} records ({analytics_result.response_time_ms:.0f}ms)")
            if analytics_result.data:
                sample = analytics_result.data[0]
                print(f"   Sample: {sample.get('name', 'N/A')} - {sample.get('contract_volume', 'N/A')} volume")
        else:
            print(f"⚠️ Government Analytics: {analytics_result.error}")
        
        # Test Regulations.gov
        print("\n📜 Testing Regulations.gov...")
        reg_result = await client.search_regulations_gov("artificial intelligence")
        if reg_result.success:
            print(f"✅ Regulations.gov: Found {reg_result.count} documents ({reg_result.response_time_ms:.0f}ms)")
            if reg_result.data:
                sample = reg_result.data[0]
                attrs = sample.get('attributes', {})
                print(f"   Sample: {attrs.get('title', 'N/A')[:60]}...")
        else:
            print(f"⚠️ Regulations.gov: {reg_result.error}")

async def test_comprehensive_search():
    """Test comprehensive market intelligence gathering"""
    print("\n\n🎯 Testing Comprehensive Market Intelligence")
    print("=" * 50)
    
    result = await search_government_opportunities("cloud computing", 10)
    
    print(f"Query: {result['query']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Total Sources: {result['summary']['total_sources']}")
    print(f"Successful Sources: {result['summary']['successful_sources']}")
    print(f"Total Records: {result['summary']['total_records']}")
    
    print("\n📊 Source Results:")
    for source_name, source_data in result['sources'].items():
        status = "✅" if source_data['success'] else "❌"
        print(f"{status} {source_name.replace('_', ' ').title()}: {source_data['count']} records ({source_data['response_time_ms']:.0f}ms)")
        if not source_data['success'] and source_data['error']:
            print(f"   Error: {source_data['error'][:80]}...")
        elif source_data['data']:
            # Show sample data
            sample = source_data['data'][0]
            if source_name == 'opportunities':
                print(f"   Sample: {sample.get('title', 'N/A')[:50]}...")
            elif source_name == 'legislation':
                print(f"   Sample: {sample.get('title', 'N/A')[:50]}...")
            elif source_name == 'federal_register':
                print(f"   Sample: {sample.get('title', 'N/A')[:50]}...")
            elif source_name == 'economic_data':
                print(f"   Sample: {sample.get('NAME', 'N/A')} - Pop: {sample.get('B01001_001E', 'N/A')}")
            elif source_name == 'government_analytics':
                print(f"   Sample: {sample.get('name', 'N/A')} - {sample.get('contract_volume', 'N/A')}")
            elif source_name == 'regulatory_docs':
                print(f"   Sample: {sample.get('title', 'N/A')[:50]}...")
            else:
                # Generic sample display
                if isinstance(sample, dict):
                    key = list(sample.keys())[0] if sample.keys() else 'data'
                    print(f"   Sample {key}: {str(sample.get(key, sample))[:50]}...")

async def performance_test():
    """Test API performance and caching"""
    print("\n\n⚡ Performance & Caching Test")
    print("=" * 50)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        # First call
        start_time = datetime.now()
        result1 = await client.search_sam_gov_opportunities("technology", 5)
        first_call_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Second call (should be cached)
        start_time = datetime.now()
        result2 = await client.search_sam_gov_opportunities("technology", 5)
        second_call_time = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"First Call: {first_call_time:.0f}ms")
        print(f"Second Call (cached): {second_call_time:.0f}ms")
        print(f"Cache Speedup: {first_call_time/second_call_time:.1f}x faster")

async def main():
    """Run comprehensive API tests"""
    print("🚀 KBI LABS ENHANCED GOVERNMENT API TEST SUITE")
    print("=" * 60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    await test_individual_apis()
    await test_comprehensive_search()
    await performance_test()
    
    print("\n" + "=" * 60)
    print("🎉 GOVERNMENT API TEST SUITE COMPLETED")
    print("=" * 60)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())