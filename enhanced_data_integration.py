#!/usr/bin/env python3
"""
Enhanced Data Integration System
Orchestrates multiple government data sources for comprehensive procurement intelligence
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass
import json

# Import our new data processors
from treasury_fiscal_integration import TreasuryFiscalProcessor
from federal_register_integration import FederalRegisterProcessor
from datagov_integration import DataGovProcessor

# Import existing processors
try:
    from gsa_calc_integration import GSACALCProcessor
    from fpds_integration import FPDSProcessor
    from sam_opportunities_integration import SAMOpportunitiesProcessor
    from unified_procurement_enrichment import UnifiedProcurementEnrichment
except ImportError as e:
    logging.warning(f"Some existing processors not available: {e}")

logger = logging.getLogger(__name__)

@dataclass
class EnhancedIntelligenceReport:
    """Comprehensive intelligence report structure"""
    company_uei: str
    analysis_date: str
    
    # Budget Intelligence
    budget_opportunities: List[Dict[str, Any]]
    budget_urgency_score: float
    optimal_timing_agencies: List[str]
    
    # Regulatory Intelligence
    regulatory_alerts: List[Dict[str, Any]]
    policy_impact_score: float
    regulatory_opportunities: List[str]
    
    # Dataset Intelligence
    relevant_datasets: List[Dict[str, Any]]
    data_richness_score: float
    intelligence_sources: List[str]
    
    # Traditional Intelligence (Existing)
    sam_matches: List[Dict[str, Any]]
    fpds_history: Dict[str, Any]
    gsa_calc_rates: Dict[str, Any]
    
    # Combined Scores
    overall_opportunity_score: float
    confidence_level: str
    recommendations: List[str]

class EnhancedDataIntegration:
    """
    Enhanced Data Integration System
    
    Orchestrates:
    - Treasury Fiscal Data (Budget Intelligence)
    - Federal Register (Regulatory Intelligence)
    - Data.gov (Dataset Intelligence)
    - Existing KBI Labs sources (SAM, FPDS, GSA CALC)
    """
    
    def __init__(self):
        self.processors = {}
        self.intelligence_cache = {}
        
    async def initialize_processors(self):
        """Initialize all data processors"""
        logger.info("Initializing enhanced data processors...")
        
        try:
            # Initialize new processors
            self.processors['treasury'] = TreasuryFiscalProcessor()
            self.processors['federal_register'] = FederalRegisterProcessor()
            self.processors['datagov'] = DataGovProcessor()
            
            # Initialize existing processors if available
            try:
                self.processors['gsa_calc'] = GSACALCProcessor()
                self.processors['fpds'] = FPDSProcessor()
                self.processors['sam_opportunities'] = SAMOpportunitiesProcessor(api_key="demo")  # Use demo key
                self.processors['unified'] = UnifiedProcurementEnrichment()
            except Exception as e:
                logger.warning(f"Some existing processors not initialized: {e}")
            
            logger.info(f"Initialized {len(self.processors)} data processors")
            
        except Exception as e:
            logger.error(f"Error initializing processors: {e}")
            raise
    
    async def get_budget_intelligence(self, target_agencies: List[str] = None) -> Dict[str, Any]:
        """Get comprehensive budget intelligence"""
        logger.info("Gathering budget intelligence...")
        
        if 'treasury' not in self.processors:
            return {'error': 'Treasury processor not available'}
        
        try:
            async with self.processors['treasury'] as treasury:
                intelligence = await treasury.get_procurement_timing_intelligence(target_agencies)
                return intelligence
        except Exception as e:
            logger.error(f"Error getting budget intelligence: {e}")
            return {'error': str(e)}
    
    async def get_regulatory_intelligence(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive regulatory intelligence"""
        logger.info("Gathering regulatory intelligence...")
        
        if 'federal_register' not in self.processors:
            return {'error': 'Federal Register processor not available'}
        
        try:
            async with self.processors['federal_register'] as fed_reg:
                intelligence = await fed_reg.get_regulatory_intelligence_summary(days)
                return intelligence
        except Exception as e:
            logger.error(f"Error getting regulatory intelligence: {e}")
            return {'error': str(e)}
    
    async def get_dataset_intelligence(self, limit: int = 100) -> Dict[str, Any]:
        """Get comprehensive dataset intelligence"""
        logger.info("Gathering dataset intelligence...")
        
        if 'datagov' not in self.processors:
            return {'error': 'Data.gov processor not available'}
        
        try:
            async with self.processors['datagov'] as datagov:
                intelligence = await datagov.get_dataset_intelligence_summary(limit)
                return intelligence
        except Exception as e:
            logger.error(f"Error getting dataset intelligence: {e}")
            return {'error': str(e)}
    
    async def get_traditional_intelligence(self, company_uei: str) -> Dict[str, Any]:
        """Get traditional KBI Labs intelligence"""
        logger.info(f"Gathering traditional intelligence for UEI: {company_uei}")
        
        intelligence = {
            'sam_matches': [],
            'fpds_history': {},
            'gsa_calc_rates': {},
            'unified_data': {}
        }
        
        # This would integrate with existing KBI Labs processors
        # For now, return mock data structure
        intelligence['message'] = 'Traditional intelligence integration pending'
        
        return intelligence
    
    def calculate_overall_opportunity_score(self, 
                                          budget_intel: Dict[str, Any],
                                          regulatory_intel: Dict[str, Any],
                                          dataset_intel: Dict[str, Any],
                                          traditional_intel: Dict[str, Any]) -> float:
        """Calculate overall opportunity score from all intelligence sources"""
        score = 0.0
        
        # Budget Intelligence Weight: 35%
        budget_score = 0.0
        if budget_intel and not budget_intel.get('error'):
            high_urgency = budget_intel.get('high_urgency_agencies', 0)
            moderate_urgency = budget_intel.get('moderate_urgency_agencies', 0)
            budget_score = min((high_urgency * 2 + moderate_urgency) / 10.0, 1.0)
        score += budget_score * 0.35
        
        # Regulatory Intelligence Weight: 25%
        regulatory_score = 0.0
        if regulatory_intel and not regulatory_intel.get('error'):
            high_impact = regulatory_intel.get('high_impact_documents', 0)
            moderate_impact = regulatory_intel.get('moderate_impact_documents', 0)
            regulatory_score = min((high_impact * 2 + moderate_impact) / 20.0, 1.0)
        score += regulatory_score * 0.25
        
        # Dataset Intelligence Weight: 20%
        dataset_score = 0.0
        if dataset_intel and not dataset_intel.get('error'):
            critical_datasets = dataset_intel.get('critical_intelligence_datasets', 0)
            high_value_datasets = dataset_intel.get('high_value_datasets', 0)
            dataset_score = min((critical_datasets * 2 + high_value_datasets) / 30.0, 1.0)
        score += dataset_score * 0.20
        
        # Traditional Intelligence Weight: 20%
        traditional_score = 0.5  # Mock score for now
        score += traditional_score * 0.20
        
        return min(score, 1.0)  # Cap at 1.0
    
    def determine_confidence_level(self, score: float, data_quality: Dict[str, bool]) -> str:
        """Determine confidence level based on score and data quality"""
        # Check how many data sources are available
        available_sources = sum(1 for available in data_quality.values() if available)
        total_sources = len(data_quality)
        
        data_coverage = available_sources / total_sources
        
        if score >= 0.8 and data_coverage >= 0.75:
            return "Very High"
        elif score >= 0.6 and data_coverage >= 0.5:
            return "High"
        elif score >= 0.4 and data_coverage >= 0.25:
            return "Medium"
        else:
            return "Low"
    
    def generate_recommendations(self,
                               budget_intel: Dict[str, Any],
                               regulatory_intel: Dict[str, Any],
                               dataset_intel: Dict[str, Any],
                               overall_score: float) -> List[str]:
        """Generate actionable recommendations based on intelligence"""
        recommendations = []
        
        # Budget-based recommendations
        if budget_intel and not budget_intel.get('error'):
            immediate_targets = budget_intel.get('recommendations', {}).get('immediate_targets', [])
            if immediate_targets:
                recommendations.append(f"PRIORITY: Target {', '.join(immediate_targets[:2])} - high budget urgency")
            
            budget_flush = budget_intel.get('recommendations', {}).get('budget_flush_prediction', '')
            if 'Q4' in budget_flush:
                recommendations.append("TIMING: Prepare for Q4 budget flush period - increased spending expected")
        
        # Regulatory-based recommendations
        if regulatory_intel and not regulatory_intel.get('error'):
            immediate_attention = regulatory_intel.get('recommendations', {}).get('immediate_attention', [])
            if immediate_attention:
                recommendations.append(f"REGULATORY: Monitor {len(immediate_attention)} high-impact regulatory changes")
        
        # Dataset-based recommendations
        if dataset_intel and not dataset_intel.get('error'):
            immediate_integration = dataset_intel.get('recommendations', {}).get('immediate_integration', [])
            if immediate_integration:
                recommendations.append(f"DATA: Integrate {len(immediate_integration)} critical datasets for competitive advantage")
        
        # Overall score recommendations
        if overall_score >= 0.8:
            recommendations.append("OPPORTUNITY: Exceptional market conditions - accelerate business development")
        elif overall_score >= 0.6:
            recommendations.append("OPPORTUNITY: Good market conditions - focus on strategic positioning")
        elif overall_score >= 0.4:
            recommendations.append("OPPORTUNITY: Moderate conditions - maintain steady pursuit activity")
        else:
            recommendations.append("OPPORTUNITY: Challenging conditions - focus on relationship building")
        
        return recommendations
    
    async def generate_enhanced_intelligence_report(self, 
                                                  company_uei: str,
                                                  target_agencies: List[str] = None,
                                                  analysis_days: int = 30) -> EnhancedIntelligenceReport:
        """Generate comprehensive enhanced intelligence report"""
        logger.info(f"Generating enhanced intelligence report for UEI: {company_uei}")
        
        # Gather all intelligence sources in parallel
        intelligence_tasks = [
            self.get_budget_intelligence(target_agencies),
            self.get_regulatory_intelligence(analysis_days),
            self.get_dataset_intelligence(100),
            self.get_traditional_intelligence(company_uei)
        ]
        
        budget_intel, regulatory_intel, dataset_intel, traditional_intel = await asyncio.gather(
            *intelligence_tasks, return_exceptions=True
        )
        
        # Handle exceptions
        for i, result in enumerate([budget_intel, regulatory_intel, dataset_intel, traditional_intel]):
            if isinstance(result, Exception):
                logger.error(f"Intelligence gathering error {i}: {result}")
                if i == 0: budget_intel = {'error': str(result)}
                elif i == 1: regulatory_intel = {'error': str(result)}
                elif i == 2: dataset_intel = {'error': str(result)}
                elif i == 3: traditional_intel = {'error': str(result)}
        
        # Calculate overall opportunity score
        overall_score = self.calculate_overall_opportunity_score(
            budget_intel, regulatory_intel, dataset_intel, traditional_intel
        )
        
        # Determine data quality
        data_quality = {
            'budget': not budget_intel.get('error'),
            'regulatory': not regulatory_intel.get('error'),
            'dataset': not dataset_intel.get('error'),
            'traditional': not traditional_intel.get('error')
        }
        
        # Determine confidence level
        confidence = self.determine_confidence_level(overall_score, data_quality)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(
            budget_intel, regulatory_intel, dataset_intel, overall_score
        )
        
        # Extract key data points
        budget_opportunities = budget_intel.get('intelligence', []) if not budget_intel.get('error') else []
        budget_urgency = budget_intel.get('high_urgency_agencies', 0) if not budget_intel.get('error') else 0
        optimal_timing = budget_intel.get('recommendations', {}).get('immediate_targets', []) if not budget_intel.get('error') else []
        
        regulatory_alerts = regulatory_intel.get('high_impact_alerts', []) if not regulatory_intel.get('error') else []
        policy_impact = len(regulatory_alerts) / 5.0 if regulatory_alerts else 0  # Normalize to 0-1
        regulatory_opportunities = regulatory_intel.get('recommendations', {}).get('immediate_attention', []) if not regulatory_intel.get('error') else []
        
        relevant_datasets = dataset_intel.get('critical_datasets', []) if not dataset_intel.get('error') else []
        data_richness = dataset_intel.get('critical_intelligence_datasets', 0) / 10.0 if not dataset_intel.get('error') else 0
        intelligence_sources = list(data_quality.keys())
        
        # Create comprehensive report
        report = EnhancedIntelligenceReport(
            company_uei=company_uei,
            analysis_date=datetime.now().isoformat(),
            
            # Budget Intelligence
            budget_opportunities=budget_opportunities[:10],  # Top 10
            budget_urgency_score=min(budget_urgency / 10.0, 1.0),
            optimal_timing_agencies=optimal_timing[:5],
            
            # Regulatory Intelligence
            regulatory_alerts=regulatory_alerts[:5],  # Top 5
            policy_impact_score=min(policy_impact, 1.0),
            regulatory_opportunities=regulatory_opportunities[:5],
            
            # Dataset Intelligence
            relevant_datasets=relevant_datasets[:10],  # Top 10
            data_richness_score=min(data_richness, 1.0),
            intelligence_sources=intelligence_sources,
            
            # Traditional Intelligence
            sam_matches=traditional_intel.get('sam_matches', []),
            fpds_history=traditional_intel.get('fpds_history', {}),
            gsa_calc_rates=traditional_intel.get('gsa_calc_rates', {}),
            
            # Combined Analysis
            overall_opportunity_score=overall_score,
            confidence_level=confidence,
            recommendations=recommendations
        )
        
        logger.info(f"Enhanced intelligence report generated with {len(recommendations)} recommendations")
        return report
    
    async def get_market_intelligence_dashboard(self) -> Dict[str, Any]:
        """Get market-wide intelligence dashboard"""
        logger.info("Generating market intelligence dashboard...")
        
        # Gather market-wide intelligence
        market_tasks = [
            self.get_budget_intelligence(),
            self.get_regulatory_intelligence(14),  # Last 2 weeks
            self.get_dataset_intelligence(50)
        ]
        
        budget_intel, regulatory_intel, dataset_intel = await asyncio.gather(
            *market_tasks, return_exceptions=True
        )
        
        # Create dashboard summary
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'market_conditions': {
                'budget_climate': 'Favorable' if not budget_intel.get('error') and budget_intel.get('high_urgency_agencies', 0) > 5 else 'Moderate',
                'regulatory_climate': 'Active' if not regulatory_intel.get('error') and regulatory_intel.get('high_impact_documents', 0) > 3 else 'Stable',
                'data_availability': 'Rich' if not dataset_intel.get('error') and dataset_intel.get('critical_intelligence_datasets', 0) > 5 else 'Adequate'
            },
            'key_metrics': {
                'agencies_with_urgent_budgets': budget_intel.get('high_urgency_agencies', 0) if not budget_intel.get('error') else 0,
                'high_impact_regulations': regulatory_intel.get('high_impact_documents', 0) if not regulatory_intel.get('error') else 0,
                'critical_datasets_available': dataset_intel.get('critical_intelligence_datasets', 0) if not dataset_intel.get('error') else 0
            },
            'intelligence_sources': {
                'budget_intelligence': not budget_intel.get('error'),
                'regulatory_intelligence': not regulatory_intel.get('error'),
                'dataset_intelligence': not dataset_intel.get('error')
            },
            'market_opportunities': {
                'immediate_budget_targets': budget_intel.get('recommendations', {}).get('immediate_targets', [])[:3] if not budget_intel.get('error') else [],
                'regulatory_driven_opportunities': regulatory_intel.get('recommendations', {}).get('immediate_attention', [])[:3] if not regulatory_intel.get('error') else [],
                'data_driven_insights': dataset_intel.get('recommendations', {}).get('immediate_integration', [])[:3] if not dataset_intel.get('error') else []
            }
        }
        
        return dashboard

