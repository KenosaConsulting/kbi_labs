"""Companies API Router"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, HTTPException
from src.schemas.company import Company, CompanyDetail, CompanyList
from src.schemas.analytics import StateAnalytics
from src.services.company_service import company_service
from src.api.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/", response_model=CompanyList)
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    state: Optional[str] = None,
    search: Optional[str] = None,
    naics: Optional[str] = None,
    grade: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """List companies with optional filters"""
    try:
        return await company_service.list_companies(
            skip=skip,
            limit=limit,
            state=state,
            search=search,
            naics=naics,
            grade=grade,
            user_context=current_user
        )
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top", response_model=List[Company])
async def get_top_companies(
    limit: int = Query(100, ge=1, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """Get top companies by PE investment score"""
    try:
        return await company_service.get_top_companies(limit)
    except Exception as e:
        logger.error(f"Error getting top companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/states", response_model=List[StateAnalytics])
async def get_state_analytics(
    current_user: Dict = Depends(get_current_user)
):
    """Get state-level analytics"""
    try:
        return await company_service.get_state_analytics()
    except Exception as e:
        logger.error(f"Error getting state analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{uei}", response_model=CompanyDetail)
async def get_company(
    uei: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get company by UEI"""
    try:
        company = await company_service.get_company_by_uei(uei)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company {uei}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{uei}/enrich")
async def enrich_company(
    uei: str,
    current_user: Dict = Depends(get_current_user)
):
    """Trigger enrichment for a specific company"""
    try:
        result = await company_service.enrich_company(uei)
        return {"status": "enrichment_started", "uei": uei, "details": result}
    except Exception as e:
        logger.error(f"Error enriching company {uei}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
