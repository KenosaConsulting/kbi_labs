"""Analytics router"""
from fastapi import APIRouter, Depends
from typing import Dict
from src.api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
async def get_overview(current_user: Dict = Depends(get_current_user)):
    """Get analytics overview"""
    return {
        "total_companies": 64350,
        "total_states": 50,
        "data_quality": "high",
        "last_updated": "2025-01-15"
    }
