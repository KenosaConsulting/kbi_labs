"""Analytics router"""
from fastapi import APIRouter, Depends
from typing import Dict
from src.auth.foundation import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
async def get_overview(current_user: Dict = Depends(get_current_user)):
    """Get analytics overview"""
    return {
        "total_companies": 64350,
        "total_states": 50,
        "data_quality": "high",
        "last_updated": "2025-01-15",
        "user_context": {
            "role": current_user.get("role", "unknown"),
            "type": current_user.get("type", "unknown")
        }
    }
