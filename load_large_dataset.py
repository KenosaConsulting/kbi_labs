#!/usr/bin/env python3
"""
Load large DSBS dataset into API
"""
import pandas as pd
import json
import os
from pathlib import Path

def load_dsbs_data():
    """Load and combine all DSBS chunk files"""
    base_path = Path("/Users/oogwayuzumaki/Desktop/Work/BI/kbi_labs/KBILabs/data/")
    chunk_files = list(base_path.glob("All_DSBS_processed_chunk_*_20250727_182259.csv"))
    
    print(f"Found {len(chunk_files)} DSBS chunk files")
    
    all_companies = []
    
    for chunk_file in sorted(chunk_files):
        print(f"Loading {chunk_file.name}...")
        try:
            df = pd.read_csv(chunk_file)
            print(f"  - Loaded {len(df)} companies")
            
            # Convert to JSON format compatible with our API
            for _, row in df.iterrows():
                company = {
                    "uei": str(row.get("UEI (Unique Entity Identifier)", "")),
                    "organization_name": str(row.get("Organization Name", "")),
                    "pe_investment_score": 100.0,  # Default score
                    "federal_contracts_value": 0,
                    "patent_count": 0,
                    "primary_naics": str(row.get("Primary NAICS code", "")),
                    "state": str(row.get("State", "")),
                    "city": str(row.get("City", "")),
                    "cage_code": "",
                    "sam_status": "Active",
                    "business_health_grade": "A",
                    "website": str(row.get("Website", "")),
                    "phone_number": str(row.get("Phone number", "")),
                    "email": str(row.get("Email", "")),
                    "capabilities_narrative": str(row.get("Capabilities narrative", "")),
                    "address_line_1": str(row.get("Address line 1", "")),
                    "zipcode": str(row.get("Zipcode", "")),
                    "legal_structure": str(row.get("Legal structure", "")),
                    "active_sba_certifications": str(row.get("Active SBA certifications", ""))
                }
                all_companies.append(company)
                
        except Exception as e:
            print(f"Error loading {chunk_file.name}: {e}")
            continue
    
    print(f"\n✅ Total companies loaded: {len(all_companies)}")
    return all_companies

def save_large_dataset(companies):
    """Save combined dataset as JSON"""
    output_file = "/Users/oogwayuzumaki/Desktop/Work/BI/kbi_labs/KBILabs-main 2/companies_large.json"
    
    print(f"Saving {len(companies)} companies to {output_file}")
    
    with open(output_file, 'w') as f:
        json.dump(companies, f, indent=2)
    
    # Create summary
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    print(f"✅ Saved {len(companies)} companies ({file_size:.1f}MB)")
    
    return output_file

if __name__ == "__main__":
    print("🚀 Loading large DSBS dataset...")
    companies = load_dsbs_data()
    
    if companies:
        output_file = save_large_dataset(companies)
        print(f"\n✅ Dataset ready: {output_file}")
        print(f"📊 Total companies: {len(companies)}")
        
        # Show sample
        if companies:
            print("\n📝 Sample company:")
            sample = companies[0]
            for key, value in list(sample.items())[:5]:
                print(f"  {key}: {value}")
    else:
        print("❌ No companies loaded")