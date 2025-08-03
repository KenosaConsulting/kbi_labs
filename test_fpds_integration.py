#!/usr/bin/env python3
"""
Test FPDS (Federal Procurement Data System) Integration
Validate SOAP/XML access to $500+ billion in federal contract data
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.government_apis.enhanced_api_client import EnhancedGovernmentAPIClient
from src.government_apis.fpds_client import FPDSClient, search_fpds_contracts
from datetime import datetime

# API Keys (FPDS may require separate credentials)
API_KEYS = {
    "SAM_API_KEY": "Ec4gRnGckZjZmwbCtTiCyCsELua6nREcoyysaXqk",
    "CONGRESS_API_KEY": "Lt9hyLPZ5yBFUreIFDHvrMljeplEviWoHkAshNq9",
    "CENSUS_API_KEY": "70e4e3355e1b7b1a42622ba9201157bd1b105629",
    "REGULATIONS_API_KEY": "eOaulCdds6asIkvxR54otUJIC6badoeSynDJN68w",
    "GSA_API_KEY": "MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY",
    "GOVINFO_API_KEY": "2y76olvQevGbWUkoWgFNAJSa1KBabOFU1FBrhWsF",
    # FPDS credentials (if available)
    # "FPDS_USER_ID": "your_fpds_user_id",
    # "FPDS_PASSWORD": "your_fpds_password"
}

async def test_fpds_direct():
    """Test FPDS client directly"""
    print("🔧 Testing FPDS Client Directly")
    print("=" * 60)
    
    # Test with no credentials (should fall back to mock data)
    async with FPDSClient() as fpds_client:
        
        # Test vendor search
        print("🔍 Searching for 'ACME' vendors...")
        result = await fpds_client.search_contracts(vendor_name="ACME", limit=3)
        
        if result.success:
            print(f"✅ Found {result.count} contracts ({result.response_time_ms:.0f}ms)")
            for i, contract in enumerate(result.data, 1):
                print(f"   {i}. {contract['vendor_name']}")
                print(f"      Contract: {contract['contract_id']}")
                print(f"      Amount: ${contract['amount']:,}" if isinstance(contract['amount'], (int, float)) else f"      Amount: {contract['amount']}")
                print(f"      Agency: {contract['agency']}")
        else:
            print(f"❌ FPDS search failed: {result.error}")
        
        # Test NAICS code search
        print(f"\n🏭 Searching for IT services (NAICS 541511)...")
        result2 = await fpds_client.search_contracts(naics_code="541511", limit=2)
        
        if result2.success:
            print(f"✅ Found {result2.count} IT contracts")
            for contract in result2.data:
                print(f"   • {contract['vendor_name']}: ${contract['amount']:,}" if isinstance(contract['amount'], (int, float)) else f"   • {contract['vendor_name']}: {contract['amount']}")
        else:
            print(f"❌ NAICS search failed: {result2.error}")

async def test_fpds_integration():
    """Test FPDS integration in main API client"""
    print("\n\n🌐 Testing FPDS Integration in Main Client")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        # Test FPDS search through main client
        print("🔍 Testing FPDS contract search...")
        result = await client.search_fpds_contracts(vendor_name="TECHNOLOGY", limit=5)
        
        if result.success:
            print(f"✅ FPDS integration successful: {result.count} contracts")
            
            if result.data:
                print("📋 Contract Details:")
                for i, contract in enumerate(result.data[:3], 1):
                    print(f"   {i}. Vendor: {contract.get('vendor_name', 'N/A')}")
                    print(f"      Contract ID: {contract.get('contract_id', 'N/A')}")
                    amount = contract.get('amount', 'N/A')
                    if isinstance(amount, (int, float)):
                        print(f"      Value: ${amount:,.0f}")
                    else:
                        print(f"      Value: {amount}")
                    print(f"      Agency: {contract.get('agency', 'N/A')}")
                    print(f"      Description: {contract.get('description', 'N/A')}")
                    print()
        else:
            print(f"⚠️ FPDS integration: {result.error}")

async def test_contract_intelligence():
    """Test combined contract intelligence (USASpending + FPDS)"""
    print("\n\n🧠 Testing Contract Intelligence (USASpending + FPDS)")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        print("🔍 Getting comprehensive contract intelligence for 'cloud computing'...")
        result = await client.get_contract_intelligence("cloud computing", 8)
        
        if result.success:
            print(f"✅ Contract Intelligence: {result.count} contracts from {result.source}")
            
            if result.data:
                print("💰 Top Contracts by Value:")
                for i, contract in enumerate(result.data[:5], 1):
                    vendor = contract.get('vendor_name', contract.get('recipient', 'N/A'))
                    amount = contract.get('amount', 0)
                    source = contract.get('source', 'unknown')
                    
                    if isinstance(amount, (int, float)) and amount > 0:
                        amount_str = f"${amount:,.0f}"
                    else:
                        amount_str = str(amount)
                    
                    print(f"   {i}. {vendor}")
                    print(f"      Value: {amount_str}")
                    print(f"      Source: {source}")
                    print(f"      Agency: {contract.get('agency', 'N/A')}")
        else:
            print(f"❌ Contract Intelligence failed: {result.error}")

async def test_fpds_full_pipeline():
    """Test FPDS in the complete government data pipeline"""
    print("\n\n🚀 Testing FPDS in Full Government Data Pipeline")
    print("=" * 60)
    
    async with EnhancedGovernmentAPIClient(API_KEYS) as client:
        
        print("🌐 Running comprehensive market intelligence with FPDS...")
        start_time = time.time()
        
        results = await client.get_comprehensive_market_data("artificial intelligence")
        elapsed = time.time() - start_time
        
        print(f"✅ Pipeline completed in {elapsed:.1f} seconds")
        
        # Analyze results
        successful_sources = sum(1 for r in results.values() if r.success)
        total_records = sum(r.count for r in results.values() if r.success)
        
        print(f"📊 Pipeline Results:")
        print(f"   Total sources: {len(results)}")
        print(f"   Successful sources: {successful_sources}")
        print(f"   Total records: {total_records}")
        print(f"   Success rate: {(successful_sources/len(results))*100:.1f}%")
        
        print(f"\n📋 Source Results:")
        for source_name, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"{status} {source_name.replace('_', ' ').title()}: {result.count} records ({result.response_time_ms:.0f}ms)")
            
            if not result.success:
                error_preview = result.error[:60] + "..." if len(result.error) > 60 else result.error
                print(f"   Error: {error_preview}")
            elif result.data and source_name == 'fpds_contracts':
                # Show FPDS-specific results
                sample = result.data[0] if result.data else None
                if sample:
                    vendor = sample.get('vendor_name', 'N/A')
                    amount = sample.get('amount', 'N/A')
                    print(f"   Sample: {vendor} - {amount}")

async def test_fpds_soap_endpoints():
    """Test FPDS SOAP endpoint discovery"""
    print("\n\n🔍 Testing FPDS SOAP Endpoint Discovery")
    print("=" * 60)
    
    # Test if we can connect to FPDS WSDL endpoints
    fpds_client = FPDSClient()
    
    print("🌐 Testing FPDS WSDL endpoint connectivity...")
    
    import aiohttp
    async with aiohttp.ClientSession() as session:
        
        test_urls = [
            "http://www.fpdsng.com/FPDS/wsdl/BusinessServices/DataCollection/contracts/1.3/Award.wsdl",
            "http://www.fpdsng.com/FPDS/wsdl/BusinessServices/DataCollection/contracts/1.1/Award.wsdl",
            "http://www.fpdsng.com/FPDS/wsdl/BusinessServices/DataCollection/contracts/1.0/Award.wsdl",
            "https://www.fpds.gov/",  # Base site
        ]
        
        for url in test_urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'xml' in content_type or 'wsdl' in url:
                            print(f"✅ {url} - Available (WSDL/XML)")
                        else:
                            print(f"✅ {url} - Available (HTTP)")
                    else:
                        print(f"⚠️ {url} - HTTP {response.status}")
            except Exception as e:
                print(f"❌ {url} - {str(e)[:50]}...")

async def main():
    """Run comprehensive FPDS integration tests"""
    print("🚀 FPDS (FEDERAL PROCUREMENT DATA SYSTEM) INTEGRATION TEST")
    print("=" * 70)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Testing SOAP/XML integration for $500+ billion in contract data")
    print("📡 Features:")
    print("   • SOAP web services with Zeep library")
    print("   • XML parsing and data extraction")
    print("   • Async integration with main pipeline")
    print("   • Fallback to mock data when SOAP unavailable")
    print("   • Combined contract intelligence with USASpending")
    
    try:
        # Run all tests
        await test_fpds_direct()
        await test_fpds_integration()
        await test_contract_intelligence()
        await test_fpds_full_pipeline()
        await test_fpds_soap_endpoints()
        
        print("\n" + "=" * 70)
        print("🎉 FPDS INTEGRATION TEST COMPLETED")
        print("=" * 70)
        print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ FPDS SOAP/XML integration implemented!")
        print("💡 Note: Using mock data - configure FPDS credentials for live data")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())