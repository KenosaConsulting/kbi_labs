#!/usr/bin/env python3
"""
PE Investment Scoring Algorithm - Updated for DSBS Data
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class ScoringWeights:
    """Adjusted weights for available data"""
    # PE Investment Score Weights
    industry_growth: float = 0.30      # Increased
    market_size: float = 0.25          # Increased
    digital_presence: float = 0.20     # Adjusted
    certification_value: float = 0.15
    scalability: float = 0.10
    
    # Business Health Weights (adjusted for no email)
    contact_completeness: float = 0.25
    digital_footprint: float = 0.30
    business_description: float = 0.15  # Reduced due to data quality
    professional_structure: float = 0.20
    location_factors: float = 0.10

class PEInvestmentScorer:
    """Scoring engine adjusted for available DSBS data"""
    
    # High-growth NAICS sectors (2-digit prefixes)
    HIGH_GROWTH_SECTORS = {
        '54': ('Professional/Technical Services', 0.9),
        '51': ('Information', 0.95),
        '62': ('Healthcare', 0.85),
        '52': ('Finance/Insurance', 0.85),
        '33': ('Manufacturing', 0.8),
        '56': ('Administrative Services', 0.75),
        '48': ('Transportation', 0.75),
        '49': ('Warehousing', 0.8),
    }
    
    # PE hub cities
    PE_HUB_CITIES = {
        'new york': 1.0, 'san francisco': 0.95, 'boston': 0.9,
        'chicago': 0.9, 'los angeles': 0.9, 'seattle': 0.85,
        'austin': 0.85, 'dallas': 0.85, 'atlanta': 0.8,
        'denver': 0.8, 'miami': 0.8, 'washington': 0.85,
        'houston': 0.8, 'phoenix': 0.75, 'detroit': 0.7,
    }
    
    # Business-friendly states
    BUSINESS_STATES = {
        'Delaware': 0.95, 'Texas': 0.9, 'Florida': 0.85,
        'Nevada': 0.9, 'Wyoming': 0.85, 'Tennessee': 0.8,
        'Colorado': 0.8, 'North Carolina': 0.8, 'Utah': 0.8,
        'California': 0.75, 'New York': 0.75, 'Illinois': 0.7,
    }
    
    # SBA certification values
    CERT_VALUES = {
        '8(A)': 0.9, 'HUBZONE': 0.85, 'WOSB': 0.8,
        'EDWOSB': 0.85, 'VOSB': 0.8, 'SDVOSB': 0.85,
    }
    
    def __init__(self):
        self.weights = ScoringWeights()
    
    def _score_industry(self, naics_code: Optional[float]) -> float:
        """Score based on industry growth potential"""
        if not naics_code or pd.isna(naics_code):
            return 0.3
        
        try:
            naics_str = str(int(naics_code))
            prefix_2 = naics_str[:2]
            
            if prefix_2 in self.HIGH_GROWTH_SECTORS:
                _, score = self.HIGH_GROWTH_SECTORS[prefix_2]
                return score
            
            # Default scores for other industries
            industry_defaults = {
                '23': 0.7,  # Construction
                '44': 0.6,  # Retail
                '45': 0.6,  # Retail
                '72': 0.6,  # Food/Accommodation
                '81': 0.5,  # Other Services
                '61': 0.7,  # Education
                '71': 0.6,  # Arts/Entertainment
            }
            
            return industry_defaults.get(prefix_2, 0.5)
            
        except:
            return 0.3
    
    def _score_digital_presence(self, website: Optional[str]) -> float:
        """Score digital maturity based on website only (no email in data)"""
        score = 0.0
        
        if website and not pd.isna(website):
            website_str = str(website).lower().strip()
            
            if website_str and website_str not in ['none', 'n/a', '', 'na']:
                score += 0.5  # Has website
                
                if website_str.startswith('https://'):
                    score += 0.3  # Secure
                elif website_str.startswith('http://'):
                    score += 0.1  # Has protocol
                
                # Professional domain
                if not any(x in website_str for x in ['wix.com', 'weebly.com', 'facebook.com', 'free']):
                    score += 0.2
        
        return min(score, 1.0)
    
    def _score_certifications(self, certs: Optional[str]) -> Tuple[float, int]:
        """Score SBA certifications"""
        if not certs or pd.isna(certs) or str(certs).strip() == '':
            return 0.3, 0
        
        cert_str = str(certs).upper()
        total_score = 0.0
        cert_count = 0
        
        for cert, value in self.CERT_VALUES.items():
            if cert in cert_str:
                total_score += value
                cert_count += 1
        
        if cert_count > 0:
            # Average cert value plus bonus for multiple
            avg_score = total_score / cert_count
            multi_bonus = min(cert_count * 0.1, 0.3)
            final_score = min(avg_score + multi_bonus, 1.0)
        else:
            final_score = 0.3
        
        return final_score, cert_count
    
    def _score_location(self, city: Optional[str], state: Optional[str]) -> float:
        """Score geographic factors"""
        score = 0.5  # Base score
        
        # City score
        if city and not pd.isna(city):
            city_lower = str(city).lower().strip()
            
            for hub, hub_score in self.PE_HUB_CITIES.items():
                if hub in city_lower:
                    score = max(score, hub_score)
                    break
        
        # State score
        if state and not pd.isna(state):
            state_str = str(state).strip()
            
            # Handle full state names or abbreviations
            state_score = self.BUSINESS_STATES.get(state_str, 0.5)
            score = (score + state_score) / 2
        
        return score
    
    def _score_business_structure(self, structure: Optional[str]) -> float:
        """Score legal structure sophistication"""
        if not structure or pd.isna(structure):
            return 0.5
        
        structure_str = str(structure).lower()
        
        if 'corporation' in structure_str:
            return 0.9
        elif 'llc' in structure_str or 'limited liability' in structure_str:
            return 0.8
        elif 'partnership' in structure_str:
            return 0.7  # Increased for DSBS data
        elif 'sole proprietor' in structure_str:
            return 0.4
        else:
            return 0.5
    
    def calculate_pe_score(self, company_data: Dict) -> Tuple[float, Dict[str, float]]:
        """Calculate PE investment score (0-100)"""
        components = {}
        
        # 1. Industry potential
        components['industry'] = self._score_industry(
            company_data.get('primary_naics_code')
        )
        
        # 2. Digital presence (website only)
        components['digital'] = self._score_digital_presence(
            company_data.get('website')
        )
        
        # 3. Certifications
        cert_score, cert_count = self._score_certifications(
            company_data.get('active_sba_certifications')
        )
        components['certifications'] = cert_score
        
        # 4. Location
        components['location'] = self._score_location(
            company_data.get('city'),
            company_data.get('state')
        )
        
        # 5. Business structure/scalability
        components['scalability'] = self._score_business_structure(
            company_data.get('legal_structure')
        )
        
        # Calculate weighted final score
        final_score = (
            components['industry'] * self.weights.industry_growth +
            components['location'] * self.weights.market_size +
            components['digital'] * self.weights.digital_presence +
            components['certifications'] * self.weights.certification_value +
            components['scalability'] * self.weights.scalability
        )
        
        # Convert to 0-100 scale
        pe_score = round(final_score * 100, 1)
        
        return pe_score, components
    
    def calculate_health_grade(self, company_data: Dict, 
                             pe_components: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """Calculate business health grade - adjusted for available data"""
        factors = {}
        
        # 1. Contact completeness (no email, so just phone/address)
        contact_fields = ['phone_number', 'address_line_1', 'city', 'state', 'zipcode']
        contact_complete = sum(1 for field in contact_fields 
                             if company_data.get(field) and 
                             not pd.isna(company_data.get(field)))
        factors['contact'] = contact_complete / len(contact_fields)
        
        # 2. Digital footprint (website only)
        factors['digital'] = pe_components.get('digital', 0.5)
        
        # 3. Business description quality (many have minimal narratives)
        capabilities = company_data.get('capabilities_narrative', '')
        if capabilities and not pd.isna(capabilities):
            cap_len = len(str(capabilities))
            # More lenient scoring for short descriptions
            if cap_len < 10:
                factors['description'] = 0.1
            elif cap_len < 50:
                factors['description'] = 0.3
            elif cap_len < 200:
                factors['description'] = 0.6
            else:
                factors['description'] = min(cap_len / 300, 1.0)
        else:
            factors['description'] = 0.0
        
        # 4. Professional structure (reuse PE component)
        factors['structure'] = pe_components.get('scalability', 0.5)
        
        # 5. Location factors (reuse PE component)
        factors['location'] = pe_components.get('location', 0.5)
        
        # Calculate weighted health score
        health_score = (
            factors['contact'] * self.weights.contact_completeness +
            factors['digital'] * self.weights.digital_footprint +
            factors['description'] * self.weights.business_description +
            factors['structure'] * self.weights.professional_structure +
            factors['location'] * self.weights.location_factors
        )
        
        # More lenient grading for DSBS data
        if health_score >= 0.8:
            grade = 'A'
        elif health_score >= 0.65:
            grade = 'B'
        elif health_score >= 0.5:
            grade = 'C'
        elif health_score >= 0.35:
            grade = 'D'
        else:
            grade = 'F'
        
        return grade, factors
    
    def score_company(self, company_data: Dict) -> Dict:
        """Complete scoring of a company"""
        # Calculate PE score and components
        pe_score, pe_components = self.calculate_pe_score(company_data)
        
        # Calculate health grade and factors
        health_grade, health_factors = self.calculate_health_grade(
            company_data, pe_components
        )
        
        return {
            'pe_investment_score': pe_score,
            'business_health_grade': health_grade,
            'scoring_details': {
                'pe_components': pe_components,
                'health_factors': health_factors,
                'scoring_version': '2.0',
                'scored_at': pd.Timestamp.now().isoformat()
            }
        }
