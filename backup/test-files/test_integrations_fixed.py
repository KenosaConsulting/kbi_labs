#!/usr/bin/env python3
"""Test the fixed integrations"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def test_integrations():
    print("🧪 Testing Fixed Integrations")
    print("=" * 40)
    
    # Test individual integrations
    print("\n1. Testing SAM.gov...")
    try:
        from src.integrations.government.sam_gov import SAMGovIntegration
        sam = SAMGovIntegration()
        result = await sam.validate_connection()
        print(f"   SAM.gov: {'✅ Connected' if result else '❌ Failed'}")
        await sam.close()
    except Exception as e:
        print(f"   SAM.gov: ❌ Error - {e}")
    
    print("\n2. Testing USASpending...")
    try:
        from src.integrations.government.usaspending import USASpendingIntegration
        usa = USASpendingIntegration()
        result = await usa.validate_connection()
        print(f"   USASpending: {'✅ Connected' if result else '❌ Failed'}")
        
        # Test actual data fetch
        if result:
            data = await usa.get_enrichment_data("SHKSNU48JHZ7")
            if "error" not in data:
                print(f"   ✅ Retrieved {data.get('federal_awards_count', 0)} awards")
        await usa.close()
    except Exception as e:
        print(f"   USASpending: ❌ Error - {e}")
    
    # Test full enrichment
    print("\n3. Testing full enrichment...")
    try:
        from src.services.enrichment_service import EnrichmentService
        service = EnrichmentService()
        await service.initialize()
        
        result = await service.enrich_company(
            "SHKSNU48JHZ7",
            "1 SYNC TECHNOLOGIES LLC"
        )
        
        print(f"   ✅ Enrichment Score: {result.get('enrichment_score', 0)}")
        print(f"   APIs used: {list(result.get('api_results', {}).keys())}")
        
        # Show successful APIs
        for api, data in result.get('api_results', {}).items():
            if data and "error" not in data and data.get("status") != "no_data":
                print(f"   ✅ {api}: Success")
            else:
                print(f"   ❌ {api}: Failed")
                
    except Exception as e:
        print(f"   ❌ Enrichment Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_integrations())
