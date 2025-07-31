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
