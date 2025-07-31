#!/bin/bash

deploy_census_fragmentation() {
    echo "🎯 Deploying Census Market Fragmentation Analysis..."
    
    # Step 1: Create the census integration file
    cat > census_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Census Bureau API Integration for Market Fragmentation Analysis
Phase 2 Implementation - Identifies PE roll-up opportunities
"""

import os
import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CensusMarketAnalyzer:
    """Analyzes market fragmentation using Census Bureau data for PE roll-up opportunities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('CENSUS_API_KEY', 'demo')
        self.base_url = "https://api.census.gov/data"
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://kbi_user:your_postgres_password_here@kbi_postgres:5432/kbi_labs')
        
        # Key Census datasets for business analysis
        self.datasets = {
            'cbp': {  # County Business Patterns
                'url': '/2022/cbp',
                'description': 'Establishment counts by industry and geography',
                'vars': ['ESTAB', 'EMP', 'PAYANN', 'EMPSZES']  # Establishments, Employment, Payroll, Size classes
            },
            'abscs': {  # Annual Business Survey
                'url': '/2021/abscs',
                'description': 'Company statistics by demographics',
                'vars': ['FIRMPDEMP', 'RCPPDEMP', 'PAYANN', 'YEAR']
            },
            'ase': {  # Annual Survey of Entrepreneurs
                'url': '/2021/ase',
                'description': 'Business owner demographics',
                'vars': ['OWNPDEMP', 'OWNCHAR', 'YEAR_EST']
            }
        }
        
    async def fetch_county_business_patterns(self, state: str, naics: str) -> pd.DataFrame:
        """Fetch establishment data by county and industry"""
        async with aiohttp.ClientSession() as session:
            params = {
                'get': 'ESTAB,EMP,PAYANN',
                'for': f'county:*',
                'in': f'state:{state}',
                'NAICS2017': naics,
                'key': self.api_key
            }
            
            url = f"{self.base_url}/2022/cbp"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    df = pd.DataFrame(data[1:], columns=data[0])
                    # Convert numeric columns
                    for col in ['ESTAB', 'EMP', 'PAYANN']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    return df
                else:
                    logger.error(f"Census API error: {response.status}")
                    return pd.DataFrame()
    
    def calculate_market_fragmentation(self, df: pd.DataFrame) -> Dict:
        """Calculate fragmentation metrics for PE roll-up analysis"""
        if df.empty:
            return {}
        
        # Remove null values
        df = df.dropna(subset=['ESTAB', 'EMP'])
        
        if len(df) == 0:
            return {}
        
        total_establishments = df['ESTAB'].sum()
        total_employment = df['EMP'].sum()
        
        # Calculate average employees per establishment
        avg_employees = total_employment / total_establishments if total_establishments > 0 else 0
        
        # Herfindahl-Hirschman Index (HHI) for market concentration
        # Lower HHI = more fragmented = better roll-up opportunity
        if total_establishments > 0:
            market_shares = df['ESTAB'] / total_establishments
            hhi = (market_shares ** 2).sum() * 10000
        else:
            hhi = 0
        
        # Count of small businesses (good acquisition targets)
        small_establishments = df[df['EMP'] < 50]['ESTAB'].sum()
        small_business_ratio = small_establishments / total_establishments if total_establishments > 0 else 0
        
        # Geographic dispersion (how spread out the market is)
        geographic_dispersion = len(df[df['ESTAB'] > 0]) / len(df) if len(df) > 0 else 0
        
        # Roll-up opportunity score (0-100)
        # Higher fragmentation + more small businesses + geographic spread = better opportunity
        fragmentation_score = 100 - (hhi / 100)  # Convert HHI to 0-100 scale
        small_biz_score = small_business_ratio * 100
        dispersion_score = geographic_dispersion * 100
        
        roll_up_score = (fragmentation_score * 0.4 + small_biz_score * 0.4 + dispersion_score * 0.2)
        
        return {
            'total_establishments': int(total_establishments),
            'total_employment': int(total_employment),
            'avg_employees_per_establishment': round(avg_employees, 1),
            'market_concentration_hhi': round(hhi, 2),
            'fragmentation_level': 'High' if hhi < 1500 else 'Medium' if hhi < 2500 else 'Low',
            'small_business_count': int(small_establishments),
            'small_business_ratio': round(small_business_ratio, 3),
            'geographic_dispersion': round(geographic_dispersion, 3),
            'roll_up_opportunity_score': round(roll_up_score, 1),
            'roll_up_potential': 'Excellent' if roll_up_score > 70 else 'Good' if roll_up_score > 50 else 'Limited'
        }
    
    async def analyze_industry_by_state(self, state: str, naics: str) -> Dict:
        """Comprehensive industry analysis for a state"""
        df = await self.fetch_county_business_patterns(state, naics)
        
        if df.empty:
            return {'error': 'No data available for this state/industry combination'}
        
        fragmentation = self.calculate_market_fragmentation(df)
        
        # Add top counties for expansion
        top_counties = df.nlargest(5, 'ESTAB')[['county', 'ESTAB', 'EMP']].to_dict('records')
        
        # Calculate market size
        total_payroll = df['PAYANN'].sum() * 1000  # Convert to dollars
        
        analysis = {
            **fragmentation,
            'state': state,
            'naics_code': naics,
            'market_size_annual_payroll': int(total_payroll),
            'top_counties': top_counties,
            'analysis_date': datetime.now().isoformat()
        }
        
        return analysis
    
    async def find_best_rollup_opportunities(self, naics_list: List[str], states: List[str]) -> List[Dict]:
        """Find the best roll-up opportunities across industries and states"""
        opportunities = []
        
        for state in states:
            for naics in naics_list:
                logger.info(f"Analyzing {naics} in {state}")
                analysis = await self.analyze_industry_by_state(state, naics)
                
                if 'error' not in analysis and analysis.get('roll_up_opportunity_score', 0) > 50:
                    opportunities.append(analysis)
        
        # Sort by roll-up opportunity score
        opportunities.sort(key=lambda x: x.get('roll_up_opportunity_score', 0), reverse=True)
        
        return opportunities[:10]  # Top 10 opportunities
    
    async def create_census_tables(self):
        """Create database tables for Census data"""
        engine = create_engine(self.db_url)
        
        with engine.connect() as conn:
            # Market fragmentation analysis table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS market_fragmentation_analysis (
                    id SERIAL PRIMARY KEY,
                    state VARCHAR(2),
                    naics_code VARCHAR(6),
                    industry_name VARCHAR(200),
                    total_establishments INTEGER,
                    total_employment INTEGER,
                    avg_employees_per_establishment DECIMAL(10,2),
                    market_concentration_hhi DECIMAL(10,2),
                    fragmentation_level VARCHAR(20),
                    small_business_count INTEGER,
                    small_business_ratio DECIMAL(5,3),
                    geographic_dispersion DECIMAL(5,3),
                    roll_up_opportunity_score DECIMAL(5,2),
                    roll_up_potential VARCHAR(20),
                    market_size_annual_payroll BIGINT,
                    top_counties JSONB,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(state, naics_code)
                )
            """))
            
            # Industry consolidation opportunities
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS consolidation_opportunities (
                    id SERIAL PRIMARY KEY,
                    naics_code VARCHAR(6),
                    industry_name VARCHAR(200),
                    nationwide_establishments INTEGER,
                    nationwide_fragmentation_score DECIMAL(5,2),
                    top_fragmented_states JSONB,
                    avg_acquisition_size INTEGER,
                    estimated_targets INTEGER,
                    consolidation_difficulty VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # PE roll-up targets
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS pe_rollup_targets (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER,
                    naics_code VARCHAR(6),
                    state VARCHAR(2),
                    employees INTEGER,
                    acquisition_attractiveness_score DECIMAL(5,2),
                    market_position VARCHAR(50),
                    consolidation_candidate BOOLEAN,
                    analysis_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """))
            
            conn.commit()
            
        logger.info("Census market analysis tables created successfully")
    
    async def analyze_companies_for_rollup(self):
        """Analyze existing companies for roll-up potential"""
        engine = create_engine(self.db_url)
        
        with engine.connect() as conn:
            # Get companies grouped by NAICS and state
            companies = conn.execute(text("""
                SELECT 
                    primary_naics_code,
                    state,
                    COUNT(*) as company_count,
                    STRING_AGG(CAST(id AS VARCHAR), ',') as company_ids
                FROM companies
                WHERE primary_naics_code IS NOT NULL 
                    AND state IS NOT NULL
                GROUP BY primary_naics_code, state
                HAVING COUNT(*) > 5
                ORDER BY COUNT(*) DESC
                LIMIT 50
            """)).fetchall()
            
            for row in companies:
                naics = str(row.primary_naics_code)[:6]  # Use 6-digit NAICS
                state = row.state
                
                # Get fragmentation analysis for this industry/state
                analysis = await self.analyze_industry_by_state(state, naics)
                
                if 'error' not in analysis:
                    # Store the analysis
                    conn.execute(text("""
                        INSERT INTO market_fragmentation_analysis
                        (state, naics_code, total_establishments, total_employment,
                         avg_employees_per_establishment, market_concentration_hhi,
                         fragmentation_level, small_business_count, small_business_ratio,
                         geographic_dispersion, roll_up_opportunity_score, roll_up_potential,
                         market_size_annual_payroll, top_counties)
                        VALUES (:state, :naics, :establishments, :employment,
                                :avg_emp, :hhi, :frag_level, :small_count, :small_ratio,
                                :dispersion, :score, :potential, :payroll, :counties)
                        ON CONFLICT (state, naics_code) DO UPDATE SET
                            total_establishments = EXCLUDED.total_establishments,
                            total_employment = EXCLUDED.total_employment,
                            roll_up_opportunity_score = EXCLUDED.roll_up_opportunity_score,
                            analysis_date = CURRENT_TIMESTAMP
                    """), {
                        'state': state,
                        'naics': naics,
                        'establishments': analysis.get('total_establishments', 0),
                        'employment': analysis.get('total_employment', 0),
                        'avg_emp': analysis.get('avg_employees_per_establishment', 0),
                        'hhi': analysis.get('market_concentration_hhi', 0),
                        'frag_level': analysis.get('fragmentation_level', 'Unknown'),
                        'small_count': analysis.get('small_business_count', 0),
                        'small_ratio': analysis.get('small_business_ratio', 0),
                        'dispersion': analysis.get('geographic_dispersion', 0),
                        'score': analysis.get('roll_up_opportunity_score', 0),
                        'potential': analysis.get('roll_up_potential', 'Unknown'),
                        'payroll': analysis.get('market_size_annual_payroll', 0),
                        'counties': json.dumps(analysis.get('top_counties', []))
                    })
                    
                    logger.info(f"Analyzed {naics} in {state}: Score {analysis.get('roll_up_opportunity_score', 0)}")
            
            conn.commit()

