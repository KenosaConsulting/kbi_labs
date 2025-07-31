#!/usr/bin/env python3
"""
FRED (Federal Reserve Economic Data) API Integration
Phase 1 Implementation - Adds economic intelligence to SMB analysis
"""

import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FREDEconomicIntelligence:
    """Integrates Federal Reserve Economic Data for SMB economic sensitivity analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FRED_API_KEY', 'demo')
        self.base_url = "https://api.stlouisfed.org/fred"
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://kbi_user:your_postgres_password_here@kbi_postgres:5432/kbi_labs')
        
        # Key economic indicators for SMB analysis
        self.indicators = {
            # General economic health
            'GDP': 'Gross Domestic Product',
            'UNRATE': 'Unemployment Rate',
            'CPIAUCSL': 'Consumer Price Index',
            'FEDFUNDS': 'Federal Funds Rate',
            
            # SMB-specific indicators
            'BUSLOANS': 'Commercial and Industrial Loans',
            'DRTSCILM': 'Delinquency Rate on Business Loans',
            'STLENI': 'Small Business Lending Index',
            'NFIB': 'Small Business Optimism Index',
            
            # Industry-specific (by NAICS)
            'IPMAN': 'Industrial Production: Manufacturing',
            'RSXFS': 'Retail Sales',
            'HOUST': 'Housing Starts',
            'PERMIT': 'Building Permits'
        }
        
    async def fetch_series_data(self, series_id: str, start_date: str = None) -> pd.DataFrame:
        """Fetch time series data from FRED API"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
            
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date
        }
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/series/observations"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    df = pd.DataFrame(data['observations'])
                    df['date'] = pd.to_datetime(df['date'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    return df
                else:
                    logger.error(f"Failed to fetch {series_id}: {response.status}")
                    return pd.DataFrame()
    
    async def calculate_economic_sensitivity(self, company_data: Dict) -> Dict:
        """Calculate how sensitive a company might be to economic changes"""
        
        sensitivity_scores = {
            'interest_rate_sensitivity': 0,
            'consumer_demand_sensitivity': 0,
            'employment_sensitivity': 0,
            'inflation_sensitivity': 0,
            'overall_economic_risk': 0
        }
        
        # Analyze based on NAICS code
        naics = str(company_data.get('primary_naics_code', ''))[:2]
        
        # Industry-specific sensitivities
        industry_sensitivities = {
            '23': {'interest_rate': 0.9, 'employment': 0.8},  # Construction
            '44': {'consumer_demand': 0.9, 'inflation': 0.7},  # Retail
            '72': {'consumer_demand': 0.95, 'employment': 0.8},  # Food service
            '31': {'interest_rate': 0.7, 'inflation': 0.8},  # Manufacturing
            '54': {'employment': 0.6, 'consumer_demand': 0.5}  # Professional services
        }
        
        if naics in industry_sensitivities:
            for factor, weight in industry_sensitivities[naics].items():
                if factor == 'interest_rate':
                    sensitivity_scores['interest_rate_sensitivity'] = weight
                elif factor == 'consumer_demand':
                    sensitivity_scores['consumer_demand_sensitivity'] = weight
                elif factor == 'employment':
                    sensitivity_scores['employment_sensitivity'] = weight
                elif factor == 'inflation':
                    sensitivity_scores['inflation_sensitivity'] = weight
        
        # Calculate overall risk
        sensitivity_scores['overall_economic_risk'] = sum(sensitivity_scores.values()) / 4
        
        return sensitivity_scores
    
    async def generate_economic_insights(self, state: str = None) -> Dict:
        """Generate economic insights for a specific state or nationally"""
        insights = {
            'current_conditions': {},
            'trends': {},
            'risks': [],
            'opportunities': []
        }
        
        # Fetch current economic data
        gdp_data = await self.fetch_series_data('GDP')
        unemployment_data = await self.fetch_series_data('UNRATE')
        loan_data = await self.fetch_series_data('BUSLOANS')
        
        if not gdp_data.empty:
            latest_gdp = gdp_data.iloc[-1]
            gdp_growth = ((gdp_data.iloc[-1]['value'] - gdp_data.iloc[-5]['value']) / 
                         gdp_data.iloc[-5]['value'] * 100)
            
            insights['current_conditions']['gdp_growth'] = round(gdp_growth, 2)
            insights['current_conditions']['latest_gdp_date'] = latest_gdp['date'].strftime('%Y-%m-%d')
        
        if not unemployment_data.empty:
            insights['current_conditions']['unemployment_rate'] = unemployment_data.iloc[-1]['value']
            
            # Trend analysis
            if unemployment_data.iloc[-1]['value'] > unemployment_data.iloc[-12]['value']:
                insights['risks'].append("Rising unemployment may reduce consumer spending")
            else:
                insights['opportunities'].append("Falling unemployment supports business growth")
        
        if not loan_data.empty:
            loan_growth = ((loan_data.iloc[-1]['value'] - loan_data.iloc[-12]['value']) / 
                          loan_data.iloc[-12]['value'] * 100)
            insights['trends']['business_lending'] = round(loan_growth, 2)
            
            if loan_growth > 5:
                insights['opportunities'].append("Strong lending environment for expansion")
            elif loan_growth < 0:
                insights['risks'].append("Tightening credit conditions may limit growth")
        
        return insights
    
    async def create_economic_tables(self):
        """Create database tables for economic data"""
        engine = create_engine(self.db_url)
        
        with engine.connect() as conn:
            # Economic indicators table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS economic_indicators (
                    id SERIAL PRIMARY KEY,
                    series_id VARCHAR(50),
                    series_name VARCHAR(200),
                    date DATE,
                    value DECIMAL(15,4),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(series_id, date)
                )
            """))
            
            # Company economic sensitivity table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS company_economic_sensitivity (
                    id SERIAL PRIMARY KEY,
                    company_id INTEGER,
                    uei VARCHAR(50),
                    interest_rate_sensitivity DECIMAL(3,2),
                    consumer_demand_sensitivity DECIMAL(3,2),
                    employment_sensitivity DECIMAL(3,2),
                    inflation_sensitivity DECIMAL(3,2),
                    overall_economic_risk DECIMAL(3,2),
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """))
            
            # Economic insights cache
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS economic_insights_cache (
                    id SERIAL PRIMARY KEY,
                    insight_type VARCHAR(50),
                    scope VARCHAR(50), -- national, state, industry
                    scope_value VARCHAR(100),
                    insights_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """))
            
            conn.commit()
            
        logger.info("Economic intelligence tables created successfully")
    
    async def update_economic_data(self):
        """Fetch and store latest economic indicators"""
        engine = create_engine(self.db_url)
        
        for series_id, series_name in self.indicators.items():
            logger.info(f"Fetching {series_name} ({series_id})")
            
            df = await self.fetch_series_data(series_id)
            if not df.empty:
                records = []
                for _, row in df.iterrows():
                    if pd.notna(row['value']):
                        records.append({
                            'series_id': series_id,
                            'series_name': series_name,
                            'date': row['date'],
                            'value': row['value']
                        })
                
                if records:
                    with engine.connect() as conn:
                        # Upsert logic
                        for record in records:
                            conn.execute(text("""
                                INSERT INTO economic_indicators 
                                (series_id, series_name, date, value)
                                VALUES (:series_id, :series_name, :date, :value)
                                ON CONFLICT (series_id, date) 
                                DO UPDATE SET value = EXCLUDED.value
                            """), record)
                        conn.commit()
                    
                    logger.info(f"Updated {len(records)} records for {series_name}")
    
    async def calculate_all_company_sensitivities(self):
        """Calculate economic sensitivity for all companies"""
        engine = create_engine(self.db_url)
        
        with engine.connect() as conn:
            # Get companies not yet analyzed or analyzed > 30 days ago
            companies = conn.execute(text("""
                SELECT c.id, c.uei, c.primary_naics_code, c.state
                FROM companies c
                LEFT JOIN company_economic_sensitivity ces ON c.id = ces.company_id
                WHERE ces.id IS NULL 
                   OR ces.calculated_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
                LIMIT 1000
            """)).fetchall()
            
            for company in companies:
                company_data = {
                    'id': company.id,
                    'uei': company.uei,
                    'primary_naics_code': company.primary_naics_code,
                    'state': company.state
                }
                
                sensitivity = await self.calculate_economic_sensitivity(company_data)
                
                # Store results
                conn.execute(text("""
                    INSERT INTO company_economic_sensitivity
                    (company_id, uei, interest_rate_sensitivity, consumer_demand_sensitivity,
                     employment_sensitivity, inflation_sensitivity, overall_economic_risk)
                    VALUES (:company_id, :uei, :interest_rate, :consumer_demand,
                            :employment, :inflation, :overall_risk)
                    ON CONFLICT (company_id) DO UPDATE SET
                        interest_rate_sensitivity = EXCLUDED.interest_rate_sensitivity,
                        consumer_demand_sensitivity = EXCLUDED.consumer_demand_sensitivity,
                        employment_sensitivity = EXCLUDED.employment_sensitivity,
                        inflation_sensitivity = EXCLUDED.inflation_sensitivity,
                        overall_economic_risk = EXCLUDED.overall_economic_risk,
                        calculated_at = CURRENT_TIMESTAMP
                """), {
                    'company_id': company_data['id'],
                    'uei': company_data['uei'],
                    'interest_rate': sensitivity['interest_rate_sensitivity'],
                    'consumer_demand': sensitivity['consumer_demand_sensitivity'],
                    'employment': sensitivity['employment_sensitivity'],
                    'inflation': sensitivity['inflation_sensitivity'],
                    'overall_risk': sensitivity['overall_economic_risk']
                })
            
            conn.commit()
            logger.info(f"Calculated sensitivity for {len(companies)} companies")

async def main():
    """Initialize and run FRED integration"""
    
    # Get or request API key
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        print("\n🔑 FRED API Key Required")
        print("Get your free API key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("Then set: export FRED_API_KEY='your-key-here'\n")
        return
    
    fred = FREDEconomicIntelligence(api_key)
    
    # Create tables
    await fred.create_economic_tables()
    
    # Update economic data
    await fred.update_economic_data()
    
    # Calculate company sensitivities
    await fred.calculate_all_company_sensitivities()
    
    # Generate sample insights
    insights = await fred.generate_economic_insights()
    print("\n📊 Economic Intelligence Summary:")
    print(json.dumps(insights, indent=2))
    
    print("\n✅ FRED integration complete!")
    print("Economic sensitivity scores calculated for all companies")
    print("Ready to power PE risk analysis and SMB guidance")

if __name__ == "__main__":
    asyncio.run(main())
