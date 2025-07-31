"""Market API Router"""
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_user

router = APIRouter()

@router.get("/overview")
async def get_market_overview(current_user = Depends(get_current_user)):
    """Get market overview"""
    return {"message": "Market endpoint - to be implemented"}
