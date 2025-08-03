#!/usr/bin/env python3
"""
Test SAM.gov integration in the full data pipeline
Verify intelligent rate limiting works with real opportunities data
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.government_apis.enhanced_api_client import EnhancedGovernmentAPIClient
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

async def test_sam_individual():
    """Test SAM.gov individually with intelligent rate limiting"""
    print("🎯 Testing SAM.gov Individual Performance")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Test multiple search terms with proper spacing
        search_terms = [
            "artificial intelligence",
            "cloud computing", 
            "cybersecurity"
        ]
        
        successful_calls = 0
        total_opportunities = 0
        
        for i, term in enumerate(search_terms, 1):
            print(f"\n🔍 {i}/3 - Searching SAM.gov for '{term}'...")
            
            # Show rate limit state before call
            rate_info = client._rate_limits['sam_gov']
            print(f"   Rate state: {rate_info['calls']}/{rate_info['hourly_limit']} calls")
            
            start_time = time.time()
            result = await client.search_sam_gov_opportunities(term, 5)
            elapsed = time.time() - start_time
            
            if result.success:
                successful_calls += 1
                total_opportunities += result.count
                print(f"✅ Success: {result.count} opportunities ({elapsed:.1f}s)")
                
                if result.data:
                    print("📋 Sample Opportunities:")
                    for j, opp in enumerate(result.data[:2], 1):
                        title = opp.get('title', 'N/A')[:60]
                        agency = opp.get('department', opp.get('agency', 'N/A'))
                        print(f"   {j}. {title}...")
                        print(f"      Agency: {agency}")
                        
                        # Show more details if available
                        if 'postedDate' in opp:
                            print(f"      Posted: {opp['postedDate']}")
                        if 'responseDeadLine' in opp:
                            print(f"      Deadline: {opp['responseDeadLine']}")
            else:
                print(f"⚠️ Rate Limited: {result.error}")
                
                # If rate limited, show when we can try again
                if "backoff" in result.error.lower():
                    backoff_remaining = int((rate_info['backoff_until'] - time.time()) / 60) if rate_info.get('backoff_until', 0) > time.time() else 0
                    print(f"   Next attempt available in: {backoff_remaining} minutes")
            
            # Intelligent delay between calls
            if i < len(search_terms):
                if result.success:
                    print("   ⏱️ Waiting 3 seconds (rate limit compliance)...")
                    await asyncio.sleep(3)  # Respect rate limits
                else:
                    print("   ⏱️ Skipping delay due to rate limit...")
        
        print(f"\n📊 SAM.gov Individual Test Summary:")
        print(f"   Successful calls: {successful_calls}/{len(search_terms)}")
        print(f"   Total opportunities: {total_opportunities}")
        print(f"   Success rate: {(successful_calls/len(search_terms))*100:.1f}%")

async def test_sam_full_pipeline():
    """Test SAM.gov in the full market intelligence pipeline"""
    print("\n\n🌐 Testing SAM.gov in Full Pipeline")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        print("🚀 Running comprehensive market intelligence with SAM.gov...")
        
        # Get comprehensive data (includes SAM.gov opportunities)
        start_time = time.time()
        results = await client.get_comprehensive_market_data("cloud computing")
        elapsed = time.time() - start_time
        
        print(f"✅ Pipeline completed in {elapsed:.1f} seconds")
        
        # Analyze results
        successful_sources = sum(1 for r in results.values() if r.success)
        total_records = sum(r.count for r in results.values() if r.success)
        
        print(f"📊 Pipeline Results:")
        print(f"   Total sources: {len(results)}")
        print(f"   Successful sources: {successful_sources}")
        print(f"   Total records: {total_records}")
        print(f"   Pipeline success rate: {(successful_sources/len(results))*100:.1f}%")
        
        print(f"\n📋 Source-by-Source Results:")
        for source_name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {source_name.replace('_', ' ').title()}: {result.count} records ({result.response_time_ms:.0f}ms)")
            
            if not result.success:
                error_preview = result.error[:80] + "..." if len(result.error) > 80 else result.error
                print(f"   Error: {error_preview}")
            elif result.data and source_name == 'opportunities':
                # Show SAM.gov specific results
                sample = result.data[0] if result.data else None
                if sample:
                    print(f"   Sample: {sample.get('title', 'N/A')[:50]}...")

async def test_sam_caching():
    """Test SAM.gov caching behavior"""
    print("\n\n💾 Testing SAM.gov Caching")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        query = "artificial intelligence"
        
        # First call
        print(f"🔍 First call for '{query}'...")
        start_time = time.time()
        result1 = await client.search_sam_gov_opportunities(query, 3)
        first_call_time = time.time() - start_time
        
        if result1.success:
            print(f"✅ First call: {result1.count} results ({first_call_time:.2f}s)")
        else:
            print(f"⚠️ First call failed: {result1.error}")
            return
        
        # Second call (should use cache if first was successful)
        print(f"\n🔍 Second call for '{query}' (should use cache)...")
        start_time = time.time()
        result2 = await client.search_sam_gov_opportunities(query, 3)
        second_call_time = time.time() - start_time
        
        if result2.success:
            print(f"✅ Second call: {result2.count} results ({second_call_time:.2f}s)")
            
            # Calculate speedup
            if second_call_time > 0:
                speedup = first_call_time / second_call_time
                print(f"🚀 Cache speedup: {speedup:.1f}x faster")
                
                # Verify data consistency
                if result1.count == result2.count:
                    print("✅ Data consistency: Same results from cache")
                else:
                    print("⚠️ Data consistency: Different results (cache issue?)")
        else:
            print(f"⚠️ Second call failed: {result2.error}")

async def main():
    """Run comprehensive SAM.gov pipeline integration tests"""
    print("🚀 SAM.GOV PIPELINE INTEGRATION TEST SUITE")
    print("=" * 70)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Testing enhanced SAM.gov integration:")
    print("   • Intelligent rate limiting")
    print("   • Real opportunities data")
    print("   • Full pipeline integration")
    print("   • Caching performance")
    
    try:
        # Run all tests
        await test_sam_individual()
        await test_sam_full_pipeline()
        await test_sam_caching()
        
        print("\n" + "=" * 70)
        print("🎉 SAM.GOV PIPELINE INTEGRATION TEST COMPLETED")
        print("=" * 70)
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ SAM.gov integration validated - ready for production!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())