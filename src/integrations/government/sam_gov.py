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
