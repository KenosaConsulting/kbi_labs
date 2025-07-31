# src/api/v1/endpoints/digital_gap.py
"""
Digital Gap Analyzer API endpoints
Powers the dashboard and customer-facing features
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd
from datetime import datetime

# Import your existing database session
from src.database import get_db

router = APIRouter()

# Pydantic models for API responses
class CompanyOpportunity(BaseModel):
    id: int
    organization_name: str
    city: Optional[str]
    state: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    website: Optional[str]
    uei: Optional[str]
    primary_naics_code: Optional[int]
    opportunity_score: int
    opportunity_level: str
    has_website: bool
    website_opportunity: bool

class OpportunityStats(BaseModel):
    total_companies: int
    companies_without_websites: int
    percentage_without_websites: float
    high_opportunities: int
    medium_opportunities: int
    total_market_value: int

class StateOpportunity(BaseModel):
    state: str
    companies_without_websites: int
    avg_opportunity_score: float
    market_value: int

class CityOpportunity(BaseModel):
    city: str
    state: str
    companies_without_websites: int
    avg_opportunity_score: float
    market_value: int

@router.get("/stats", response_model=OpportunityStats)
async def get_opportunity_stats(db: Session = Depends(get_db)):
    """Get overall opportunity statistics"""
    
    # Get basic counts
    total_companies = db.execute(text("SELECT COUNT(*) FROM digital_gap_companies")).scalar()
    companies_without_websites = db.execute(text("SELECT COUNT(*) FROM digital_gap_companies WHERE website_opportunity = true")).scalar()
    high_opportunities = db.execute(text("SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'HIGH'")).scalar()
    medium_opportunities = db.execute(text("SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'MEDIUM'")).scalar()
    
    percentage_without_websites = (companies_without_websites / total_companies * 100) if total_companies > 0 else 0
    total_market_value = companies_without_websites * 25000  # $25K average project
    
    return OpportunityStats(
        total_companies=total_companies,
        companies_without_websites=companies_without_websites,
        percentage_without_websites=round(percentage_without_websites, 1),
        high_opportunities=high_opportunities,
        medium_opportunities=medium_opportunities,
        total_market_value=total_market_value
    )

@router.get("/companies", response_model=List[CompanyOpportunity])
async def get_companies(
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    opportunity_level: Optional[str] = Query(None, description="Filter by opportunity level (HIGH, MEDIUM, LOW)"),
    website_opportunity: Optional[bool] = Query(None, description="Filter companies without websites"),
    min_score: Optional[int] = Query(None, description="Minimum opportunity score"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get companies with filtering and pagination"""
    
    query = "SELECT * FROM digital_gap_companies WHERE 1=1"
    params = {}
    
    if state:
        query += " AND LOWER(state) = LOWER(:state)"
        params['state'] = state
    
    if city:
        query += " AND LOWER(city) = LOWER(:city)"
        params['city'] = city
    
    if opportunity_level:
        query += " AND opportunity_level = :opportunity_level"
        params['opportunity_level'] = opportunity_level.upper()
    
    if website_opportunity is not None:
        query += " AND website_opportunity = :website_opportunity"
        params['website_opportunity'] = website_opportunity
    
    if min_score:
        query += " AND opportunity_score >= :min_score"
        params['min_score'] = min_score
    
    query += " ORDER BY opportunity_score DESC, organization_name"
    query += " LIMIT :limit OFFSET :offset"
    params['limit'] = limit
    params['offset'] = offset
    
    result = db.execute(text(query), params)
    companies = result.fetchall()
    
    return [
        CompanyOpportunity(
            id=row.id,
            organization_name=row.organization_name,
            city=row.city,
            state=row.state,
            email=row.email,
            phone_number=row.phone_number,
            website=row.website,
            uei=row.uei,
            primary_naics_code=row.primary_naics_code,
            opportunity_score=row.opportunity_score,
            opportunity_level=row.opportunity_level,
            has_website=row.has_website,
            website_opportunity=row.website_opportunity
        )
        for row in companies
    ]

@router.get("/states", response_model=List[StateOpportunity])
async def get_state_opportunities(db: Session = Depends(get_db)):
    """Get opportunity breakdown by state"""
    
    query = """
        SELECT 
            state,
            COUNT(*) as companies_without_websites,
            AVG(opportunity_score) as avg_opportunity_score
        FROM digital_gap_companies 
        WHERE website_opportunity = true AND state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY companies_without_websites DESC
        LIMIT 20
    """
    
    result = db.execute(text(query))
    states = result.fetchall()
    
    return [
        StateOpportunity(
            state=row.state,
            companies_without_websites=row.companies_without_websites,
            avg_opportunity_score=round(row.avg_opportunity_score, 1),
            market_value=row.companies_without_websites * 25000
        )
        for row in states
    ]

@router.get("/export/csv")
async def export_companies_csv(
    state: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    opportunity_level: Optional[str] = Query(None),
    website_opportunity: bool = Query(True, description="Export only companies without websites"),
    db: Session = Depends(get_db)
):
    """Export filtered companies as CSV"""
    
    query = """
        SELECT 
            organization_name,
            city,
            state,
            email,
            phone_number,
            primary_naics_code,
            opportunity_score,
            opportunity_level,
            uei,
            active_sba_certifications
        FROM digital_gap_companies 
        WHERE website_opportunity = :website_opportunity
    """
    
    params = {'website_opportunity': website_opportunity}
    
    if state:
        query += " AND LOWER(state) = LOWER(:state)"
        params['state'] = state
    
    if city:
        query += " AND LOWER(city) = LOWER(:city)"
        params['city'] = city
    
    if opportunity_level:
        query += " AND opportunity_level = :opportunity_level"
        params['opportunity_level'] = opportunity_level.upper()
    
    query += " ORDER BY opportunity_score DESC"
    
    result = db.execute(text(query), params)
    companies = result.fetchall()
    
    # Convert to CSV format
    df = pd.DataFrame([dict(row._mapping) for row in companies])
    csv_content = df.to_csv(index=False)
    
    from fastapi.responses import Response
    
    filename = f"prospects_{state or 'all'}_{opportunity_level or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
