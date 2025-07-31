# src/api/v1/endpoints/market_fragmentation.py
"""
Market Fragmentation API Endpoints
Identifies PE roll-up opportunities using Census data
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import json

from ....database.connection import get_db

router = APIRouter()

# Response models
class MarketFragmentation(BaseModel):
    state: str
    naics_code: str
    industry_name: Optional[str]
    total_establishments: int
    total_employment: int
    avg_employees_per_establishment: float
    market_concentration_hhi: float
    fragmentation_level: str
    small_business_count: int
    small_business_ratio: float
    roll_up_opportunity_score: float
    roll_up_potential: str
    market_size_annual_payroll: int

class TopCounty(BaseModel):
    county: str
    establishments: int
    employment: int

class RollupOpportunity(BaseModel):
    rank: int
    state: str
    naics_code: str
    industry_name: str
    roll_up_score: float
    total_targets: int
    fragmentation_level: str
    market_size_millions: float
    top_counties: List[TopCounty]
    acquisition_strategy: str

class IndustryConsolidation(BaseModel):
    naics_code: str
    industry_name: str
    nationwide_establishments: int
    fragmentation_score: float
    best_states: List[Dict]
    consolidation_difficulty: str
    estimated_targets: int

class CompanyRollupCandidate(BaseModel):
    company_id: int
    company_name: str
    state: str
    employees: Optional[int]
    industry_fragmentation_score: float
    market_position: str
    acquisition_attractiveness: float
    consolidation_fit: str

@router.get("/opportunities", response_model=List[RollupOpportunity])
async def get_rollup_opportunities(
    db: Session = Depends(get_db),
    min_score: float = Query(50, description="Minimum roll-up opportunity score"),
    states: Optional[str] = Query(None, description="Comma-separated state codes"),
    industries: Optional[str] = Query(None, description="Comma-separated NAICS codes"),
    limit: int = Query(10, le=50)
):
    """Get top PE roll-up opportunities ranked by fragmentation and market size"""
    
    query = """
        WITH ranked_opportunities AS (
            SELECT 
                mfa.*,
                ROW_NUMBER() OVER (ORDER BY roll_up_opportunity_score DESC) as rank,
                CASE 
                    WHEN roll_up_opportunity_score > 80 THEN 'Platform acquisition + rapid consolidation'
                    WHEN roll_up_opportunity_score > 65 THEN 'Regional roll-up strategy'
                    ELSE 'Selective tuck-in acquisitions'
                END as acquisition_strategy
            FROM market_fragmentation_analysis mfa
            WHERE roll_up_opportunity_score >= :min_score
        """
    
    params = {"min_score": min_score}
    
    if states:
        state_list = states.split(',')
        states_str = ','.join([f"'{s}'" for s in state_list])
        query += f" AND state IN ({states_str})"
    
    if industries:
        industry_list = industries.split(',')
        industries_str = ','.join([f"'{i}'" for i in industry_list])
        query += f" AND naics_code IN ({industries_str})"
    
    query += """
        )
        SELECT * FROM ranked_opportunities
        ORDER BY rank
        LIMIT :limit
    """
    
    params["limit"] = limit
    results = db.execute(text(query), params).fetchall()
    
    # Industry name mapping
    industry_names = {
        '238': 'Specialty Trade Contractors',
        '423': 'Merchant Wholesalers', 
        '541': 'Professional Services',
        '561': 'Administrative Services',
        '811': 'Repair and Maintenance',
        '444': 'Building Material Dealers',
        '453': 'Miscellaneous Retailers',
        '624': 'Social Assistance'
    }
    
    opportunities = []
    for r in results:
        top_counties = r.top_counties if isinstance(r.top_counties, list) else json.loads(r.top_counties or "[]") if r.top_counties else []
        
        opportunities.append(RollupOpportunity(
            rank=r.rank,
            state=r.state,
            naics_code=r.naics_code,
            industry_name=industry_names.get(r.naics_code[:3], f"NAICS {r.naics_code}"),
            roll_up_score=r.roll_up_opportunity_score,
            total_targets=r.total_establishments,
            fragmentation_level=r.fragmentation_level,
            market_size_millions=round(r.market_size_annual_payroll / 1_000_000, 1),
            top_counties=[TopCounty(
                county=c.get('county', ''),
                establishments=c.get('ESTAB', 0),
                employment=c.get('EMP', 0)
            ) for c in top_counties[:3]],
            acquisition_strategy=r.acquisition_strategy
        ))
    
    return opportunities

@router.get("/analysis/{state}/{naics}", response_model=MarketFragmentation)
async def get_market_analysis(
    state: str,
    naics: str,
    db: Session = Depends(get_db)
):
    """Get detailed fragmentation analysis for a specific state and industry"""
    
    result = db.execute(text("""
        SELECT * FROM market_fragmentation_analysis
        WHERE state = :state AND naics_code = :naics
    """), {"state": state.upper(), "naics": naics}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found for this state/industry")
    
    # Get industry name
    industry_names = {
        '238': 'Specialty Trade Contractors',
        '423': 'Merchant Wholesalers',
        '541': 'Professional Services',
        '561': 'Administrative Services',
        '811': 'Repair and Maintenance'
    }
    
    return MarketFragmentation(
        state=result.state,
        naics_code=result.naics_code,
        industry_name=industry_names.get(result.naics_code[:3], f"NAICS {result.naics_code}"),
        total_establishments=result.total_establishments,
        total_employment=result.total_employment,
        avg_employees_per_establishment=result.avg_employees_per_establishment,
        market_concentration_hhi=result.market_concentration_hhi,
        fragmentation_level=result.fragmentation_level,
        small_business_count=result.small_business_count,
        small_business_ratio=result.small_business_ratio,
        roll_up_opportunity_score=result.roll_up_opportunity_score,
        roll_up_potential=result.roll_up_potential,
        market_size_annual_payroll=result.market_size_annual_payroll
    )

@router.get("/consolidation-map")
async def get_consolidation_heatmap(
    db: Session = Depends(get_db),
    naics: Optional[str] = None
):
    """Get geographic heatmap data for consolidation opportunities"""
    
    query = """
        SELECT 
            state,
            naics_code,
            roll_up_opportunity_score,
            total_establishments,
            small_business_ratio,
            fragmentation_level
        FROM market_fragmentation_analysis
        WHERE roll_up_opportunity_score > 40
    """
    
    params = {}
    if naics:
        query += " AND naics_code = :naics"
        params["naics"] = naics
    
    query += " ORDER BY state, naics_code"
    
    results = db.execute(text(query), params).fetchall()
    
    # Group by state for heatmap
    heatmap_data = {}
    for r in results:
        if r.state not in heatmap_data:
            heatmap_data[r.state] = {
                'avg_rollup_score': 0,
                'total_opportunities': 0,
                'industries': []
            }
        
        heatmap_data[r.state]['industries'].append({
            'naics': r.naics_code,
            'score': r.roll_up_opportunity_score,
            'targets': r.total_establishments
        })
        heatmap_data[r.state]['total_opportunities'] += 1
    
    # Calculate average scores
    for state, data in heatmap_data.items():
        scores = [ind['score'] for ind in data['industries']]
        data['avg_rollup_score'] = round(sum(scores) / len(scores), 1)
    
    return heatmap_data

@router.get("/candidates", response_model=List[CompanyRollupCandidate])
async def get_rollup_candidates(
    db: Session = Depends(get_db),
    state: Optional[str] = None,
    naics: Optional[str] = None,
    min_fragmentation: float = 60,
    limit: int = 20
):
    """Get companies that are good roll-up candidates based on market fragmentation"""
    
    query = """
        WITH company_scores AS (
            SELECT 
                c.id,
                c.organization_name,
                c.state,
                c.primary_naics_code,
                mfa.roll_up_opportunity_score as industry_fragmentation,
                mfa.avg_employees_per_establishment,
                CASE 
                    WHEN mfa.small_business_ratio > 0.7 THEN 'Small player - acquisition target'
                    WHEN mfa.total_establishments > 100 THEN 'Fragmented market player'
                    ELSE 'Market participant'
                END as market_position,
                CASE
                    WHEN mfa.roll_up_opportunity_score > 80 THEN 0.9
                    WHEN mfa.roll_up_opportunity_score > 65 THEN 0.7
                    ELSE 0.5
                END * 
                CASE 
                    WHEN ces.overall_economic_risk < 0.3 THEN 1.2
                    WHEN ces.overall_economic_risk < 0.5 THEN 1.0
                    ELSE 0.8
                END as acquisition_attractiveness
            FROM companies c
            LEFT JOIN market_fragmentation_analysis mfa 
                ON c.state = mfa.state 
                AND SUBSTRING(c.primary_naics_code::text, 1, 3) = SUBSTRING(mfa.naics_code, 1, 3)
            LEFT JOIN company_economic_sensitivity ces ON c.id = ces.company_id
            WHERE mfa.roll_up_opportunity_score >= :min_frag
        """
    
    params = {"min_frag": min_fragmentation}
    
    if state:
        query += " AND c.state = :state"
        params["state"] = state
        
    if naics:
        query += " AND c.primary_naics_code LIKE :naics"
        params["naics"] = f"{naics}%"
    
    query += """
        )
        SELECT 
            id as company_id,
            organization_name as company_name,
            state,
            NULL as employees,
            industry_fragmentation as industry_fragmentation_score,
            market_position,
            ROUND(acquisition_attractiveness::numeric, 2) as acquisition_attractiveness,
            CASE 
                WHEN acquisition_attractiveness > 0.8 THEN 'High priority target'
                WHEN acquisition_attractiveness > 0.6 THEN 'Good consolidation fit'
                ELSE 'Potential target'
            END as consolidation_fit
        FROM company_scores
        ORDER BY acquisition_attractiveness DESC
        LIMIT :limit
    """
    
    params["limit"] = limit
    results = db.execute(text(query), params).fetchall()
    
    return [
        CompanyRollupCandidate(
            company_id=r.company_id,
            company_name=r.company_name,
            state=r.state,
            employees=r.employees,
            industry_fragmentation_score=r.industry_fragmentation_score,
            market_position=r.market_position,
            acquisition_attractiveness=r.acquisition_attractiveness,
            consolidation_fit=r.consolidation_fit
        )
        for r in results
    ]

@router.get("/insights/by-industry")
async def get_industry_consolidation_insights(
    db: Session = Depends(get_db)
):
    """Get consolidation insights grouped by industry"""
    
    results = db.execute(text("""
        SELECT 
            SUBSTRING(naics_code, 1, 3) as industry_group,
            COUNT(DISTINCT state) as states_analyzed,
            AVG(roll_up_opportunity_score) as avg_opportunity_score,
            SUM(total_establishments) as total_establishments,
            AVG(small_business_ratio) as avg_small_biz_ratio,
            MAX(roll_up_opportunity_score) as best_opportunity_score,
            STRING_AGG(
                CASE 
                    WHEN roll_up_opportunity_score = MAX(roll_up_opportunity_score) OVER (PARTITION BY SUBSTRING(naics_code, 1, 3))
                    THEN state 
                END, ', '
            ) as best_states
        FROM market_fragmentation_analysis
        GROUP BY industry_group
        HAVING AVG(roll_up_opportunity_score) > 50
        ORDER BY avg_opportunity_score DESC
    """)).fetchall()
    
    industry_names = {
        '238': 'Specialty Trade Contractors',
        '423': 'Merchant Wholesalers',
        '541': 'Professional Services',
        '561': 'Administrative Services',
        '811': 'Repair and Maintenance',
        '444': 'Building Material Dealers',
        '453': 'Miscellaneous Retailers'
    }
    
    insights = []
    for r in results:
        insights.append({
            'industry_code': r.industry_group,
            'industry_name': industry_names.get(r.industry_group, f"NAICS {r.industry_group}"),
            'consolidation_opportunity': 'High' if r.avg_opportunity_score > 70 else 'Medium',
            'states_with_data': r.states_analyzed,
            'total_potential_targets': r.total_establishments,
            'avg_fragmentation_score': round(r.avg_opportunity_score, 1),
            'best_state': r.best_states,
            'small_business_dominance': round(r.avg_small_biz_ratio * 100, 1),
            'pe_strategy': 'Platform + bolt-ons' if r.avg_opportunity_score > 75 else 'Regional consolidation'
        })
    
    return {
        'summary': f"Found {len(insights)} industries ripe for consolidation",
        'top_opportunities': insights[:5],
        'methodology': 'Based on market fragmentation, small business ratios, and geographic dispersion'
    }

@router.post("/analyze-new-market")
async def analyze_new_market(
    state: str,
    naics: str,
    db: Session = Depends(get_db)
):
    """Trigger analysis for a new state/industry combination"""
    
    # This would typically call the census_integration.py analyze function
    # For now, return a message
    
    return {
        "message": f"Analysis requested for {naics} in {state}",
        "note": "Run census_integration.py to fetch and analyze new market data",
        "existing_data_check": f"Use GET /api/v1/fragmentation/analysis/{state}/{naics} to check if data exists"
    }
