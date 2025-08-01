"""
Procurement Intelligence Processor

Central AI engine that coordinates all analysis capabilities to provide
comprehensive procurement intelligence and strategic recommendations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import openai
from dataclasses import dataclass, asdict

from .opportunity_analyzer import OpportunityAnalyzer
from .competitive_intelligence import CompetitiveIntelligenceEngine
from .document_analyzer import DocumentAnalyzer
from .recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)

@dataclass
class IntelligenceReport:
    """Comprehensive intelligence report for procurement opportunities"""
    report_id: str
    generated_at: str
    company_uei: str
    opportunity_id: Optional[str] = None
    
    # Core Analysis
    opportunity_assessment: Dict[str, Any] = None
    competitive_landscape: Dict[str, Any] = None
    win_probability: float = 0.0
    risk_assessment: Dict[str, Any] = None
    
    # Strategic Recommendations
    recommended_actions: List[str] = None
    teaming_recommendations: List[Dict] = None
    proposal_strategy: Dict[str, Any] = None
    
    # Supporting Data
    market_intelligence: Dict[str, Any] = None
    historical_context: Dict[str, Any] = None
    budget_analysis: Dict[str, Any] = None
    
    # Metadata
    confidence_score: float = 0.0
    data_sources: List[str] = None
    analysis_duration_seconds: float = 0.0

class ProcurementIntelligenceProcessor:
    """
    Central AI-powered intelligence processor that coordinates all analysis
    capabilities to provide comprehensive procurement intelligence.
    """
    
    def __init__(self, openai_api_key: str, redis_client=None):
        self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.redis_client = redis_client
        
        # Initialize analysis engines
        self.opportunity_analyzer = OpportunityAnalyzer(openai_api_key, redis_client)
        self.competitive_intelligence = CompetitiveIntelligenceEngine(openai_api_key, redis_client)
        self.document_analyzer = DocumentAnalyzer(openai_api_key, redis_client)
        self.recommendation_engine = RecommendationEngine(openai_api_key, redis_client)
        
        # Analysis configuration
        self.analysis_config = {
            'max_concurrent_analyses': 5,
            'cache_ttl_hours': 6,
            'confidence_threshold': 0.7,
            'enable_deep_analysis': True
        }
    
    async def generate_comprehensive_intelligence(
        self, 
        company_uei: str,
        opportunity_data: Optional[Dict] = None,
        analysis_depth: str = 'standard'
    ) -> IntelligenceReport:
        """
        Generate comprehensive procurement intelligence report for a company
        """
        start_time = datetime.utcnow()
        report_id = f"intel_{company_uei}_{int(start_time.timestamp())}"
        
        logger.info(f"Generating comprehensive intelligence report {report_id}")
        
        try:
            # Initialize report
            report = IntelligenceReport(
                report_id=report_id,
                generated_at=start_time.isoformat(),
                company_uei=company_uei,
                opportunity_id=opportunity_data.get('notice_id') if opportunity_data else None,
                recommended_actions=[],
                teaming_recommendations=[],
                data_sources=[]
            )
            
            # Parallel analysis execution
            analysis_tasks = []
            
            # Core opportunity analysis
            if opportunity_data:
                analysis_tasks.append(
                    self._analyze_opportunity(opportunity_data, company_uei)
                )
            
            # Competitive landscape analysis
            analysis_tasks.append(
                self._analyze_competitive_landscape(company_uei, opportunity_data)
            )
            
            # Market intelligence gathering
            analysis_tasks.append(
                self._gather_market_intelligence(company_uei, opportunity_data)
            )
            
            # Historical context analysis
            analysis_tasks.append(
                self._analyze_historical_context(company_uei, opportunity_data)
            )
            
            # Execute all analyses in parallel
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(analysis_results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis task {i} failed: {result}")
                    continue
                
                # Merge results into report
                if i == 0 and opportunity_data:  # Opportunity analysis
                    report.opportunity_assessment = result
                elif i == 1 or (i == 0 and not opportunity_data):  # Competitive analysis
                    report.competitive_landscape = result
                elif i == 2 or (i == 1 and not opportunity_data):  # Market intelligence
                    report.market_intelligence = result
                elif i == 3 or (i == 2 and not opportunity_data):  # Historical context
                    report.historical_context = result
            
            # Generate strategic recommendations
            report = await self._generate_strategic_recommendations(report)
            
            # Calculate overall metrics
            report.win_probability = self._calculate_win_probability(report)
            report.confidence_score = self._calculate_confidence_score(report)
            report.analysis_duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            # Cache the report
            await self._cache_report(report)
            
            logger.info(f"Intelligence report {report_id} generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating intelligence report: {e}")
            raise
    
    async def _analyze_opportunity(self, opportunity_data: Dict, company_uei: str) -> Dict[str, Any]:
        """Analyze specific procurement opportunity"""
        return await self.opportunity_analyzer.analyze_opportunity(
            opportunity_data, 
            company_uei
        )
    
    async def _analyze_competitive_landscape(
        self, 
        company_uei: str, 
        opportunity_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Analyze competitive landscape"""
        return await self.competitive_intelligence.analyze_competition(
            company_uei, 
            opportunity_data
        )
    
    async def _gather_market_intelligence(
        self, 
        company_uei: str, 
        opportunity_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Gather comprehensive market intelligence"""
        
        market_context = {
            'agency_analysis': None,
            'spending_trends': None,
            'similar_opportunities': [],
            'market_conditions': {}
        }
        
        try:
            # Analyze agency spending patterns if opportunity provided
            if opportunity_data and opportunity_data.get('department'):
                agency_analysis = await self._analyze_agency_patterns(
                    opportunity_data['department']
                )
                market_context['agency_analysis'] = agency_analysis
            
            # Get spending trends for relevant NAICS codes
            naics_code = None
            if opportunity_data:
                naics_code = opportunity_data.get('naics_code')
            
            if naics_code:
                spending_trends = await self._analyze_spending_trends(naics_code)
                market_context['spending_trends'] = spending_trends
            
            # Find similar opportunities
            similar_opps = await self._find_similar_opportunities(
                company_uei, 
                opportunity_data
            )
            market_context['similar_opportunities'] = similar_opps
            
        except Exception as e:
            logger.error(f"Error gathering market intelligence: {e}")
        
        return market_context
    
    async def _analyze_historical_context(
        self, 
        company_uei: str, 
        opportunity_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Analyze historical contracting context"""
        
        historical_context = {
            'company_performance': {},
            'agency_relationships': {},
            'past_competitions': [],
            'success_patterns': {}
        }
        
        try:
            # Analyze company's past performance with this agency
            if opportunity_data and opportunity_data.get('department'):
                agency_history = await self._analyze_company_agency_history(
                    company_uei, 
                    opportunity_data['department']
                )
                historical_context['agency_relationships'] = agency_history
            
            # Analyze similar past competitions
            past_competitions = await self._analyze_past_competitions(
                company_uei, 
                opportunity_data
            )
            historical_context['past_competitions'] = past_competitions
            
        except Exception as e:
            logger.error(f"Error analyzing historical context: {e}")
        
        return historical_context
    
    async def _generate_strategic_recommendations(self, report: IntelligenceReport) -> IntelligenceReport:
        """Generate strategic recommendations based on analysis"""
        
        try:
            # Generate recommendations using AI
            recommendations = await self.recommendation_engine.generate_recommendations(
                report.company_uei,
                report.opportunity_assessment,
                report.competitive_landscape,
                report.market_intelligence,
                report.historical_context
            )
            
            report.recommended_actions = recommendations.get('actions', [])
            report.teaming_recommendations = recommendations.get('teaming', [])
            report.proposal_strategy = recommendations.get('strategy', {})
            report.risk_assessment = recommendations.get('risks', {})
            
        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {e}")
        
        return report
    
    def _calculate_win_probability(self, report: IntelligenceReport) -> float:
        """Calculate overall win probability based on analysis"""
        
        probability_factors = []
        
        # Opportunity fit score
        if report.opportunity_assessment:
            fit_score = report.opportunity_assessment.get('fit_score', 0.5)
            probability_factors.append(('fit_score', fit_score, 0.3))
        
        # Competitive positioning
        if report.competitive_landscape:
            competitive_score = report.competitive_landscape.get('positioning_score', 0.5)
            probability_factors.append(('competitive', competitive_score, 0.25))
        
        # Historical performance
        if report.historical_context:
            history_score = report.historical_context.get('success_rate', 0.5)
            probability_factors.append(('history', history_score, 0.2))
        
        # Market conditions
        if report.market_intelligence:
            market_score = report.market_intelligence.get('favorability_score', 0.5)
            probability_factors.append(('market', market_score, 0.15))
        
        # Capability match
        capability_score = 0.5  # Default - should be calculated from company profile
        probability_factors.append(('capability', capability_score, 0.1))
        
        # Calculate weighted average
        if probability_factors:
            weighted_sum = sum(score * weight for _, score, weight in probability_factors)
            total_weight = sum(weight for _, _, weight in probability_factors)
            return weighted_sum / total_weight if total_weight > 0 else 0.5
        
        return 0.5
    
    def _calculate_confidence_score(self, report: IntelligenceReport) -> float:
        """Calculate confidence score for the analysis"""
        
        confidence_factors = []
        
        # Data completeness
        data_completeness = 0.0
        total_sections = 5
        completed_sections = 0
        
        if report.opportunity_assessment:
            completed_sections += 1
        if report.competitive_landscape:
            completed_sections += 1
        if report.market_intelligence:
            completed_sections += 1
        if report.historical_context:
            completed_sections += 1
        if report.recommended_actions:
            completed_sections += 1
        
        data_completeness = completed_sections / total_sections
        confidence_factors.append(data_completeness * 0.4)
        
        # Data freshness (newer data = higher confidence)
        data_freshness = 0.8  # Assume relatively fresh data
        confidence_factors.append(data_freshness * 0.3)
        
        # Analysis depth
        analysis_depth = 0.7  # Standard analysis depth
        confidence_factors.append(analysis_depth * 0.3)
        
        return sum(confidence_factors)
    
    async def _cache_report(self, report: IntelligenceReport):
        """Cache the intelligence report"""
        if self.redis_client:
            try:
                cache_key = f"intelligence_report:{report.report_id}"
                cache_data = json.dumps(asdict(report), default=str)
                ttl = self.analysis_config['cache_ttl_hours'] * 3600
                
                self.redis_client.setex(cache_key, ttl, cache_data)
                
            except Exception as e:
                logger.error(f"Error caching report: {e}")
    
    async def _analyze_agency_patterns(self, agency_name: str) -> Dict[str, Any]:
        """Analyze agency-specific contracting patterns"""
        # This would analyze historical data for the specific agency
        return {
            'preferred_contract_types': [],
            'average_award_timeline': 90,
            'common_evaluation_criteria': [],
            'small_business_utilization_rate': 0.0
        }
    
    async def _analyze_spending_trends(self, naics_code: str) -> Dict[str, Any]:
        """Analyze spending trends for specific NAICS code"""
        return {
            'trend_direction': 'stable',
            'year_over_year_change': 0.0,
            'seasonal_patterns': {},
            'forecast': {}
        }
    
    async def _find_similar_opportunities(
        self, 
        company_uei: str, 
        opportunity_data: Optional[Dict]
    ) -> List[Dict]:
        """Find similar opportunities for comparison"""
        return []
    
    async def _analyze_company_agency_history(
        self, 
        company_uei: str, 
        agency_name: str
    ) -> Dict[str, Any]:
        """Analyze company's history with specific agency"""
        return {
            'past_contracts_count': 0,
            'total_contract_value': 0.0,
            'success_rate': 0.0,
            'performance_ratings': [],
            'relationship_strength': 'unknown'
        }
    
    async def _analyze_past_competitions(
        self, 
        company_uei: str, 
        opportunity_data: Optional[Dict]
    ) -> List[Dict]:
        """Analyze similar past competitions"""
        return []
    
    async def get_cached_report(self, report_id: str) -> Optional[IntelligenceReport]:
        """Retrieve cached intelligence report"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"intelligence_report:{report_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                report_dict = json.loads(cached_data)
                return IntelligenceReport(**report_dict)
                
        except Exception as e:
            logger.error(f"Error retrieving cached report: {e}")
        
        return None
    
    async def analyze_multiple_opportunities(
        self, 
        company_uei: str, 
        opportunities: List[Dict]
    ) -> List[IntelligenceReport]:
        """Analyze multiple opportunities in parallel"""
        
        logger.info(f"Analyzing {len(opportunities)} opportunities for {company_uei}")
        
        # Process in batches to avoid overwhelming the system
        batch_size = self.analysis_config['max_concurrent_analyses']
        results = []
        
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            
            # Create analysis tasks for this batch
            batch_tasks = [
                self.generate_comprehensive_intelligence(company_uei, opp, 'quick')
                for opp in batch
            ]
            
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis failed: {result}")
                else:
                    results.append(result)
            
            # Brief pause between batches
            await asyncio.sleep(1)
        
        logger.info(f"Completed analysis of {len(results)} opportunities")
        return results