import os

# Update SAM.gov integration
content = '''"""SAM.gov API Integration"""
from typing import Dict, Any, Optional
from src.integrations.base_enhanced import EnhancedAPIIntegration
import os
import logging

logger = logging.getLogger(__name__)


class SAMGovIntegration(EnhancedAPIIntegration):
    """SAM.gov Entity Management API Integration"""
    
    def __init__(self):
        super().__init__(
            name="SAM.gov",
            base_url="https://api.sam.gov/entity-information/v3",
            api_key=os.getenv("SAM_GOV_API_KEY"),
            rate_limit=10,  # 10 requests per minute
            timeout=30
        )
    
    async def validate_connection(self) -> bool:
        """Validate SAM.gov API connection"""
        try:
            # Use a test UEI that should exist
            test_uei = "ZQGGHJH74DW7"  # This is a test UEI
            response = await self._make_request(
                "GET",
                f"/entities/{test_uei}",
                params={
                    "api_key": self.api_key,
                    "includeSections": "entityRegistration"
                }
            )
            return True
        except Exception as e:
            logger.error(f"SAM.gov validation failed: {e}")
            return False
    
    async def get_enrichment_data(self, uei: str) -> Dict[str, Any]:
        """Get entity information from SAM.gov"""
        try:
            response = await self._make_request(
                "GET",
                f"/entities/{uei}",
                params={
                    "api_key": self.api_key,
                    "includeSections": "entityRegistration,coreData,assertions,repsAndCerts"
                }
            )
            
            return self._parse_entity_response(response)
        except Exception as e:
            logger.error(f"Error fetching SAM.gov data for {uei}: {e}")
            return {"error": str(e)}
    
    def _parse_entity_response(self, data: Dict) -> Dict[str, Any]:
        """Parse SAM.gov entity response"""
        if "entityData" in data and len(data["entityData"]) > 0:
            entity = data["entityData"][0]
        else:
            entity = data
            
        registration = entity.get("entityRegistration", {})
        core_data = entity.get("coreData", {})
        assertions = entity.get("assertions", {})
        
        return {
            "sam_registration_status": registration.get("registrationStatus"),
            "sam_registration_date": registration.get("registrationDate"),
            "sam_expiration_date": registration.get("expirationDate"),
            "cage_code": registration.get("cageCode"),
            "uei": registration.get("ueiSAM"),
            "legal_name": registration.get("legalBusinessName"),
            "dba_name": registration.get("dbaName"),
            "business_types": core_data.get("businessTypes", {}).get("businessTypeList", []),
            "primary_naics": core_data.get("naics", {}).get("primaryNaics", {}).get("naicsCode"),
            "sam_certifications": assertions,
            "physical_address": core_data.get("physicalAddress", {}),
            "mailing_address": core_data.get("mailingAddress", {}),
            "congressional_district": core_data.get("congressionalDistrict"),
            "business_start_date": core_data.get("businessStartDate"),
            "entity_url": core_data.get("entityURL"),
            "sam_points_of_contact": entity.get("pointsOfContact", [])
        }
'''

with open('src/integrations/government/sam_gov.py', 'w') as f:
    f.write(content)

print("✅ Fixed SAM.gov integration")
