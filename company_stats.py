#!/usr/bin/env python3
"""Show statistics about the DSBS dataset"""

import pandas as pd
import json
from collections import Counter
import os

def load_all_data():
    """Load all DSBS CSV chunks into a single DataFrame"""
    chunks = []
    # Check if we have the combined file first
    combined_file = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
    
    if os.path.exists(combined_file):
        print(f"Found combined file: {combined_file}")
        try:
            df = pd.read_csv(combined_file, low_memory=False)
            print(f"✓ Loaded combined file: {len(df):,} rows")
            return df
        except Exception as e:
            print(f"✗ Error loading combined file: {e}")
    
    # Otherwise load individual chunks
    files = [
        'data/dsbs_raw/All_DSBS_processed_chunk_001_20250727_182259.csv',
        'data/dsbs_raw/All_DSBS_processed_chunk_002_20250727_182259.csv',
        'data/dsbs_raw/All_DSBS_processed_chunk_003_20250727_182259.csv',
        'data/dsbs_raw/All_DSBS_processed_chunk_004_20250727_182259.csv',
        'data/dsbs_raw/All_DSBS_processed_chunk_005_20250727_182259.csv',
        'data/dsbs_raw/All_DSBS_processed_chunk_006_20250727_182259.csv',
        'data/dsbs_raw/All_DSBS_processed_chunk_007_20250727_182259.csv'
    ]
    
    for filename in files:
        try:
            df = pd.read_csv(filename, low_memory=False)
            chunks.append(df)
            print(f"✓ Loaded {os.path.basename(filename)}: {len(df):,} rows")
        except Exception as e:
            print(f"✗ Error loading {os.path.basename(filename)}: {e}")
    
    if chunks:
        return pd.concat(chunks, ignore_index=True)
    return None

def find_column(df, possible_names):
    """Find column by trying multiple possible names"""
    for name in possible_names:
        if name in df.columns:
            return name
    return None

