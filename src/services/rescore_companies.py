#!/usr/bin/env python3
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
        
        print(f"\nRescoring {total} companies with advanced algorithm...")
        print("=" * 60)
        
        score_distribution = []
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for i, company in enumerate(companies):
            # Prepare company data
            company_data = {
                'organization_name': company.organization_name,
                'primary_naics_code': float(company.primary_naics) if company.primary_naics_code else None,
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
        print(f"\n✓ Successfully rescored all {total} companies!")
        print("\n" + "=" * 60)
        print("SCORING RESULTS")
        print("=" * 60)
        
        # PE Score statistics
        print("\nPE Investment Score Distribution:")
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
        
        print("\nScore Ranges:")
        for range_name, count in ranges.items():
            pct = (count / total) * 100
            print(f"  {range_name}: {count} companies ({pct:.1f}%)")
        
        # Health grades
        print("\nBusiness Health Grade Distribution:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_counts[grade]
            pct = (count / total) * 100
            print(f"  Grade {grade}: {count} companies ({pct:.1f}%)")
        
        # Top companies
        print("\nTop 5 Scoring Companies:")
        top_companies = db.query(EnrichedCompany).order_by(
            EnrichedCompany.pe_investment_score.desc()
        ).limit(5).all()
        
        for i, company in enumerate(top_companies, 1):
            print(f"  {i}. {company.organization_name} (Score: {company.pe_investment_score}, Grade: {company.business_health_grade})")
            print(f"     Location: {company.city}, {company.state}")
            if company.active_sba_certifications:
                print(f"     Certifications: {company.active_sba_certifications}")
        
    except Exception as e:
        print(f"\nError: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
