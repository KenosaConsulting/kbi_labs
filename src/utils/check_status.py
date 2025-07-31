#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from src.database.connection import SessionLocal
from src.enrichment.models import EnrichedCompany
import pandas as pd

def main():
    # Check database
    db = SessionLocal()
    total = db.query(EnrichedCompany).count()
    print(f"\n=== KBI Labs Platform Status ===")
    print(f"Database: SQLite (kbi_enriched.db)")
    print(f"Total enriched companies: {total}")
    
    # Check CSV files
    print(f"\n=== Available Data Files ===")
    files = [
        ("Sample (50)", "data/dsbs_raw/sample_50.csv"),
        ("Full dataset", "data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv")
    ]
    
    for name, path in files:
        try:
            df = pd.read_csv(path)
            print(f"{name}: {len(df)} companies")
        except:
            print(f"{name}: Not found")
    
    # Show sample enriched company
    if total > 0:
        sample = db.query(EnrichedCompany).first()
        print(f"\n=== Sample Enriched Company ===")
        print(f"Name: {sample.organization_name}")
        print(f"UEI: {sample.uei}")
        print(f"State: {sample.state}")
        print(f"PE Score: {sample.pe_investment_score}")
        print(f"Health Grade: {sample.business_health_grade}")
    
    db.close()
    
    print("\n✓ System check complete!")

if __name__ == "__main__":
    main()
