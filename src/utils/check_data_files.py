#!/usr/bin/env python3
import glob
import pandas as pd

print("Checking DSBS CSV files...")

csv_files = glob.glob("All_DSBS_processed_chunk_*.csv")
print(f"\nFound {len(csv_files)} CSV files")

if csv_files:
    # Check first file
    df = pd.read_csv(csv_files[0])
    print(f"\nFirst file: {csv_files[0]}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst company: {df.iloc[0]['Organization Name']}")
else:
    print("\n⚠️  No DSBS CSV files found!")
    print("Make sure your CSV files are in the KBILabs directory")
