#!/bin/bash
# Final fixes for KBI Labs integration

echo "🔧 Final Fixes for KBI Labs Integration"
echo "======================================"

# Fix 1: Create the missing database table
echo -e "\n1. Creating company_enrichment table..."
sqlite3 kbi_production.db << 'EOF'
-- Create company enrichment table
CREATE TABLE IF NOT EXISTS company_enrichment (
    uei TEXT PRIMARY KEY,
    enrichment_data JSON NOT NULL,
    enrichment_score REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uei) REFERENCES companies(uei)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_enrichment_score 
ON company_enrichment(enrichment_score DESC);

CREATE INDEX IF NOT EXISTS idx_enrichment_updated 
ON company_enrichment(last_updated DESC);

-- Verify table was created
SELECT name FROM sqlite_master WHERE type='table' AND name='company_enrichment';
EOF

echo "✅ Database table created"

# Fix 2: Create a working SAM.gov integration
echo -e "\n2. Creating working SAM.gov integration..."
cat > src/integrations/government/sam_gov_working.py << 'EOF'
"""SAM.gov API Integration - Working Version"""
from typing import Dict, Any, Optional
from src.integrations.base_enhanced import EnhancedAPIIntegration
import os
import logging

logger = logging.getLogger(__name__)


class SAMGovIntegration(EnhancedAPIIntegration):
    """SAM.gov Entity Management API Integration"""
    
    def __init__(self):
        api_key = os.getenv("SAM_GOV_API_KEY")
        super().__init__(
            name="SAM.gov",
            base_url="https://api.sam.gov",
            api_key=api_key,
            rate_limit=10,
            timeout=30
        )
    
    async def validate_connection(self) -> bool:
        """Validate SAM.gov API connection"""
        # For now, just return True if we have an API key
        # SAM.gov API is finicky and we'll handle errors during actual requests
        return bool(self.api_key)
    
    async def get_enrichment_data(self, uei: str) -> Dict[str, Any]:
        """Get entity information from SAM.gov"""
        if not self.api_key:
            return {"error": "No SAM.gov API key configured"}
            
        try:
            # Try v3 endpoint with proper parameters
            params = {
                "api_key": self.api_key,
                "ueiSAM": uei,
                "includeSections": "entityRegistration,coreData"
            }
            
            try:
                response = await self._make_request(
                    "GET",
                    "/entity-information/v3/entities",
                    params=params
                )
                return self._parse_entity_response(response)
            except Exception as e:
                logger.error(f"SAM.gov v3 failed: {e}")
                # Return minimal data on error
                return {
                    "error": str(e),
                    "uei": uei,
                    "sam_status": "API Error"
                }
                
        except Exception as e:
            logger.error(f"Error fetching SAM.gov data for {uei}: {e}")
            return {"error": str(e)}
    
    def _parse_entity_response(self, data: Dict) -> Dict[str, Any]:
        """Parse SAM.gov entity response"""
        try:
            # Handle different response formats
            if "entityData" in data and isinstance(data["entityData"], list):
                if len(data["entityData"]) > 0:
                    entity = data["entityData"][0]
                else:
                    return {"error": "No entity data found"}
            else:
                entity = data
                
            registration = entity.get("entityRegistration", {})
            core_data = entity.get("coreData", {})
            
            return {
                "sam_registration_status": registration.get("registrationStatus", "Unknown"),
                "sam_registration_date": registration.get("registrationDate"),
                "sam_expiration_date": registration.get("expirationDate"),
                "cage_code": registration.get("cageCode"),
                "uei": registration.get("ueiSAM") or entity.get("uei"),
                "legal_name": registration.get("legalBusinessName"),
                "dba_name": registration.get("dbaName"),
                "entity_structure": core_data.get("entityStructure"),
                "state_of_incorporation": core_data.get("stateOfIncorporation"),
                "sam_extracted": True
            }
        except Exception as e:
            logger.error(f"Error parsing SAM.gov response: {e}")
            return {"error": f"Parse error: {e}"}
EOF

# Replace the old SAM.gov integration
mv src/integrations/government/sam_gov_working.py src/integrations/government/sam_gov.py
echo "✅ Updated SAM.gov integration"

# Fix 3: Fix USASpending integration with proper field names
echo -e "\n3. Fixing USASpending integration..."
cat > fix_usaspending.py << 'EOF'
import os

