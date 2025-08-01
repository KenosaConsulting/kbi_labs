#!/usr/bin/env python3
"""
Integrated enrichment pipeline combining Google Places + Domain Analysis
"""

import pandas as pd
import asyncio
import sqlite3
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import aiohttp

# Import your enrichment modules
from enrichment_apis import RealAPIEnrichmentPipeline
from domain_enrichment import enrich_smb_with_domain

load_dotenv()

async def full_enrichment_pipeline():
    """Run comprehensive enrichment on SMB data"""
    
    print("🚀 Starting integrated enrichment pipeline...")
    
    # Load your data
    df = pd.read_csv('data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv')
    
    # Take a sample for testing
    sample_size = 50  # Start small
    sample_data = df.head(sample_size).to_dict('records')
    
    # Initialize Google Places enrichment
    google_pipeline = RealAPIEnrichmentPipeline()
    
    # Create results database
    conn = sqlite3.connect('smb_full_enrichment.db')
    cursor = conn.cursor()
    
    # Create comprehensive table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fully_enriched_smbs (
            uei TEXT PRIMARY KEY,
            organization_name TEXT,
            email TEXT,
            state TEXT,
            city TEXT,
            
            -- Google Places data
            google_rating REAL,
            google_reviews_count INTEGER,
            google_place_id TEXT,
            
            -- Domain analysis
            domain TEXT,
            website_status TEXT,
            has_ssl BOOLEAN,
            domain_age_years REAL,
            technology_signals TEXT,
            digital_maturity_score REAL,
            email_provider TEXT,
            
            -- Calculated scores
            succession_risk_score REAL,
            digital_presence_score REAL,
            estimated_revenue REAL,
            
            -- Risk factors
            risk_factors TEXT,
            
            last_enriched TIMESTAMP
        )
    ''')
    conn.commit()
    
    # Process in batches
    batch_size = 5
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(sample_data), batch_size):
            batch = sample_data[i:i+batch_size]
            print(f"\n📊 Processing batch {i//batch_size + 1}")
            
            for smb in batch:
                try:
                    # 1. Google Places enrichment
                    enhanced_smb = await google_pipeline.enrich_single_smb(session, smb)
                    
                    # 2. Domain enrichment
                    domain_data = await enrich_smb_with_domain(smb)
                    
                    # 3. Combine insights
                    combined_risk = enhanced_smb.succession_risk_score
                    if domain_data.get('website_status') != 'active':
                        combined_risk += 1.5
                    if (domain_data.get('domain_age_years') or 0) < 2:
                        combined_risk += 1.0
                    
                    # Save to database
                    cursor.execute('''
                        INSERT OR REPLACE INTO fully_enriched_smbs VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    ''', (
                        enhanced_smb.uei,
                        enhanced_smb.organization_name,
                        enhanced_smb.email,
                        enhanced_smb.state,
                        enhanced_smb.city,
                        enhanced_smb.google_rating,
                        enhanced_smb.google_reviews_count,
                        enhanced_smb.google_place_id,
                        domain_data.get('domain'),
                        domain_data.get('website_status'),
                        domain_data.get('has_ssl'),
                        domain_data.get('domain_age_years'),
                        json.dumps(domain_data.get('technology_signals', [])),
                        domain_data.get('digital_maturity_score'),
                        domain_data.get('email_provider'),
                        min(combined_risk, 10.0),
                        enhanced_smb.digital_presence_score,
                        enhanced_smb.estimated_revenue,
                        json.dumps(domain_data.get('succession_risk_factors', [])),
                        datetime.now()
                    ))
                    
                    print(f"  ✅ {enhanced_smb.organization_name[:30]}: Risk={combined_risk:.1f}")
                    
                except Exception as e:
                    print(f"  ❌ Error: {str(e)[:50]}")
            
            conn.commit()
            await asyncio.sleep(1)
    
    # Show final statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(succession_risk_score) as avg_risk,
            COUNT(CASE WHEN website_status = 'active' THEN 1 END) as with_websites,
            COUNT(CASE WHEN google_rating IS NOT NULL THEN 1 END) as with_google,
            COUNT(CASE WHEN domain_age_years > 10 THEN 1 END) as established
        FROM fully_enriched_smbs
    ''')
    
    stats = cursor.fetchone()
    print(f"\n📈 Final Statistics:")
    print(f"  Total: {stats[0]}")
    print(f"  Avg Risk: {stats[1]:.1f}")
    print(f"  Active Websites: {stats[2]}")
    print(f"  Google Presence: {stats[3]}")
    print(f"  Established (10+ yrs): {stats[4]}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(full_enrichment_pipeline())
