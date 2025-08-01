"""SBIR/STTR API Integration"""
from typing import Dict, Any, List
from src.integrations.base_enhanced import EnhancedAPIIntegration
import logging

logger = logging.getLogger(__name__)


class SBIRIntegration(EnhancedAPIIntegration):
    """SBIR/STTR Awards API Integration"""
    
    def __init__(self):
        super().__init__(
            name="SBIR",
            base_url="https://www.sbir.gov/api",
            api_key=None,  # Public API
            rate_limit=60,
            timeout=30
        )
    
    async def validate_connection(self) -> bool:
        """Validate SBIR API connection"""
        try:
            await self._make_request("GET", "/awards", params={"rows": 1})
            return True
        except Exception as e:
            logger.error(f"SBIR validation failed: {e}")
            return False
    
    async def get_enrichment_data(self, company_name: str) -> Dict[str, Any]:
        """Get SBIR/STTR awards for a company"""
        try:
            params = {
                "firm": company_name,
                "rows": 100,
                "sort": "award_date desc"
            }
            
            response = await self._make_request("GET", "/awards", params=params)
            return self._parse_sbir_response(response)
            
        except Exception as e:
            logger.error(f"Error fetching SBIR data for {company_name}: {e}")
            return {"error": str(e)}
    
    def _parse_sbir_response(self, data: Dict) -> Dict[str, Any]:
        """Parse SBIR response"""
        awards = data.get("response", {}).get("docs", [])
        
        if not awards:
            return {
                "sbir_awards_count": 0,
                "sbir_awards_total_value": 0,
                "sbir_awards_by_phase": {},
                "sbir_recent_awards": []
            }
        
        total_value = 0
        phases = {}
        
        for award in awards:
            amount = float(award.get("award_amount", 0))
            total_value += amount
            
            phase = award.get("phase", "Unknown")
            if phase not in phases:
                phases[phase] = {"count": 0, "value": 0}
            phases[phase]["count"] += 1
            phases[phase]["value"] += amount
        
        return {
            "sbir_awards_count": len(awards),
            "sbir_awards_total_value": total_value,
            "sbir_awards_by_phase": phases,
            "sbir_recent_awards": awards[:10]
        }
