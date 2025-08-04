#!/usr/bin/env python3
"""
Budget & Program Office Intelligence Analyzer
Deep Government Financial and Organizational Intelligence

This module provides granular analysis of government program offices, their budgets,
spending patterns, and procurement behaviors to guide SMB opportunity targeting.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import aiohttp
import re
from decimal import Decimal

logger = logging.getLogger(__name__)

class BudgetCategory(Enum):
    PERSONNEL = "Personnel Compensation and Benefits"
    TRAVEL = "Travel and Transportation"
    RENT = "Rent, Communications, and Utilities"
    PRINTING = "Printing and Reproduction"
    SERVICES = "Other Services from Non-Federal Sources"
    SUPPLIES = "Supplies and Materials"
    EQUIPMENT = "Equipment"
    GRANTS = "Grants, Subsidies, and Contributions"
    INSURANCE = "Insurance Claims and Indemnities"

class ContractType(Enum):
    FFP = "Firm Fixed Price"
    CPFF = "Cost Plus Fixed Fee"
    CPIF = "Cost Plus Incentive Fee"
    IDIQ = "Indefinite Delivery/Indefinite Quantity"
    GSA_SCHEDULE = "GSA Schedule"
    BPA = "Blanket Purchase Agreement"
    DELIVERY_ORDER = "Delivery Order"
    TASK_ORDER = "Task Order"

@dataclass
class BudgetLineItem:
    """Detailed budget line item analysis"""
    appropriation_code: str
    appropriation_title: str
    fiscal_year: int
    
    # Financial Details
    budget_authority: float
    outlays: float
    obligations: float
    unobligated_balance: float
    
    # Breakdown Analysis
    object_class_breakdown: Dict[str, float]  # by object class (personnel, travel, etc.)
    program_activity_breakdown: Dict[str, float]  # by program activity
    
    # Execution Intelligence
    execution_rate: float  # % of budget actually spent
    burn_rate_monthly: List[float]  # monthly spending pattern
    seasonal_patterns: Dict[str, float]  # Q1, Q2, Q3, Q4 spending
    
    # Procurement Intelligence
    procurement_percentage: float  # % that goes to contracts
    small_business_percentage: float
    competitive_percentage: float
    
    # Trend Analysis
    year_over_year_change: float
    three_year_trend: str  # "increasing", "decreasing", "stable"
    volatility_score: float  # budget stability measure

@dataclass
class ProgramOfficeDetails:
    """Comprehensive program office intelligence"""
    office_symbol: str
    office_name: str
    parent_organization: str
    
    # Organizational Intelligence
    office_type: str  # "Program Office", "Staff Office", "Field Office"
    mission_statement: str
    core_responsibilities: List[str]
    geographic_scope: List[str]
    
    # Personnel Intelligence
    authorized_positions: int
    current_staffing: int
    staffing_level: float  # current/authorized
    key_positions: List[Dict[str, str]]
    
    # Budget Intelligence
    total_budget_authority: float
    budget_line_items: List[BudgetLineItem]
    major_programs: List[Dict[str, Any]]
    
    # Procurement Intelligence
    annual_procurement_volume: float
    typical_contract_sizes: Dict[str, Tuple[float, float]]  # min, max by type
    preferred_contract_vehicles: List[str]
    procurement_timing_patterns: Dict[str, List[str]]  # by month/quarter
    
    # Performance Intelligence
    performance_metrics: Dict[str, Any]
    strategic_objectives: List[str]
    current_initiatives: List[Dict[str, Any]]
    modernization_projects: List[Dict[str, Any]]
    
    # Risk Intelligence
    budget_risks: List[str]
    operational_challenges: List[str]
    dependency_analysis: Dict[str, List[str]]

@dataclass
class SpendingPattern:
    """Detailed spending pattern analysis"""
    pattern_type: str  # "monthly", "quarterly", "seasonal", "cyclical"
    
    # Timing Intelligence
    peak_spending_periods: List[str]
    low_spending_periods: List[str]
    procurement_windows: List[Dict[str, str]]
    planning_cycles: Dict[str, str]
    
    # Volume Intelligence
    average_contract_size: float
    contract_size_distribution: Dict[str, int]  # size ranges and counts
    spending_velocity: float  # contracts per month
    
    # Competitive Intelligence
    incumbent_retention_rate: float
    new_vendor_success_rate: float
    small_business_participation: float
    competition_intensity: float

class BudgetProgramAnalyzer:
    """
    Advanced analyzer for government budget and program office intelligence
    Provides deep insights into spending patterns, organizational structure, and opportunity timing
    """
    
    def __init__(self):
        self.data_sources = {
            'usaspending': 'https://api.usaspending.gov/api/v2/',
            'treasury': 'https://api.fiscaldata.treasury.gov/services/api/v1/',
            'sam_gov': 'https://api.sam.gov/data-services/v1/',
            'performance_gov': 'https://api.performance.gov/api/v1/',
            'cio_gov': 'https://api.cio.gov/v1/',
            'max_gov': 'https://max.omb.gov/api/beta/'
        }
        
        # Budget analysis components
        self.budget_parser = FederalBudgetParser()
        self.spending_analyzer = SpendingPatternAnalyzer()
        self.procurement_intel = ProcurementIntelligenceEngine()
        self.org_mapper = OrganizationalMapper()
    
    async def analyze_program_office(
        self, 
        agency_code: str, 
        office_code: str,
        fiscal_years: List[int] = None
    ) -> ProgramOfficeDetails:
        """
        Comprehensive analysis of specific program office
        
        Args:
            agency_code: Agency identifier (e.g., '9700' for DoD)
            office_code: Office identifier within agency
            fiscal_years: List of fiscal years to analyze (default: last 3 years)
            
        Returns:
            Detailed program office intelligence
        """
        
        if fiscal_years is None:
            current_fy = self._get_current_fiscal_year()
            fiscal_years = [current_fy - 2, current_fy - 1, current_fy]
        
        logger.info(f"Analyzing program office {office_code} in agency {agency_code}")
        
        try:
            # 1. Organizational Intelligence
            org_intel = await self._gather_organizational_intelligence(agency_code, office_code)
            
            # 2. Budget Analysis
            budget_analysis = await self._analyze_office_budget(
                agency_code, office_code, fiscal_years
            )
            
            # 3. Procurement Intelligence
            procurement_intel = await self._analyze_procurement_patterns(
                agency_code, office_code, fiscal_years
            )
            
            # 4. Performance Intelligence
            performance_intel = await self._gather_performance_intelligence(
                agency_code, office_code
            )
            
            # 5. Risk Assessment
            risk_intel = await self._assess_office_risks(agency_code, office_code)
            
            # 6. Personnel Intelligence
            personnel_intel = await self._analyze_personnel_structure(agency_code, office_code)
            
            # Compile comprehensive office details
            office_details = ProgramOfficeDetails(
                office_symbol=office_code,
                office_name=org_intel['office_name'],
                parent_organization=org_intel['parent_org'],
                office_type=org_intel['office_type'],
                mission_statement=org_intel['mission'],
                core_responsibilities=org_intel['responsibilities'],
                geographic_scope=org_intel['geographic_scope'],
                authorized_positions=personnel_intel['authorized'],
                current_staffing=personnel_intel['current'],
                staffing_level=personnel_intel['staffing_ratio'],
                key_positions=personnel_intel['key_positions'],
                total_budget_authority=budget_analysis['total_budget'],
                budget_line_items=budget_analysis['line_items'],
                major_programs=budget_analysis['major_programs'],
                annual_procurement_volume=procurement_intel['annual_volume'],
                typical_contract_sizes=procurement_intel['contract_sizes'],
                preferred_contract_vehicles=procurement_intel['preferred_vehicles'],
                procurement_timing_patterns=procurement_intel['timing_patterns'],
                performance_metrics=performance_intel['metrics'],
                strategic_objectives=performance_intel['objectives'],
                current_initiatives=performance_intel['initiatives'],
                modernization_projects=performance_intel['modernization'],
                budget_risks=risk_intel['budget_risks'],
                operational_challenges=risk_intel['operational_challenges'],
                dependency_analysis=risk_intel['dependencies']
            )
            
            logger.info(f"Program office analysis complete: {office_details.office_name}")
            return office_details
            
        except Exception as e:
            logger.error(f"Error analyzing program office: {str(e)}")
            raise
    
    async def _analyze_office_budget(
        self, 
        agency_code: str, 
        office_code: str, 
        fiscal_years: List[int]
    ) -> Dict[str, Any]:
        """Detailed budget analysis for program office"""
        
        budget_data = {}
        line_items = []
        
        for fiscal_year in fiscal_years:
            
            # Fetch budget data from Treasury
            treasury_data = await self._fetch_treasury_budget_data(
                agency_code, office_code, fiscal_year
            )
            
            # Fetch obligations data from USASpending
            spending_data = await self._fetch_usaspending_obligations(
                agency_code, office_code, fiscal_year
            )
            
            # Parse and analyze budget line items
            fy_line_items = await self._parse_budget_line_items(
                treasury_data, spending_data, fiscal_year
            )
            
            line_items.extend(fy_line_items)
        
        # Calculate total budget and trends
        total_budget = sum([item.budget_authority for item in line_items])
        major_programs = await self._identify_major_programs(line_items)
        
        budget_data = {
            'total_budget': total_budget,
            'line_items': line_items,
            'major_programs': major_programs
        }
        
        return budget_data
    
    async def _fetch_treasury_budget_data(
        self, 
        agency_code: str, 
        office_code: str, 
        fiscal_year: int
    ) -> Dict[str, Any]:
        """Fetch detailed budget data from Treasury API"""
        
        async with aiohttp.ClientSession() as session:
            
            # Treasury Fiscal Service API call
            url = f"{self.data_sources['treasury']}accounting/od/outlays"
            params = {
                'filter': f'reporting_fiscal_year:eq:{fiscal_year},agency_code:eq:{agency_code}',
                'fields': 'agency_code,bureau_code,account_code,account_title,budget_authority_amount,outlay_amount',
                'sort': '-budget_authority_amount'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.warning(f"Treasury API error {response.status} for {agency_code}")
                    return []
    
    async def _fetch_usaspending_obligations(
        self, 
        agency_code: str, 
        office_code: str, 
        fiscal_year: int
    ) -> Dict[str, Any]:
        """Fetch spending obligations from USASpending API"""
        
        async with aiohttp.ClientSession() as session:
            
            url = f"{self.data_sources['usaspending']}search/spending_by_award/"
            
            payload = {
                "filters": {
                    "agencies": [{"type": "awarding", "tier": "toptier", "code": agency_code}],
                    "time_period": [{"start_date": f"{fiscal_year}-10-01", "end_date": f"{fiscal_year+1}-09-30"}]
                },
                "fields": [
                    "Award ID", "Recipient Name", "Award Amount", 
                    "Award Type", "Awarding Agency", "Awarding Sub Agency",
                    "Contract Award Type", "NAICS Code", "NAICS Description"
                ],
                "sort": "Award Amount",
                "order": "desc",
                "limit": 500
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    logger.warning(f"USASpending API error {response.status}")
                    return []
    
    async def _parse_budget_line_items(
        self, 
        treasury_data: List[Dict], 
        spending_data: List[Dict], 
        fiscal_year: int
    ) -> List[BudgetLineItem]:
        """Parse and enrich budget line items with detailed analysis"""
        
        line_items = []
        
        for budget_item in treasury_data:
            
            # Calculate execution metrics
            budget_authority = float(budget_item.get('budget_authority_amount', 0))
            outlays = float(budget_item.get('outlay_amount', 0))
            execution_rate = (outlays / budget_authority) if budget_authority > 0 else 0
            
            # Analyze related spending patterns
            related_spending = self._find_related_spending(budget_item, spending_data)
            procurement_analysis = self._analyze_procurement_component(related_spending)
            
            # Calculate trend analysis
            trend_analysis = await self._calculate_budget_trends(budget_item, fiscal_year)
            
            # Create detailed line item
            line_item = BudgetLineItem(
                appropriation_code=budget_item.get('account_code', ''),
                appropriation_title=budget_item.get('account_title', ''),
                fiscal_year=fiscal_year,
                budget_authority=budget_authority,
                outlays=outlays,
                obligations=procurement_analysis['total_obligations'],
                unobligated_balance=budget_authority - outlays,
                object_class_breakdown=procurement_analysis['object_class_breakdown'],
                program_activity_breakdown=procurement_analysis['program_breakdown'],
                execution_rate=execution_rate,
                burn_rate_monthly=trend_analysis['monthly_burn_rate'],
                seasonal_patterns=trend_analysis['seasonal_patterns'],
                procurement_percentage=procurement_analysis['procurement_percentage'],
                small_business_percentage=procurement_analysis['small_business_percentage'],
                competitive_percentage=procurement_analysis['competitive_percentage'],
                year_over_year_change=trend_analysis['yoy_change'],
                three_year_trend=trend_analysis['three_year_trend'],
                volatility_score=trend_analysis['volatility_score']
            )
            
            line_items.append(line_item)
        
        return line_items
    
    async def _analyze_procurement_patterns(
        self, 
        agency_code: str, 
        office_code: str, 
        fiscal_years: List[int]
    ) -> Dict[str, Any]:
        """Analyze detailed procurement patterns and behaviors"""
        
        procurement_intel = {}
        
        # Fetch procurement data across fiscal years
        all_contracts = []
        for fiscal_year in fiscal_years:
            contracts = await self._fetch_office_contracts(agency_code, office_code, fiscal_year)
            all_contracts.extend(contracts)
        
        # Analyze contract patterns
        volume_analysis = self._analyze_procurement_volume(all_contracts)
        timing_analysis = self._analyze_procurement_timing(all_contracts)
        vehicle_analysis = self._analyze_contract_vehicles(all_contracts)
        size_analysis = self._analyze_contract_sizes(all_contracts)
        
        procurement_intel = {
            'annual_volume': volume_analysis['annual_average'],
            'contract_sizes': size_analysis['size_ranges'],
            'preferred_vehicles': vehicle_analysis['top_vehicles'],
            'timing_patterns': timing_analysis['patterns']
        }
        
        return procurement_intel
    
    def _analyze_procurement_volume(self, contracts: List[Dict]) -> Dict[str, Any]:
        """Analyze procurement volume patterns"""
        
        if not contracts:
            return {'annual_average': 0, 'trend': 'no_data'}
        
        # Group by fiscal year
        volume_by_year = {}
        for contract in contracts:
            fy = self._extract_fiscal_year(contract.get('award_date'))
            if fy not in volume_by_year:
                volume_by_year[fy] = 0
            volume_by_year[fy] += float(contract.get('award_amount', 0))
        
        # Calculate statistics
        annual_volumes = list(volume_by_year.values())
        annual_average = np.mean(annual_volumes) if annual_volumes else 0
        trend = self._calculate_trend(annual_volumes)
        
        return {
            'annual_average': annual_average,
            'by_year': volume_by_year,
            'trend': trend,
            'volatility': np.std(annual_volumes) if len(annual_volumes) > 1 else 0
        }
    
    def _analyze_procurement_timing(self, contracts: List[Dict]) -> Dict[str, Any]:
        """Analyze when procurement typically occurs"""
        
        timing_patterns = {
            'by_month': {str(i): 0 for i in range(1, 13)},
            'by_quarter': {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0},
            'seasonal_trends': {}
        }
        
        for contract in contracts:
            award_date = contract.get('award_date')
            if award_date:
                try:
                    date_obj = datetime.strptime(award_date, '%Y-%m-%d')
                    month = str(date_obj.month)
                    quarter = f"Q{(date_obj.month - 1) // 3 + 1}"
                    
                    timing_patterns['by_month'][month] += 1
                    timing_patterns['by_quarter'][quarter] += 1
                    
                except ValueError:
                    continue
        
        # Identify peak periods
        peak_month = max(timing_patterns['by_month'], key=timing_patterns['by_month'].get)
        peak_quarter = max(timing_patterns['by_quarter'], key=timing_patterns['by_quarter'].get)
        
        timing_patterns['peak_month'] = peak_month
        timing_patterns['peak_quarter'] = peak_quarter
        
        return {'patterns': timing_patterns}
    
    def _analyze_contract_vehicles(self, contracts: List[Dict]) -> Dict[str, Any]:
        """Analyze preferred contract vehicles and mechanisms"""
        
        vehicle_usage = {}
        
        for contract in contracts:
            vehicle = contract.get('contract_award_type', 'Unknown')
            if vehicle not in vehicle_usage:
                vehicle_usage[vehicle] = {'count': 0, 'total_value': 0}
            
            vehicle_usage[vehicle]['count'] += 1
            vehicle_usage[vehicle]['total_value'] += float(contract.get('award_amount', 0))
        
        # Sort by usage frequency and value
        top_vehicles = sorted(
            vehicle_usage.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:5]
        
        return {
            'vehicle_usage': vehicle_usage,
            'top_vehicles': [vehicle[0] for vehicle in top_vehicles]
        }
    
    def _analyze_contract_sizes(self, contracts: List[Dict]) -> Dict[str, Any]:
        """Analyze typical contract size ranges"""
        
        amounts = [float(contract.get('award_amount', 0)) for contract in contracts if contract.get('award_amount')]
        
        if not amounts:
            return {'size_ranges': {}, 'statistics': {}}
        
        # Define size categories
        size_categories = {
            'Micro ($0-$10K)': (0, 10000),
            'Small ($10K-$250K)': (10000, 250000),
            'Medium ($250K-$1M)': (250000, 1000000),
            'Large ($1M-$10M)': (1000000, 10000000),
            'Major ($10M+)': (10000000, float('inf'))
        }
        
        size_distribution = {}
        for category, (min_val, max_val) in size_categories.items():
            count = len([amt for amt in amounts if min_val <= amt < max_val])
            size_distribution[category] = count
        
        # Calculate statistics
        statistics = {
            'average': np.mean(amounts),
            'median': np.median(amounts),
            'min': min(amounts),
            'max': max(amounts),
            'std_dev': np.std(amounts)
        }
        
        return {
            'size_ranges': size_distribution,
            'statistics': statistics
        }
    
    def _get_current_fiscal_year(self) -> int:
        """Calculate current federal fiscal year"""
        today = date.today()
        if today.month >= 10:  # FY starts Oct 1
            return today.year + 1
        else:
            return today.year
    
    def _extract_fiscal_year(self, date_string: str) -> int:
        """Extract fiscal year from date string"""
        try:
            date_obj = datetime.strptime(date_string, '%Y-%m-%d')
            if date_obj.month >= 10:
                return date_obj.year + 1
            else:
                return date_obj.year
        except (ValueError, TypeError):
            return self._get_current_fiscal_year()

class SpendingPatternAnalyzer:
    """Specialized analyzer for government spending patterns"""
    
    def analyze_spending_patterns(
        self, 
        contracts: List[Dict], 
        fiscal_years: List[int]
    ) -> SpendingPattern:
        """Analyze detailed spending patterns"""
        
        # Timing analysis
        timing_analysis = self._analyze_timing_patterns(contracts)
        
        # Volume analysis  
        volume_analysis = self._analyze_volume_patterns(contracts)
        
        # Competitive analysis
        competitive_analysis = self._analyze_competitive_patterns(contracts)
        
        return SpendingPattern(
            pattern_type="comprehensive",
            peak_spending_periods=timing_analysis['peak_periods'],
            low_spending_periods=timing_analysis['low_periods'],
            procurement_windows=timing_analysis['procurement_windows'],
            planning_cycles=timing_analysis['planning_cycles'],
            average_contract_size=volume_analysis['average_size'],
            contract_size_distribution=volume_analysis['size_distribution'],
            spending_velocity=volume_analysis['velocity'],
            incumbent_retention_rate=competitive_analysis['retention_rate'],
            new_vendor_success_rate=competitive_analysis['new_vendor_rate'],
            small_business_participation=competitive_analysis['small_business_rate'],
            competition_intensity=competitive_analysis['competition_score']
        )

class FederalBudgetParser:
    """Parser for federal budget documents and data"""
    
    def parse_budget_justification(self, document_path: str) -> Dict[str, Any]:
        """Parse congressional budget justification documents"""
        # Implementation for parsing budget justifications
        pass

class ProcurementIntelligenceEngine:
    """Engine for procurement-specific intelligence"""
    
    def analyze_procurement_intelligence(self, office_data: Dict) -> Dict[str, Any]:
        """Analyze procurement-specific intelligence"""
        # Implementation for procurement intelligence
        pass

class OrganizationalMapper:
    """Mapper for organizational structure and relationships"""
    
    def map_organizational_relationships(self, agency_code: str) -> Dict[str, Any]:
        """Map organizational relationships and hierarchy"""
        # Implementation for organizational mapping
        pass

# Example usage
async def main():
    """Example: Analyze a specific program office"""
    
    analyzer = BudgetProgramAnalyzer()
    
    # Analyze Air Force Research Laboratory (AFRL)
    afrl_details = await analyzer.analyze_program_office(
        agency_code='5700',  # Air Force
        office_code='AFRL',  # Research Laboratory
        fiscal_years=[2022, 2023, 2024]
    )
    
    print(f"AFRL Analysis Complete:")
    print(f"- Total Budget: ${afrl_details.total_budget_authority:,.0f}")
    print(f"- Annual Procurement: ${afrl_details.annual_procurement_volume:,.0f}")
    print(f"- Staffing Level: {afrl_details.staffing_level:.1%}")
    print(f"- Budget Line Items: {len(afrl_details.budget_line_items)}")

if __name__ == "__main__":
    asyncio.run(main())