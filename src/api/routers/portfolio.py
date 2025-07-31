"""Portfolio API Router"""
from fastapi import APIRouter, Depends
from src.api.dependencies import get_current_user

router = APIRouter()

@router.get("/")
async def get_portfolio(current_user = Depends(get_current_user)):
    """Get user portfolio"""
    return {"message": "Portfolio endpoint - to be implemented"}
