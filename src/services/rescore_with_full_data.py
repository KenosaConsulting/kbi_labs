#!/usr/bin/env python3
"""Rescore companies using original DSBS data"""

import sys
sys.path.insert(0, '.')

import pandas as pd
from src.database.connection import SessionLocal
from src.enrichment.models import EnrichedCompany
from src.enrichment.scoring import PEInvestmentScorer
import json
from datetime import datetime

def main():
    db = SessionLocal()
    scorer = PEInvestmentScorer()
    
    try:
        # Try to load the original sample data
        sample_path = 'data/dsbs_raw/sample_50.csv'
        
        try:
            # Load original data with all fields
            original_df = pd.read_csv(sample_path, dtype={'Zipcode': str, 'Phone number': str})
            print(f"✓ Loaded original data with {len(original_df)} companies")
            print(f"  Columns: {', '.join(original_df.columns[:5])}...")
            
            # Create UEI lookup dictionary
            original_data = {}
            for _, row in original_df.iterrows():
                uei = row.get('UEI (Unique Entity Identifier)', '')
                if uei:
                    original_data[uei] = row.to_dict()
            
        except Exception as e:
            print(f"! Could not load original data: {e}")
            original_data = {}
        
        # Get companies from database
        companies = db.query(EnrichedCompany).all()
        total = len(companies)
        
        print(f"\nRescoring {total} companies with full data...")
        print("=" * 60)
        
        score_distribution = []
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for i, company in enumerate(companies):
            # Get original data if available
            orig = original_data.get(company.uei, {})
            
            # Combine database fields with original data
            company_data = {
                'organization_name': company.organization_name,
                'primary_naics_code': float(company.primary_naics) if company.primary_naics else None,
                'website': company.website or orig.get('Website'),
                'city': company.city or orig.get('City'),
                'state': company.state or orig.get('State'),
                'zipcode': company.zipcode or orig.get('Zipcode'),
                'phone_number': company.phone_number or orig.get('Phone number'),
                # Add fields from original data
                'legal_structure': orig.get('Legal structure'),
                'email': orig.get('Email'),
                'address_line_1': orig.get('Address line 1'),
                'address_line_2': orig.get('Address line 2'),
                'active_sba_certifications': orig.get('Active SBA certifications'),
                'capabilities_narrative': orig.get('Capabilities narrative'),
                'first_name': orig.get('First Name'),
                'last_name': orig.get('Last Name'),
                'job_title': orig.get('Job Title'),
            }
            
            # Calculate scores with full data
            results = scorer.score_company(company_data)
            
            # Update database
            company.pe_investment_score = results['pe_investment_score']
            company.business_health_grade = results['business_health_grade']
            
            # Store full scoring details if we have metadata field
            if hasattr(company, 'metadata'):
                company.metadata = json.dumps(results['scoring_details'])
            
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
        if score_distribution:
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
        
        # Top companies with details
        print("\nTop 5 Scoring Companies (with details):")
        top_companies = db.query(EnrichedCompany).order_by(
            EnrichedCompany.pe_investment_score.desc()
        ).limit(5).all()
        
        for i, company in enumerate(top_companies, 1):
            orig = original_data.get(company.uei, {})
            print(f"\n  {i}. {company.organization_name}")
            print(f"     Score: {company.pe_investment_score:.1f}/100, Grade: {company.business_health_grade}")
            print(f"     Location: {company.city}, {company.state}")
            print(f"     NAICS: {company.primary_naics}")
            if company.website:
                print(f"     Website: {company.website}")
            if orig.get('Email'):
                print(f"     Email: {orig.get('Email')}")
            if orig.get('Active SBA certifications'):
                print(f"     Certifications: {orig.get('Active SBA certifications')}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
