#!/usr/bin/env python3
"""
Process the full 64,799 company dataset with all enrichments
"""
import pandas as pd
import sqlite3
import time
from enrichment_final_fixed import FinalEnrichment
import os

def main():
    print("\n" + "="*60)
    print("KBI LABS - FULL DATASET PROCESSING")
    print("="*60)
    
    # Check if full dataset exists
    full_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
    
    if not os.path.exists(full_path):
        print(f"Error: Full dataset not found at {full_path}")
        return
    
    # Count total rows
    print("\nCounting companies...")
    total_rows = sum(1 for _ in open(full_path)) - 1
    print(f"Total companies to process: {total_rows:,}")
    
    print("\nThis will:")
    print("- Calculate PE investment scores")
    print("- Match against 497,513 patent holders")
    print("- Get Census demographic data")
    print("- Get FRED economic indicators")
    print("- Process NSF grant data")
    print(f"\nEstimated time: {total_rows/5000:.0f}-{total_rows/3000:.0f} minutes")
    
    response = input("\nProceed with full enrichment? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Initialize enricher
    enricher = FinalEnrichment()
    
    # Process full dataset
    start_time = time.time()
    output_db = 'kbi_full_dataset_enriched.db'
    
    # Process with a reasonable limit first to test
    # Remove limit parameter to process all
    enricher.process_dataset(full_path, output_db, limit=5000)
    
    elapsed = time.time() - start_time
    print(f"\nTotal processing time: {elapsed/60:.1f} minutes")
    
    # Generate final report
    generate_final_report(output_db)

def generate_final_report(db_path):
    """Generate comprehensive final report"""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM companies_enriched", conn)
    
    print("\n" + "="*60)
    print("FINAL ENRICHMENT REPORT")
    print("="*60)
    
    print(f"\nTotal companies enriched: {len(df):,}")
    print(f"Average PE Score: {df['pe_score'].mean():.1f}")
    
    # Score distribution
    print("\nPE Score Distribution:")
    bins = [0, 50, 60, 70, 80, 90, 100]
    labels = ['0-50', '51-60', '61-70', '71-80', '81-90', '91-100']
    df['score_range'] = pd.cut(df['pe_score'], bins=bins, labels=labels)
    
    for range_label in labels:
        count = (df['score_range'] == range_label).sum()
        pct = count / len(df) * 100
        print(f"  {range_label}: {count:,} ({pct:.1f}%)")
    
    # State distribution
    print("\nTop 10 States by Company Count:")
    state_counts = df['state'].value_counts().head(10)
    for state, count in state_counts.items():
        avg_score = df[df['state'] == state]['pe_score'].mean()
        print(f"  {state}: {count:,} companies (avg score: {avg_score:.1f})")
    
    # Patent holders
    patent_holders = df[df['patent_count'] > 0]
    print(f"\nPatent Statistics:")
    print(f"  Companies with patents: {len(patent_holders):,} ({len(patent_holders)/len(df)*100:.1f}%)")
    print(f"  Total patents: {df['patent_count'].sum():,}")
    print(f"  Max patents per company: {df['patent_count'].max():,}")
    
    # Save summary to CSV
    summary_path = 'enrichment_summary.csv'
    df.to_csv(summary_path, index=False)
    print(f"\nFull data exported to: {summary_path}")
    
    conn.close()

if __name__ == "__main__":
    main()
