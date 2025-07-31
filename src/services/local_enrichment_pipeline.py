#!/usr/bin/env python3
"""
Enrichment pipeline that works without external APIs
Uses only local data files and scoring algorithms
"""
import pandas as pd
import sqlite3
import json
from datetime import datetime
import os

class LocalEnrichmentPipeline:
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'patent_matched': 0,
            'nsf_matched': 0
        }
        
    def enrich_companies(self, csv_path, output_db, limit=None):
        """Process companies using only local data"""
        print(f"Processing {csv_path}...")
        
        # Create database
        conn = sqlite3.connect(output_db)
        
        # Read companies
        if limit:
            df = pd.read_csv(csv_path, nrows=limit)
        else:
            df = pd.read_csv(csv_path)
            
        print(f"Loaded {len(df)} companies")
        
        # Process each company
        enriched_data = []
        for idx, company in df.iterrows():
            enriched = self.enrich_single_company(company)
            enriched_data.append(enriched)
            
            if idx % 100 == 0:
                print(f"Processed {idx}/{len(df)} companies...")
                
        # Save to database
        enriched_df = pd.DataFrame(enriched_data)
        enriched_df.to_sql('enriched_companies', conn, if_exists='replace', index=False)
        
        print(f"\nEnrichment complete!")
        print(f"Total processed: {len(enriched_df)}")
        print(f"Average PE Score: {enriched_df['pe_investment_score'].mean():.1f}")
        
        conn.close()
        
    def enrich_single_company(self, company):
        """Enrich using scoring algorithm only"""
        # Basic info
        enriched = {
            'uei': company.get('UEI (Unique Entity Identifier)'),
            'organization_name': company.get('Organization Name'),
            'state': company.get('State'),
            'city': company.get('City'),
            'primary_naics': str(company.get('Primary NAICS code', '')),
            'website': company.get('Website'),
            'email': company.get('Email'),
            'active_sba_certifications': company.get('Active SBA certifications'),
            'legal_structure': company.get('Legal structure')
        }
        
        # Calculate PE investment score
        score = 50.0  # Base score
        
        # Industry bonus
        naics = str(enriched['primary_naics'])[:2]
        tech_industries = ['51', '54', '52']  # Information, Professional Services, Finance
        if naics in tech_industries:
            score += 15
        
        # Location bonus
        top_states = ['California', 'Texas', 'New York', 'Florida']
        if enriched['state'] in top_states:
            score += 10
            
        # Digital presence
        if enriched['website']:
            score += 10
            
        # Certifications
        if enriched['active_sba_certifications']:
            score += 10
            
        # Business structure
        if 'LLC' in str(enriched['legal_structure']) or 'Corporation' in str(enriched['legal_structure']):
            score += 5
            
        # Assign grade
        if score >= 80:
            grade = 'A'
        elif score >= 70:
            grade = 'B'
        elif score >= 60:
            grade = 'C'
        elif score >= 50:
            grade = 'D'
        else:
            grade = 'F'
            
        enriched['pe_investment_score'] = score
        enriched['business_health_grade'] = grade
        enriched['enrichment_date'] = datetime.now().isoformat()
        
        return enriched

if __name__ == "__main__":
    pipeline = LocalEnrichmentPipeline()
    
    # Test with sample
    pipeline.enrich_companies(
        'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv',
        'kbi_local_enriched.db',
        limit=1000  # Test with first 1000
    )
