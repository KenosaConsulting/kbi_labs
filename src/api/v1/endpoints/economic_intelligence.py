# src/api/v1/endpoints/economic_intelligence.py
"""
Economic Intelligence API Endpoints
Serves FRED data and economic sensitivity analysis
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

from ....database.connection import get_db

router = APIRouter()

# Response models
class EconomicIndicator(BaseModel):
    series_id: str
    series_name: str
    latest_value: float
    previous_value: float
    change_percent: float
    last_updated: datetime

class CompanyEconomicSensitivity(BaseModel):
    company_id: int
    organization_name: str
    interest_rate_sensitivity: float
    consumer_demand_sensitivity: float
    employment_sensitivity: float
    inflation_sensitivity: float
    overall_economic_risk: float
    risk_level: str  # LOW, MEDIUM, HIGH

class EconomicInsights(BaseModel):
    current_conditions: Dict
    trends: Dict
    risks: List[str]
    opportunities: List[str]
    companies_at_risk: int
    companies_positioned_well: int

class IndustryEconomicAnalysis(BaseModel):
    naics_code: str
    industry_name: str
    avg_economic_sensitivity: float
    top_risks: List[str]
    economic_outlook: str
    companies_analyzed: int

@router.get("/indicators", response_model=List[EconomicIndicator])
async def get_economic_indicators(
    db: Session = Depends(get_db),
    series_ids: Optional[str] = Query(None, description="Comma-separated series IDs")
):
    """Get current economic indicators"""
    
    query = """
        WITH latest_data AS (
            SELECT DISTINCT ON (series_id) 
                series_id, series_name, date, value
            FROM economic_indicators
            ORDER BY series_id, date DESC
        ),
        previous_data AS (
            SELECT DISTINCT ON (series_id)
                series_id, value as prev_value
            FROM economic_indicators
            WHERE date < (SELECT MAX(date) FROM economic_indicators)
            ORDER BY series_id, date DESC
        )
        SELECT 
            l.series_id,
            l.series_name,
            l.value as latest_value,
            p.prev_value as previous_value,
            ROUND(((l.value - p.prev_value) / p.prev_value * 100)::numeric, 2) as change_percent,
            l.date as last_updated
        FROM latest_data l
        LEFT JOIN previous_data p ON l.series_id = p.series_id
    """
    
    if series_ids:
        series_list = series_ids.split(',')
        series_list_str = ",".join([f"'{s}'" for s in series_list])
        query += f" WHERE l.series_id IN ({series_list_str})"
    
    results = db.execute(text(query)).fetchall()
    
    return [
        EconomicIndicator(
            series_id=r.series_id,
            series_name=r.series_name,
            latest_value=float(r.latest_value),
            previous_value=float(r.previous_value) if r.previous_value else 0,
            change_percent=float(r.change_percent) if r.change_percent else 0,
            last_updated=r.last_updated
        )
        for r in results
    ]

@router.get("/company/{company_id}/sensitivity", response_model=CompanyEconomicSensitivity)
async def get_company_economic_sensitivity(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Get economic sensitivity analysis for a specific company"""
    
    result = db.execute(text("""
        SELECT 
            c.id as company_id,
            c.organization_name,
            ces.interest_rate_sensitivity,
            ces.consumer_demand_sensitivity,
            ces.employment_sensitivity,
            ces.inflation_sensitivity,
            ces.overall_economic_risk
        FROM companies c
        JOIN company_economic_sensitivity ces ON c.id = ces.company_id
        WHERE c.id = :company_id
    """), {"company_id": company_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Company sensitivity analysis not found")
    
    # Determine risk level
    risk_score = result.overall_economic_risk
    risk_level = "LOW" if risk_score < 0.3 else "MEDIUM" if risk_score < 0.7 else "HIGH"
    
    return CompanyEconomicSensitivity(
        company_id=result.company_id,
        organization_name=result.organization_name,
        interest_rate_sensitivity=result.interest_rate_sensitivity,
        consumer_demand_sensitivity=result.consumer_demand_sensitivity,
        employment_sensitivity=result.employment_sensitivity,
        inflation_sensitivity=result.inflation_sensitivity,
        overall_economic_risk=result.overall_economic_risk,
        risk_level=risk_level
    )

@router.get("/insights", response_model=EconomicInsights)
async def get_economic_insights(
    state: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get economic insights and market conditions"""
    
    # Get current economic indicators
    indicators = db.execute(text("""
        WITH latest AS (
            SELECT DISTINCT ON (series_id) *
            FROM economic_indicators
            ORDER BY series_id, date DESC
        )
        SELECT * FROM latest
    """)).fetchall()
    
    current_conditions = {}
    for ind in indicators:
        current_conditions[ind.series_id] = {
            'value': float(ind.value),
            'name': ind.series_name
        }
    
    # Analyze trends
    trends = {}
    unemployment = next((i for i in indicators if i.series_id == 'UNRATE'), None)
    if unemployment:
        trends['unemployment_direction'] = 'rising' if unemployment.value > 4.0 else 'stable'
    
    # Count at-risk companies
    risk_query = """
        SELECT 
            COUNT(CASE WHEN overall_economic_risk >= 0.7 THEN 1 END) as high_risk,
            COUNT(CASE WHEN overall_economic_risk < 0.3 THEN 1 END) as low_risk
        FROM company_economic_sensitivity ces
        JOIN companies c ON ces.company_id = c.id
    """
    
    params = {}
    if state:
        risk_query += " WHERE c.state = :state"
        params['state'] = state
    
    risk_counts = db.execute(text(risk_query), params).fetchone()
    
    # Generate insights
    risks = []
    opportunities = []
    
    if current_conditions.get('FEDFUNDS', {}).get('value', 0) > 5:
        risks.append("High interest rates may limit business expansion and increase borrowing costs")
    
    if current_conditions.get('UNRATE', {}).get('value', 0) < 4:
        opportunities.append("Low unemployment supports consumer spending and business growth")
    
    if current_conditions.get('BUSLOANS'):
        loan_value = current_conditions['BUSLOANS']['value']
        if loan_value > 2500:  # Billions
            opportunities.append("Strong business lending environment supports expansion")
    
    return EconomicInsights(
        current_conditions=current_conditions,
        trends=trends,
        risks=risks,
        opportunities=opportunities,
        companies_at_risk=risk_counts.high_risk if risk_counts else 0,
        companies_positioned_well=risk_counts.low_risk if risk_counts else 0
    )

@router.get("/industries/analysis", response_model=List[IndustryEconomicAnalysis])
async def get_industry_economic_analysis(
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Get economic analysis by industry"""
    
    results = db.execute(text("""
        SELECT 
            SUBSTRING(c.primary_naics_code, 1, 2) as naics_2digit,
            COUNT(DISTINCT c.id) as company_count,
            AVG(ces.overall_economic_risk) as avg_sensitivity,
            AVG(ces.interest_rate_sensitivity) as avg_interest_sensitivity,
            AVG(ces.consumer_demand_sensitivity) as avg_demand_sensitivity
        FROM companies c
        JOIN company_economic_sensitivity ces ON c.id = ces.company_id
        WHERE c.primary_naics_code IS NOT NULL
        GROUP BY naics_2digit
        ORDER BY avg_sensitivity DESC
        LIMIT :limit
    """), {"limit": limit}).fetchall()
    
    # Industry names mapping
    industry_names = {
        '23': 'Construction',
        '31': 'Manufacturing',
        '44': 'Retail Trade',
        '54': 'Professional Services',
        '72': 'Food Services',
        '62': 'Health Care',
        '51': 'Information',
        '52': 'Finance and Insurance'
    }
    
    analyses = []
    for r in results:
        naics = r.naics_2digit
        risks = []
        
        if r.avg_interest_sensitivity > 0.7:
            risks.append("High sensitivity to interest rate changes")
        if r.avg_demand_sensitivity > 0.7:
            risks.append("Vulnerable to consumer spending shifts")
        
        outlook = "Stable" if r.avg_sensitivity < 0.5 else "Cautious" if r.avg_sensitivity < 0.7 else "Challenging"
        
        analyses.append(IndustryEconomicAnalysis(
            naics_code=naics,
            industry_name=industry_names.get(naics, f"Industry {naics}"),
            avg_economic_sensitivity=round(r.avg_sensitivity, 2),
            top_risks=risks,
            economic_outlook=outlook,
            companies_analyzed=r.company_count
        ))
    
    return analyses

@router.get("/alerts/high-risk-companies")
async def get_high_risk_companies(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    min_risk_score: float = 0.7,
    limit: int = 20
):
    """Get companies with high economic risk scores - useful for PE firms"""
    
    query = """
        SELECT 
            c.id,
            c.organization_name,
            c.city,
            c.state,
            c.primary_naics_code,
            ces.overall_economic_risk,
            ces.interest_rate_sensitivity,
            ces.consumer_demand_sensitivity,
            CASE 
                WHEN ces.overall_economic_risk >= 0.8 THEN 'CRITICAL'
                WHEN ces.overall_economic_risk >= 0.7 THEN 'HIGH'
                ELSE 'ELEVATED'
            END as risk_category
        FROM companies c
        JOIN company_economic_sensitivity ces ON c.id = ces.company_id
        WHERE ces.overall_economic_risk >= :min_risk
    """
    
    params = {"min_risk": min_risk_score}
    
    if state:
        query += " AND c.state = :state"
        params["state"] = state
    
    query += " ORDER BY ces.overall_economic_risk DESC LIMIT :limit"
    params["limit"] = limit
    
    results = db.execute(text(query), params).fetchall()
    
    return {
        "high_risk_companies": [
            {
                "id": r.id,
                "name": r.organization_name,
                "location": f"{r.city}, {r.state}",
                "naics": r.primary_naics_code,
                "risk_score": round(r.overall_economic_risk, 2),
                "risk_category": r.risk_category,
                "key_vulnerabilities": {
                    "interest_rates": r.interest_rate_sensitivity > 0.7,
                    "consumer_demand": r.consumer_demand_sensitivity > 0.7
                }
            }
            for r in results
        ],
        "total_count": len(results),
        "analysis_note": "Companies with high economic sensitivity may present acquisition opportunities during downturns"
    }

@router.post("/refresh-indicators")
async def refresh_economic_indicators(
    db: Session = Depends(get_db),
    api_key: Optional[str] = None
):
    """Manually refresh economic indicators (admin endpoint)"""
    
    # This would typically be protected by authentication
    # For now, we'll just return a message
    
    return {
        "message": "Economic indicator refresh initiated",
        "note": "Run the fred_integration.py script to update data"
    }
