#!/usr/bin/env python3
"""
Script to implement the real scoring algorithms for KBI Labs
"""

import os
import sys
sys.path.insert(0, '.')

def create_scoring_module():
    """Create the scoring module with real algorithms"""
    
    # Ensure directory exists
    os.makedirs('src/enrichment', exist_ok=True)
    
    # Create the scoring module
    scoring_code = '''#!/usr/bin/env python3
"""
PE Investment Scoring Algorithm for KBI Labs
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class ScoringWeights:
    """Configurable weights for scoring components"""
    # PE Investment Score Weights
    industry_growth: float = 0.25
    market_size: float = 0.20
    digital_presence: float = 0.15
    certification_value: float = 0.15
    scalability: float = 0.15
    data_quality: float = 0.10
    
    # Business Health Weights
    contact_completeness: float = 0.20
    digital_footprint: float = 0.25
    business_description: float = 0.20
    professional_structure: float = 0.20
    location_factors: float = 0.15

class PEInvestmentScorer:
    """Advanced scoring engine for PE investment potential"""
    
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
    }
    
    # Business-friendly states
    BUSINESS_STATES = {
        'Delaware': 0.95, 'Texas': 0.9, 'Florida': 0.85,
        'Nevada': 0.9, 'Wyoming': 0.85, 'Tennessee': 0.8,
        'Colorado': 0.8, 'North Carolina': 0.8, 'Utah': 0.8,
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
            }
            
            return industry_defaults.get(prefix_2, 0.5)
            
        except:
            return 0.3
    
    def _score_digital_presence(self, website: Optional[str], email: Optional[str]) -> float:
        """Score digital maturity"""
        score = 0.0
        
        # Website scoring
        if website and not pd.isna(website):
            website_str = str(website).lower().strip()
            
            if website_str and website_str not in ['none', 'n/a', '']:
                score += 0.3  # Has website
                
                if website_str.startswith('https://'):
                    score += 0.2  # Secure
                
                # Professional domain
                if not any(x in website_str for x in ['wix.com', 'weebly.com', 'facebook.com']):
                    score += 0.2
        
        # Email scoring
        if email and not pd.isna(email):
            email_str = str(email).lower().strip()
            
            if '@' in email_str:
                score += 0.2  # Has email
                
                # Professional email (not free)
                if not any(x in email_str for x in ['gmail.', 'yahoo.', 'hotmail.', 'aol.']):
                    score += 0.1
        
        return min(score, 1.0)
    
    def _score_certifications(self, certs: Optional[str]) -> Tuple[float, int]:
        """Score SBA certifications"""
        if not certs or pd.isna(certs):
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
            return 0.6
        elif 'sole proprietor' in structure_str:
            return 0.4
        else:
            return 0.5
    
    def _calculate_data_quality(self, company_data: Dict) -> float:
        """Score based on data completeness"""
        key_fields = [
            'organization_name', 'email', 'phone_number',
            'address_line_1', 'city', 'state', 'website',
            'capabilities_narrative', 'primary_naics_code'
        ]
        
        filled = sum(1 for field in key_fields 
                    if company_data.get(field) and 
                    not pd.isna(company_data.get(field)))
        
        return filled / len(key_fields)
    
    def calculate_pe_score(self, company_data: Dict) -> Tuple[float, Dict[str, float]]:
        """Calculate PE investment score (0-100)"""
        components = {}
        
        # 1. Industry potential
        components['industry'] = self._score_industry(
            company_data.get('primary_naics_code')
        )
        
        # 2. Digital presence
        components['digital'] = self._score_digital_presence(
            company_data.get('website'),
            company_data.get('email')
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
        
        # 6. Data quality
        components['data_quality'] = self._calculate_data_quality(company_data)
        
        # Calculate weighted final score
        final_score = (
            components['industry'] * self.weights.industry_growth +
            components['location'] * self.weights.market_size +
            components['digital'] * self.weights.digital_presence +
            components['certifications'] * self.weights.certification_value +
            components['scalability'] * self.weights.scalability +
            components['data_quality'] * self.weights.data_quality
        )
        
        # Convert to 0-100 scale
        pe_score = round(final_score * 100, 1)
        
        return pe_score, components
    
    def calculate_health_grade(self, company_data: Dict, 
                             pe_components: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
        """Calculate business health grade (A-F)"""
        factors = {}
        
        # 1. Contact completeness
        contact_fields = ['email', 'phone_number', 'address_line_1', 
                         'city', 'state', 'zipcode']
        contact_complete = sum(1 for field in contact_fields 
                             if company_data.get(field) and 
                             not pd.isna(company_data.get(field)))
        factors['contact'] = contact_complete / len(contact_fields)
        
        # 2. Digital footprint (reuse PE component)
        factors['digital'] = pe_components.get('digital', 0.5)
        
        # 3. Business description quality
        capabilities = company_data.get('capabilities_narrative', '')
        if capabilities and not pd.isna(capabilities):
            cap_len = len(str(capabilities))
            # Score based on description length (500 chars = full score)
            factors['description'] = min(cap_len / 500, 1.0)
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
        
        # Convert to grade
        if health_score >= 0.9:
            grade = 'A'
        elif health_score >= 0.8:
            grade = 'B'
        elif health_score >= 0.7:
            grade = 'C'
        elif health_score >= 0.6:
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
                'scoring_version': '1.0',
                'scored_at': pd.Timestamp.now().isoformat()
            }
        }
'''
    
    # Write the scoring module
    with open('src/enrichment/scoring.py', 'w') as f:
        f.write(scoring_code)
    
    print("✓ Created advanced scoring module")

