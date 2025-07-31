#!/usr/bin/env python3
"""Process all DSBS companies and create a searchable index"""

import pandas as pd
import json
from pathlib import Path
import sys

print("🔄 Processing 99,121 companies from DSBS dataset...")

# Read the CSV
csv_path = Path('data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv')
print(f"Reading {csv_path}...")

try:
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} companies")
    
    # Show sample
    print("\nSample companies:")
    for idx, row in df.head(10).iterrows():
        uei = row['UEI (Unique Entity Identifier)']
        name = row['Organization Name']
        state = row['State']
        print(f"  {idx+1}. {name} ({state}) -> UEI: {uei}")
    
    # Create a simple index file for quick lookups
    print("\n📝 Creating company index...")
    index = {}
    for idx, row in df.iterrows():
        uei = str(row['UEI (Unique Entity Identifier)'])
        index[uei] = {
            'name': row['Organization Name'],
            'state': row['State'],
            'city': row['City'],
            'row_index': idx
        }
        if idx % 10000 == 0:
            print(f"  Processed {idx} companies...")
    
    # Save index
    with open('data/company_index.json', 'w') as f:
        json.dump(index, f)
    
    print(f"\n✅ Created index with {len(index)} companies")
    print("📍 Index saved to data/company_index.json")
    
    # Show some statistics
    print("\n📊 Dataset Statistics:")
    print(f"  Total companies: {len(df)}")
    print(f"  States represented: {df['State'].nunique()}")
    print(f"  Top 5 states:")
    for state, count in df['State'].value_counts().head().items():
        print(f"    {state}: {count} companies")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
