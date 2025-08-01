#!/usr/bin/env python3
"""Minimal test for integration setup"""
import asyncio
import os

async def test_minimal():
    print("🧪 Testing KBI Labs Integration (Minimal)")
    print("=" * 50)
    
    # Check environment
    print("\n🔑 Checking API Keys:")
    sam_key = os.getenv("SAM_GOV_API_KEY", "")
    print(f"  SAM.gov API Key: {'✅ Set' if sam_key else '❌ Not set'}")
    
    # Test imports
    try:
        from src.integrations.base_enhanced import EnhancedAPIIntegration
        print("\n✅ Base integration imported successfully")
    except Exception as e:
        print(f"\n❌ Failed to import base integration: {e}")
        return
    
    try:
        from src.integrations.registry import integration_registry
        print("✅ Registry imported successfully")
    except Exception as e:
        print(f"❌ Failed to import registry: {e}")
        return
    
    try:
        from src.services.enrichment_service import EnrichmentService
        print("✅ Enrichment service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import enrichment service: {e}")
        return
    
    print("\n✅ All core components are properly installed!")
    
    if not sam_key:
        print("\n⚠️  To enable API integrations, add your API keys to .env:")
        print("   SAM_GOV_API_KEY=your-key-here")
        print("\n📚 Get SAM.gov API key from: https://open.gsa.gov/api/")

if __name__ == "__main__":
    asyncio.run(test_minimal())
