# src/api/v1/endpoints/companies.py
"""
Companies API endpoints for DSBS data
Powers the Compass platform SMB intelligence
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
import logging
from ....database.connection import get_db
from ....models.companies import Company
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Response models
class CompanyResponse(BaseModel):
    id: int
    organization_name: str
    capabilities_narrative: Optional[str]
    contact_first_name: Optional[str]
    contact_last_name: Optional[str]
    job_title: Optional[str]
    email: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zipcode: Optional[str]
    website: Optional[str]
    phone_number: Optional[str]
    primary_naics_code: Optional[str]
    legal_structure: Optional[str]
    
    class Config:
        from_attributes = True

class CompanySearchResponse(BaseModel):
    companies: List[CompanyResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool

class IndustryStatsResponse(BaseModel):
    naics_code: str
    industry_name: str
    company_count: int
    percentage: float

@router.get("/", response_model=CompanySearchResponse)
async def search_companies(
    db: Session = Depends(get_db),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    naics_code: Optional[str] = Query(None, description="Filter by NAICS code"),
    search_term: Optional[str] = Query(None, description="Search in company names"),
    has_website: Optional[bool] = Query(None, description="Filter companies with websites"),
    has_email: Optional[bool] = Query(None, description="Filter companies with email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    Search and filter companies from the DSBS dataset
    Core endpoint for Compass platform SMB intelligence
    """
    try:
        # Build query with filters
        query = db.query(Company)
        
        if state:
            query = query.filter(Company.state.ilike(f"%{state}%"))
        
        if city:
            query = query.filter(Company.city.ilike(f"%{city}%"))
            
        if naics_code:
            query = query.filter(Company.primary_naics_code.like(f"{naics_code}%"))
            
        if search_term:
            query = query.filter(
                or_(
                    Company.organization_name.ilike(f"%{search_term}%"),
                    Company.capabilities_narrative.ilike(f"%{search_term}%")
                )
            )
            
        if has_website is not None:
            if has_website:
                query = query.filter(Company.website.isnot(None))
            else:
                query = query.filter(Company.website.is_(None))
                
        if has_email is not None:
            if has_email:
                query = query.filter(Company.email.isnot(None))
            else:
                query = query.filter(Company.email.is_(None))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        companies = query.offset(offset).limit(limit).all()
        
        # Calculate pagination info
        has_next = offset + limit < total_count
        
        return CompanySearchResponse(
            companies=companies,
            total_count=total_count,
            page=page,
            limit=limit,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Error searching companies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific company"""
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company {company_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/by-state")
async def get_companies_by_state(db: Session = Depends(get_db)):
    """Get company count statistics by state"""
    try:
        stats = db.query(
            Company.state,
            func.count(Company.id).label('count')
        ).filter(
            Company.state.isnot(None)
        ).group_by(Company.state).order_by(func.count(Company.id).desc()).all()
        
        total_companies = db.query(func.count(Company.id)).scalar()
        
        return [
            {
                "state": stat.state,
                "company_count": stat.count,
                "percentage": round((stat.count / total_companies) * 100, 2)
            }
            for stat in stats
        ]
    except Exception as e:
        logger.error(f"Error getting state stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/compass/insights")
async def get_compass_insights(
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get SMB intelligence insights for Compass platform
    This endpoint provides business intelligence for SMB market analysis
    """
    try:
        base_query = db.query(Company)
        
        if state:
            base_query = base_query.filter(Company.state.ilike(f"%{state}%"))
        
        # Key metrics
        total_companies = base_query.count()
        companies_with_websites = base_query.filter(Company.website.isnot(None)).count()
        companies_with_emails = base_query.filter(Company.email.isnot(None)).count()
        
        # Industry distribution
        industry_stats = base_query.with_entities(
            func.substr(Company.primary_naics_code, 1, 2).label('sector'),
            func.count().label('count')
        ).filter(
            Company.primary_naics_code.isnot(None)
        ).group_by('sector').order_by(func.count().desc()).limit(10).all()
        
        # Geographic distribution
        state_stats = base_query.with_entities(
            Company.state,
            func.count().label('count')
        ).filter(
            Company.state.isnot(None)
        ).group_by(Company.state).order_by(func.count().desc()).limit(10).all()
        
        return {
            "market_overview": {
                "total_companies": total_companies,
                "digital_presence": {
                    "with_websites": companies_with_websites,
                    "with_emails": companies_with_emails,
                    "website_adoption_rate": round((companies_with_websites / total_companies) * 100, 2),
                    "email_adoption_rate": round((companies_with_emails / total_companies) * 100, 2)
                }
            },
            "top_industries": [
                {"sector": stat.sector, "count": stat.count}
                for stat in industry_stats
            ],
            "top_states": [
                {"state": stat.state, "count": stat.count}
                for stat in state_stats
            ],
            "insights": {
                "market_opportunity": f"SMB market with {total_companies:,} companies",
                "digitalization_gap": f"{100 - round((companies_with_websites / total_companies) * 100, 2)}% of companies lack websites",
                "target_segments": "Focus on Professional Services and Construction sectors"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting compass insights: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
