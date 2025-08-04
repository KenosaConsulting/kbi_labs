"""Companies API Router - Foundation Auth Enabled"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, HTTPException
from src.auth.foundation import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/")
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
    # Foundation auth working - ready for your SMB database connection
    return {
        "status": "success",
        "message": "Foundation auth working - ready for SMB database",
        "user_context": {
            "role": current_user.get("role", "unknown"),
            "type": current_user.get("type", "unknown"),
            "authenticated": current_user.get("authenticated", False)
        },
        "filters": {
            "skip": skip,
            "limit": limit,
            "state": state,
            "search": search,
            "naics": naics,
            "grade": grade
        },
        "next_steps": [
            "Connect to your full SMB database",
            "Load your competitive analysis data",
            "Enable real SMB intelligence queries"
        ]
    }

@router.get("/health")
async def companies_health_check():
    """Health check for companies API"""
    return {
        "status": "ready",
        "message": "Companies API ready for database connection",
        "auth_system": "Foundation Auth - Operational",
        "database_status": "Awaiting SMB data connection"
    }