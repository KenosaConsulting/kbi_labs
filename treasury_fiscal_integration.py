#!/usr/bin/env python3
"""
Treasury Fiscal Data API Integration
Provides federal budget allocation and spending intelligence for procurement predictions
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BudgetIntelligence:
    """Budget intelligence data structure"""
    agency_name: str
    fiscal_year: int
    total_budget: float
    spent_to_date: float
    remaining_budget: float
    spending_rate: float
    urgency_score: float
    optimal_timing: str

class TreasuryFiscalProcessor:
    """
    Treasury Fiscal Data API Integration
    
    Provides:
    - Federal agency budget allocations
    - Spending patterns and rates
    - Budget flush period predictions
    - Procurement timing intelligence
    """
    
    def __init__(self):
        self.base_url = "https://api.fiscaldata.treasury.gov/services/api/v1"
        self.session = None
        self.rate_limit = 1.0  # 1 second between requests
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'KBI-Labs-Procurement-Intelligence/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_agency_budget_data(self, fiscal_year: int = None) -> List[Dict[str, Any]]:
        """Get federal agency budget and spending data"""
        if fiscal_year is None:
            fiscal_year = datetime.now().year
        
        logger.info(f"Fetching agency budget data for FY {fiscal_year}")
        
        # Treasury dataset: Federal Agency Spending
        endpoint = f"{self.base_url}/accounting/od/agency_spending"
        
        params = {
            'filter': f'fiscal_year:eq:{fiscal_year}',
            'fields': 'agency_name,fiscal_year,current_month_outlay_amount,ytd_outlay_amount,budget_authority_amount',
            'format': 'json',
            'page[size]': 1000
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data.get('data', []))} agency budget records")
                    return data.get('data', [])
                else:
                    logger.error(f"Treasury API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching Treasury data: {e}")
            return []
    
    async def get_monthly_spending_trends(self, agency_name: str = None, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly spending trends for analysis"""
        logger.info(f"Fetching monthly spending trends for {agency_name or 'all agencies'}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        endpoint = f"{self.base_url}/accounting/od/agency_spending"
        
        params = {
            'filter': f'record_date:gte:{start_date.strftime("%Y-%m-%d")},record_date:lte:{end_date.strftime("%Y-%m-%d")}',
            'fields': 'agency_name,record_date,current_month_outlay_amount,ytd_outlay_amount',
            'format': 'json',
            'page[size]': 1000
        }
        
        if agency_name:
            params['filter'] += f',agency_name:eq:{agency_name}'
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"Treasury API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching spending trends: {e}")
            return []
    
    async def get_debt_and_deficit_data(self) -> List[Dict[str, Any]]:
        """Get federal debt and deficit data for economic context"""
        logger.info("Fetching federal debt and deficit data")
        
        endpoint = f"{self.base_url}/accounting/od/debt_to_penny"
        
        params = {
            'fields': 'record_date,debt_held_public_amt,intragov_hold_amt,tot_pub_debt_out_amt',
            'format': 'json',
            'sort': '-record_date',
            'page[size]': 30  # Last 30 days
        }
        
        try:
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"Treasury API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching debt data: {e}")
            return []
    
    def analyze_budget_intelligence(self, budget_data: List[Dict[str, Any]]) -> List[BudgetIntelligence]:
        """Analyze budget data to generate procurement intelligence"""
        logger.info("Analyzing budget data for procurement intelligence")
        
        intelligence = []
        
        for record in budget_data:
            try:
                agency_name = record.get('agency_name', 'Unknown')
                fiscal_year = int(record.get('fiscal_year', datetime.now().year))
                
                # Calculate budget metrics
                budget_authority = float(record.get('budget_authority_amount', 0))
                ytd_spending = float(record.get('ytd_outlay_amount', 0))
                remaining_budget = budget_authority - ytd_spending
                
                # Calculate spending rate (spending per month)
                current_month = datetime.now().month
                fiscal_month = current_month - 9 if current_month >= 10 else current_month + 3  # Fiscal year starts Oct 1
                spending_rate = ytd_spending / max(fiscal_month, 1) if fiscal_month > 0 else 0
                
                # Calculate urgency score (higher = more urgent to spend)
                months_remaining = 12 - fiscal_month
                urgency_score = remaining_budget / max(months_remaining * spending_rate, 1) if months_remaining > 0 else 10.0
                
                # Determine optimal timing
                if urgency_score > 2.0:
                    optimal_timing = "High urgency - Budget needs to be spent soon"
                elif urgency_score > 1.2:
                    optimal_timing = "Moderate urgency - Good timing for proposals"
                elif urgency_score > 0.8:
                    optimal_timing = "Normal spending pace"
                else:
                    optimal_timing = "Low urgency - Budget well managed"
                
                intelligence.append(BudgetIntelligence(
                    agency_name=agency_name,
                    fiscal_year=fiscal_year,
                    total_budget=budget_authority,
                    spent_to_date=ytd_spending,
                    remaining_budget=remaining_budget,
                    spending_rate=spending_rate,
                    urgency_score=urgency_score,
                    optimal_timing=optimal_timing
                ))
                
            except Exception as e:
                logger.error(f"Error analyzing record for {record.get('agency_name', 'Unknown')}: {e}")
                continue
        
        # Sort by urgency score (highest first)
        intelligence.sort(key=lambda x: x.urgency_score, reverse=True)
        
        logger.info(f"Generated budget intelligence for {len(intelligence)} agencies")
        return intelligence
    
    async def get_procurement_timing_intelligence(self, target_agencies: List[str] = None) -> Dict[str, Any]:
        """Get comprehensive procurement timing intelligence"""
        logger.info("Generating comprehensive procurement timing intelligence")
        
        # Get current fiscal year budget data
        budget_data = await self.get_agency_budget_data()
        
        if not budget_data:
            logger.warning("No budget data available")
            return {}
        
        # Analyze budget intelligence
        intelligence = self.analyze_budget_intelligence(budget_data)
        
        # Filter for target agencies if specified
        if target_agencies:
            intelligence = [i for i in intelligence if any(agency.lower() in i.agency_name.lower() for agency in target_agencies)]
        
        # Generate insights
        high_urgency = [i for i in intelligence if i.urgency_score > 2.0]
        moderate_urgency = [i for i in intelligence if 1.2 < i.urgency_score <= 2.0]
        
        total_budget = sum(i.total_budget for i in intelligence)
        total_remaining = sum(i.remaining_budget for i in intelligence)
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'total_agencies_analyzed': len(intelligence),
            'total_federal_budget': total_budget,
            'total_remaining_budget': total_remaining,
            'budget_utilization_rate': (total_budget - total_remaining) / total_budget if total_budget > 0 else 0,
            'high_urgency_agencies': len(high_urgency),
            'moderate_urgency_agencies': len(moderate_urgency),
            'intelligence': [
                {
                    'agency_name': i.agency_name,
                    'urgency_score': i.urgency_score,
                    'remaining_budget': i.remaining_budget,
                    'optimal_timing': i.optimal_timing,
                    'budget_utilization': (i.total_budget - i.remaining_budget) / i.total_budget if i.total_budget > 0 else 0
                }
                for i in intelligence[:20]  # Top 20 agencies
            ],
            'recommendations': {
                'immediate_targets': [i.agency_name for i in high_urgency[:5]],
                'good_timing_targets': [i.agency_name for i in moderate_urgency[:5]],
                'budget_flush_prediction': 'Q4 FY (July-September)' if datetime.now().month in [7, 8, 9] else 'Q4 FY expected high spending'
            }
        }

