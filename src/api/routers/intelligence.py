"""Intelligence API Router"""
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_user

router = APIRouter()

@router.get("/insights/{uei}")
async def get_company_insights(uei: str, current_user = Depends(get_current_user)):
    """Get AI-powered insights for a company"""
    return {"message": "Intelligence endpoint - to be implemented"}
