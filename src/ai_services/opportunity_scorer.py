"""
KBI Labs AI-Powered Opportunity Scoring Engine
Advanced ML-based evaluation of government contracting opportunities
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
import json
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib

# For ML capabilities (install with: pip install scikit-learn)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available - using simplified scoring")

logger = logging.getLogger(__name__)

@dataclass
class CompanyProfile:
    """Company profile for personalized scoring"""
    primary_naics: List[str]
    capabilities: List[str]
    security_clearance: bool
    small_business: bool
    preferred_agencies: List[str]
    team_size: int
    max_contract_value: float
    past_performance_score: float = 0.8

@dataclass
class ScoringWeights:
    """Configurable weights for different scoring factors"""
    value_alignment: float = 0.25
    competitive_analysis: float = 0.20
    agency_relationship: float = 0.15
    technical_match: float = 0.15
    financial_viability: float = 0.10
    time_constraints: float = 0.10
    risk_assessment: float = 0.05

class OpportunityScorer:
    """Advanced ML-powered opportunity evaluation and scoring system"""
    
    def __init__(self, company_profile: Optional[CompanyProfile] = None):
        self.version = "2.0.0"
        self.model = None
        self.features = []
        self.is_trained = False
        
        # Default company profile
        self.company_profile = company_profile or CompanyProfile(
            primary_naics=['541511', '541512', '541513'],  # IT services
            capabilities=['cloud computing', 'cybersecurity', 'software development', 
                         'it consulting', 'data analytics', 'system integration'],
            security_clearance=True,
            small_business=True,
            preferred_agencies=['DoD', 'DHS', 'VA', 'GSA'],
            team_size=25,
            max_contract_value=5_000_000,
            past_performance_score=0.85
        )
        
        self.weights = ScoringWeights()
        
        # Initialize text processing
        if SKLEARN_AVAILABLE:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.scaler = MinMaxScaler()
        
        # Cache for performance
        self._scoring_cache = {}
        
        logger.info(f"OpportunityScorer v{self.version} initialized")
    
    def score_opportunity(self, opportunity_data: Dict) -> Dict:
        """
        Score a single opportunity using advanced AI/ML models
        
        Args:
            opportunity_data: Raw opportunity data from government APIs
            
        Returns:
            Dictionary with comprehensive scoring results and recommendations
        """
        start_time = datetime.now()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(opportunity_data)
            if cache_key in self._scoring_cache:
                cached_result = self._scoring_cache[cache_key]
                logger.debug(f"Returning cached score for opportunity {opportunity_data.get('id', 'unknown')}")
                return cached_result
            
            # Normalize and extract features
            normalized_opp = self._normalize_opportunity_data(opportunity_data)
            features = self._extract_features(normalized_opp)
            
            # Calculate individual factor scores
            factor_scores = {
                'value_alignment': self._calculate_value_alignment(normalized_opp, features),
                'competitive_analysis': self._calculate_competitive_analysis(normalized_opp, features),
                'agency_relationship': self._calculate_agency_relationship(normalized_opp, features),
                'technical_match': self._calculate_technical_match(normalized_opp, features),
                'financial_viability': self._calculate_financial_viability(normalized_opp, features),
                'time_constraints': self._calculate_time_constraints(normalized_opp, features),
                'risk_assessment': self._calculate_risk_assessment(normalized_opp, features)
            }
            
            # Calculate weighted overall score
            overall_score = self._calculate_weighted_score(factor_scores)
            
            # Generate recommendation and confidence
            recommendation = self._generate_recommendation(overall_score, factor_scores)
            confidence = self._calculate_confidence(factor_scores, features)
            win_probability = self._calculate_win_probability(overall_score, factor_scores)
            
            # Generate detailed analysis
            analysis = self._generate_detailed_analysis(normalized_opp, factor_scores, overall_score)
            
            # Processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                'opportunity_id': normalized_opp.get('id', 'unknown'),
                'overall_score': round(overall_score, 1),
                'recommendation': recommendation['action'],
                'recommendation_priority': recommendation['priority'],
                'confidence': round(confidence * 100),
                'win_probability': round(win_probability),
                
                'factor_scores': {k: round(v, 1) for k, v in factor_scores.items()},
                
                'analysis': {
                    'strengths': analysis['strengths'],
                    'concerns': analysis['concerns'],
                    'recommendations': analysis['recommendations'],
                    'reasoning': analysis['reasoning']
                },
                
                'metadata': {
                    'scorer_version': self.version,
                    'processing_time_ms': round(processing_time, 2),
                    'timestamp': datetime.now().isoformat(),
                    'ml_features_used': SKLEARN_AVAILABLE,
                    'cache_key': cache_key
                }
            }
            
            # Cache the result
            self._scoring_cache[cache_key] = result
            
            logger.info(f"Scored opportunity {normalized_opp.get('id')}: {overall_score:.1f} ({recommendation['action']})")
            
            return result
            
        except Exception as error:
            logger.error(f"Scoring error for opportunity {opportunity_data.get('id', 'unknown')}: {error}")
            return self._generate_fallback_score(opportunity_data, str(error))
    
    def _normalize_opportunity_data(self, opportunity_data: Dict) -> Dict:
        """Normalize opportunity data from various government API formats"""
        return {
            'id': opportunity_data.get('id') or opportunity_data.get('notice_id') or f"opp_{hash(str(opportunity_data))%10000}",
            'title': opportunity_data.get('title') or opportunity_data.get('solicitation_number') or 'Unknown Opportunity',
            'description': opportunity_data.get('description') or opportunity_data.get('synopsis') or '',
            'agency': opportunity_data.get('agency') or opportunity_data.get('department') or 'Unknown Agency',
            'naics_codes': opportunity_data.get('naics_codes') or opportunity_data.get('naics') or [],
            'set_aside': opportunity_data.get('set_aside_code') or opportunity_data.get('set_aside'),
            'value': self._parse_contract_value(opportunity_data.get('award_amount') or opportunity_data.get('estimated_value')),
            'deadline': opportunity_data.get('response_date') or opportunity_data.get('due_date'),
            'posted_date': opportunity_data.get('posted_date') or opportunity_data.get('created_date'),
            'location': opportunity_data.get('place_of_performance') or opportunity_data.get('location'),
            'classification': opportunity_data.get('classification_code'),
            'contact_info': opportunity_data.get('contact_info') or {},
            'requirements': opportunity_data.get('requirements') or [],
            'raw_data': opportunity_data
        }
    
    def _extract_features(self, opportunity: Dict) -> Dict:
        """Extract and engineer features for ML processing"""
        features = {}
        
        # Text features
        combined_text = f"{opportunity['title']} {opportunity['description']}"
        features['text_length'] = len(combined_text)
        features['word_count'] = len(combined_text.split())
        
        # Keyword features
        keywords = {
            'cloud': ['cloud', 'aws', 'azure', 'gcp'],
            'security': ['security', 'cyber', 'clearance', 'classified'],
            'software': ['software', 'development', 'programming', 'code'],
            'data': ['data', 'analytics', 'database', 'big data'],
            'network': ['network', 'infrastructure', 'system']
        }
        
        for category, words in keywords.items():
            features[f'has_{category}'] = any(word in combined_text.lower() for word in words)
            features[f'{category}_count'] = sum(combined_text.lower().count(word) for word in words)
        
        # Financial features
        features['contract_value'] = opportunity['value'] or 0
        features['value_category'] = self._categorize_contract_value(features['contract_value'])
        
        # Timeline features
        features['days_to_deadline'] = self._calculate_days_to_deadline(opportunity['deadline'])
        features['is_urgent'] = features['days_to_deadline'] < 7 if features['days_to_deadline'] else False
        
        # Agency features
        features['agency_category'] = self._categorize_agency(opportunity['agency'])
        features['is_preferred_agency'] = self._is_preferred_agency(opportunity['agency'])
        
        # NAICS features
        features['naics_match_score'] = self._calculate_naics_match_score(opportunity['naics_codes'])
        features['has_matching_naics'] = features['naics_match_score'] > 0.5
        
        # Set-aside features
        features['is_small_business'] = self._is_small_business_opportunity(opportunity['set_aside'])
        features['set_aside_category'] = self._categorize_set_aside(opportunity['set_aside'])
        
        return features
    
    def _calculate_value_alignment(self, opportunity: Dict, features: Dict) -> float:
        """Calculate value alignment score using advanced feature analysis"""
        score = 50.0  # Base score
        
        # NAICS alignment (25 points)
        naics_score = features.get('naics_match_score', 0.3) * 25
        score += naics_score
        
        # Keyword matching using TF-IDF if available (20 points)
        if SKLEARN_AVAILABLE:
            text_score = self._calculate_text_similarity(opportunity['title'], opportunity['description'])
            score += text_score * 20
        else:
            # Fallback to simple keyword matching
            capability_matches = sum(1 for cap in self.company_profile.capabilities 
                                   if cap.lower() in opportunity['description'].lower())
            score += (capability_matches / len(self.company_profile.capabilities)) * 20
        
        # Set-aside bonus (15 points)
        if features.get('is_small_business') and self.company_profile.small_business:
            score += 15
        
        # Agency preference (10 points)
        if features.get('is_preferred_agency'):
            score += 10
        
        return max(0, min(100, score))
    
    def _calculate_competitive_analysis(self, opportunity: Dict, features: Dict) -> float:
        """Calculate competitive landscape score"""
        score = 60.0  # Base competitive score
        
        # Contract size impact on competition
        value_category = features.get('value_category', 'medium')
        competition_adjustments = {
            'micro': 15,    # < $50K - low competition
            'small': 10,    # $50K-$250K - moderate competition  
            'medium': 0,    # $250K-$1M - normal competition
            'large': -10,   # $1M-$10M - high competition
            'mega': -20     # > $10M - very high competition
        }
        score += competition_adjustments.get(value_category, 0)
        
        # Set-aside advantages
        if features.get('is_small_business'):
            score += 15  # Reduced competition pool
            
        # Specialized requirements reduce competition
        specialized_keywords = ['clearance', 'specialized', 'custom', 'proprietary']
        if any(keyword in opportunity['description'].lower() for keyword in specialized_keywords):
            score += 10
            
        # Timeline pressure may reduce competition
        if features.get('is_urgent'):
            score += 8  # Rush jobs often have fewer bidders
            
        # Geographic considerations
        if opportunity.get('location') and 'remote' in opportunity['location'].lower():
            score += 5  # Remote work reduces geographic competition
            
        return max(0, min(100, score))
    
    def _calculate_agency_relationship(self, opportunity: Dict, features: Dict) -> float:
        """Calculate agency relationship and history score"""
        score = 40.0  # Base score
        
        # Preferred agency bonus
        if features.get('is_preferred_agency'):
            score += 30
            
        # Agency category scoring
        agency_scores = {
            'defense': 25,      # DoD - high value, good for IT
            'homeland': 20,     # DHS - cybersecurity focus
            'civilian': 15,     # Other civilian agencies
            'independent': 10,  # Independent agencies
            'unknown': 5        # Unknown agencies
        }
        agency_category = features.get('agency_category', 'unknown')
        score += agency_scores.get(agency_category, 5)
        
        # Historical performance simulation (would use real data)
        historical_multiplier = self.company_profile.past_performance_score
        score *= historical_multiplier
        
        return max(0, min(100, score))
    
    def _calculate_technical_match(self, opportunity: Dict, features: Dict) -> float:
        """Calculate technical capability match score"""
        score = 50.0  # Base score
        
        # Capability keyword matching
        capability_score = 0
        for capability in self.company_profile.capabilities:
            if capability.lower() in opportunity['description'].lower():
                capability_score += 5
        score += min(25, capability_score)  # Cap at 25 points
        
        # Security clearance requirements
        if 'clearance' in opportunity['description'].lower():
            if self.company_profile.security_clearance:
                score += 15  # We have clearance - advantage
            else:
                score -= 25  # We don't have clearance - major disadvantage
                
        # Technical complexity assessment
        complex_keywords = ['integration', 'migration', 'architecture', 'enterprise']
        complexity_score = sum(1 for keyword in complex_keywords 
                             if keyword in opportunity['description'].lower())
        if complexity_score >= 2:
            score += 10  # We handle complex projects well
            
        # Team size vs project scope
        if features.get('contract_value', 0) > 1000000:  # Large projects
            if self.company_profile.team_size >= 20:
                score += 10  # Adequate team size
            else:
                score -= 10  # May need to grow team
                
        return max(0, min(100, score))
    
    def _calculate_financial_viability(self, opportunity: Dict, features: Dict) -> float:
        """Calculate financial viability and ROI potential"""
        score = 70.0  # Base score
        
        contract_value = features.get('contract_value', 0)
        max_capacity = self.company_profile.max_contract_value
        
        # Contract size vs company capacity
        if contract_value > max_capacity:
            score -= 40  # Too large - major risk
        elif contract_value > max_capacity * 0.8:
            score -= 15  # Stretch but manageable
        elif contract_value < max_capacity * 0.05:
            score -= 10  # May be too small for overhead
        else:
            score += 10   # Good size for company
            
        # ROI potential based on contract type and value
        value_category = features.get('value_category', 'medium')
        roi_multipliers = {
            'micro': 0.8,   # Lower margins on small contracts
            'small': 1.0,   # Standard margins
            'medium': 1.1,  # Good margins
            'large': 1.2,   # Better margins
            'mega': 0.9     # Complex but potentially lower margins
        }
        score *= roi_multipliers.get(value_category, 1.0)
        
        # Payment terms assessment (simplified)
        if 'gsa' in opportunity.get('agency', '').lower():
            score += 5  # GSA typically has good payment terms
            
        return max(0, min(100, score))
    
    def _calculate_time_constraints(self, opportunity: Dict, features: Dict) -> float:
        """Calculate timeline feasibility score"""
        days_left = features.get('days_to_deadline', 30)
        
        if days_left <= 0:
            return 0  # Expired
        elif days_left <= 3:
            score = 15  # Very tight - high risk
        elif days_left <= 7:
            score = 35  # Tight but possible
        elif days_left <= 14:
            score = 65  # Reasonable timeline
        elif days_left <= 30:
            score = 85  # Good timeline
        else:
            score = 90  # Generous timeline
            
        # Adjust for proposal complexity
        contract_value = features.get('contract_value', 0)
        if contract_value > 5000000:  # Large contracts need more time
            score *= 0.8
        elif contract_value > 1000000:  # Medium contracts
            score *= 0.9
            
        # Security clearance requirements add complexity
        if 'clearance' in opportunity['description'].lower():
            score *= 0.85
            
        return max(0, min(100, score))
    
    def _calculate_risk_assessment(self, opportunity: Dict, features: Dict) -> float:
        """Calculate overall risk score (higher score = lower risk)"""
        score = 80.0  # Base low-risk assumption
        
        # New agency risk
        if not features.get('is_preferred_agency'):
            score -= 10
            
        # Large contract risk
        if features.get('contract_value', 0) > self.company_profile.max_contract_value * 0.7:
            score -= 15
            
        # Timeline risk
        if features.get('is_urgent'):
            score -= 12
            
        # Technical risk
        if not features.get('has_security') and 'security' in opportunity['description'].lower():
            score -= 15  # Security work without security background
            
        # Competition risk
        if not features.get('is_small_business') and features.get('contract_value', 0) > 1000000:
            score -= 12  # Open competition on large contracts
            
        # Complexity risk
        if features.get('word_count', 0) > 2000:  # Very detailed RFP
            score -= 8
            
        return max(0, min(100, score))
    
    def _calculate_weighted_score(self, factor_scores: Dict) -> float:
        """Calculate weighted overall score using configured weights"""
        total_score = 0
        total_weight = 0
        
        weight_map = {
            'value_alignment': self.weights.value_alignment,
            'competitive_analysis': self.weights.competitive_analysis,
            'agency_relationship': self.weights.agency_relationship,
            'technical_match': self.weights.technical_match,
            'financial_viability': self.weights.financial_viability,
            'time_constraints': self.weights.time_constraints,
            'risk_assessment': self.weights.risk_assessment
        }
        
        for factor, score in factor_scores.items():
            weight = weight_map.get(factor, 0)
            total_score += score * weight
            total_weight += weight
            
        return total_score / total_weight if total_weight > 0 else 50
    
    def _generate_recommendation(self, overall_score: float, factor_scores: Dict) -> Dict:
        """Generate recommendation based on score and risk factors"""
        # Base recommendation
        if overall_score >= 85:
            action, priority = 'pursue', 'high'
            reason = 'Excellent opportunity with strong alignment'
        elif overall_score >= 70:
            action, priority = 'pursue', 'medium'
            reason = 'Good opportunity with solid potential'
        elif overall_score >= 55:
            action, priority = 'analyze', 'medium'
            reason = 'Mixed signals - detailed analysis recommended'
        elif overall_score >= 40:
            action, priority = 'analyze', 'low'
            reason = 'Significant concerns but may have potential'
        else:
            action, priority = 'pass', 'low'
            reason = 'Poor fit or high risk'
            
        # Risk-based adjustments
        if factor_scores.get('risk_assessment', 50) < 30:
            if action == 'pursue':
                action = 'analyze'
                reason += ' - high risk factors detected'
                
        # Timeline-based adjustments
        if factor_scores.get('time_constraints', 50) < 25:
            if action == 'pursue':
                priority = 'low'
                reason += ' - timeline concerns'
                
        return {'action': action, 'priority': priority, 'reason': reason}
    
    def _calculate_confidence(self, factor_scores: Dict, features: Dict) -> float:
        """Calculate confidence in the scoring result"""
        base_confidence = 0.7
        
        # Data quality affects confidence
        text_length = features.get('text_length', 0)
        if text_length > 1000:
            base_confidence += 0.1  # More detailed description
        elif text_length < 200:
            base_confidence -= 0.1  # Limited information
            
        # Consistency of factor scores affects confidence
        scores = list(factor_scores.values())
        score_std = np.std(scores) if len(scores) > 1 else 0
        if score_std < 15:  # Consistent scores
            base_confidence += 0.1
        elif score_std > 30:  # Inconsistent scores
            base_confidence -= 0.1
            
        # Missing critical information reduces confidence
        if not features.get('contract_value'):
            base_confidence -= 0.05
        if not features.get('days_to_deadline'):
            base_confidence -= 0.05
            
        return max(0.3, min(1.0, base_confidence))
    
    def _calculate_win_probability(self, overall_score: float, factor_scores: Dict) -> float:
        """Calculate estimated win probability"""
        # Base probability from overall score
        base_prob = max(10, min(85, (overall_score - 20) * 1.1))
        
        # Adjust based on key factors
        adjustments = 0
        
        # Agency relationship is critical
        agency_score = factor_scores.get('agency_relationship', 50)
        if agency_score > 70:
            adjustments += 5
        elif agency_score < 30:
            adjustments -= 10
            
        # Technical match is important
        tech_score = factor_scores.get('technical_match', 50)
        if tech_score > 80:
            adjustments += 3
        elif tech_score < 40:
            adjustments -= 8
            
        # Competition level affects win rate
        comp_score = factor_scores.get('competitive_analysis', 50)
        if comp_score > 75:
            adjustments += 5
        elif comp_score < 40:
            adjustments -= 10
            
        # Risk factors
        risk_score = factor_scores.get('risk_assessment', 50)
        if risk_score < 40:
            adjustments -= 5
            
        final_prob = base_prob + adjustments
        return max(5, min(90, final_prob))
    
    def _generate_detailed_analysis(self, opportunity: Dict, factor_scores: Dict, overall_score: float) -> Dict:
        """Generate comprehensive analysis with actionable insights"""
        strengths = []
        concerns = []
        recommendations = []
        
        # Analyze each factor
        for factor, score in factor_scores.items():
            if score > 75:
                strengths.append(self._get_strength_message(factor, score))
            elif score < 40:
                concerns.append(self._get_concern_message(factor, score))
                
        # Generate specific recommendations
        if factor_scores.get('time_constraints', 50) < 40:
            recommendations.append('Consider early no-bid decision if timeline is unworkable')
            recommendations.append('Evaluate team availability and proposal capacity')
            
        if factor_scores.get('technical_match', 50) < 50:
            recommendations.append('Consider teaming arrangements for missing capabilities')
            recommendations.append('Evaluate subcontracting options')
            
        if factor_scores.get('competitive_analysis', 50) < 45:
            recommendations.append('Develop strong differentiators and value propositions')
            recommendations.append('Consider pricing strategy carefully')
            
        # Generate reasoning
        top_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        reasoning = f"Overall score of {overall_score:.1f} driven primarily by "
        reasoning += ", ".join([f"{factor.replace('_', ' ')} ({score:.0f})" for factor, score in top_factors])
        
        if overall_score > 70:
            reasoning += ". Strong opportunity alignment with company capabilities and market position."
        elif overall_score > 50:
            reasoning += ". Moderate opportunity with mixed success factors requiring careful evaluation."
        else:
            reasoning += ". Challenging opportunity with significant barriers to success."
            
        return {
            'strengths': strengths[:5],  # Limit to top 5
            'concerns': concerns[:5],    # Limit to top 5  
            'recommendations': recommendations[:5],  # Limit to top 5
            'reasoning': reasoning
        }
    
    # Helper methods
    def _generate_cache_key(self, opportunity_data: Dict) -> str:
        """Generate cache key for opportunity"""
        key_data = {
            'id': opportunity_data.get('id', ''),
            'title': opportunity_data.get('title', ''),
            'agency': opportunity_data.get('agency', ''),
            'value': opportunity_data.get('award_amount', 0)
        }
        return hashlib.md5(str(key_data).encode()).hexdigest()[:16]
    
    def _parse_contract_value(self, value) -> float:
        """Parse contract value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = re.sub(r'[,$]', '', value.lower())
            try:
                if 'm' in cleaned:
                    return float(cleaned.replace('m', '')) * 1_000_000
                elif 'k' in cleaned:
                    return float(cleaned.replace('k', '')) * 1_000
                else:
                    return float(cleaned)
            except ValueError:
                return 0
        return 0
    
    def _categorize_contract_value(self, value: float) -> str:
        """Categorize contract value into size ranges"""
        if value < 50_000:
            return 'micro'
        elif value < 250_000:
            return 'small'
        elif value < 1_000_000:
            return 'medium'
        elif value < 10_000_000:
            return 'large'
        else:
            return 'mega'
    
    def _calculate_days_to_deadline(self, deadline) -> Optional[int]:
        """Calculate days until deadline"""
        if not deadline:
            return None
        try:
            if isinstance(deadline, str):
                deadline_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            else:
                deadline_date = deadline
            return max(0, (deadline_date - datetime.now()).days)
        except:
            return None
    
    def _categorize_agency(self, agency: str) -> str:
        """Categorize agency by type"""
        if not agency:
            return 'unknown'
        agency_lower = agency.lower()
        if any(term in agency_lower for term in ['defense', 'dod', 'army', 'navy', 'air force']):
            return 'defense'
        elif any(term in agency_lower for term in ['homeland', 'dhs']):
            return 'homeland'
        elif any(term in agency_lower for term in ['gsa', 'treasury', 'commerce', 'transportation']):
            return 'civilian'
        else:
            return 'independent'
    
    def _is_preferred_agency(self, agency: str) -> bool:
        """Check if agency is in preferred list"""
        if not agency:
            return False
        return any(pref.lower() in agency.lower() for pref in self.company_profile.preferred_agencies)
    
    def _calculate_naics_match_score(self, naics_codes: List[str]) -> float:
        """Calculate NAICS code matching score"""
        if not naics_codes:
            return 0.3  # Default moderate score
        matches = 0
        for naics in naics_codes:
            for primary in self.company_profile.primary_naics:
                if naics.startswith(primary[:4]):  # Match first 4 digits
                    matches += 1
                    break
        return min(1.0, matches / len(naics_codes))
    
    def _is_small_business_opportunity(self, set_aside: str) -> bool:
        """Check if opportunity is set aside for small business"""
        if not set_aside:
            return False
        return any(term in set_aside.upper() for term in ['SB', 'SMALL', 'HUBZONE', '8A', 'SDVOSB'])
    
    def _categorize_set_aside(self, set_aside: str) -> str:
        """Categorize set-aside type"""
        if not set_aside:
            return 'none'
        set_aside_upper = set_aside.upper()
        if 'SB' in set_aside_upper or 'SMALL' in set_aside_upper:
            return 'small_business'
        elif '8A' in set_aside_upper:
            return '8a'
        elif 'HUBZONE' in set_aside_upper:
            return 'hubzone'
        elif 'SDVOSB' in set_aside_upper:
            return 'sdvosb'
        else:
            return 'other'
    
    def _calculate_text_similarity(self, title: str, description: str) -> float:
        """Calculate text similarity using TF-IDF (if available)"""
        if not SKLEARN_AVAILABLE:
            return 0.5  # Fallback score
        
        try:
            # Combine company capabilities for comparison
            company_text = " ".join(self.company_profile.capabilities)
            opportunity_text = f"{title} {description}"
            
            # Create TF-IDF vectors
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([company_text, opportunity_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except:
            return 0.5  # Fallback on error
    
    def _get_strength_message(self, factor: str, score: float) -> str:
        """Get human-readable strength message for factor"""
        messages = {
            'value_alignment': 'Excellent alignment with company capabilities and NAICS codes',
            'competitive_analysis': 'Favorable competitive landscape with good positioning',
            'agency_relationship': 'Strong relationship and history with this agency',
            'technical_match': 'Perfect technical fit for company expertise',
            'financial_viability': 'Excellent financial opportunity with strong ROI potential',
            'time_constraints': 'Adequate timeline for quality proposal preparation',
            'risk_assessment': 'Low risk opportunity with minimal barriers'
        }
        return messages.get(factor, f'Strong {factor.replace("_", " ")} factor')
    
    def _get_concern_message(self, factor: str, score: float) -> str:
        """Get human-readable concern message for factor"""
        messages = {
            'value_alignment': 'Poor fit with current capabilities - may require teaming',
            'competitive_analysis': 'High competition expected - need strong differentiators',
            'agency_relationship': 'Limited history with this agency - relationship risk',
            'technical_match': 'Technical requirements may be challenging to meet',
            'financial_viability': 'Financial terms may not be favorable',
            'time_constraints': 'Very tight timeline for proposal preparation',
            'risk_assessment': 'High risk factors identified - careful evaluation needed'
        }
        return messages.get(factor, f'Concerns with {factor.replace("_", " ")} factor')
    
    def _generate_fallback_score(self, opportunity_data: Dict, error_msg: str) -> Dict:
        """Generate fallback score when main algorithm fails"""
        return {
            'opportunity_id': opportunity_data.get('id', 'unknown'),
            'overall_score': 55.0,
            'recommendation': 'analyze',
            'recommendation_priority': 'medium',
            'confidence': 40,
            'win_probability': 50,
            'factor_scores': {
                'value_alignment': 55,
                'competitive_analysis': 55,
                'agency_relationship': 50,
                'technical_match': 55,
                'financial_viability': 60,
                'time_constraints': 55,
                'risk_assessment': 60
            },
            'analysis': {
                'strengths': ['Opportunity identified for evaluation'],
                'concerns': ['Limited data available for comprehensive analysis'],
                'recommendations': ['Gather additional information before making bid decision'],
                'reasoning': f'Fallback scoring due to processing error: {error_msg}'
            },
            'metadata': {
                'scorer_version': self.version,
                'processing_time_ms': 5,
                'timestamp': datetime.now().isoformat(),
                'ml_features_used': SKLEARN_AVAILABLE,
                'fallback': True,
                'error': error_msg
            }
        }

# Global scorer instance with default configuration
opportunity_scorer = OpportunityScorer()

# Export functions for API use
def score_single_opportunity(opportunity_data: Dict) -> Dict:
    """Convenience function to score a single opportunity"""
    return opportunity_scorer.score_opportunity(opportunity_data)

def batch_score_opportunities(opportunities: List[Dict]) -> List[Dict]:
    """Score multiple opportunities efficiently"""
    results = []
    for opp in opportunities:
        try:
            result = opportunity_scorer.score_opportunity(opp)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to score opportunity {opp.get('id', 'unknown')}: {e}")
            results.append(opportunity_scorer._generate_fallback_score(opp, str(e)))
    return results