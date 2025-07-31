#!/usr/bin/env python3
"""Check data quality in the sample"""

import pandas as pd

# Load the sample data
df = pd.read_csv('data/dsbs_raw/sample_50.csv', dtype={'Zipcode': str, 'Phone number': str})

print("=== DATA QUALITY REPORT ===\n")
print(f"Total companies: {len(df)}")
print("\nField Completeness:")

fields = ['Email', 'Website', 'Phone number', 'Address line 1', 
          'Legal structure', 'Active SBA certifications', 
          'Capabilities narrative']

for field in fields:
    non_null = df[field].notna().sum()
    pct = (non_null / len(df)) * 100
    print(f"  {field}: {non_null}/{len(df)} ({pct:.1f}%)")

print("\nCapabilities Narrative Length:")
cap_lengths = df['Capabilities narrative'].fillna('').str.len()
print(f"  Average: {cap_lengths.mean():.0f} chars")
print(f"  Median: {cap_lengths.median():.0f} chars")
print(f"  Max: {cap_lengths.max():.0f} chars")

print("\nCertifications Distribution:")
cert_counts = df['Active SBA certifications'].value_counts()
print(f"  Companies with certs: {df['Active SBA certifications'].notna().sum()}")
print(f"  Most common: {cert_counts.head(3).to_dict()}")