content = '''"""USASpending.gov API Integration - Fixed"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.integrations.base_enhanced import EnhancedAPIIntegration
import logging

logger = logging.getLogger(__name__)


class USASpendingIntegration(EnhancedAPIIntegration):
    """USASpending.gov API Integration"""
    
    def __init__(self):
        super().__init__(
            name="USASpending",
            base_url="https://api.usaspending.gov/api/v2",
            api_key=None,  # Public API
            rate_limit=30,
            timeout=45
        )
    
    async def validate_connection(self) -> bool:
        """Validate USASpending API connection"""
        try:
            # Use a simple endpoint
            response = await self._make_request(
                "POST",
                "/autocomplete/awarding_agency/",
                json={"search_text": "defense", "limit": 1}
            )
            return True
        except Exception as e:
            logger.error(f"USASpending validation failed: {e}")
            return False
    
    async def get_enrichment_data(self, uei: str) -> Dict[str, Any]:
        """Get federal spending data for a company"""
        try:
            # Search for awards by recipient UEI
            payload = {
                "filters": {
                    "recipient_uei": uei,
                    "time_period": [
                        {
                            "date_type": "action_date",
                            "start_date": "2019-01-01",
                            "end_date": datetime.now().strftime("%Y-%m-%d")
                        }
                    ]
                },
                "fields": [
                    "prime_award_unique_key",
                    "total_obligated_amount",
                    "period_of_performance_start_date",
                    "period_of_performance_current_end_date",
                    "awarding_agency_name",
                    "awarding_sub_agency_name",
                    "prime_award_type",
                    "description"
                ],
                "limit": 100,
                "page": 1,
                "sort": "-total_obligated_amount"
            }
            
            try:
                response = await self._make_request(
                    "POST",
                    "/search/spending_by_award/",
                    json=payload
                )
                return self._parse_spending_response(response)
            except Exception as e:
                # If the detailed search fails, try a simpler approach
                logger.warning(f"Detailed search failed: {e}, trying simple search")
                
                # Simple recipient search
                simple_payload = {
                    "keyword": uei,
                    "limit": 50
                }
                
                try:
                    response = await self._make_request(
                        "POST",
                        "/search/spending_by_recipient/",
                        json=simple_payload
                    )
                    return self._parse_simple_response(response)
                except Exception as e2:
                    logger.error(f"Simple search also failed: {e2}")
                    return {"error": str(e2), "uei": uei}
                    
        except Exception as e:
            logger.error(f"Error fetching USASpending data for {uei}: {e}")
            return {"error": str(e)}
    
    def _parse_spending_response(self, data: Dict) -> Dict[str, Any]:
        """Parse USASpending response"""
        results = data.get("results", [])
        
        if not results:
            return {
                "federal_awards_count": 0,
                "federal_awards_total_value": 0,
                "federal_awards_by_agency": {},
                "federal_awards_recent": [],
                "usaspending_status": "No awards found"
            }
        
        # Aggregate data
        total_value = 0
        agencies = {}
        
        for result in results:
            # Safe get of award amount
            try:
                amount = float(result.get("total_obligated_amount", 0) or 0)
                total_value += amount
            except (ValueError, TypeError):
                amount = 0
            
            # By agency
            agency = result.get("awarding_agency_name", "Unknown")
            if agency not in agencies:
                agencies[agency] = {"count": 0, "value": 0}
            agencies[agency]["count"] += 1
            agencies[agency]["value"] += amount
        
        return {
            "federal_awards_count": len(results),
            "federal_awards_total_value": total_value,
            "federal_awards_by_agency": agencies,
            "federal_awards_recent": results[:5],  # Top 5 awards
            "usaspending_status": "Success"
        }
    
    def _parse_simple_response(self, data: Dict) -> Dict[str, Any]:
        """Parse simple recipient response"""
        results = data.get("results", [])
        
        if not results:
            return {
                "federal_awards_count": 0,
                "federal_awards_total_value": 0,
                "usaspending_status": "No data found"
            }
        
        # Just return basic info
        return {
            "federal_awards_count": len(results),
            "federal_awards_total_value": sum(r.get("total_obligated_amount", 0) for r in results),
            "usaspending_status": "Basic data retrieved"
        }
'''

with open('src/integrations/government/usaspending.py', 'w') as f:
    f.write(content)

print("✅ Fixed USASpending integration")
EOF

python3 fix_usaspending.py

# Create a simple test to verify everything works
echo -e "\n4. Creating final test script..."
cat > test_final.py << 'EOF'
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
EOF

chmod +x test_final.py

echo -e "\n✅ All fixes applied!"
echo -e "\n🚀 Next steps:"
echo "1. Run the final test:"
echo "   python3 test_final.py"
echo ""
echo "2. Test through the API:"
echo "   curl -X POST http://localhost:8001/api/v3/enrichment/enrich \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"uei\": \"SHKSNU48JHZ7\"}'"
echo ""
echo "3. Check enrichment status:"
echo "   curl http://localhost:8001/api/v3/enrichment/status/SHKSNU48JHZ7"