def analyze_dataset(df):
    """Generate comprehensive statistics"""
    print("\n📊 DSBS Dataset Statistics")
    print("=" * 60)
    print(f"Total Companies: {len(df):,}")
    print(f"States/Territories: {df['State'].nunique()}")
    print(f"Cities: {df['City'].nunique():,}")
    
    # State analysis
    print("\n🏢 Top 10 States by Company Count:")
    for state, count in df['State'].value_counts().head(10).items():
        print(f"  {state}: {count:,} companies ({count/len(df)*100:.1f}%)")
    
    # Digital presence
    print("\n🌐 Digital Presence:")
    has_website = df['Website'].notna().sum()
    print(f"  With website: {has_website:,} ({has_website/len(df)*100:.1f}%)")
    print(f"  Without website: {len(df)-has_website:,} ({(len(df)-has_website)/len(df)*100:.1f}%)")
    
    # Phone analysis - handle potential column name variations
    phone_col = find_column(df, ['Phone number', 'Phone', 'Phone Number'])
    if phone_col:
        print(f"\n📞 Contact Information:")
        print(f"  With phone: {df[phone_col].notna().sum():,}")
    
    # Certifications
    cert_col = find_column(df, ['Active SBA certifications', 'SBA certifications', 'Certifications'])
    if cert_col:
        print("\n📜 SBA Certifications:")
        has_certs = df[cert_col].notna().sum()
        print(f"  With SBA certifications: {has_certs:,} ({has_certs/len(df)*100:.1f}%)")
        
        # Count specific certifications
        cert_counts = Counter()
        for certs in df[cert_col].dropna():
            for cert in str(certs).split(','):
                cert_counts[cert.strip()] += 1
        
        if cert_counts:
            print("  Top certifications:")
            for cert, count in cert_counts.most_common(5):
                print(f"    {cert}: {count:,} companies")
    
    # Legal structure
    legal_col = find_column(df, ['Legal structure', 'Legal Structure', 'Business Structure'])
    if legal_col:
        print("\n⚖️ Legal Structure Distribution:")
        for structure, count in df[legal_col].value_counts().head(5).items():
            print(f"  {structure}: {count:,} ({count/len(df)*100:.1f}%)")
        
        # High-value targets for PE firms
        print("\n🎯 High-Value PE Targets:")
        pe_targets = df[
            (df['Website'].isna()) & 
            (df[legal_col].str.contains('Corporate|LLC', case=False, na=False))
        ]
        print(f"  Total potential targets: {len(pe_targets):,}")
        
        # Show top states for PE targets
        print("  Top states for acquisition targets:")
        for state, count in pe_targets['State'].value_counts().head(5).items():
            print(f"    {state}: {count:,} companies")
    
    # Industry analysis
    naics_col = find_column(df, ['Primary NAICS code', 'NAICS code', 'NAICS'])
    if naics_col:
        print("\n🏗️ Top Industries (by NAICS prefix):")
        df['NAICS_prefix'] = df[naics_col].astype(str).str[:2]
        naics_mapping = {
            '11': 'Agriculture',
            '21': 'Mining',
            '22': 'Utilities',
            '23': 'Construction',
            '31': 'Manufacturing',
            '32': 'Manufacturing',
            '33': 'Manufacturing',
            '42': 'Wholesale Trade',
            '44': 'Retail Trade',
            '45': 'Retail Trade',
            '48': 'Transportation',
            '49': 'Transportation',
            '51': 'Information',
            '52': 'Finance/Insurance',
            '53': 'Real Estate',
            '54': 'Professional Services',
            '55': 'Management',
            '56': 'Admin Support',
            '61': 'Education',
            '62': 'Healthcare',
            '71': 'Arts/Entertainment',
            '72': 'Accommodation/Food',
            '81': 'Other Services',
            '92': 'Public Admin'
        }
        
        for naics, count in df['NAICS_prefix'].value_counts().head(10).items():
            industry = naics_mapping.get(naics, 'Unknown')
            print(f"  {naics} - {industry}: {count:,} companies")
    
    # SMB improvement opportunities
    print("\n💡 SMB Improvement Opportunities:")
    needs_digital = df[df['Website'].isna()]
    
    if legal_col:
        sole_props = df[df[legal_col].str.contains('Sole', case=False, na=False)]
        print(f"  Sole proprietorships (succession planning): {len(sole_props):,}")
    
    capabilities_col = find_column(df, ['Capabilities narrative', 'Capabilities', 'Capability Statement'])
    if capabilities_col:
        no_capabilities = df[df[capabilities_col].isna()]
        print(f"  Companies without capability statements: {len(no_capabilities):,}")
    
    print(f"  Companies needing websites: {len(needs_digital):,}")
    
    # Export insights for API use
    insights = {
        'total_companies': int(len(df)),
        'states': df['State'].value_counts().head(20).to_dict(),
        'digital_presence': {
            'with_website': int(has_website),
            'without_website': int(len(df) - has_website)
        }
    }
    
    # Add optional fields if columns exist
    if 'NAICS_prefix' in df.columns:
        insights['industries'] = df['NAICS_prefix'].value_counts().head(10).to_dict()
    
    if cert_col and cert_counts:
        insights['certifications'] = dict(cert_counts.most_common(10))
    
    if legal_col:
        pe_targets = df[
            (df['Website'].isna()) & 
            (df[legal_col].str.contains('Corporate|LLC', case=False, na=False))
        ]
        insights['pe_targets'] = {
            'total': int(len(pe_targets)),
            'by_state': pe_targets['State'].value_counts().head(10).to_dict()
        }
    
    # Save insights
    with open('data/market_insights.json', 'w') as f:
        json.dump(insights, f, indent=2)
    print("\n✅ Market insights exported to data/market_insights.json")
    
    # Print available columns for debugging
    print("\n📋 Available columns in dataset:")
    print(", ".join(df.columns))
    
    return df

if __name__ == "__main__":
    print("Loading DSBS dataset...")
    df = load_all_data()
    
    if df is not None:
        analyze_dataset(df)
    else:
        print("Failed to load data!")
