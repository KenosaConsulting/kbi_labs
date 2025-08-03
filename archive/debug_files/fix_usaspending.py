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
