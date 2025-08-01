#!/usr/bin/env python3
"""Analyze scoring details to understand grade distribution"""

import sys
sys.path.insert(0, '.')

import pandas as pd
from src.database.connection import SessionLocal
from src.enrichment.models import EnrichedCompany
from src.enrichment.scoring import PEInvestmentScorer
import json

def main():
    db = SessionLocal()
    scorer = PEInvestmentScorer()
    
    # Load original data
    original_df = pd.read_csv('data/dsbs_raw/sample_50.csv', dtype={'Zipcode': str, 'Phone number': str})
    
    # Get a few companies to analyze in detail
    companies = db.query(EnrichedCompany).order_by(
        EnrichedCompany.pe_investment_score.desc()
    ).limit(3).all()
    
    print("=== DETAILED SCORING ANALYSIS ===\n")
    
    for company in companies:
        # Get original data
        orig_row = original_df[original_df['UEI (Unique Entity Identifier)'] == company.uei]
        if len(orig_row) > 0:
            orig = orig_row.iloc[0].to_dict()
            
            print(f"\n{company.organization_name}")
            print("=" * 60)
            
            # Prepare full data
            company_data = {
                'organization_name': company.organization_name,
                'primary_naics_code': float(company.primary_naics) if company.primary_naics else None,
                'website': company.website or orig.get('Website'),
                'city': company.city or orig.get('City'),
                'state': company.state or orig.get('State'),
                'zipcode': company.zipcode or orig.get('Zipcode'),
                'phone_number': company.phone_number or orig.get('Phone number'),
                'legal_structure': orig.get('Legal structure'),
                'email': orig.get('Email'),
                'address_line_1': orig.get('Address line 1'),
                'address_line_2': orig.get('Address line 2'),
                'active_sba_certifications': orig.get('Active SBA certifications'),
                'capabilities_narrative': orig.get('Capabilities narrative'),
            }
            
            # Get detailed scores
            results = scorer.score_company(company_data)
            
            print(f"PE Score: {results['pe_investment_score']}/100")
            print(f"Health Grade: {results['business_health_grade']}")
            
            print("\nData Available:")
            print(f"  Email: {'✓' if company_data['email'] else '✗'} {company_data.get('email', '')[:30] if company_data.get('email') else ''}")
            print(f"  Website: {'✓' if company_data['website'] else '✗'} {company_data.get('website', '')}")
            print(f"  Phone: {'✓' if company_data['phone_number'] else '✗'}")
            print(f"  Address: {'✓' if company_data['address_line_1'] else '✗'}")
            print(f"  Legal Structure: {company_data.get('legal_structure', 'N/A')}")
            print(f"  Capabilities: {len(str(company_data.get('capabilities_narrative', '')))} chars")
            
            print("\nPE Score Components:")
            for comp, score in results['scoring_details']['pe_components'].items():
                print(f"  {comp}: {score:.3f}")
            
            print("\nHealth Grade Factors:")
            for factor, score in results['scoring_details']['health_factors'].items():
                print(f"  {factor}: {score:.3f}")
    
    db.close()

if __name__ == "__main__":
    main()