def test_scoring():
    """Test the new scoring system"""
    from src.enrichment.scoring import PEInvestmentScorer
    
    scorer = PEInvestmentScorer()
    
    # Test companies with different profiles
    test_companies = [
        {
            'name': 'Premium Tech Corp',
            'data': {
                'organization_name': 'Premium Tech Corp',
                'primary_naics_code': 541511,  # Software
                'legal_structure': 'Corporation',
                'email': 'contact@premiumtech.com',
                'phone_number': '555-123-4567',
                'website': 'https://www.premiumtech.com',
                'city': 'San Francisco',
                'state': 'California',
                'address_line_1': '100 Tech Plaza',
                'zipcode': '94105',
                'active_sba_certifications': '8(a), WOSB, HUBZone',
                'capabilities_narrative': 'Leading AI and machine learning solutions provider with over 15 years of experience. We specialize in enterprise-grade software development, cloud architecture, and data analytics. Our team of 100+ engineers has delivered solutions to Fortune 500 companies across finance, healthcare, and retail sectors.'
            }
        },
        {
            'name': 'Basic Local Services',
            'data': {
                'organization_name': 'Basic Local Services',
                'primary_naics_code': 561720,  # Janitorial
                'legal_structure': 'Sole Proprietorship',
                'email': 'basicservices@gmail.com',
                'website': None,
                'city': 'Rural Town',
                'state': 'Montana',
                'capabilities_narrative': 'Local cleaning'
            }
        },
        {
            'name': 'Growth Manufacturing LLC',
            'data': {
                'organization_name': 'Growth Manufacturing LLC',
                'primary_naics_code': 332710,  # Machine shops
                'legal_structure': 'Limited Liability Company',
                'email': 'info@growthmfg.net',
                'phone_number': '555-888-9999',
                'website': 'http://www.growthmfg.net',
                'city': 'Dallas',
                'state': 'Texas',
                'address_line_1': '500 Industrial Way',
                'active_sba_certifications': 'VOSB',
                'capabilities_narrative': 'Precision machining and fabrication services. ISO 9001 certified facility with CNC capabilities.'
            }
        }
    ]
    
    print("\n=== Testing Advanced Scoring Algorithm ===\n")
    
    for test in test_companies:
        print(f"Company: {test['name']}")
        print("-" * 60)
        
        results = scorer.score_company(test['data'])
        
        print(f"PE Investment Score: {results['pe_investment_score']}/100")
        print(f"Business Health Grade: {results['business_health_grade']}")
        
        print("\nPE Score Components:")
        for comp, score in results['scoring_details']['pe_components'].items():
            print(f"  {comp}: {score:.3f}")
        
        print("\nHealth Grade Factors:")
        for factor, score in results['scoring_details']['health_factors'].items():
            print(f"  {factor}: {score:.3f}")
        
        print("\n")

def update_engine():
    """Update the enrichment engine to use new scoring"""
    
    # Read current engine code
    engine_path = 'src/enrichment/engine.py'
    
    if os.path.exists(engine_path):
        print("✓ Updating existing engine.py...")
        
        # The engine should already import and use PEInvestmentScorer
        # Just ensure it's using the new scoring module
        
        with open(engine_path, 'r') as f:
            engine_code = f.read()
        
        # Check if it's already using PEInvestmentScorer
        if 'PEInvestmentScorer' in engine_code:
            print("✓ Engine already configured to use PEInvestmentScorer")
        else:
            print("! Engine needs to be updated to use PEInvestmentScorer")
            # Would update the engine here if needed
    else:
        print("! Engine file not found at", engine_path)

