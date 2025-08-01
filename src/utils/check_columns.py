#!/usr/bin/env python3
"""Check the actual column names in the dataset"""

import pandas as pd

# Load a small sample to check column names
df = pd.read_csv('data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv', nrows=5)

print("Column names in the dataset:")
print("=" * 50)
for i, col in enumerate(df.columns):
    print(f"{i+1}. '{col}'")

print("\nFirst row sample:")
print("=" * 50)
for col in df.columns:
    value = df[col].iloc[0] if len(df) > 0 else "N/A"
    print(f"{col}: {value}")
