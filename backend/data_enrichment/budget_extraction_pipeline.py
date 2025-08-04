#!/usr/bin/env python3
"""
Budget Data Extraction Pipeline
Advanced Government Budget Intelligence System

This pipeline extracts, processes, and analyzes government budget data from multiple sources
to provide granular insights into agency spending patterns, procurement opportunities, and budget trends.
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import re
import xml.etree.ElementTree as ET
from decimal import Decimal
import ssl
import certifi

logger = logging.getLogger(__name__)

class BudgetCategory(Enum):
    PERSONNEL = "Personnel Compensation and Benefits"
    CONTRACTUAL = "Contractual Services"
    EQUIPMENT = "Equipment"
    SUPPLIES = "Supplies and Materials"
    TRAVEL = "Travel and Transportation"
    RENT = "Rent, Communications, and Utilities"
    GRANTS = "Grants, Subsidies, and Contributions"
    OTHER = "Other"

class AppropriationType(Enum):
    DISCRETIONARY = "Discretionary"
    MANDATORY = "Mandatory"
    SUPPLEMENTAL = "Supplemental"

@dataclass
class BudgetLineItem:
    """Detailed budget line item with comprehensive analysis"""
    
    # Basic Identification
    account_code: str
    account_title: str
    appropriation_code: str
    fiscal_year: int
    
    # Financial Data
    budget_authority: Decimal
    outlays: Decimal
    obligations: Decimal
    unobligated_balance: Decimal
    
    # Classification
    budget_category: BudgetCategory
    appropriation_type: AppropriationType
    object_class: str
    program_activity: str
    
    # Analysis Data
    execution_rate: float  # outlays / budget_authority
    obligation_rate: float  # obligations / budget_authority
    burn_rate_monthly: List[float]  # monthly spending pattern
    
    # Trend Analysis
    previous_year_amount: Optional[Decimal] = None
    year_over_year_change: Optional[float] = None
    three_year_trend: Optional[str] = None
    volatility_score: Optional[float] = None
    
    # Procurement Intelligence
    procurement_percentage: Optional[float] = None
    small_business_percentage: Optional[float] = None
    competitive_percentage: Optional[float] = None
    
    # Metadata
    data_sources: List[str] = None
    last_updated: datetime = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = []
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class BudgetAnalysis:
    """Comprehensive budget analysis for an agency or program"""
    
    agency_code: str
    agency_name: str
    fiscal_year: int
    analysis_date: datetime
    
    # Summary Statistics
    total_budget_authority: Decimal
    total_outlays: Decimal
    total_obligations: Decimal
    overall_execution_rate: float
    
    # Budget Breakdown
    by_appropriation: Dict[str, Decimal]
    by_category: Dict[str, Decimal]
    by_program: Dict[str, Decimal]
    by_object_class: Dict[str, Decimal]
    
    # Line Items
    budget_line_items: List[BudgetLineItem]
    
    # Trends and Patterns
    spending_patterns: Dict[str, Any]
    seasonal_trends: Dict[str, float]
    historical_trends: Dict[str, List[float]]
    
    # Procurement Intelligence
    procurement_analysis: Dict[str, Any]
    contracting_opportunities: List[Dict[str, Any]]
    
    # Risk Assessment
    budget_risks: List[str]
    execution_challenges: List[str]
    
    # Quality Metrics
    data_completeness: float
    analysis_confidence: float

class BudgetExtractionPipeline:
    """
    Advanced budget data extraction and analysis pipeline
    Processes government budget data from multiple authoritative sources
    """
    
    def __init__(self):
        self.data_sources = {
            'treasury_fiscal': {
                'url': 'https://api.fiscaldata.treasury.gov/services/api/v1/',
                'endpoints': {
                    'federal_account_spending': 'accounting/od/outlays',
                    'agency_financial_reports': 'accounting/od/accounts_and_outlays',
                    'budget_execution': 'accounting/od/budget_execution'
                },
                'rate_limit': 120
            },
            'usaspending': {
                'url': 'https://api.usaspending.gov/api/v2/',
                'endpoints': {
                    'agency_spending': 'search/spending_by_agency/',
                    'account_spending': 'federal_accounts/',
                    'awards_spending': 'search/spending_by_award/'
                },
                'rate_limit': 100
            },
            'omb_max': {
                'url': 'https://max.omb.gov/api/beta/',
                'endpoints': {
                    'budget_requests': 'budget/agency/',
                    'execution_data': 'budget/execution/'
                },
                'rate_limit': 60
            },
            'congressional_budget': {
                'url': 'https://api.congress.gov/v3/',
                'endpoints': {
                    'appropriations': 'bill/appropriations',
                    'budget_resolutions': 'bill/budget'
                },
                'rate_limit': 50
            }
        }
        
        # Processing components
        self.treasury_processor = TreasuryDataProcessor()
        self.usaspending_processor = USASpendingProcessor()
        self.budget_analyzer = BudgetAnalyzer()
        self.trend_analyzer = BudgetTrendAnalyzer()
        self.procurement_analyzer = ProcurementBudgetAnalyzer()
        
        # Session management
        self.session = None
        self.rate_limiters = {}
    
    async def initialize(self):
        """Initialize the budget extraction pipeline"""
        
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=20)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'KBI-Labs-Budget-Pipeline/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        
        # Initialize rate limiters
        for source_name, config in self.data_sources.items():
            self.rate_limiters[source_name] = RateLimiter(config['rate_limit'])
        
        logger.info("Budget extraction pipeline initialized")
    
    async def extract_agency_budget(
        self, 
        agency_code: str,
        fiscal_years: List[int] = None,
        analysis_depth: str = "comprehensive"  # basic, detailed, comprehensive
    ) -> BudgetAnalysis:
        """
        Extract and analyze comprehensive budget data for agency
        
        Args:
            agency_code: Federal agency code
            fiscal_years: List of fiscal years to analyze
            analysis_depth: Level of analysis detail
            
        Returns:
            Comprehensive budget analysis
        """
        
        if fiscal_years is None:
            current_fy = self._get_current_fiscal_year()
            fiscal_years = [current_fy - 2, current_fy - 1, current_fy]
        
        logger.info(f"Extracting budget data for agency {agency_code}, FY {fiscal_years}")
        
        try:
            # 1. Extract Treasury Fiscal Data
            treasury_data = await self._extract_treasury_data(agency_code, fiscal_years)
            
            # 2. Extract USASpending Data
            usaspending_data = await self._extract_usaspending_data(agency_code, fiscal_years)
            
            # 3. Extract OMB Budget Data
            omb_data = await self._extract_omb_data(agency_code, fiscal_years)
            
            # 4. Extract Congressional Budget Data
            congressional_data = await self._extract_congressional_data(agency_code, fiscal_years)
            
            # 5. Process and Merge Data
            processed_data = await self._process_and_merge_budget_data(
                treasury_data, usaspending_data, omb_data, congressional_data
            )
            
            # 6. Create Budget Line Items
            budget_line_items = await self._create_budget_line_items(processed_data, fiscal_years)
            
            # 7. Perform Budget Analysis
            budget_analysis = await self._perform_budget_analysis(
                agency_code, budget_line_items, processed_data, analysis_depth
            )
            
            logger.info(f"Budget analysis complete: {len(budget_line_items)} line items")
            return budget_analysis
            
        except Exception as e:
            logger.error(f"Error extracting agency budget: {str(e)}")
            raise
    
    async def _extract_treasury_data(self, agency_code: str, fiscal_years: List[int]) -> Dict[str, Any]:
        """Extract data from Treasury Fiscal Data API"""
        
        treasury_data = {}
        
        for fiscal_year in fiscal_years:
            await self.rate_limiters['treasury_fiscal'].wait()
            
            try:
                # Federal Account Spending
                account_url = f"{self.data_sources['treasury_fiscal']['url']}{self.data_sources['treasury_fiscal']['endpoints']['federal_account_spending']}"
                
                params = {
                    'filter': f'reporting_fiscal_year:eq:{fiscal_year},agency_code:eq:{agency_code}',
                    'fields': 'agency_code,agency_name,bureau_code,bureau_name,account_code,account_title,budget_authority_amount,outlay_amount,object_class,program_activity',
                    'sort': '-budget_authority_amount',
                    'limit': 1000
                }
                
                async with self.session.get(account_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        treasury_data[f'fy_{fiscal_year}'] = data.get('data', [])
                        logger.info(f"Treasury data FY{fiscal_year}: {len(data.get('data', []))} records")
                    else:
                        logger.warning(f"Treasury API error {response.status} for FY{fiscal_year}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching Treasury data for FY{fiscal_year}: {str(e)}")
                continue
        
        return treasury_data
    
    async def _extract_usaspending_data(self, agency_code: str, fiscal_years: List[int]) -> Dict[str, Any]:
        """Extract data from USASpending API"""
        
        usaspending_data = {}
        
        for fiscal_year in fiscal_years:
            await self.rate_limiters['usaspending'].wait()
            
            try:
                # Agency spending summary
                url = f"{self.data_sources['usaspending']['url']}{self.data_sources['usaspending']['endpoints']['agency_spending']}"
                
                payload = {
                    "filters": {
                        "fy": str(fiscal_year),
                        "agencies": [{"type": "awarding", "tier": "toptier", "code": agency_code}]
                    },
                    "spending_type": "total"
                }
                
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        usaspending_data[f'fy_{fiscal_year}'] = data
                        logger.info(f"USASpending data FY{fiscal_year}: ${data.get('total_budgetary_resources', 0):,.0f}")
                    else:
                        logger.warning(f"USASpending API error {response.status} for FY{fiscal_year}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error fetching USASpending data for FY{fiscal_year}: {str(e)}")
                continue
        
        return usaspending_data
    
    async def _extract_omb_data(self, agency_code: str, fiscal_years: List[int]) -> Dict[str, Any]:
        """Extract budget data from OMB MAX"""
        
        omb_data = {}
        
        # Note: OMB MAX API access is typically restricted
        # This provides structure for when access is available
        
        for fiscal_year in fiscal_years:
            omb_data[f'fy_{fiscal_year}'] = {
                'budget_requests': [],
                'execution_data': [],
                'policy_guidance': []
            }
        
        logger.info(f"OMB data structure prepared for agency {agency_code}")
        return omb_data
    
    async def _extract_congressional_data(self, agency_code: str, fiscal_years: List[int]) -> Dict[str, Any]:
        """Extract congressional budget and appropriations data"""
        
        congressional_data = {}
        
        for fiscal_year in fiscal_years:
            congressional_data[f'fy_{fiscal_year}'] = {
                'appropriations_bills': [],
                'budget_resolutions': [],
                'committee_reports': []
            }
        
        logger.info(f"Congressional data structure prepared for agency {agency_code}")
        return congressional_data
    
    async def _process_and_merge_budget_data(
        self, 
        treasury_data: Dict[str, Any],
        usaspending_data: Dict[str, Any],
        omb_data: Dict[str, Any],
        congressional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and merge budget data from all sources"""
        
        processed_data = {
            'merged_accounts': {},
            'spending_summary': {},
            'data_quality': {},
            'source_coverage': {}
        }
        
        # Merge Treasury and USASpending data by fiscal year
        for fy_key in treasury_data.keys():
            fiscal_year = fy_key.split('_')[1]
            
            # Process Treasury data
            treasury_fy_data = treasury_data.get(fy_key, [])
            usaspending_fy_data = usaspending_data.get(fy_key, {})
            
            # Merge account-level data
            merged_accounts = self._merge_account_data(treasury_fy_data, usaspending_fy_data)
            processed_data['merged_accounts'][fiscal_year] = merged_accounts
            
            # Calculate spending summary
            spending_summary = self._calculate_spending_summary(merged_accounts)
            processed_data['spending_summary'][fiscal_year] = spending_summary
            
            # Assess data quality
            data_quality = self._assess_data_quality(treasury_fy_data, usaspending_fy_data)
            processed_data['data_quality'][fiscal_year] = data_quality
        
        return processed_data
    
    def _merge_account_data(self, treasury_data: List[Dict], usaspending_data: Dict) -> List[Dict]:
        """Merge Treasury and USASpending account-level data"""
        
        merged_accounts = []
        
        for treasury_account in treasury_data:
            merged_account = {
                'account_code': treasury_account.get('account_code'),
                'account_title': treasury_account.get('account_title'),
                'bureau_code': treasury_account.get('bureau_code'),
                'bureau_name': treasury_account.get('bureau_name'),
                'budget_authority': Decimal(str(treasury_account.get('budget_authority_amount', 0))),
                'outlays': Decimal(str(treasury_account.get('outlay_amount', 0))),
                'object_class': treasury_account.get('object_class'),
                'program_activity': treasury_account.get('program_activity'),
                'data_sources': ['treasury']
            }
            
            # Add USASpending data if available
            if usaspending_data:
                merged_account['total_budgetary_resources'] = Decimal(str(usaspending_data.get('total_budgetary_resources', 0)))
                merged_account['data_sources'].append('usaspending')
            
            merged_accounts.append(merged_account)
        
        return merged_accounts
    
    def _calculate_spending_summary(self, merged_accounts: List[Dict]) -> Dict[str, Any]:
        """Calculate spending summary statistics"""
        
        total_budget_authority = sum(acc.get('budget_authority', 0) for acc in merged_accounts)
        total_outlays = sum(acc.get('outlays', 0) for acc in merged_accounts)
        
        summary = {
            'total_budget_authority': total_budget_authority,
            'total_outlays': total_outlays,
            'execution_rate': float(total_outlays / total_budget_authority) if total_budget_authority > 0 else 0,
            'account_count': len(merged_accounts),
            'largest_accounts': sorted(merged_accounts, key=lambda x: x.get('budget_authority', 0), reverse=True)[:10]
        }
        
        return summary
    
    def _assess_data_quality(self, treasury_data: List[Dict], usaspending_data: Dict) -> Dict[str, Any]:
        """Assess quality and completeness of budget data"""
        
        quality_assessment = {
            'treasury_records': len(treasury_data),
            'usaspending_available': bool(usaspending_data),
            'completeness_score': 0.0,
            'quality_issues': []
        }
        
        # Calculate completeness score
        if treasury_data:
            quality_assessment['completeness_score'] += 0.6
        if usaspending_data:
            quality_assessment['completeness_score'] += 0.4
        
        # Identify quality issues
        if not treasury_data:
            quality_assessment['quality_issues'].append('No Treasury data available')
        if not usaspending_data:
            quality_assessment['quality_issues'].append('No USASpending data available')
        
        return quality_assessment
    
    async def _create_budget_line_items(
        self, 
        processed_data: Dict[str, Any], 
        fiscal_years: List[int]
    ) -> List[BudgetLineItem]:
        """Create detailed budget line items from processed data"""
        
        budget_line_items = []
        
        for fiscal_year in fiscal_years:
            fy_str = str(fiscal_year)
            merged_accounts = processed_data['merged_accounts'].get(fy_str, [])
            
            for account in merged_accounts:
                
                # Determine budget category
                budget_category = self._classify_budget_category(account.get('object_class', ''))
                
                # Calculate rates
                budget_authority = account.get('budget_authority', Decimal('0'))
                outlays = account.get('outlays', Decimal('0'))
                execution_rate = float(outlays / budget_authority) if budget_authority > 0 else 0
                
                # Create budget line item
                line_item = BudgetLineItem(
                    account_code=account.get('account_code', ''),
                    account_title=account.get('account_title', ''),
                    appropriation_code=account.get('account_code', ''),  # Use account code as appropriation code
                    fiscal_year=fiscal_year,
                    budget_authority=budget_authority,
                    outlays=outlays,
                    obligations=budget_authority,  # Assume fully obligated for now
                    unobligated_balance=budget_authority - outlays,
                    budget_category=budget_category,
                    appropriation_type=AppropriationType.DISCRETIONARY,  # Default assumption
                    object_class=account.get('object_class', ''),
                    program_activity=account.get('program_activity', ''),
                    execution_rate=execution_rate,
                    obligation_rate=1.0,  # Assume fully obligated
                    burn_rate_monthly=[],  # Would be calculated with monthly data
                    data_sources=account.get('data_sources', []),
                    confidence_score=0.8 if len(account.get('data_sources', [])) > 1 else 0.6
                )
                
                budget_line_items.append(line_item)
        
        return budget_line_items
    
    def _classify_budget_category(self, object_class: str) -> BudgetCategory:
        """Classify budget category based on object class"""
        
        if not object_class:
            return BudgetCategory.OTHER
        
        object_class_lower = object_class.lower()
        
        if 'personnel' in object_class_lower or 'compensation' in object_class_lower:
            return BudgetCategory.PERSONNEL
        elif 'contractual' in object_class_lower or 'services' in object_class_lower:
            return BudgetCategory.CONTRACTUAL
        elif 'equipment' in object_class_lower:
            return BudgetCategory.EQUIPMENT
        elif 'supplies' in object_class_lower or 'materials' in object_class_lower:
            return BudgetCategory.SUPPLIES
        elif 'travel' in object_class_lower or 'transportation' in object_class_lower:
            return BudgetCategory.TRAVEL
        elif 'rent' in object_class_lower or 'utilities' in object_class_lower:
            return BudgetCategory.RENT
        elif 'grants' in object_class_lower or 'subsidies' in object_class_lower:
            return BudgetCategory.GRANTS
        else:
            return BudgetCategory.OTHER
    
    async def _perform_budget_analysis(
        self,
        agency_code: str,
        budget_line_items: List[BudgetLineItem],
        processed_data: Dict[str, Any],
        analysis_depth: str
    ) -> BudgetAnalysis:
        """Perform comprehensive budget analysis"""
        
        # Get current fiscal year data
        current_fy = max([item.fiscal_year for item in budget_line_items])
        current_fy_items = [item for item in budget_line_items if item.fiscal_year == current_fy]
        
        # Calculate summary statistics
        total_budget_authority = sum(item.budget_authority for item in current_fy_items)
        total_outlays = sum(item.outlays for item in current_fy_items)
        total_obligations = sum(item.obligations for item in current_fy_items)
        overall_execution_rate = float(total_outlays / total_budget_authority) if total_budget_authority > 0 else 0
        
        # Budget breakdowns
        by_appropriation = {}
        by_category = {}
        by_program = {}
        by_object_class = {}
        
        for item in current_fy_items:
            # By appropriation
            by_appropriation[item.appropriation_code] = by_appropriation.get(item.appropriation_code, Decimal('0')) + item.budget_authority
            
            # By category
            category_name = item.budget_category.value
            by_category[category_name] = by_category.get(category_name, Decimal('0')) + item.budget_authority
            
            # By program
            by_program[item.program_activity] = by_program.get(item.program_activity, Decimal('0')) + item.budget_authority
            
            # By object class
            by_object_class[item.object_class] = by_object_class.get(item.object_class, Decimal('0')) + item.budget_authority
        
        # Analysis components
        spending_patterns = await self._analyze_spending_patterns(budget_line_items)
        seasonal_trends = await self._analyze_seasonal_trends(budget_line_items)
        historical_trends = await self._analyze_historical_trends(budget_line_items)
        procurement_analysis = await self._analyze_procurement_opportunities(budget_line_items)
        
        # Risk assessment
        budget_risks = self._assess_budget_risks(budget_line_items, processed_data)
        execution_challenges = self._identify_execution_challenges(budget_line_items)
        
        # Data quality assessment
        data_completeness = np.mean([item.confidence_score for item in budget_line_items])
        analysis_confidence = self._calculate_analysis_confidence(processed_data)
        
        return BudgetAnalysis(
            agency_code=agency_code,
            agency_name=self._get_agency_name(agency_code),
            fiscal_year=current_fy,
            analysis_date=datetime.now(),
            total_budget_authority=total_budget_authority,
            total_outlays=total_outlays,
            total_obligations=total_obligations,
            overall_execution_rate=overall_execution_rate,
            by_appropriation=by_appropriation,
            by_category=by_category,
            by_program=by_program,
            by_object_class=by_object_class,
            budget_line_items=budget_line_items,
            spending_patterns=spending_patterns,
            seasonal_trends=seasonal_trends,
            historical_trends=historical_trends,
            procurement_analysis=procurement_analysis,
            contracting_opportunities=procurement_analysis.get('opportunities', []),
            budget_risks=budget_risks,
            execution_challenges=execution_challenges,
            data_completeness=data_completeness,
            analysis_confidence=analysis_confidence
        )
    
    async def _analyze_spending_patterns(self, budget_line_items: List[BudgetLineItem]) -> Dict[str, Any]:
        """Analyze spending patterns across budget line items"""
        
        patterns = {
            'execution_distribution': {},
            'category_trends': {},
            'volatility_analysis': {}
        }
        
        # Execution rate distribution
        execution_rates = [item.execution_rate for item in budget_line_items if item.execution_rate is not None]
        if execution_rates:
            patterns['execution_distribution'] = {
                'mean': np.mean(execution_rates),
                'median': np.median(execution_rates),
                'std_dev': np.std(execution_rates),
                'min': min(execution_rates),
                'max': max(execution_rates)
            }
        
        return patterns
    
    async def _analyze_seasonal_trends(self, budget_line_items: List[BudgetLineItem]) -> Dict[str, float]:
        """Analyze seasonal spending trends"""
        
        # Placeholder for seasonal analysis
        seasonal_trends = {
            'Q1': 0.15,  # October-December
            'Q2': 0.20,  # January-March
            'Q3': 0.25,  # April-June
            'Q4': 0.40   # July-September (end of fiscal year)
        }
        
        return seasonal_trends
    
    async def _analyze_historical_trends(self, budget_line_items: List[BudgetLineItem]) -> Dict[str, List[float]]:
        """Analyze historical budget trends"""
        
        historical_trends = {}
        
        # Group by account and analyze trends
        accounts = {}
        for item in budget_line_items:
            if item.account_code not in accounts:
                accounts[item.account_code] = []
            accounts[item.account_code].append(item)
        
        for account_code, items in accounts.items():
            # Sort by fiscal year
            sorted_items = sorted(items, key=lambda x: x.fiscal_year)
            budget_trend = [float(item.budget_authority) for item in sorted_items]
            historical_trends[account_code] = budget_trend
        
        return historical_trends
    
    async def _analyze_procurement_opportunities(self, budget_line_items: List[BudgetLineItem]) -> Dict[str, Any]:
        """Analyze procurement opportunities in budget data"""
        
        procurement_analysis = {
            'total_contractual_spending': Decimal('0'),
            'opportunities': [],
            'trends': {}
        }
        
        # Find contractual spending
        contractual_items = [item for item in budget_line_items if item.budget_category == BudgetCategory.CONTRACTUAL]
        
        total_contractual = sum(item.budget_authority for item in contractual_items)
        procurement_analysis['total_contractual_spending'] = total_contractual
        
        # Identify large procurement opportunities
        large_contracts = [item for item in contractual_items if item.budget_authority > 1000000]
        
        for item in large_contracts:
            opportunity = {
                'account_title': item.account_title,
                'budget_authority': float(item.budget_authority),
                'fiscal_year': item.fiscal_year,
                'program_activity': item.program_activity,
                'opportunity_type': 'Large Contract Opportunity'
            }
            procurement_analysis['opportunities'].append(opportunity)
        
        return procurement_analysis
    
    def _assess_budget_risks(self, budget_line_items: List[BudgetLineItem], processed_data: Dict[str, Any]) -> List[str]:
        """Assess budget execution risks"""
        
        risks = []
        
        # Low execution rate risk
        low_execution_items = [item for item in budget_line_items if item.execution_rate < 0.5]
        if len(low_execution_items) > len(budget_line_items) * 0.2:
            risks.append("High percentage of accounts with low execution rates")
        
        # Data quality risks
        low_confidence_items = [item for item in budget_line_items if item.confidence_score < 0.5]
        if len(low_confidence_items) > len(budget_line_items) * 0.3:
            risks.append("Significant data quality concerns")
        
        # Large unobligated balances
        high_unobligated = [item for item in budget_line_items if item.unobligated_balance > item.budget_authority * 0.5]
        if high_unobligated:
            risks.append("Large unobligated balances indicate potential execution challenges")
        
        return risks
    
    def _identify_execution_challenges(self, budget_line_items: List[BudgetLineItem]) -> List[str]:
        """Identify budget execution challenges"""
        
        challenges = []
        
        # Varied execution rates
        execution_rates = [item.execution_rate for item in budget_line_items if item.execution_rate is not None]
        if execution_rates and np.std(execution_rates) > 0.3:
            challenges.append("High variability in execution rates across accounts")
        
        # Large accounts with low execution
        large_low_execution = [
            item for item in budget_line_items 
            if item.budget_authority > 10000000 and item.execution_rate < 0.6
        ]
        if large_low_execution:
            challenges.append("Large budget accounts with low execution rates")
        
        return challenges
    
    def _calculate_analysis_confidence(self, processed_data: Dict[str, Any]) -> float:
        """Calculate overall analysis confidence score"""
        
        confidence_scores = []
        
        for fy, quality_data in processed_data.get('data_quality', {}).items():
            confidence_scores.append(quality_data.get('completeness_score', 0.0))
        
        return np.mean(confidence_scores) if confidence_scores else 0.0
    
    def _get_agency_name(self, agency_code: str) -> str:
        """Convert agency code to agency name"""
        
        agency_mapping = {
            '9700': 'Department of Defense',
            '7000': 'Department of Homeland Security',
            '7500': 'Department of Health and Human Services',
            '1400': 'Department of the Interior',
            '4700': 'General Services Administration',
            '3600': 'Department of Veterans Affairs'
        }
        
        return agency_mapping.get(agency_code, f"Agency {agency_code}")
    
    def _get_current_fiscal_year(self) -> int:
        """Get current federal fiscal year"""
        today = date.today()
        if today.month >= 10:  # FY starts Oct 1
            return today.year + 1
        else:
            return today.year
    
    async def close(self):
        """Close the budget extraction pipeline"""
        if self.session:
            await self.session.close()
        logger.info("Budget extraction pipeline closed")

