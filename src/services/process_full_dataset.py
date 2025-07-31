#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from src.enrichment.engine import EnrichmentEngine

print("Starting full dataset processing...")
print("This will process 64,799 companies")
print("Estimated time: 1-2 hours")

response = input("\nProceed? (y/n): ")
if response.lower() == 'y':
    engine = EnrichmentEngine(batch_size=50)
    engine.process_csv('data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv')
    print("\n✓ Processing complete!")
else:
    print("Processing cancelled.")
