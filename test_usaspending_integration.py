#!/usr/bin/env python3
"""
Test USASpending.gov API integration
Validate our access to $6+ trillion in federal spending data
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.government_apis.enhanced_api_client import EnhancedGovernmentAPIClient
from datetime import datetime

# API Keys (USASpending requires none!)
API_KEYS = {
    "SAM_API_KEY": "Ec4gRnGckZjZmwbCtTiCyCsELua6nREcoyysaXqk",
    "CONGRESS_API_KEY": "Lt9hyLPZ5yBFUreIFDHvrMljeplEviWoHkAshNq9",
    "CENSUS_API_KEY": "70e4e3355e1b7b1a42622ba9201157bd1b105629",
    "REGULATIONS_API_KEY": "eOaulCdds6asIkvxR54otUJIC6badoeSynDJN68w",
    "GSA_API_KEY": "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY",
    "GOVINFO_API_KEY": "2y76olvQevGbWUkoWgFNAJSa1KBabOFU1FBrhWsF"
}

async def test_usaspending_awards():
    """Test USASpending award search functionality"""
    print("💰 Testing USASpending.gov Award Search (NO AUTH REQUIRED)")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Test different search terms
        search_terms = [
            "artificial intelligence",
            "cloud computing", 
            "cybersecurity",
            "technology"
        ]
        
        for term in search_terms:
            print(f"\n🔍 Searching for '{term}' contracts...")
            
            result = await client.search_usaspending_awards(term, 5)
            
            if result.success:
                print(f"✅ Found {result.count} awards ({result.response_time_ms:.0f}ms)")
                
                if result.data:
                    print("📊 Sample Awards:")
                    for i, award in enumerate(result.data[:3], 1):
                        amount_formatted = f"${award['amount']:,.0f}" if isinstance(award['amount'], (int, float)) and award['amount'] > 0 else "N/A"
                        print(f"   {i}. {award['title'][:70]}...")
                        print(f"      Recipient: {award['recipient']}")
                        print(f"      Amount: {amount_formatted}")
                        print(f"      Agency: {award['agency']}")
                        print()
                else:
                    print("   No data returned")
            else:
                print(f"❌ Error: {result.error}")
                if "404" in result.error:
                    print("   This might be an endpoint issue - let's debug")
                elif "timeout" in result.error.lower():
                    print("   Server timeout - this is normal for large queries")

async def test_agency_spending():
    """Test agency spending data functionality"""  
    print("\n\n🏛️ Testing Agency Spending Data")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Test overall agency spending
        print("📈 Getting top agency spending data...")
        
        result = await client.get_agency_spending_data()
        
        if result.success:
            print(f"✅ Found {result.count} agencies ({result.response_time_ms:.0f}ms)")
            
            if result.data:
                print("💸 Top Agency Budgets (FY2024):")
                for i, agency in enumerate(result.data[:5], 1):
                    budget = agency.get('total_budgetary_resources', 0)
                    obligations = agency.get('obligations_incurred', 0)
                    unobligated = agency.get('unobligated_balance', 0)
                    
                    budget_formatted = f"${budget/1000000000:.1f}B" if budget > 1000000000 else f"${budget/1000000:.1f}M"
                    obligations_formatted = f"${obligations/1000000000:.1f}B" if obligations > 1000000000 else f"${obligations/1000000:.1f}M"
                    
                    print(f"   {i}. {agency['agency_name']}")
                    print(f"      Budget: {budget_formatted} | Obligated: {obligations_formatted}")
                    
                    if budget > 0:
                        utilization = (obligations / budget) * 100
                        print(f"      Utilization: {utilization:.1f}%")
                    print()
        else:
            print(f"❌ Error: {result.error}")
            
        # Test specific agency
        print("\n🎯 Testing specific agency search...")
        dod_result = await client.get_agency_spending_data("Defense", 2024)
        
        if dod_result.success and dod_result.data:
            agency = dod_result.data[0]
            budget = agency.get('total_budgetary_resources', 0)
            print(f"✅ Department of Defense Budget: ${budget/1000000000:.1f}B")
        else:
            print(f"⚠️ Specific agency search: {dod_result.error if not dod_result.success else 'No data'}")

async def test_comprehensive_with_usaspending():
    """Test comprehensive market data with USASpending integration"""
    print("\n\n🎯 Testing Enhanced Market Intelligence (with USASpending)")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Get comprehensive data
        results = await client.get_comprehensive_market_data("artificial intelligence")
        
        print(f"Query: artificial intelligence")
        print(f"Total Sources: {len(results)}")
        
        successful = sum(1 for r in results.values() if r.success)
        total_records = sum(r.count for r in results.values() if r.success)
        
        print(f"Successful Sources: {successful}/{len(results)}")
        print(f"Total Records: {total_records}")
        
        print("\n📊 Source Results:")
        for source_name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {source_name.replace('_', ' ').title()}: {result.count} records ({result.response_time_ms:.0f}ms)")
            
            if not result.success:
                print(f"   Error: {result.error[:80]}...")
            elif result.data and source_name in ['federal_awards', 'agency_spending']:
                # Show USASpending specific data
                sample = result.data[0]
                if source_name == 'federal_awards':
                    amount = sample.get('amount', 0)
                    amount_str = f"${amount:,.0f}" if isinstance(amount, (int, float)) and amount > 0 else "N/A"
                    print(f"   Sample: {sample.get('title', 'N/A')[:50]}... | ${amount_str}")
                elif source_name == 'agency_spending':
                    budget = sample.get('total_budgetary_resources', 0)
                    budget_str = f"${budget/1000000000:.1f}B" if budget > 1000000000 else f"${budget/1000000:.1f}M"
                    print(f"   Sample: {sample.get('agency_name', 'N/A')} | Budget: {budget_str}")

async def main():
    """Run comprehensive USASpending integration tests"""
    print("🚀 USASPENDING.GOV API INTEGRATION TEST")
    print("=" * 70)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Testing access to $6+ trillion in federal spending data")
    print("🔑 NO API KEY REQUIRED for USASpending.gov!")
    
    try:
        # Run all tests
        await test_usaspending_awards()
        await test_agency_spending() 
        await test_comprehensive_with_usaspending()
        
        print("\n" + "=" * 70)
        print("🎉 USASPENDING INTEGRATION TEST COMPLETED")
        print("=" * 70)
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ Federal spending data pipeline enhanced!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())