async def main():
    """Initialize and run Census integration"""
    
    # Note: Census API doesn't require a key for public data
    census = CensusMarketAnalyzer()
    
    # Create tables
    await census.create_census_tables()
    
    # Example: Find best roll-up opportunities in key industries
    target_industries = [
        '238',    # Specialty Trade Contractors
        '423',    # Merchant Wholesalers
        '541',    # Professional Services
        '561',    # Administrative Services
        '811',    # Repair and Maintenance
    ]
    
    target_states = ['FL', 'TX', 'CA', 'NY', 'IL']  # Top PE markets
    
    logger.info("Finding best roll-up opportunities...")
    opportunities = await census.find_best_rollup_opportunities(target_industries, target_states)
    
    print("\n🎯 Top PE Roll-up Opportunities:")
    for opp in opportunities[:5]:
        print(f"\n{opp['naics_code']} in {opp['state']}:")
        print(f"  Roll-up Score: {opp['roll_up_opportunity_score']}/100")
        print(f"  Total Targets: {opp['total_establishments']:,}")
        print(f"  Fragmentation: {opp['fragmentation_level']}")
        print(f"  Small Biz Ratio: {opp['small_business_ratio']:.1%}")
    
    # Analyze companies in database
    await census.analyze_companies_for_rollup()
    
    print("\n✅ Census market fragmentation analysis complete!")
    print("PE firms can now identify the best roll-up opportunities by industry and geography")

