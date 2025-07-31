#!/usr/bin/env python3
import asyncio
import sys
import pandas as pd
sys.path.insert(0, '.')

from src.enrichment.engine import process_csv_batch

async def main():
    # Use the sample file
    sample_file = "data/dsbs_raw/sample_50.csv"
    
    # Check if it exists
    try:
        df = pd.read_csv(sample_file)
        print(f"Found {len(df)} companies in sample file")
    except:
        # Create a sample from the full file
        print("Creating sample file...")
        full_df = pd.read_csv("data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv")
        sample_df = full_df.head(50)
        sample_df.to_csv(sample_file, index=False)
        print(f"Created sample with {len(sample_df)} companies")
    
    # Process the sample
    print("\nProcessing sample file...")
    await process_csv_batch(sample_file, batch_size=10)
    print("✓ Sample enrichment complete!")

if __name__ == "__main__":
    asyncio.run(main())
