"""USASpending API Router"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict
import logging
from src.integrations.usaspending_integration import USASpendingAPI, get_cached_spending

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search/{uei}")
async def search_usaspending(
    uei: str,
    fiscal_year: Optional[int] = Query(None, description="Fiscal year filter"),
    use_cache: bool = Query(True, description="Use cached results")
) -> Dict:
    """
    Search USASpending.gov for federal contracts by UEI
    
    Args:
        uei: Unique Entity Identifier
        fiscal_year: Optional fiscal year filter
        use_cache: Whether to use cached results
    """
    try:
        logger.info(f"USASpending search for UEI: {uei}")
        
        if use_cache and not fiscal_year:
            # Use cached summary
            result = get_cached_spending(uei)
        else:
            # Fresh lookup
            client = USASpendingAPI()
            if fiscal_year:
                result = client.search_spending_by_recipient(uei, fiscal_year)
            else:
                result = client.get_awards_summary(uei)
        
        if result["success"]:
            return {
                "status": "success",
                "uei": uei,
                "data": result.get("summary", result)
            }
        else:
            return {
                "status": "error",
                "uei": uei,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"Error in USASpending search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{uei}")
async def get_recipient_profile(uei: str) -> Dict:
    """
    Get detailed recipient profile from USASpending.gov
    
    Args:
        uei: Unique Entity Identifier
    """
    try:
        client = USASpendingAPI()
        result = client.get_recipient_profile(uei)
        
        if result["success"]:
            return {
                "status": "success",
                "uei": uei,
                "profile": result["profile"]
            }
        else:
            return {
                "status": "error",
                "uei": uei,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"Error getting recipient profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def usaspending_health():
    """Check USASpending API connectivity"""
    try:
        client = USASpendingAPI()
        # Test with a known UEI
        test_response = client.session.get(
            f"{client.BASE_URL}/references/filter_tree/psc/",
            timeout=5
        )
        
        if test_response.status_code == 200:
            return {
                "status": "healthy",
                "service": "USASpending API",
                "endpoint": client.BASE_URL
            }
        else:
            return {
                "status": "unhealthy",
                "service": "USASpending API",
                "error": f"API returned {test_response.status_code}"
            }
    except Exception as e:
        return {
            "status": "error",
            "service": "USASpending API",
            "error": str(e)
        }
