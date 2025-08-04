#!/usr/bin/env python3
"""
Personnel Intelligence System
Government Contact and Decision-Maker Intelligence Platform

This system identifies, maps, and profiles key government personnel for strategic
opportunity shaping, providing SMBs with detailed intelligence on who to approach,
when, and how for maximum effectiveness.
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
from pathlib import Path
import nltk
from textblob import TextBlob

logger = logging.getLogger(__name__)

class InfluenceLevel(Enum):
    EXECUTIVE = "Executive Leadership"
    SENIOR_MANAGEMENT = "Senior Management"
    MIDDLE_MANAGEMENT = "Middle Management"
    TECHNICAL_EXPERT = "Technical Expert"
    PROCUREMENT_SPECIALIST = "Procurement Specialist"
    SUPPORT_STAFF = "Support Staff"

class DecisionAuthority(Enum):
    FINAL_APPROVER = "Final Decision Authority"
    STRONG_INFLUENCER = "Strong Influencer"
    TECHNICAL_ADVISOR = "Technical Advisor"
    PROCUREMENT_GATEKEEPER = "Procurement Gatekeeper"
    BUDGET_CONTROLLER = "Budget Controller"
    REQUIREMENTS_OWNER = "Requirements Owner"
    EVALUATION_COMMITTEE = "Evaluation Committee Member"

class CommunicationStyle(Enum):
    FORMAL_EXECUTIVE = "Formal Executive"
    TECHNICAL_DETAILED = "Technical Detailed"
    RESULTS_ORIENTED = "Results Oriented"
    COLLABORATIVE = "Collaborative"
    DATA_DRIVEN = "Data Driven"
    RELATIONSHIP_FOCUSED = "Relationship Focused"

@dataclass
class PersonnelContact:
    """Comprehensive government personnel intelligence profile"""
    
    # Basic Information
    full_name: str
    title: str
    office: str
    agency: str
    grade_level: Optional[str]  # GS-15, SES, etc.
    
    # Contact Information
    email: Optional[str]
    phone: Optional[str]
    office_address: str
    mailing_address: Optional[str]
    
    # Organizational Intelligence
    direct_supervisor: Optional[str]
    direct_reports: List[str]
    reporting_chain: List[str]  # up to agency head
    matrix_relationships: List[str]  # cross-functional relationships
    
    # Authority & Influence
    influence_level: InfluenceLevel
    decision_authority: DecisionAuthority
    budget_authority: Optional[float]
    procurement_authority: Optional[float]
    technical_authority: List[str]  # areas of technical authority
    
    # Professional Background
    years_in_government: int
    years_in_current_role: float
    previous_positions: List[Dict[str, str]]
    education: List[Dict[str, str]]
    certifications: List[str]
    expertise_areas: List[str]
    
    # Network & Relationships
    internal_network: List[str]  # key internal relationships
    external_relationships: List[str]  # industry contacts
    mentor_relationships: List[str]
    professional_associations: List[str]
    
    # Communication Intelligence
    communication_style: CommunicationStyle
    preferred_meeting_types: List[str]  # "formal briefing", "technical demo", etc.
    optimal_contact_timing: Dict[str, str]  # best days/times
    response_patterns: Dict[str, str]  # typical response times
    
    # Strategic Intelligence
    current_priorities: List[str]
    pain_points: List[str]
    success_metrics: List[str]
    upcoming_challenges: List[str]
    strategic_initiatives: List[str]
    
    # Engagement History
    industry_interactions: List[Dict[str, Any]]
    conference_appearances: List[Dict[str, Any]]
    published_articles: List[Dict[str, Any]]
    public_statements: List[Dict[str, Any]]
    
    # Opportunity Intelligence
    procurement_involvement: List[str]  # recent procurements involved in
    upcoming_requirements: List[str]
    budget_planning_involvement: List[str]
    modernization_project_involvement: List[str]

@dataclass
class EngagementStrategy:
    """Personalized engagement strategy for government personnel"""
    
    target_person: str
    optimal_approach: str
    
    # Timing Strategy
    best_contact_window: str
    seasonal_considerations: List[str]
    budget_cycle_timing: str
    
    # Message Strategy
    key_value_propositions: List[str]
    technical_focus_areas: List[str]
    business_case_elements: List[str]
    risk_mitigation_themes: List[str]
    
    # Engagement Sequence
    initial_contact_method: str
    follow_up_sequence: List[Dict[str, str]]
    relationship_building_activities: List[str]
    
    # Supporting Intelligence
    mutual_connections: List[str]
    shared_interests: List[str]
    professional_commonalities: List[str]
    
    # Success Metrics
    engagement_kpis: List[str]
    relationship_milestones: List[str]

@dataclass
class DecisionMakingUnit:
    """Analysis of decision-making group for specific procurement"""
    
    procurement_title: str
    estimated_value: float
    decision_timeline: str
    
    # Key Stakeholders
    final_decision_maker: PersonnelContact
    technical_evaluators: List[PersonnelContact]
    procurement_team: List[PersonnelContact]
    budget_approvers: List[PersonnelContact]
    end_users: List[PersonnelContact]
    
    # Influence Mapping
    influence_network: Dict[str, List[str]]  # relationships between stakeholders
    power_dynamics: Dict[str, str]  # influence relationships
    coalition_opportunities: List[List[str]]  # potential supporter groups
    
    # Engagement Strategy
    engagement_sequence: List[Dict[str, str]]
    key_messages_by_stakeholder: Dict[str, List[str]]
    demonstration_opportunities: List[Dict[str, Any]]

class PersonnelIntelligenceSystem:
    """
    Advanced system for government personnel intelligence and engagement strategy
    Maps decision-makers, influencers, and provides detailed engagement guidance
    """
    
    def __init__(self):
        self.data_sources = {
            'fedscope': 'https://www.fedscope.opm.gov/api/',
            'usaspending': 'https://api.usaspending.gov/api/v2/',
            'sam_gov': 'https://api.sam.gov/data-services/',
            'linkedin': 'https://api.linkedin.com/v2/',
            'governmentexecutive': 'https://www.govexec.com/api/',
            'federalnews': 'https://federalnewsnetwork.com/api/',
            'fedweek': 'https://www.fedweek.com/api/'
        }
        
        # Intelligence components
        self.contact_mapper = GovernmentContactMapper()
        self.network_analyzer = PersonnelNetworkAnalyzer()
        self.engagement_strategist = EngagementStrategist()
        self.influence_mapper = InfluenceMapper()
    
    async def map_agency_personnel(
        self, 
        agency_code: str,
        focus_areas: List[str] = None,
        authority_levels: List[InfluenceLevel] = None
    ) -> List[PersonnelContact]:
        """
        Map comprehensive personnel intelligence for agency
        
        Args:
            agency_code: Agency identifier
            focus_areas: Specific program areas to focus on
            authority_levels: Target authority levels to map
            
        Returns:
            List of detailed personnel contacts
        """
        
        if authority_levels is None:
            authority_levels = [
                InfluenceLevel.EXECUTIVE,
                InfluenceLevel.SENIOR_MANAGEMENT,
                InfluenceLevel.PROCUREMENT_SPECIALIST
            ]
        
        logger.info(f"Mapping personnel for agency {agency_code}")
        
        try:
            # 1. Identify Key Personnel
            personnel_list = await self._identify_agency_personnel(agency_code, focus_areas)
            
            # 2. Enrich with Detailed Intelligence
            enriched_personnel = []
            for person_data in personnel_list:
                if self._meets_authority_criteria(person_data, authority_levels):
                    enriched_person = await self._enrich_personnel_profile(person_data)
                    enriched_personnel.append(enriched_person)
            
            # 3. Map Relationships and Networks
            enriched_personnel = await self._map_personnel_networks(enriched_personnel)
            
            # 4. Add Strategic Intelligence
            enriched_personnel = await self._add_strategic_intelligence(enriched_personnel)
            
            logger.info(f"Personnel mapping complete: {len(enriched_personnel)} profiles")
            return enriched_personnel
            
        except Exception as e:
            logger.error(f"Error mapping agency personnel: {str(e)}")
            raise
    
    async def analyze_decision_making_unit(
        self, 
        procurement_opportunity: Dict[str, Any],
        agency_personnel: List[PersonnelContact]
    ) -> DecisionMakingUnit:
        """
        Analyze decision-making unit for specific procurement opportunity
        
        Args:
            procurement_opportunity: Details of the procurement
            agency_personnel: Available personnel intelligence
            
        Returns:
            Comprehensive decision-making unit analysis
        """
        
        logger.info(f"Analyzing DMU for: {procurement_opportunity.get('title', 'Unknown')}")
        
        try:
            # 1. Identify Key Decision Makers
            decision_makers = await self._identify_decision_makers(
                procurement_opportunity, agency_personnel
            )
            
            # 2. Map Influence Networks
            influence_network = await self._map_influence_networks(decision_makers)
            
            # 3. Analyze Power Dynamics
            power_dynamics = await self._analyze_power_dynamics(decision_makers)
            
            # 4. Develop Engagement Strategy
            engagement_strategy = await self._develop_dmu_engagement_strategy(
                decision_makers, influence_network
            )
            
            # 5. Compile Decision Making Unit
            dmu = DecisionMakingUnit(
                procurement_title=procurement_opportunity.get('title', ''),
                estimated_value=float(procurement_opportunity.get('value', 0)),
                decision_timeline=procurement_opportunity.get('timeline', ''),
                final_decision_maker=decision_makers['final_authority'],
                technical_evaluators=decision_makers['technical_team'],
                procurement_team=decision_makers['procurement_team'],
                budget_approvers=decision_makers['budget_team'],
                end_users=decision_makers['end_users'],
                influence_network=influence_network,
                power_dynamics=power_dynamics,
                coalition_opportunities=engagement_strategy['coalitions'],
                engagement_sequence=engagement_strategy['sequence'],
                key_messages_by_stakeholder=engagement_strategy['messages'],
                demonstration_opportunities=engagement_strategy['demonstrations']
            )
            
            logger.info(f"DMU analysis complete: {len(decision_makers['all'])} stakeholders")
            return dmu
            
        except Exception as e:
            logger.error(f"Error analyzing decision-making unit: {str(e)}")
            raise
    
    async def generate_engagement_strategy(
        self, 
        target_personnel: List[PersonnelContact],
        business_objective: str,
        company_profile: Dict[str, Any]
    ) -> List[EngagementStrategy]:
        """
        Generate personalized engagement strategies for target personnel
        
        Args:
            target_personnel: List of personnel to engage
            business_objective: What you're trying to achieve
            company_profile: Your company's capabilities and background
            
        Returns:
            Personalized engagement strategies for each person
        """
        
        engagement_strategies = []
        
        for person in target_personnel:
            
            # Analyze optimal engagement approach
            approach_analysis = await self._analyze_optimal_approach(
                person, business_objective, company_profile
            )
            
            # Develop timing strategy
            timing_strategy = await self._develop_timing_strategy(person)
            
            # Create message strategy
            message_strategy = await self._create_message_strategy(
                person, business_objective, company_profile
            )
            
            # Plan engagement sequence
            engagement_sequence = await self._plan_engagement_sequence(person)
            
            # Identify mutual connections
            mutual_connections = await self._identify_mutual_connections(
                person, company_profile
            )
            
            strategy = EngagementStrategy(
                target_person=person.full_name,
                optimal_approach=approach_analysis['approach'],
                best_contact_window=timing_strategy['contact_window'],
                seasonal_considerations=timing_strategy['seasonal_factors'],
                budget_cycle_timing=timing_strategy['budget_timing'],
                key_value_propositions=message_strategy['value_props'],
                technical_focus_areas=message_strategy['technical_focus'],
                business_case_elements=message_strategy['business_case'],
                risk_mitigation_themes=message_strategy['risk_mitigation'],
                initial_contact_method=engagement_sequence['initial_method'],
                follow_up_sequence=engagement_sequence['follow_ups'],
                relationship_building_activities=engagement_sequence['relationship_building'],
                mutual_connections=mutual_connections['connections'],
                shared_interests=mutual_connections['interests'],
                professional_commonalities=mutual_connections['commonalities'],
                engagement_kpis=approach_analysis['success_metrics'],
                relationship_milestones=approach_analysis['milestones']
            )
            
            engagement_strategies.append(strategy)
        
        return engagement_strategies
    
    async def _identify_agency_personnel(
        self, 
        agency_code: str, 
        focus_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """Identify key personnel within agency and focus areas"""
        
        personnel_data = []
        
        # 1. Federal personnel databases
        fedscope_data = await self._fetch_fedscope_personnel(agency_code)
        
        # 2. Organizational charts from agency websites
        org_chart_data = await self._scrape_agency_org_charts(agency_code)
        
        # 3. USASpending contracting officer data
        co_data = await self._fetch_contracting_officers(agency_code)
        
        # 4. Public directory information
        public_directory_data = await self._fetch_public_directories(agency_code)
        
        # 5. Professional network data
        professional_data = await self._fetch_professional_network_data(agency_code)
        
        # Merge and deduplicate personnel data
        personnel_data = self._merge_personnel_data([
            fedscope_data, org_chart_data, co_data, 
            public_directory_data, professional_data
        ])
        
        # Filter by focus areas if specified
        if focus_areas:
            personnel_data = self._filter_by_focus_areas(personnel_data, focus_areas)
        
        return personnel_data
    
    async def _enrich_personnel_profile(self, person_data: Dict[str, Any]) -> PersonnelContact:
        """Enrich basic personnel data with comprehensive intelligence"""
        
        # Professional background research
        background = await self._research_professional_background(person_data)
        
        # Network and relationships analysis
        network_data = await self._analyze_professional_network(person_data)
        
        # Authority and influence assessment
        authority_data = await self._assess_authority_influence(person_data)
        
        # Communication style analysis
        comm_style = await self._analyze_communication_style(person_data)
        
        # Strategic context research
        strategic_context = await self._research_strategic_context(person_data)
        
        # Engagement history analysis
        engagement_history = await self._analyze_engagement_history(person_data)
        
        # Opportunity intelligence
        opportunity_intel = await self._gather_opportunity_intelligence(person_data)
        
        return PersonnelContact(
            full_name=person_data['name'],
            title=person_data['title'],
            office=person_data['office'],
            agency=person_data['agency'],
            grade_level=person_data.get('grade_level'),
            email=person_data.get('email'),
            phone=person_data.get('phone'),
            office_address=person_data.get('office_address', ''),
            mailing_address=person_data.get('mailing_address'),
            direct_supervisor=network_data.get('supervisor'),
            direct_reports=network_data.get('reports', []),
            reporting_chain=network_data.get('chain', []),
            matrix_relationships=network_data.get('matrix', []),
            influence_level=InfluenceLevel(authority_data['influence_level']),
            decision_authority=DecisionAuthority(authority_data['decision_authority']),
            budget_authority=authority_data.get('budget_authority'),
            procurement_authority=authority_data.get('procurement_authority'),
            technical_authority=authority_data.get('technical_authority', []),
            years_in_government=background.get('gov_years', 0),
            years_in_current_role=background.get('current_role_years', 0),
            previous_positions=background.get('previous_positions', []),
            education=background.get('education', []),
            certifications=background.get('certifications', []),
            expertise_areas=background.get('expertise', []),
            internal_network=network_data.get('internal_network', []),
            external_relationships=network_data.get('external_relationships', []),
            mentor_relationships=network_data.get('mentors', []),
            professional_associations=network_data.get('associations', []),
            communication_style=CommunicationStyle(comm_style['style']),
            preferred_meeting_types=comm_style.get('meeting_preferences', []),
            optimal_contact_timing=comm_style.get('contact_timing', {}),
            response_patterns=comm_style.get('response_patterns', {}),
            current_priorities=strategic_context.get('priorities', []),
            pain_points=strategic_context.get('pain_points', []),
            success_metrics=strategic_context.get('success_metrics', []),
            upcoming_challenges=strategic_context.get('challenges', []),
            strategic_initiatives=strategic_context.get('initiatives', []),
            industry_interactions=engagement_history.get('industry_interactions', []),
            conference_appearances=engagement_history.get('conferences', []),
            published_articles=engagement_history.get('articles', []),
            public_statements=engagement_history.get('statements', []),
            procurement_involvement=opportunity_intel.get('procurements', []),
            upcoming_requirements=opportunity_intel.get('upcoming_requirements', []),
            budget_planning_involvement=opportunity_intel.get('budget_planning', []),
            modernization_project_involvement=opportunity_intel.get('modernization', [])
        )
    
    async def _research_professional_background(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Research comprehensive professional background"""
        
        background = {
            'gov_years': 0,
            'current_role_years': 0,
            'previous_positions': [],
            'education': [],
            'certifications': [],
            'expertise': []
        }
        
        # Search professional databases
        name = person_data['name']
        
        # LinkedIn professional data
        linkedin_data = await self._search_linkedin_profile(name)
        if linkedin_data:
            background.update(self._parse_linkedin_background(linkedin_data))
        
        # Government biographical data
        gov_bio_data = await self._search_government_bios(name)
        if gov_bio_data:
            background.update(self._parse_government_bio(gov_bio_data))
        
        # Professional publication searches
        publication_data = await self._search_professional_publications(name)
        if publication_data:
            background['expertise'].extend(self._extract_expertise_from_publications(publication_data))
        
        # Conference and speaking engagement data
        speaking_data = await self._search_speaking_engagements(name)
        if speaking_data:
            background['expertise'].extend(self._extract_expertise_from_speaking(speaking_data))
        
        return background
    
    async def _analyze_communication_style(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze communication style and preferences"""
        
        comm_analysis = {
            'style': 'FORMAL_EXECUTIVE',  # default
            'meeting_preferences': [],
            'contact_timing': {},
            'response_patterns': {}
        }
        
        # Analyze public communications
        public_comms = await self._gather_public_communications(person_data['name'])
        
        if public_comms:
            # Analyze communication style from public statements
            style_analysis = self._analyze_writing_style(public_comms)
            comm_analysis['style'] = style_analysis['primary_style']
            
            # Extract meeting and communication preferences
            comm_analysis['meeting_preferences'] = style_analysis['meeting_preferences']
        
        # Analyze role-based communication patterns
        role_patterns = self._get_role_communication_patterns(person_data['title'])
        comm_analysis.update(role_patterns)
        
        return comm_analysis
    
    def _analyze_writing_style(self, communications: List[str]) -> Dict[str, Any]:
        """Analyze writing style to determine communication preferences"""
        
        # Combine all communications
        text = ' '.join(communications)
        
        # Use TextBlob for basic analysis
        blob = TextBlob(text)
        
        # Analyze style characteristics
        avg_sentence_length = np.mean([len(sentence.words) for sentence in blob.sentences])
        complexity_score = len([word for word in blob.words if len(word) > 6]) / len(blob.words)
        technical_terms = len([word for word in blob.words if self._is_technical_term(word.lower())])
        
        # Determine communication style
        if avg_sentence_length > 20 and complexity_score > 0.3:
            primary_style = 'TECHNICAL_DETAILED'
        elif technical_terms > 10:
            primary_style = 'DATA_DRIVEN'
        elif 'result' in text.lower() or 'outcome' in text.lower():
            primary_style = 'RESULTS_ORIENTED'
        else:
            primary_style = 'FORMAL_EXECUTIVE'
        
        return {
            'primary_style': primary_style,
            'meeting_preferences': self._infer_meeting_preferences(primary_style),
            'complexity_score': complexity_score,
            'technical_focus': technical_terms > 5
        }
    
    def _is_technical_term(self, word: str) -> bool:
        """Check if word is likely a technical term"""
        technical_indicators = [
            'api', 'system', 'technology', 'platform', 'infrastructure',
            'cybersecurity', 'cloud', 'data', 'analytics', 'software',
            'hardware', 'network', 'security', 'integration', 'architecture'
        ]
        return word in technical_indicators or len(word) > 8
    
    def _infer_meeting_preferences(self, communication_style: str) -> List[str]:
        """Infer meeting preferences based on communication style"""
        
        preferences_map = {
            'TECHNICAL_DETAILED': ['technical demo', 'deep-dive session', 'whiteboard session'],
            'DATA_DRIVEN': ['data presentation', 'analytics review', 'metrics briefing'],
            'RESULTS_ORIENTED': ['executive briefing', 'roi presentation', 'success story'],
            'FORMAL_EXECUTIVE': ['formal presentation', 'executive briefing', 'structured meeting'],
            'COLLABORATIVE': ['workshop', 'collaborative session', 'team meeting'],
            'RELATIONSHIP_FOCUSED': ['informal meeting', 'networking event', 'one-on-one']
        }
        
        return preferences_map.get(communication_style, ['formal presentation'])

class GovernmentContactMapper:
    """Specialized mapper for government contact information"""
    
    async def map_contacts_by_function(self, agency_code: str, function: str) -> List[Dict]:
        """Map contacts by specific government function"""
        # Implementation for function-based contact mapping
        pass

class PersonnelNetworkAnalyzer:
    """Analyzer for personnel networks and relationships"""
    
    async def analyze_influence_network(self, personnel: List[PersonnelContact]) -> Dict[str, Any]:
        """Analyze influence networks within personnel group"""
        # Implementation for network analysis
        pass

class EngagementStrategist:
    """Strategic planner for personnel engagement"""
    
    async def develop_engagement_plan(self, target: PersonnelContact, objective: str) -> Dict[str, Any]:
        """Develop comprehensive engagement plan"""
        # Implementation for engagement planning
        pass

class InfluenceMapper:
    """Mapper for influence relationships and power dynamics"""
    
    async def map_decision_influence(self, personnel: List[PersonnelContact]) -> Dict[str, Any]:
        """Map decision-making influence relationships"""
        # Implementation for influence mapping
        pass

# Example usage
async def main():
    """Example: Map personnel intelligence for agency"""
    
    personnel_system = PersonnelIntelligenceSystem()
    
    # Map Department of Defense personnel
    dod_personnel = await personnel_system.map_agency_personnel(
        agency_code='9700',
        focus_areas=['AI/ML', 'Cybersecurity', 'Cloud Computing'],
        authority_levels=[InfluenceLevel.EXECUTIVE, InfluenceLevel.SENIOR_MANAGEMENT]
    )
    
    print(f"DoD Personnel Intelligence:")
    print(f"- {len(dod_personnel)} key personnel mapped")
    print(f"- Authority levels: {set([p.influence_level.value for p in dod_personnel])}")
    
    # Generate engagement strategies
    engagement_strategies = await personnel_system.generate_engagement_strategy(
        target_personnel=dod_personnel[:5],  # Top 5 targets
        business_objective="Win AI/ML modernization contract",
        company_profile={'name': 'TechCorp', 'capabilities': ['AI/ML', 'Cloud'], 'past_performance': 'Strong'}
    )
    
    print(f"- {len(engagement_strategies)} engagement strategies generated")

if __name__ == "__main__":
    asyncio.run(main())