async def test_treasury_integration():
    """Test Treasury Fiscal Data integration"""
    print("🏛️ Testing Treasury Fiscal Data Integration...")
    
    async with TreasuryFiscalProcessor() as treasury:
        # Test basic budget data
        budget_data = await treasury.get_agency_budget_data()
        print(f"✅ Retrieved budget data for {len(budget_data)} agencies")
        
        # Test procurement timing intelligence
        intelligence = await treasury.get_procurement_timing_intelligence()
        print(f"✅ Generated intelligence for {intelligence.get('total_agencies_analyzed', 0)} agencies")
        
        # Display top insights
        if intelligence.get('intelligence'):
            print("\n🎯 Top Budget Intelligence Insights:")
            for i, agency in enumerate(intelligence['intelligence'][:5], 1):
                print(f"{i}. {agency['agency_name']}")
                print(f"   Urgency Score: {agency['urgency_score']:.2f}")
                print(f"   Remaining Budget: ${agency['remaining_budget']:,.0f}")
                print(f"   Timing: {agency['optimal_timing']}")
                print()
        
        # Display recommendations
        if intelligence.get('recommendations'):
            recs = intelligence['recommendations']
            print("📋 Procurement Recommendations:")
            print(f"   Immediate Targets: {', '.join(recs.get('immediate_targets', []))}")
            print(f"   Good Timing Targets: {', '.join(recs.get('good_timing_targets', []))}")
            print(f"   Budget Flush Period: {recs.get('budget_flush_prediction', 'N/A')}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_treasury_integration())