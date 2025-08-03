"""
KBI Labs Intelligent Recommendation Engine
Advanced AI-powered recommendation system for government contracting
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
from enum import Enum

# Import our opportunity scorer
from .opportunity_scorer import OpportunityScorer, CompanyProfile

logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    OPPORTUNITY = "opportunity"
    STRATEGY = "strategy" 
    MARKET = "market"
    CAPABILITY = "capability"
    ALERT = "alert"

class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Recommendation:
    id: str
    type: RecommendationType
    priority: Priority
    title: str
    description: str
    action_items: List[str]
    confidence: float
    expires_at: Optional[datetime] = None
    related_opportunity_id: Optional[str] = None
    metadata: Optional[Dict] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self):
        data = asdict(self)
        # Convert enums to strings
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        # Convert datetime to ISO format
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

class IntelligentRecommendationEngine:
    """Advanced AI-powered recommendation system for government contracting intelligence"""
    
    def __init__(self, company_profile: Optional[CompanyProfile] = None):
        self.version = "1.0.0"
        self.opportunity_scorer = OpportunityScorer(company_profile)
        self.company_profile = company_profile or self.opportunity_scorer.company_profile
        self._recommendation_cache = {}
        self._historical_patterns = {}
        
        logger.info(f"Intelligent Recommendation Engine v{self.version} initialized")
    
    def generate_recommendations(self, opportunities: List[Dict], market_data: Optional[Dict] = None) -> List[Recommendation]:
        """
        Generate comprehensive AI-powered recommendations based on opportunity data and market intelligence
        
        Args:
            opportunities: List of opportunity data
            market_data: Optional market intelligence data
            
        Returns:
            List of prioritized recommendations
        """
        recommendations = []
        
        try:
            # Score all opportunities first
            scored_opportunities = []
            for opp in opportunities:
                try:
                    score_result = self.opportunity_scorer.score_opportunity(opp)
                    scored_opportunities.append({
                        'opportunity': opp,
                        'score': score_result
                    })
                except Exception as e:
                    logger.warning(f"Failed to score opportunity {opp.get('id', 'unknown')}: {e}")
            
            # Generate different types of recommendations
            recommendations.extend(self._generate_opportunity_recommendations(scored_opportunities))
            recommendations.extend(self._generate_strategy_recommendations(scored_opportunities))
            recommendations.extend(self._generate_market_recommendations(scored_opportunities, market_data))
            recommendations.extend(self._generate_capability_recommendations(scored_opportunities))
            recommendations.extend(self._generate_alert_recommendations(scored_opportunities))
            
            # Sort by priority and confidence
            recommendations.sort(key=lambda r: (
                self._priority_weight(r.priority),
                -r.confidence
            ))
            
            # Limit to top recommendations
            return recommendations[:15]
            
        except Exception as error:
            logger.error(f"Recommendation generation failed: {error}")
            return self._generate_fallback_recommendations()
    
    def _generate_opportunity_recommendations(self, scored_opportunities: List[Dict]) -> List[Recommendation]:
        """Generate opportunity-specific recommendations"""
        recommendations = []
        
        # High-value opportunities
        high_value_opps = [so for so in scored_opportunities if so['score']['overall_score'] >= 80]
        if high_value_opps:
            top_opp = max(high_value_opps, key=lambda x: x['score']['overall_score'])
            recommendations.append(Recommendation(
                id=self._generate_id("high_value_opp"),
                type=RecommendationType.OPPORTUNITY,
                priority=Priority.HIGH,
                title=f"Prioritize High-Value Opportunity",
                description=f"'{top_opp['opportunity'].get('title', 'Unknown')}' scored {top_opp['score']['overall_score']:.1f}/100 with excellent alignment.",
                action_items=[
                    "Schedule immediate bid/no-bid meeting",
                    "Assign senior proposal manager",
                    "Begin competitive intelligence gathering",
                    "Develop win theme and strategy"
                ],
                confidence=0.92,
                related_opportunity_id=str(top_opp['opportunity'].get('id')),
                expires_at=datetime.now() + timedelta(days=3)
            ))
        
        # Time-sensitive opportunities
        urgent_opps = [so for so in scored_opportunities 
                      if so['score']['factor_scores'].get('time_constraints', 50) < 40
                      and so['score']['overall_score'] >= 60]
        if urgent_opps:
            recommendations.append(Recommendation(
                id=self._generate_id("urgent_deadline"),
                type=RecommendationType.ALERT,
                priority=Priority.CRITICAL,
                title="Urgent Deadline Alert",
                description=f"{len(urgent_opps)} opportunities have tight deadlines but good scores.",
                action_items=[
                    "Review proposal capacity immediately",
                    "Make go/no-go decisions within 24 hours",
                    "Consider teaming to increase bandwidth"
                ],
                confidence=0.88,
                expires_at=datetime.now() + timedelta(hours=24)
            ))
        
        # Opportunities requiring teaming
        teaming_opps = [so for so in scored_opportunities 
                       if so['score']['factor_scores'].get('technical_match', 50) < 50
                       and so['score']['overall_score'] >= 65]
        if teaming_opps:
            recommendations.append(Recommendation(
                id=self._generate_id("teaming_opportunity"),
                type=RecommendationType.STRATEGY,
                priority=Priority.MEDIUM,
                title="Strategic Teaming Opportunities",
                description=f"{len(teaming_opps)} high-value opportunities may require teaming partners.",
                action_items=[
                    "Identify complementary capabilities needed",
                    "Reach out to potential teaming partners",
                    "Negotiate teaming agreements",
                    "Joint proposal development planning"
                ],
                confidence=0.75
            ))
        
        return recommendations
    
    def _generate_strategy_recommendations(self, scored_opportunities: List[Dict]) -> List[Recommendation]:
        """Generate strategic business recommendations"""
        recommendations = []
        
        # Portfolio analysis
        pursue_count = len([so for so in scored_opportunities if so['score']['recommendation'] == 'pursue'])
        total_count = len(scored_opportunities)
        
        if pursue_count / total_count < 0.3:
            recommendations.append(Recommendation(
                id=self._generate_id("low_pursue_rate"),
                type=RecommendationType.STRATEGY,
                priority=Priority.MEDIUM,
                title="Low Opportunity Pursuit Rate",
                description=f"Only {pursue_count}/{total_count} opportunities recommended for pursuit. Consider strategy adjustment.",
                action_items=[
                    "Review company capabilities vs market demand",
                    "Consider expanding service offerings",
                    "Analyze competitive positioning",
                    "Evaluate pricing strategy"
                ],
                confidence=0.82
            ))
        
        # Agency relationship analysis
        agency_scores = {}
        for so in scored_opportunities:
            agency = so['opportunity'].get('agency', 'Unknown')
            if agency not in agency_scores:
                agency_scores[agency] = []
            agency_scores[agency].append(so['score']['factor_scores'].get('agency_relationship', 50))
        
        weak_agencies = [agency for agency, scores in agency_scores.items() 
                        if sum(scores) / len(scores) < 40]
        
        if weak_agencies and len(weak_agencies) <= 3:
            recommendations.append(Recommendation(
                id=self._generate_id("agency_relationship"),
                type=RecommendationType.STRATEGY,
                priority=Priority.MEDIUM,
                title="Strengthen Agency Relationships",
                description=f"Weak relationships detected with {', '.join(weak_agencies[:2])}{'...' if len(weak_agencies) > 2 else ''}.",
                action_items=[
                    "Schedule relationship building meetings",
                    "Attend agency industry days",
                    "Engage in capability presentations",
                    "Develop agency-specific value propositions"
                ],
                confidence=0.78,
                metadata={"weak_agencies": weak_agencies}
            ))
        
        return recommendations
    
    def _generate_market_recommendations(self, scored_opportunities: List[Dict], market_data: Optional[Dict]) -> List[Recommendation]:
        """Generate market intelligence recommendations"""
        recommendations = []
        
        # NAICS analysis
        naics_performance = {}
        for so in scored_opportunities:
            naics_codes = so['opportunity'].get('naics_codes', [])
            value_score = so['score']['factor_scores'].get('value_alignment', 50)
            
            for naics in naics_codes:
                if naics not in naics_performance:
                    naics_performance[naics] = []
                naics_performance[naics].append(value_score)
        
        # Find underperforming NAICS
        underperforming = []
        for naics, scores in naics_performance.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 45 and len(scores) >= 2:
                underperforming.append((naics, avg_score))
        
        if underperforming:
            worst_naics = min(underperforming, key=lambda x: x[1])
            recommendations.append(Recommendation(
                id=self._generate_id("naics_performance"),
                type=RecommendationType.MARKET,
                priority=Priority.LOW,
                title="NAICS Performance Analysis",
                description=f"NAICS {worst_naics[0]} showing low alignment scores ({worst_naics[1]:.1f}/100).",
                action_items=[
                    "Review service offerings for this NAICS",
                    "Assess competitive landscape",
                    "Consider capability development",
                    "Evaluate market exit strategy"
                ],
                confidence=0.71
            ))
        
        # Contract size analysis
        large_contracts = [so for so in scored_opportunities 
                          if so['score']['factor_scores'].get('financial_viability', 50) < 40]
        if len(large_contracts) >= 3:
            recommendations.append(Recommendation(
                id=self._generate_id("contract_sizing"),
                type=RecommendationType.MARKET,
                priority=Priority.MEDIUM,
                title="Contract Size Optimization",
                description=f"{len(large_contracts)} opportunities show financial viability concerns.",
                action_items=[
                    "Focus on right-sized opportunities",
                    "Consider joint ventures for large contracts",
                    "Evaluate growth capacity and financing",
                    "Develop scalable delivery models"
                ],
                confidence=0.79
            ))
        
        return recommendations
    
    def _generate_capability_recommendations(self, scored_opportunities: List[Dict]) -> List[Recommendation]:
        """Generate capability development recommendations"""
        recommendations = []
        
        # Technical capability gaps
        low_tech_scores = [so for so in scored_opportunities 
                          if so['score']['factor_scores'].get('technical_match', 50) < 45]
        
        if len(low_tech_scores) >= 3:
            # Analyze common missing capabilities
            common_keywords = self._extract_capability_gaps(low_tech_scores)
            
            recommendations.append(Recommendation(
                id=self._generate_id("capability_gap"),
                type=RecommendationType.CAPABILITY,
                priority=Priority.HIGH,
                title="Strategic Capability Gaps Identified",
                description=f"Multiple opportunities show technical misalignment. Common gaps: {', '.join(common_keywords[:3])}.",
                action_items=[
                    "Assess ROI of capability development",
                    "Plan training and certification programs",
                    "Consider strategic hiring",
                    "Evaluate partnership opportunities"
                ],
                confidence=0.85,
                metadata={"capability_gaps": common_keywords}
            ))
        
        # Security clearance requirements
        clearance_opps = [so for so in scored_opportunities 
                         if 'clearance' in so['opportunity'].get('description', '').lower()]
        
        if clearance_opps and not self.company_profile.security_clearance:
            recommendations.append(Recommendation(
                id=self._generate_id("security_clearance"),
                type=RecommendationType.CAPABILITY,
                priority=Priority.HIGH,
                title="Security Clearance Investment Opportunity",
                description=f"{len(clearance_opps)} opportunities require security clearance.",
                action_items=[
                    "Evaluate clearance investment ROI",
                    "Identify key personnel for clearance",
                    "Plan facility security requirements",
                    "Develop FSO capabilities"
                ],
                confidence=0.89
            ))
        
        return recommendations
    
    def _generate_alert_recommendations(self, scored_opportunities: List[Dict]) -> List[Recommendation]:
        """Generate time-sensitive alerts and notifications"""
        recommendations = []
        
        # Deadline tracking
        today = datetime.now()
        critical_deadlines = []
        
        for so in scored_opportunities:
            deadline_str = so['opportunity'].get('deadline') or so['opportunity'].get('response_date')
            if deadline_str:
                try:
                    if isinstance(deadline_str, str):
                        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                    else:
                        deadline = deadline_str
                    
                    days_left = (deadline - today).days
                    if days_left <= 7 and so['score']['overall_score'] >= 60:
                        critical_deadlines.append((so, days_left))
                except:
                    pass
        
        if critical_deadlines:
            critical_deadlines.sort(key=lambda x: x[1])  # Sort by days left
            soonest = critical_deadlines[0]
            
            recommendations.append(Recommendation(
                id=self._generate_id("critical_deadline"),
                type=RecommendationType.ALERT,
                priority=Priority.CRITICAL,
                title=f"Critical Deadline: {soonest[1]} Days Remaining",
                description=f"'{soonest[0]['opportunity'].get('title', 'Unknown')}' deadline approaching with good scoring potential.",
                action_items=[
                    "Immediate go/no-go decision required",
                    "Alert proposal team",
                    "Confirm submission requirements",
                    "Prepare emergency proposal timeline"
                ],
                confidence=0.95,
                related_opportunity_id=str(soonest[0]['opportunity'].get('id')),
                expires_at=datetime.now() + timedelta(hours=12)
            ))
        
        return recommendations
    
    def _extract_capability_gaps(self, low_scoring_opportunities: List[Dict]) -> List[str]:
        """Extract common capability gaps from opportunity descriptions"""
        gap_keywords = []
        
        # Common government technology keywords
        tech_keywords = [
            'cloud', 'aws', 'azure', 'devops', 'kubernetes', 'docker',
            'cybersecurity', 'zero trust', 'siem', 'soc',
            'ai', 'machine learning', 'data analytics', 'big data',
            'agile', 'scrum', 'ci/cd', 'automation',
            'microservices', 'api', 'integration', 'migration'
        ]
        
        keyword_counts = {}
        for so in low_scoring_opportunities:
            description = so['opportunity'].get('description', '').lower()
            for keyword in tech_keywords:
                if keyword in description:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Return most common gaps
        sorted_gaps = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [gap[0] for gap in sorted_gaps[:5]]
    
    def _priority_weight(self, priority: Priority) -> int:
        """Convert priority to numeric weight for sorting"""
        weights = {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }
        return weights.get(priority, 1)
    
    def _generate_id(self, base: str) -> str:
        """Generate unique recommendation ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{base}_{timestamp}".encode()).hexdigest()[:12]
    
    def _generate_fallback_recommendations(self) -> List[Recommendation]:
        """Generate basic recommendations when main algorithm fails"""
        return [
            Recommendation(
                id=self._generate_id("fallback"),
                type=RecommendationType.STRATEGY,
                priority=Priority.MEDIUM,
                title="Platform Ready for Analysis",
                description="AI recommendation engine is online and ready to analyze opportunities.",
                action_items=[
                    "Upload opportunity data for analysis",
                    "Review company profile settings",
                    "Set up automated alerts"
                ],
                confidence=0.80
            )
        ]

# Global recommendation engine instance
recommendation_engine = IntelligentRecommendationEngine()

# Export functions for API use
def generate_recommendations_for_opportunities(opportunities: List[Dict], market_data: Optional[Dict] = None) -> List[Dict]:
    """Convenience function to generate recommendations and return as dictionaries"""
    recommendations = recommendation_engine.generate_recommendations(opportunities, market_data)
    return [rec.to_dict() for rec in recommendations]

def get_recommendation_summary(opportunities: List[Dict]) -> Dict:
    """Get a summary of recommendations for dashboard display"""
    recommendations = recommendation_engine.generate_recommendations(opportunities)
    
    summary = {
        'total_recommendations': len(recommendations),
        'critical_count': len([r for r in recommendations if r.priority == Priority.CRITICAL]),
        'high_count': len([r for r in recommendations if r.priority == Priority.HIGH]),
        'categories': {},
        'top_recommendations': [rec.to_dict() for rec in recommendations[:5]]
    }
    
    # Count by category
    for rec in recommendations:
        category = rec.type.value
        summary['categories'][category] = summary['categories'].get(category, 0) + 1
    
    return summary