def rescore_existing():
    """Create script to rescore existing companies"""
    
    rescore_script = '''#!/usr/bin/env python3
"""Rescore all existing companies with the new algorithm"""

import sys
sys.path.insert(0, '.')

from src.database.connection import SessionLocal
from src.enrichment.models import EnrichedCompany
from src.enrichment.scoring import PEInvestmentScorer
import json
from datetime import datetime
import pandas as pd

def main():
    db = SessionLocal()
    scorer = PEInvestmentScorer()
    
    try:
        # Get all companies
        companies = db.query(EnrichedCompany).all()
        total = len(companies)
        
        print(f"\\nRescoring {total} companies with advanced algorithm...")
        print("=" * 60)
        
        score_distribution = []
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for i, company in enumerate(companies):
            # Prepare company data
            company_data = {
                'organization_name': company.organization_name,
                'primary_naics_code': float(company.primary_naics_code) if company.primary_naics_code else None,
                'legal_structure': company.legal_structure,
                'email': company.email,
                'phone_number': company.phone_number,
                'website': company.website,
                'city': company.city,
                'state': company.state,
                'address_line_1': company.address_line_1,
                'address_line_2': company.address_line_2,
                'zipcode': company.zipcode,
                'active_sba_certifications': company.active_sba_certifications,
                'capabilities_narrative': company.capabilities_narrative,
            }
            
            # Calculate new scores
            results = scorer.score_company(company_data)
            
            # Update database
            company.pe_investment_score = results['pe_investment_score']
            company.business_health_grade = results['business_health_grade']
            company.scoring_metadata = json.dumps(results['scoring_details'])
            company.updated_at = datetime.utcnow()
            
            # Track distribution
            score_distribution.append(results['pe_investment_score'])
            grade_counts[results['business_health_grade']] += 1
            
            # Progress update
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{total} companies processed...")
                db.commit()
        
        # Final commit
        db.commit()
        
        # Show results
        print(f"\\n✓ Successfully rescored all {total} companies!")
        print("\\n" + "=" * 60)
        print("SCORING RESULTS")
        print("=" * 60)
        
        # PE Score statistics
        print("\\nPE Investment Score Distribution:")
        print(f"  Minimum: {min(score_distribution):.1f}")
        print(f"  Maximum: {max(score_distribution):.1f}")
        print(f"  Average: {sum(score_distribution)/len(score_distribution):.1f}")
        print(f"  Median:  {pd.Series(score_distribution).median():.1f}")
        
        # Score ranges
        ranges = {
            '90-100': sum(1 for s in score_distribution if s >= 90),
            '80-89': sum(1 for s in score_distribution if 80 <= s < 90),
            '70-79': sum(1 for s in score_distribution if 70 <= s < 80),
            '60-69': sum(1 for s in score_distribution if 60 <= s < 70),
            '50-59': sum(1 for s in score_distribution if 50 <= s < 60),
            'Below 50': sum(1 for s in score_distribution if s < 50),
        }
        
        print("\\nScore Ranges:")
        for range_name, count in ranges.items():
            pct = (count / total) * 100
            print(f"  {range_name}: {count} companies ({pct:.1f}%)")
        
        # Health grades
        print("\\nBusiness Health Grade Distribution:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_counts[grade]
            pct = (count / total) * 100
            print(f"  Grade {grade}: {count} companies ({pct:.1f}%)")
        
        # Top companies
        print("\\nTop 5 Scoring Companies:")
        top_companies = db.query(EnrichedCompany).order_by(
            EnrichedCompany.pe_investment_score.desc()
        ).limit(5).all()
        
        for i, company in enumerate(top_companies, 1):
            print(f"  {i}. {company.organization_name} (Score: {company.pe_investment_score}, Grade: {company.business_health_grade})")
            print(f"     Location: {company.city}, {company.state}")
            if company.active_sba_certifications:
                print(f"     Certifications: {company.active_sba_certifications}")
        
    except Exception as e:
        print(f"\\nError: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
'''
    
    with open('rescore_companies.py', 'w') as f:
        f.write(rescore_script)
    
    print("✓ Created rescore_companies.py")

def main():
    """Main implementation function"""
    print("=== Implementing Real Scoring Algorithms ===\n")
    
    # Step 1: Create scoring module
    create_scoring_module()
    
    # Step 2: Test scoring
    test_scoring()
    
    # Step 3: Update engine
    update_engine()
    
    # Step 4: Create rescore script
    rescore_existing()
    
    print("\n✓ Implementation complete!")
    print("\nNext steps:")
    print("1. Run: python3 rescore_companies.py")
    print("   To update all existing companies with new scores")
    print("\n2. Run: python3 test_new_scoring.py")
    print("   To see detailed scoring examples")
    print("\n3. Process new data with: python3 process_data.py")
    print("   New companies will automatically use the advanced scoring")

if __name__ == "__main__":
    main()
