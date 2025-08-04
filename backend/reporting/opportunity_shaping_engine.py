#!/usr/bin/env python3
"""
Opportunity Shaping Guidance Engine
Strategic Intelligence for Government Contract Opportunity Development

This engine provides SMBs with detailed, actionable guidance on how to shape
government contracting opportunities before they're formally released,
maximizing win probability through strategic stakeholder engagement.
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
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class ShapingPhase(Enum):
    MARKET_RESEARCH = "Market Research Phase"
    REQUIREMENTS_DEVELOPMENT = "Requirements Development"
    BUDGET_PLANNING = "Budget Planning"
    ACQUISITION_PLANNING = "Acquisition Planning"
    PRE_SOLICITATION = "Pre-Solicitation"
    SOLICITATION_ACTIVE = "Solicitation Active"
    EVALUATION = "Evaluation Phase"
    AWARD = "Award Phase"

class EngagementType(Enum):
    MARKET_RESEARCH_RESPONSE = "Market Research Response"
    INDUSTRY_DAY_PARTICIPATION = "Industry Day Participation"
    ONE_ON_ONE_MEETING = "One-on-One Meeting"
    TECHNICAL_DEMONSTRATION = "Technical Demonstration"
    WHITE_PAPER_SUBMISSION = "White Paper Submission"
    CAPABILITY_BRIEFING = "Capability Briefing"
    PARTNERSHIP_DISCUSSION = "Partnership Discussion"
    PROTOTYPE_DEMONSTRATION = "Prototype Demonstration"

class ShapingOutcome(Enum):
    REQUIREMENTS_INFLUENCED = "Requirements Successfully Influenced"
    INCUMBENT_POSITION_ESTABLISHED = "Incumbent Position Established"
    PARTNERSHIP_SECURED = "Strategic Partnership Secured"
    TECHNICAL_APPROACH_VALIDATED = "Technical Approach Validated"
    BUDGET_ALLOCATED = "Budget Allocation Secured"
    TIMELINE_ADJUSTED = "Timeline Favorably Adjusted"
    COMPETITIVE_ADVANTAGE_GAINED = "Competitive Advantage Gained"

@dataclass
class ShapingOpportunity:
    """Specific opportunity shaping intelligence"""
    
    # Opportunity Identification
    opportunity_id: str
    opportunity_title: str
    agency: str
    office: str
    estimated_value: float
    
    # Timing Intelligence
    current_phase: ShapingPhase
    phase_timeline: Dict[str, str]  # phase -> expected date
    shaping_window: Tuple[str, str]  # start date, end date
    optimal_engagement_timing: List[Dict[str, str]]
    
    # Requirements Intelligence
    preliminary_requirements: List[str]
    requirements_flexibility: float  # 0-1 score
    technical_requirements: Dict[str, Any]
    performance_requirements: Dict[str, Any]
    emerging_requirements: List[str]
    
    # Stakeholder Mapping
    requirements_owners: List[str]
    technical_evaluators: List[str]
    budget_decision_makers: List[str]
    end_users: List[str]
    contracting_personnel: List[str]
    
    # Competitive Intelligence
    likely_competitors: List[Dict[str, Any]]
    incumbent_advantages: List[str]
    market_gaps: List[str]
    differentiation_opportunities: List[str]
    
    # Shaping Strategy
    shaping_objectives: List[str]
    influence_tactics: List[Dict[str, Any]]
    engagement_plan: List[Dict[str, Any]]
    message_strategy: Dict[str, List[str]]
    
    # Risk Assessment
    shaping_risks: List[str]
    mitigation_strategies: List[str]
    success_probability: float

@dataclass
class ShapingTactic:
    """Specific shaping tactic with implementation guidance"""
    
    tactic_name: str
    tactic_type: EngagementType
    target_stakeholders: List[str]
    
    # Implementation Details
    execution_timeline: str
    required_resources: List[str]
    preparation_requirements: List[str]
    success_metrics: List[str]
    
    # Message Strategy
    key_messages: List[str]
    supporting_evidence: List[str]
    technical_content: List[str]
    business_case_elements: List[str]
    
    # Execution Guidance
    optimal_format: str  # meeting, presentation, demo, etc.
    duration_recommendation: str
    attendee_recommendations: List[str]
    follow_up_actions: List[str]
    
    # Risk Factors
    execution_risks: List[str]
    contingency_plans: List[str]

@dataclass
class ShapingCampaign:
    """Comprehensive opportunity shaping campaign"""
    
    campaign_id: str
    opportunity: ShapingOpportunity
    campaign_timeline: str
    
    # Campaign Strategy
    strategic_objectives: List[str]
    success_criteria: List[str]
    key_performance_indicators: List[str]
    
    # Tactical Execution
    shaping_tactics: List[ShapingTactic]
    engagement_sequence: List[Dict[str, str]]
    milestone_checkpoints: List[Dict[str, Any]]
    
    # Resource Planning
    budget_requirements: Dict[str, float]
    personnel_requirements: List[str]
    timeline_dependencies: List[str]
    
    # Monitoring & Adaptation
    progress_indicators: List[str]
    adaptation_triggers: List[str]
    contingency_scenarios: List[Dict[str, Any]]

class OpportunityShapingEngine:
    """
    Advanced engine for opportunity shaping strategy and execution guidance
    Provides SMBs with detailed, actionable intelligence for pre-RFP market shaping
    """
    
    def __init__(self):
        # Integration with other KBI Labs components
        from .agency_intelligence_mapper import AgencyIntelligenceMapper
        from .personnel_intelligence_system import PersonnelIntelligenceSystem
        from .budget_program_analyzer import BudgetProgramAnalyzer
        
        self.agency_mapper = AgencyIntelligenceMapper()
        self.personnel_system = PersonnelIntelligenceSystem()
        self.budget_analyzer = BudgetProgramAnalyzer()
        
        # Shaping intelligence components
        self.opportunity_identifier = OpportunityIdentifier()
        self.requirements_analyzer = RequirementsAnalyzer()
        self.stakeholder_mapper = StakeholderMapper()
        self.competitive_analyzer = CompetitiveIntelligenceAnalyzer()
        self.tactic_generator = ShapingTacticGenerator()
    
    async def identify_shaping_opportunities(
        self, 
        agency_code: str,
        focus_areas: List[str] = None,
        value_threshold: float = 100000,
        time_horizon_months: int = 18
    ) -> List[ShapingOpportunity]:
        """
        Identify and analyze opportunities suitable for strategic shaping
        
        Args:
            agency_code: Target agency
            focus_areas: Technology/service areas of interest
            value_threshold: Minimum contract value to consider
            time_horizon_months: How far ahead to look
            
        Returns:
            List of identified shaping opportunities
        """
        
        logger.info(f"Identifying shaping opportunities for agency {agency_code}")
        
        try:
            # 1. Scan for emerging opportunities
            emerging_opportunities = await self._scan_emerging_opportunities(
                agency_code, focus_areas, value_threshold, time_horizon_months
            )
            
            # 2. Analyze each opportunity for shaping potential
            shaping_opportunities = []
            for opp_data in emerging_opportunities:
                
                # Assess shaping viability
                shaping_viability = await self._assess_shaping_viability(opp_data)
                
                if shaping_viability['viable']:
                    # Build comprehensive shaping opportunity
                    shaping_opp = await self._build_shaping_opportunity(opp_data)
                    shaping_opportunities.append(shaping_opp)
            
            # 3. Prioritize opportunities
            prioritized_opportunities = self._prioritize_shaping_opportunities(shaping_opportunities)
            
            logger.info(f"Identified {len(prioritized_opportunities)} shaping opportunities")
            return prioritized_opportunities
            
        except Exception as e:
            logger.error(f"Error identifying shaping opportunities: {str(e)}")
            raise
    
    async def develop_shaping_campaign(
        self, 
        opportunity: ShapingOpportunity,
        company_profile: Dict[str, Any],
        resource_constraints: Dict[str, Any] = None
    ) -> ShapingCampaign:
        """
        Develop comprehensive shaping campaign for specific opportunity
        
        Args:
            opportunity: Target shaping opportunity
            company_profile: SMB company capabilities and constraints
            resource_constraints: Budget, time, personnel constraints
            
        Returns:
            Detailed shaping campaign with tactical guidance
        """
        
        logger.info(f"Developing shaping campaign for: {opportunity.opportunity_title}")
        
        try:
            # 1. Strategic Analysis
            strategic_analysis = await self._conduct_strategic_analysis(
                opportunity, company_profile
            )
            
            # 2. Stakeholder Engagement Planning
            stakeholder_plan = await self._develop_stakeholder_engagement_plan(
                opportunity, company_profile
            )
            
            # 3. Tactical Development
            shaping_tactics = await self._develop_shaping_tactics(
                opportunity, company_profile, resource_constraints
            )
            
            # 4. Campaign Timeline
            campaign_timeline = await self._create_campaign_timeline(
                opportunity, shaping_tactics
            )
            
            # 5. Resource Planning
            resource_plan = await self._plan_campaign_resources(
                shaping_tactics, resource_constraints
            )
            
            # 6. Monitoring Framework
            monitoring_framework = await self._create_monitoring_framework(opportunity)
            
            # 7. Compile Campaign
            campaign = ShapingCampaign(
                campaign_id=f"CAMP_{opportunity.opportunity_id}_{datetime.now().strftime('%Y%m%d')}",
                opportunity=opportunity,
                campaign_timeline=campaign_timeline['overall_timeline'],
                strategic_objectives=strategic_analysis['objectives'],
                success_criteria=strategic_analysis['success_criteria'],
                key_performance_indicators=strategic_analysis['kpis'],
                shaping_tactics=shaping_tactics,
                engagement_sequence=stakeholder_plan['sequence'],
                milestone_checkpoints=campaign_timeline['milestones'],
                budget_requirements=resource_plan['budget'],
                personnel_requirements=resource_plan['personnel'],
                timeline_dependencies=resource_plan['dependencies'],
                progress_indicators=monitoring_framework['indicators'],
                adaptation_triggers=monitoring_framework['triggers'],
                contingency_scenarios=monitoring_framework['contingencies']
            )
            
            logger.info(f"Shaping campaign developed: {len(shaping_tactics)} tactics")
            return campaign
            
        except Exception as e:
            logger.error(f"Error developing shaping campaign: {str(e)}")
            raise
    
    async def _scan_emerging_opportunities(
        self, 
        agency_code: str,
        focus_areas: List[str],
        value_threshold: float,
        time_horizon_months: int
    ) -> List[Dict[str, Any]]:
        """Scan for emerging opportunities in agency"""
        
        opportunities = []
        
        # 1. Budget analysis for upcoming procurements
        budget_opportunities = await self._scan_budget_signals(
            agency_code, value_threshold, time_horizon_months
        )
        
        # 2. Strategic plan analysis
        strategic_opportunities = await self._scan_strategic_plans(
            agency_code, focus_areas
        )
        
        # 3. Market research notices
        market_research_opportunities = await self._scan_market_research(
            agency_code, focus_areas
        )
        
        # 4. Congressional intelligence
        congressional_opportunities = await self._scan_congressional_intelligence(
            agency_code, time_horizon_months
        )
        
        # 5. Industry intelligence
        industry_opportunities = await self._scan_industry_intelligence(
            agency_code, focus_areas
        )
        
        # Merge and deduplicate opportunities
        all_opportunities = (
            budget_opportunities + strategic_opportunities + 
            market_research_opportunities + congressional_opportunities + 
            industry_opportunities
        )
        
        opportunities = self._deduplicate_opportunities(all_opportunities)
        
        return opportunities
    
    async def _assess_shaping_viability(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess whether opportunity is viable for shaping efforts"""
        
        viability_factors = {
            'timeline_adequate': False,
            'requirements_flexible': False,
            'stakeholder_accessible': False,
            'competitive_advantage_possible': False,
            'resource_requirements_reasonable': False
        }
        
        # Timeline assessment
        if opportunity_data.get('estimated_timeline_months', 0) >= 6:
            viability_factors['timeline_adequate'] = True
        
        # Requirements flexibility assessment
        requirements_stage = opportunity_data.get('requirements_stage', 'unknown')
        if requirements_stage in ['concept', 'early_development', 'draft']:
            viability_factors['requirements_flexible'] = True
        
        # Stakeholder accessibility
        stakeholder_count = len(opportunity_data.get('known_stakeholders', []))
        if stakeholder_count >= 3:
            viability_factors['stakeholder_accessible'] = True
        
        # Competitive advantage potential
        market_maturity = opportunity_data.get('market_maturity', 'unknown')
        if market_maturity in ['emerging', 'developing']:
            viability_factors['competitive_advantage_possible'] = True
        
        # Resource requirements
        estimated_effort = opportunity_data.get('estimated_shaping_effort', 'unknown')
        if estimated_effort in ['low', 'medium']:
            viability_factors['resource_requirements_reasonable'] = True
        
        # Overall viability assessment
        viable_count = sum(viability_factors.values())
        overall_viable = viable_count >= 3  # Need at least 3 positive factors
        
        return {
            'viable': overall_viable,
            'viability_score': viable_count / len(viability_factors),
            'factors': viability_factors,
            'recommendations': self._generate_viability_recommendations(viability_factors)
        }
    
    async def _build_shaping_opportunity(self, opportunity_data: Dict[str, Any]) -> ShapingOpportunity:
        """Build comprehensive shaping opportunity from raw data"""
        
        # Extract basic opportunity information
        opp_id = opportunity_data.get('id', f"OPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Analyze timing and phases
        phase_analysis = await self._analyze_opportunity_phases(opportunity_data)
        
        # Requirements analysis
        requirements_analysis = await self._analyze_requirements(opportunity_data)
        
        # Stakeholder mapping
        stakeholder_analysis = await self._map_opportunity_stakeholders(opportunity_data)
        
        # Competitive analysis
        competitive_analysis = await self._analyze_competitive_landscape(opportunity_data)
        
        # Develop initial shaping strategy
        initial_strategy = await self._develop_initial_shaping_strategy(
            opportunity_data, requirements_analysis, stakeholder_analysis, competitive_analysis
        )
        
        return ShapingOpportunity(
            opportunity_id=opp_id,
            opportunity_title=opportunity_data.get('title', 'Unknown Opportunity'),
            agency=opportunity_data.get('agency', ''),
            office=opportunity_data.get('office', ''),
            estimated_value=float(opportunity_data.get('estimated_value', 0)),
            current_phase=ShapingPhase(phase_analysis['current_phase']),
            phase_timeline=phase_analysis['timeline'],
            shaping_window=phase_analysis['shaping_window'],
            optimal_engagement_timing=phase_analysis['optimal_timing'],
            preliminary_requirements=requirements_analysis['preliminary'],
            requirements_flexibility=requirements_analysis['flexibility_score'],
            technical_requirements=requirements_analysis['technical'],
            performance_requirements=requirements_analysis['performance'],
            emerging_requirements=requirements_analysis['emerging'],
            requirements_owners=stakeholder_analysis['requirements_owners'],
            technical_evaluators=stakeholder_analysis['technical_evaluators'],
            budget_decision_makers=stakeholder_analysis['budget_makers'],
            end_users=stakeholder_analysis['end_users'],
            contracting_personnel=stakeholder_analysis['contracting'],
            likely_competitors=competitive_analysis['competitors'],
            incumbent_advantages=competitive_analysis['incumbent_advantages'],
            market_gaps=competitive_analysis['market_gaps'],
            differentiation_opportunities=competitive_analysis['differentiation'],
            shaping_objectives=initial_strategy['objectives'],
            influence_tactics=initial_strategy['tactics'],
            engagement_plan=initial_strategy['engagement_plan'],
            message_strategy=initial_strategy['messages'],
            shaping_risks=initial_strategy['risks'],
            mitigation_strategies=initial_strategy['mitigations'],
            success_probability=initial_strategy['success_probability']
        )
    
    async def _develop_shaping_tactics(
        self, 
        opportunity: ShapingOpportunity,
        company_profile: Dict[str, Any],
        resource_constraints: Dict[str, Any]
    ) -> List[ShapingTactic]:
        """Develop specific shaping tactics for opportunity"""
        
        tactics = []
        
        # 1. Market Research Response Tactic
        if opportunity.current_phase in [ShapingPhase.MARKET_RESEARCH, ShapingPhase.REQUIREMENTS_DEVELOPMENT]:
            mr_tactic = await self._create_market_research_tactic(opportunity, company_profile)
            tactics.append(mr_tactic)
        
        # 2. Stakeholder Engagement Tactics
        stakeholder_tactics = await self._create_stakeholder_engagement_tactics(
            opportunity, company_profile
        )
        tactics.extend(stakeholder_tactics)
        
        # 3. Technical Demonstration Tactic
        if self._should_include_tech_demo(opportunity, company_profile):
            tech_demo_tactic = await self._create_tech_demo_tactic(opportunity, company_profile)
            tactics.append(tech_demo_tactic)
        
        # 4. White Paper/Capability Brief Tactic
        white_paper_tactic = await self._create_white_paper_tactic(opportunity, company_profile)
        tactics.append(white_paper_tactic)
        
        # 5. Partnership Development Tactic
        if opportunity.estimated_value > 1000000:  # Large opportunities
            partnership_tactic = await self._create_partnership_tactic(opportunity, company_profile)
            tactics.append(partnership_tactic)
        
        # Filter tactics based on resource constraints
        if resource_constraints:
            tactics = self._filter_tactics_by_resources(tactics, resource_constraints)
        
        return tactics
    
    async def _create_market_research_tactic(
        self, 
        opportunity: ShapingOpportunity, 
        company_profile: Dict[str, Any]
    ) -> ShapingTactic:
        """Create market research response tactic"""
        
        return ShapingTactic(
            tactic_name="Strategic Market Research Response",
            tactic_type=EngagementType.MARKET_RESEARCH_RESPONSE,
            target_stakeholders=opportunity.requirements_owners + opportunity.technical_evaluators,
            execution_timeline="Within 2 weeks of market research notice",
            required_resources=["Technical SME", "Business Development", "Proposal Writer"],
            preparation_requirements=[
                "Research agency pain points",
                "Develop technical approach overview",
                "Prepare capability demonstrations",
                "Identify potential partnerships"
            ],
            success_metrics=[
                "Follow-up meeting requested",
                "Included in vendor communication list",
                "Requirements feedback incorporated",
                "Technical approach validated"
            ],
            key_messages=self._generate_market_research_messages(opportunity, company_profile),
            supporting_evidence=[
                "Relevant past performance examples",
                "Technical capability demonstrations",
                "Innovation case studies",
                "Cost-effectiveness data"
            ],
            technical_content=self._generate_technical_content(opportunity, company_profile),
            business_case_elements=[
                "Cost savings potential",
                "Risk mitigation approaches",
                "Implementation timeline advantages",
                "Long-term value proposition"
            ],
            optimal_format="Comprehensive written response with executive summary",
            duration_recommendation="10-15 page response document",
            attendee_recommendations=["Technical lead", "Program manager", "Business development"],
            follow_up_actions=[
                "Request clarification meeting",
                "Offer technical demonstration",
                "Propose pilot or prototype",
                "Submit additional technical materials"
            ],
            execution_risks=[
                "Generic response blends with competition",
                "Technical approach too advanced/simple",
                "Misalignment with agency priorities"
            ],
            contingency_plans=[
                "Develop multiple technical approach options",
                "Prepare varying levels of technical detail",
                "Create modular response sections"
            ]
        )
    
    def _generate_market_research_messages(
        self, 
        opportunity: ShapingOpportunity, 
        company_profile: Dict[str, Any]
    ) -> List[str]:
        """Generate key messages for market research response"""
        
        messages = [
            f"Proven experience in {', '.join(company_profile.get('core_capabilities', []))}",
            f"Deep understanding of {opportunity.agency} mission and challenges",
            "Innovative technical approach that reduces risk and cost",
            "Strong track record of on-time, on-budget delivery",
            "Commitment to small business utilization and partnership"
        ]
        
        # Add opportunity-specific messages
        if 'cybersecurity' in opportunity.opportunity_title.lower():
            messages.append("Advanced cybersecurity expertise with FedRAMP experience")
        
        if 'modernization' in opportunity.opportunity_title.lower():
            messages.append("Legacy system modernization expertise with minimal disruption")
        
        return messages
    
    def _generate_technical_content(
        self, 
        opportunity: ShapingOpportunity, 
        company_profile: Dict[str, Any]
    ) -> List[str]:
        """Generate technical content recommendations"""
        
        content = [
            "High-level technical architecture overview",
            "Key technical differentiators and innovations",
            "Risk mitigation technical approaches",
            "Scalability and performance considerations",
            "Security and compliance framework"
        ]
        
        # Add specific content based on opportunity
        for req in opportunity.technical_requirements:
            if isinstance(req, str):
                content.append(f"Technical approach for {req}")
        
        return content

class OpportunityIdentifier:
    """Specialized component for identifying emerging opportunities"""
    
    async def scan_budget_signals(self, agency_code: str) -> List[Dict[str, Any]]:
        """Scan budget documents for procurement signals"""
        # Implementation for budget signal scanning
        pass

class RequirementsAnalyzer:
    """Analyzer for government requirements development"""
    
    async def analyze_requirements_flexibility(self, opportunity_data: Dict) -> float:
        """Analyze how flexible requirements are for shaping"""
        # Implementation for requirements analysis
        pass

class StakeholderMapper:
    """Mapper for opportunity-specific stakeholders"""
    
    async def map_decision_makers(self, opportunity_data: Dict) -> Dict[str, List[str]]:
        """Map decision makers for specific opportunity"""
        # Implementation for stakeholder mapping
        pass

class CompetitiveIntelligenceAnalyzer:
    """Analyzer for competitive landscape"""
    
    async def analyze_competitive_dynamics(self, opportunity_data: Dict) -> Dict[str, Any]:
        """Analyze competitive dynamics for opportunity"""
        # Implementation for competitive analysis
        pass

class ShapingTacticGenerator:
    """Generator for specific shaping tactics"""
    
    async def generate_engagement_tactics(self, opportunity: ShapingOpportunity) -> List[ShapingTactic]:
        """Generate specific engagement tactics"""
        # Implementation for tactic generation
        pass

# Example usage
async def main():
    """Example: Develop opportunity shaping campaign"""
    
    shaping_engine = OpportunityShapingEngine()
    
    # Identify shaping opportunities in Department of Defense
    opportunities = await shaping_engine.identify_shaping_opportunities(
        agency_code='9700',
        focus_areas=['AI/ML', 'Cybersecurity', 'Cloud Computing'],
        value_threshold=500000,
        time_horizon_months=12
    )
    
    print(f"Identified {len(opportunities)} shaping opportunities")
    
    if opportunities:
        # Develop campaign for top opportunity
        top_opportunity = opportunities[0]
        
        company_profile = {
            'name': 'TechSolutions Inc',
            'core_capabilities': ['AI/ML', 'Cloud Computing', 'Data Analytics'],
            'past_performance': 'Strong DoD experience',
            'team_size': 50,
            'revenue': 10000000
        }
        
        campaign = await shaping_engine.develop_shaping_campaign(
            opportunity=top_opportunity,
            company_profile=company_profile,
            resource_constraints={'budget': 100000, 'timeline_months': 6}
        )
        
        print(f"Developed shaping campaign: {len(campaign.shaping_tactics)} tactics")
        print(f"Campaign timeline: {campaign.campaign_timeline}")
        print(f"Success probability: {top_opportunity.success_probability:.1%}")

if __name__ == "__main__":
    asyncio.run(main())