async def test_enhanced_integration():
    """Test the enhanced data integration system"""
    print("🚀 Testing Enhanced Data Integration System...")
    
    integration = EnhancedDataIntegration()
    await integration.initialize_processors()
    
    # Test market intelligence dashboard
    dashboard = await integration.get_market_intelligence_dashboard()
    print(f"✅ Generated market intelligence dashboard")
    
    print("\n📊 Market Conditions:")
    conditions = dashboard.get('market_conditions', {})
    for condition, status in conditions.items():
        print(f"   {condition.replace('_', ' ').title()}: {status}")
    
    print("\n📈 Key Metrics:")
    metrics = dashboard.get('key_metrics', {})
    for metric, value in metrics.items():
        print(f"   {metric.replace('_', ' ').title()}: {value}")
    
    # Test enhanced intelligence report
    test_uei = "TEST123456789"
    report = await integration.generate_enhanced_intelligence_report(
        company_uei=test_uei,
        target_agencies=["Department of Defense", "General Services Administration"]
    )
    
    print(f"\n🎯 Enhanced Intelligence Report for {test_uei}:")
    print(f"   Overall Opportunity Score: {report.overall_opportunity_score:.2f}")
    print(f"   Confidence Level: {report.confidence_level}")
    print(f"   Budget Urgency Score: {report.budget_urgency_score:.2f}")
    print(f"   Policy Impact Score: {report.policy_impact_score:.2f}")
    print(f"   Data Richness Score: {report.data_richness_score:.2f}")
    
    print(f"\n📋 Recommendations ({len(report.recommendations)}):")
    for i, rec in enumerate(report.recommendations[:5], 1):
        print(f"   {i}. {rec}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_enhanced_integration())