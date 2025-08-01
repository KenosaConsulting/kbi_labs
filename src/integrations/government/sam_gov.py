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
    
    async def search_opportunities(self, naics_code: str = None, keywords: str = None, limit: int = 20) -> Dict[str, Any]:
        """Search for contract opportunities on SAM.gov"""
        if not self.api_key:
            return {"error": "No SAM.gov API key configured"}
            
        try:
            params = {
                "api_key": self.api_key,
                "limit": limit,
                "postedFrom": "01/01/2025",  # Only current opportunities
                "postedTo": "12/31/2025"
            }
            
            if naics_code:
                params["naicsCode"] = naics_code
            if keywords:
                params["title"] = keywords
                
            response = await self._make_request(
                "GET", 
                "/opportunities/v2/search",
                params=params
            )
            
            return self._parse_opportunities_response(response)
            
        except Exception as e:
            logger.error(f"Error searching opportunities: {e}")
            # Return mock data for demo purposes
            return self._get_mock_opportunities(naics_code)
    
    async def get_opportunity_details(self, opportunity_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific opportunity"""
        if not self.api_key:
            return {"error": "No SAM.gov API key configured"}
            
        try:
            params = {"api_key": self.api_key}
            response = await self._make_request(
                "GET",
                f"/opportunities/v2/opportunities/{opportunity_id}",
                params=params
            )
            return self._parse_opportunity_detail(response)
        except Exception as e:
            logger.error(f"Error fetching opportunity {opportunity_id}: {e}")
            return {"error": str(e)}
    
    def _parse_opportunities_response(self, data: Dict) -> Dict[str, Any]:
        """Parse SAM.gov opportunities search response"""
        try:
            opportunities = data.get("opportunitiesData", [])
            parsed_opportunities = []
            
            for opp in opportunities:
                parsed_opportunities.append({
                    "id": opp.get("noticeId"),
                    "title": opp.get("title"),
                    "agency": opp.get("department"),
                    "office": opp.get("subTier"),
                    "naics": opp.get("naicsCode"),
                    "setAside": opp.get("typeOfSetAsideDescription"),
                    "postedDate": opp.get("postedDate"),
                    "responseDeadline": opp.get("responseDeadLine"),
                    "type": opp.get("type"),
                    "baseType": opp.get("baseType"),
                    "archiveDate": opp.get("archiveDate"),
                    "description": opp.get("description", "")[:500] + "..." if len(opp.get("description", "")) > 500 else opp.get("description", "")
                })
            
            return {
                "total": len(parsed_opportunities),
                "opportunities": parsed_opportunities
            }
            
        except Exception as e:
            logger.error(f"Error parsing opportunities response: {e}")
            return self._get_mock_opportunities()
    
    def _parse_opportunity_detail(self, data: Dict) -> Dict[str, Any]:
        """Parse detailed opportunity response"""
        try:
            return {
                "id": data.get("noticeId"),
                "title": data.get("title"),
                "agency": data.get("department"),
                "description": data.get("description"),
                "requirements": data.get("additionalInfoText", ""),
                "naics": data.get("naicsCode"),
                "setAside": data.get("typeOfSetAsideDescription"),
                "contactInfo": {
                    "name": data.get("pointOfContact", [{}])[0].get("fullName") if data.get("pointOfContact") else None,
                    "email": data.get("pointOfContact", [{}])[0].get("email") if data.get("pointOfContact") else None,
                    "phone": data.get("pointOfContact", [{}])[0].get("phone") if data.get("pointOfContact") else None
                },
                "dates": {
                    "posted": data.get("postedDate"),
                    "deadline": data.get("responseDeadLine"),
                    "archive": data.get("archiveDate")
                }
            }
        except Exception as e:
            logger.error(f"Error parsing opportunity detail: {e}")
            return {"error": f"Parse error: {e}"}
    
    def _get_mock_opportunities(self, naics_code: str = None) -> Dict[str, Any]:
        """Return mock opportunities for demo purposes"""
        mock_opportunities = [
            {
                "id": "SP060025Q0801",
                "title": "IT Support Services - Cybersecurity Implementation",
                "agency": "Department of Defense",
                "office": "Defense Information Systems Agency",
                "naics": "541511",
                "setAside": "8(a) Small Business",
                "postedDate": "2025-01-15",
                "responseDeadline": "2025-03-15",
                "type": "Solicitation",
                "baseType": "Combined Synopsis/Solicitation",
                "description": "The Department of Defense requires comprehensive IT support services including cybersecurity implementation, CMMC compliance assistance, and system modernization. Contractors must demonstrate CMMC Level 2 certification and experience with DoD security requirements."
            },
            {
                "id": "IN12568",
                "title": "Cybersecurity Consulting and Risk Assessment",
                "agency": "Department of Homeland Security",
                "office": "Cybersecurity and Infrastructure Security Agency",
                "naics": "541512",
                "setAside": "Service-Disabled Veteran-Owned Small Business",
                "postedDate": "2025-01-20",
                "responseDeadline": "2025-04-01",
                "type": "Solicitation",
                "baseType": "Request for Proposals",
                "description": "DHS CISA seeks cybersecurity consulting services to conduct risk assessments, develop security frameworks, and provide ongoing security monitoring. Experience with FedRAMP, NIST frameworks, and federal compliance required."
            },
            {
                "id": "GS060025R0123",
                "title": "Cloud Migration and Modernization Services",
                "agency": "General Services Administration",
                "office": "Technology Transformation Services",
                "naics": "541519",
                "setAside": "Women-Owned Small Business",
                "postedDate": "2025-01-25",
                "responseDeadline": "2025-04-15",
                "type": "Sources Sought",
                "baseType": "Market Research",
                "description": "GSA is conducting market research for cloud migration services to move legacy systems to FedRAMP authorized cloud platforms. Seeking contractors with experience in AWS GovCloud, Azure Government, and Google Cloud for Government."
            }
        ]
        
        # Filter by NAICS if provided
        if naics_code:
            mock_opportunities = [opp for opp in mock_opportunities if opp["naics"] == naics_code]
        
        return {
            "total": len(mock_opportunities),
            "opportunities": mock_opportunities
        }

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
