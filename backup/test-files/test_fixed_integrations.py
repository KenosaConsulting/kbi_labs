#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def test_fixed():
    print("🧪 Testing Fixed Integrations")
    print("=" * 40)
    
    try:
        from src.integrations.government.sam_gov import SAMGovIntegration
        from src.integrations.government.usaspending import USASpendingIntegration
        
        # Test SAM.gov
        print("\n📊 Testing SAM.gov...")
        sam = SAMGovIntegration()
        if await sam.validate_connection():
            print("✅ SAM.gov connection successful!")
            
            # Test with a real UEI
            test_uei = "ZQGGHJH74DW7"
            data = await sam.get_enrichment_data(test_uei)
            if "error" not in data:
                print(f"✅ Retrieved data for test UEI")
                print(f"   Legal Name: {data.get('legal_name', 'N/A')}")
                print(f"   Status: {data.get('sam_registration_status', 'N/A')}")
        else:
            print("❌ SAM.gov connection failed")
        await sam.close()
        
        # Test USASpending
        print("\n📊 Testing USASpending...")
        usa = USASpendingIntegration()
        if await usa.validate_connection():
            print("✅ USASpending connection successful!")
        else:
            print("❌ USASpending connection failed")
        await usa.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed())
