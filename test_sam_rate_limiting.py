#!/usr/bin/env python3
"""
Test the enhanced SAM.gov rate limiting system
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

async def test_sam_rate_limiting():
    """Test SAM.gov intelligent rate limiting"""
    print("🚦 Testing SAM.gov Intelligent Rate Limiting")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Show initial rate limit state
        rate_info = client._rate_limits['sam_gov']
        print(f"📊 Initial Rate Limit State:")
        print(f"   Hourly Limit: {rate_info['hourly_limit']}")
        print(f"   Calls Made: {rate_info['calls']}")
        print(f"   Per-Second Limit: {rate_info['per_second_limit']}")
        print(f"   Consecutive Failures: {rate_info['consecutive_failures']}")
        
        # Test rapid successive calls to trigger throttling
        search_terms = [
            "artificial intelligence",
            "cloud computing",
            "cybersecurity", 
            "blockchain",
            "data analytics"
        ]
        
        print(f"\n🔄 Testing rapid successive calls (should trigger throttling)...")
        
        for i, term in enumerate(search_terms, 1):
            print(f"\n{i}/5 - Searching for '{term}'...")
            start_time = time.time()
            
            result = await client.search_sam_gov_opportunities(term, 3)
            
            elapsed = time.time() - start_time
            
            if result.success:
                print(f"✅ Success: {result.count} opportunities ({elapsed:.1f}s)")
                if result.data:
                    sample = result.data[0]
                    print(f"   Sample: {sample.get('title', 'N/A')[:50]}...")
            else:
                print(f"⚠️ Rate Limited: {result.error}")
                
                # Show current rate limit state after failure
                rate_info = client._rate_limits['sam_gov']
                print(f"   Current state: {rate_info['calls']}/{rate_info['hourly_limit']} calls")
                if rate_info.get('backoff_until', 0) > time.time():
                    backoff_remaining = int((rate_info['backoff_until'] - time.time()) / 60)
                    print(f"   Backoff: {backoff_remaining} minutes remaining")
                
            # Show timing between calls
            if i < len(search_terms):
                print(f"   Waiting for next call...")
                time.sleep(0.5)  # Small delay to see throttling behavior

async def test_sam_recovery():
    """Test SAM.gov rate limit recovery"""
    print("\n\n🔄 Testing SAM.gov Rate Limit Recovery")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Manually trigger a few failures to test recovery
        rate_info = client._rate_limits['sam_gov']
        
        # Simulate some failures
        print("🧪 Simulating rate limit errors to test recovery...")
        for i in range(3):
            client._handle_sam_rate_limit_error(429)
            rate_info = client._rate_limits['sam_gov']
            backoff_minutes = int((rate_info['backoff_until'] - time.time()) / 60) if rate_info['backoff_until'] > time.time() else 0
            print(f"   Failure {i+1}: Backoff = {backoff_minutes} minutes, Limit = {rate_info['hourly_limit']}")
        
        # Test recovery
        print("\n✅ Simulating successful call to test recovery...")
        client._handle_sam_success()
        rate_info = client._rate_limits['sam_gov']
        print(f"   After success: Failures = {rate_info['consecutive_failures']}, Backoff cleared = {rate_info['backoff_until'] == 0}")

async def test_sam_detailed_error_messages():
    """Test detailed SAM.gov error messages"""
    print("\n\n📋 Testing Detailed SAM.gov Error Messages")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Manually set different rate limit states to test error messages
        rate_info = client._rate_limits['sam_gov']
        
        # Test 1: Hourly limit reached
        print("🧪 Test 1: Hourly limit reached")
        rate_info['calls'] = 900  # At limit
        rate_info['reset_time'] = time.time() + 1800  # 30 minutes until reset
        
        result = await client.search_sam_gov_opportunities("test", 1)
        print(f"   Error: {result.error}")
        
        # Test 2: Throttling (too fast)
        print("\n🧪 Test 2: Per-second throttling")
        rate_info['calls'] = 10  # Under limit
        rate_info['last_call'] = time.time() - 0.5  # Called 0.5 seconds ago (needs 2 second gap)
        
        result = await client.search_sam_gov_opportunities("test", 1)
        print(f"   Error: {result.error}")
        
        # Test 3: Exponential backoff
        print("\n🧪 Test 3: Exponential backoff")
        rate_info['calls'] = 10  # Under limit
        rate_info['last_call'] = 0  # Long time ago
        rate_info['backoff_until'] = time.time() + 300  # 5 minutes backoff
        rate_info['consecutive_failures'] = 2
        
        result = await client.search_sam_gov_opportunities("test", 1)
        print(f"   Error: {result.error}")

async def main():
    """Run comprehensive SAM.gov rate limiting tests"""
    print("🚀 SAM.GOV ENHANCED RATE LIMITING TEST SUITE")
    print("=" * 70)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Features:")
    print("   • Intelligent per-second throttling (2s intervals)")
    print("   • Hourly limits with adaptive reduction")
    print("   • Exponential backoff on failures")
    print("   • Detailed error messages")
    print("   • Automatic recovery on success")
    
    try:
        # Run all tests
        await test_sam_rate_limiting()
        await test_sam_recovery()
        await test_sam_detailed_error_messages()
        
        print("\n" + "=" * 70)
        print("🎉 SAM.GOV RATE LIMITING TEST COMPLETED")
        print("=" * 70)
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ Intelligent rate limiting system implemented!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())