if __name__ == "__main__":
    asyncio.run(main())
EOF

    # Step 2: Create the API endpoints file  
    mkdir -p src/api/v1/endpoints
    cat > src/api/v1/endpoints/market_fragmentation.py << 'EOF'
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
        top_counties = json.loads(r.top_counties) if r.top_counties else []
        
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
EOF

    # Step 3: Update API router
    docker exec kbi_api bash -c "
    if ! grep -q 'market_fragmentation' src/api/v1/api.py; then
        sed -i 's/from .endpoints import companies, economic_intelligence,/from .endpoints import companies, economic_intelligence, market_fragmentation,/' src/api/v1/api.py
        echo 'api_router.include_router(market_fragmentation.router, prefix=\"/fragmentation\", tags=[\"fragmentation\"])' >> src/api/v1/api.py
    fi
    "
    
    # Step 4: Restart API
    docker restart kbi_api
    echo "⏳ Waiting for API to restart..."
    sleep 15
    
    # Step 5: Run the analysis
    echo "📊 Running market fragmentation analysis..."
    docker exec kbi_api python census_integration.py
    
    # Step 6: Test endpoints
    echo -e "\n🧪 Testing Market Fragmentation API..."
    
    echo -e "\n🎯 Top Roll-up Opportunities:"
    curl -s "http://localhost:8000/api/v1/fragmentation/opportunities?limit=3" | jq '.' 2>/dev/null || echo "Check if analysis completed"
    
    echo -e "\n✅ Census Market Fragmentation Analysis Complete!"
    echo "📊 PE firms can now identify the best roll-up opportunities"
}

# Run the deployment
deploy_census_fragmentation
