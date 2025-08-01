"""
Simplified Companies API endpoints for enriched SMBs data
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
import logging
from ....database.connection import get_db
from ....models.enriched_smbs import EnrichedSMB
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Response models
class CompanyResponse(BaseModel):
    uei: str
    organization_name: str
    email: Optional[str]
    state: Optional[str]
    naics_code: Optional[str]
    google_reviews_rating: Optional[float]
    google_reviews_count: Optional[int]
    estimated_revenue: Optional[float]
    employee_count: Optional[int]
    succession_risk_score: Optional[float]
    digital_presence_score: Optional[float]
    
    class Config:
        from_attributes = True

@router.get("/")
async def search_companies(
    db: Session = Depends(get_db),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(10, ge=1, le=100, description="Items to return")
):
    """Search companies by state"""
    try:
        query = db.query(EnrichedSMB)
        
        if state:
            query = query.filter(EnrichedSMB.state == state)
        
        companies = query.limit(limit).all()
        
        return {"companies": companies}
        
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compass/insights")
async def get_compass_insights(
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get SMB intelligence insights"""
    try:
        base_query = db.query(EnrichedSMB)
        
        if state:
            base_query = base_query.filter(EnrichedSMB.state == state)
        
        total_companies = base_query.count()
        avg_revenue = db.query(func.avg(EnrichedSMB.estimated_revenue)).filter(
            EnrichedSMB.estimated_revenue.isnot(None)
        ).scalar() or 0
        
        high_risk_count = base_query.filter(
            EnrichedSMB.succession_risk_score >= 7
        ).count()
        
        return {
            "market_overview": {
                "total_companies": total_companies,
                "average_revenue": round(avg_revenue, 2),
                "high_succession_risk": high_risk_count,
                "risk_percentage": round((high_risk_count / total_companies * 100), 2) if total_companies > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
