#!/usr/bin/env python3
import asyncio
import glob
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enrichment.engine import process_csv_batch

async def main():
    """Run enrichment on all DSBS CSV files"""
    print(f"Starting enrichment run at {datetime.now()}")
    
    # Look for CSV files in multiple locations
    csv_patterns = [
        "data/dsbs_raw/All_DSBS_processed_chunk_*.csv",
        "data/All_DSBS_processed_chunk_*.csv",
        "All_DSBS_processed_chunk_*.csv"
    ]
    
    csv_files = []
    for pattern in csv_patterns:
        csv_files.extend(glob.glob(pattern))
    
    # Remove duplicates
    csv_files = list(set(csv_files))
    
    print(f"Found {len(csv_files)} CSV files to process:")
    for f in csv_files:
        print(f"  - {f}")
    
    # Process each file
    for csv_file in sorted(csv_files):
        print(f"\nProcessing {csv_file}...")
        try:
            await process_csv_batch(csv_file, batch_size=100)
            print(f"✓ Completed {csv_file}")
        except Exception as e:
            print(f"✗ Error processing {csv_file}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nEnrichment completed at {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
