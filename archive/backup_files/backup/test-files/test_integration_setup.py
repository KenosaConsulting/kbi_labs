#!/usr/bin/env python3
"""Test script to verify integration setup"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_setup():
    print("🧪 Testing KBI Labs Integration Setup")
    print("=" * 50)
    
    # Test imports
    try:
        from integrations.base_enhanced import EnhancedAPIIntegration
        print("✅ Base integration class imported")
    except ImportError as e:
        print(f"❌ Failed to import base class: {e}")
        return
    
    try:
        from integrations.registry import integration_registry
        print("✅ Integration registry imported")
    except ImportError as e:
        print(f"❌ Failed to import registry: {e}")
        return
    
    try:
        from services.enrichment_service import EnrichmentService
        print("✅ Enrichment service imported")
    except ImportError as e:
        print(f"❌ Failed to import service: {e}")
        return
    
    # Test initialization
    print("\n📊 Testing integration initialization...")
    await integration_registry.initialize_all()
    
    integrations = integration_registry.get_all()
    print(f"\n✅ Successfully initialized {len(integrations)} integrations:")
    for name in integrations:
        print(f"   - {name}")
    
    # Cleanup
    await integration_registry.close_all()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_setup())
