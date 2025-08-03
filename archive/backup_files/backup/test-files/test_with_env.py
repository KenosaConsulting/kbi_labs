#!/usr/bin/env python3
"""Test integration with proper environment loading"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_with_env():
    print("🧪 Testing KBI Labs Integration with Environment")
    print("=" * 50)
    
    # Check environment variables
    print("\n🔑 Checking API Keys:")
    sam_key = os.getenv("SAM_GOV_API_KEY", "")
    census_key = os.getenv("CENSUS_API_KEY", "")
    fred_key = os.getenv("FRED_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    print(f"  SAM.gov API Key: {'✅ Set' if sam_key else '❌ Not set'} {f'({sam_key[:10]}...)' if sam_key else ''}")
    print(f"  Census API Key: {'✅ Set' if census_key else '❌ Not set'}")
    print(f"  FRED API Key: {'✅ Set' if fred_key else '❌ Not set'}")
    print(f"  OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
    
    # Import and test integrations
    print("\n📊 Testing API Integrations...")
    
    try:
        from src.integrations.registry import integration_registry
        
        # Initialize all integrations
        await integration_registry.initialize_all()
        
        # Show results
        integrations = integration_registry.get_all()
        print(f"\n✅ Successfully initialized {len(integrations)} integrations:")
        
        for name, integration in integrations.items():
            health = await integration.health_check()
            status_emoji = "✅" if health["status"] == "active" else "❌"
            print(f"   {status_emoji} {name}: {health['status']}")
            if health.get("last_error"):
                print(f"      Last error: {health['last_error']}")
        
        # Test enrichment with a real UEI
        if len(integrations) > 0:
            print("\n🧪 Testing enrichment with a sample company...")
            from src.services.enrichment_service import EnrichmentService
            
            service = EnrichmentService()
            await service.initialize()
            
            # Use a test UEI
            test_uei = "SHKSNU48JHZ7"
            test_company = "BLUE RIDGE SYSTEMS"
            
            print(f"   Testing with: {test_company} (UEI: {test_uei})")
            
            # Try to enrich
            result = await service.enrich_company(test_uei, test_company, apis=["sam_gov"])
            
            if result:
                print(f"   ✅ Enrichment completed!")
                print(f"   Score: {result.get('enrichment_score', 'N/A')}")
                
                # Show SAM.gov results if available
                sam_data = result.get("api_results", {}).get("sam_gov", {})
                if sam_data and "error" not in sam_data:
                    print(f"   SAM.gov Status: {sam_data.get('sam_registration_status', 'Unknown')}")
                    print(f"   CAGE Code: {sam_data.get('cage_code', 'N/A')}")
        
        # Close all integrations
        await integration_registry.close_all()
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n📊 Available API files in your project:")
    # List the API files found
    api_files = [
        "src/main_update.py",
        "src/main_with_static.py",
        "src/services/sam_api_enhanced.py",
        "src/services/enrichment_apis.py"
    ]
    
    for f in api_files:
        if os.path.exists(f):
            print(f"   ✅ {f}")
    
    print("\n🚀 To start your API, try one of these:")
    print("   python3 -m uvicorn src.main_update:app --reload")
    print("   python3 -m uvicorn src.main_with_static:app --reload")
    print("   python3 src/main_update.py")

if __name__ == "__main__":
    asyncio.run(test_with_env())
