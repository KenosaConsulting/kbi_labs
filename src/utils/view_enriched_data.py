#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from src.database.connection import SessionLocal
from src.enrichment.models import EnrichedCompany

def main():
    db = SessionLocal()
    
    # Get statistics
    total = db.query(EnrichedCompany).count()
    print(f"\nTotal enriched companies: {total}")
    
    if total > 0:
        # Show first few companies
        companies = db.query(EnrichedCompany).limit(5).all()
        print("\nFirst 5 companies:")
        for c in companies:
            print(f"\n- {c.organization_name} ({c.uei})")
            print(f"  State: {c.state}, City: {c.city}")
            print(f"  NAICS: {c.primary_naics}")
            print(f"  PE Score: {c.pe_investment_score}")
            print(f"  Health Grade: {c.business_health_grade}")
    
    # Count by state
    if total > 0:
        from sqlalchemy import func
        states = db.query(
            EnrichedCompany.state, 
            func.count(EnrichedCompany.uei)
        ).group_by(EnrichedCompany.state).all()
        
        print("\nCompanies by state:")
        for state, count in sorted(states, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {state}: {count}")
    
    db.close()

if __name__ == "__main__":
    main()