class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.request_times = []
    
    async def wait(self):
        """Wait if necessary to respect rate limits"""
        
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)

class TreasuryDataProcessor:
    """Processor for Treasury Fiscal Service data"""
    
    def process_account_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process raw Treasury account data"""
        # Implementation for Treasury data processing
        pass

class USASpendingProcessor:
    """Processor for USASpending.gov data"""
    
    def process_spending_data(self, raw_data: Dict) -> Dict:
        """Process raw USASpending data"""
        # Implementation for USASpending data processing
        pass

class BudgetAnalyzer:
    """Analyzer for budget patterns and trends"""
    
    def analyze_execution_patterns(self, budget_items: List[BudgetLineItem]) -> Dict[str, Any]:
        """Analyze budget execution patterns"""
        # Implementation for execution analysis
        pass

class BudgetTrendAnalyzer:
    """Analyzer for budget trends over time"""
    
    def analyze_multi_year_trends(self, budget_items: List[BudgetLineItem]) -> Dict[str, Any]:
        """Analyze budget trends across multiple fiscal years"""
        # Implementation for trend analysis
        pass

class ProcurementBudgetAnalyzer:
    """Analyzer for procurement opportunities in budget data"""
    
    def identify_procurement_opportunities(self, budget_items: List[BudgetLineItem]) -> List[Dict]:
        """Identify procurement opportunities from budget data"""
        # Implementation for procurement opportunity identification
        pass

# Example usage
async def main():
    """Example: Extract and analyze agency budget"""
    
    pipeline = BudgetExtractionPipeline()
    await pipeline.initialize()
    
    try:
        # Extract budget for Department of Defense
        dod_budget = await pipeline.extract_agency_budget(
            agency_code='9700',
            fiscal_years=[2022, 2023, 2024],
            analysis_depth='comprehensive'
        )
        
        print(f"DoD Budget Analysis Results:")
        print(f"- Total Budget Authority: ${dod_budget.total_budget_authority:,.0f}")
        print(f"- Total Outlays: ${dod_budget.total_outlays:,.0f}")
        print(f"- Execution Rate: {dod_budget.overall_execution_rate:.1%}")
        print(f"- Budget Line Items: {len(dod_budget.budget_line_items)}")
        print(f"- Procurement Opportunities: {len(dod_budget.contracting_opportunities)}")
        print(f"- Data Completeness: {dod_budget.data_completeness:.1%}")
        
        # Show largest budget categories
        print(f"\nLargest Budget Categories:")
        for category, amount in sorted(dod_budget.by_category.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"- {category}: ${amount:,.0f}")
        
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())