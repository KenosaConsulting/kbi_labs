#!/usr/bin/env python3
"""Final test of integrations"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def test_final():
    print("🧪 Final Integration Test")
    print("=" * 40)
    
    # Test database
    import sqlite3
    conn = sqlite3.connect("kbi_production.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_enrichment'")
    if cursor.fetchone():
        print("✅ Database table exists")
    else:
        print("❌ Database table missing")
    conn.close()
    
    # Test enrichment service
    from src.services.enrichment_service import EnrichmentService
    
    service = EnrichmentService()
    await service.initialize()
    
    # Test with a known company
    test_uei = "SHKSNU48JHZ7"
    test_company = "1 SYNC TECHNOLOGIES LLC"
    
    print(f"\n🏢 Testing enrichment for: {test_company}")
    print(f"   UEI: {test_uei}")
    
    result = await service.enrich_company(test_uei, test_company)
    
    print(f"\n📊 Results:")
    print(f"   Enrichment Score: {result.get('enrichment_score', 0)}")
    print(f"   Timestamp: {result.get('enrichment_timestamp')}")
    
    api_results = result.get('api_results', {})
    for api, data in api_results.items():
        if data and "error" not in data:
            print(f"   ✅ {api}: Success")
            # Show some data
            if api == "usaspending" and "federal_awards_count" in data:
                print(f"      - Federal awards: {data['federal_awards_count']}")
                print(f"      - Total value: ${data.get('federal_awards_total_value', 0):,.2f}")
        else:
            error = data.get("error", "Unknown error") if data else "No data"
            print(f"   ❌ {api}: {error}")
    
    # Check if it was saved
    status = await service.get_enrichment_status(test_uei)
    print(f"\n💾 Saved to database: {status['status'] == 'enriched'}")

if __name__ == "__main__":
    asyncio.run(test_final())
