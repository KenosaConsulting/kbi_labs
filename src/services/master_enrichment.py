#!/usr/bin/env python3
"""
KBI Labs Master Enrichment Script
Processes all 64,799 companies with available enrichments
"""
import pandas as pd
import sqlite3
import json
from datetime import datetime
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, '.')
load_dotenv()

class MasterEnrichment:
    def __init__(self):
        self.db_path = 'kbi_enriched_master.db'
        self.setup_database()
        self.start_time = time.time()
        
    def setup_database(self):
        """Create master database with all fields"""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS companies_master (
                -- Primary fields
                uei TEXT PRIMARY KEY,
                organization_name TEXT,
                primary_naics TEXT,
                state TEXT,
                city TEXT,
                zipcode TEXT,
                website TEXT,
                phone_number TEXT,
                email TEXT,
                legal_structure TEXT,
                active_sba_certifications TEXT,
                capabilities_narrative TEXT,
                address_line_1 TEXT,
                address_line_2 TEXT,
                first_name TEXT,
                last_name TEXT,
                job_title TEXT,
                capabilities_statement_link TEXT,
                
                -- Scoring
                pe_investment_score REAL,
                business_health_grade TEXT,
                
                -- Industry analysis
                industry_sector TEXT,
                industry_growth_score REAL,
                market_position_score REAL,
                
                -- Location analysis
                location_score REAL,
                state_business_climate TEXT,
                metro_area TEXT,
                
                -- Digital presence
                has_website INTEGER,
                website_quality_score REAL,
                digital_maturity_score REAL,
                
                -- Certification analysis
                certification_count INTEGER,
                certification_value_score REAL,
                federal_contractor_potential REAL,
                
                -- Size and scale
                estimated_employees TEXT,
                estimated_revenue TEXT,
                business_age_estimate INTEGER,
                
                -- Risk assessment
                overall_risk_score REAL,
                data_completeness_score REAL,
                
                -- Metadata
                enrichment_timestamp TIMESTAMP,
                processing_time_seconds REAL,
                data_sources TEXT,
                enrichment_version TEXT DEFAULT '3.0'
            )
        ''')
        
        # Create indexes for performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_pe_score ON companies_master(pe_investment_score DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_state ON companies_master(state)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_naics ON companies_master(primary_naics)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_grade ON companies_master(business_health_grade)')
        
        conn.commit()
        conn.close()
        print("✓ Master database created")
    
    def enrich_company(self, company):
        """Comprehensive enrichment for each company"""
        start = time.time()
        
        # Base data
        enriched = {
            'uei': company.get('UEI (Unique Entity Identifier)'),
            'organization_name': company.get('Organization Name'),
            'primary_naics': str(company.get('Primary NAICS code', '')),
            'state': company.get('State'),
            'city': company.get('City'),
            'zipcode': str(company.get('Zipcode', '')),
            'website': company.get('Website'),
            'phone_number': str(company.get('Phone number', '')),
            'email': company.get('Contact person\'s email'),
            'legal_structure': company.get('Legal structure'),
            'active_sba_certifications': company.get('Active SBA certifications'),
            'capabilities_narrative': company.get('Capabilities narrative'),
            'address_line_1': company.get('Address line 1'),
            'address_line_2': company.get('Address line 2'),
            'first_name': company.get('First Name'),
            'last_name': company.get('Last Name'),
            'job_title': company.get('Job Title'),
            'capabilities_statement_link': company.get('Capabilities statement link'),
            'enrichment_timestamp': datetime.now()
        }
        
        # Industry analysis
        if enriched['primary_naics']:
            naics_2 = enriched['primary_naics'][:2]
            enriched['industry_sector'] = self.get_industry_sector(naics_2)
            enriched['industry_growth_score'] = self.calculate_industry_growth(naics_2)
        
        # Location analysis
        enriched['location_score'] = self.calculate_location_score(
            enriched['city'], enriched['state']
        )
        enriched['metro_area'] = self.identify_metro_area(enriched['city'], enriched['state'])
        
        # Digital presence
        enriched['has_website'] = 1 if enriched['website'] else 0
        enriched['website_quality_score'] = self.assess_website_quality(enriched['website'])
        enriched['digital_maturity_score'] = self.calculate_digital_maturity(enriched)
        
        # Certifications
        cert_analysis = self.analyze_certifications(enriched['active_sba_certifications'])
        enriched.update(cert_analysis)
        
        # Risk and completeness
        enriched['data_completeness_score'] = self.calculate_completeness(enriched)
        enriched['overall_risk_score'] = self.calculate_risk_score(enriched)
        
        # Scoring
        from src.enrichment.scoring import PEInvestmentScorer
        scorer = PEInvestmentScorer()
        scores = scorer.score_company(enriched)
        enriched['pe_investment_score'] = scores['pe_investment_score']
        enriched['business_health_grade'] = scores['business_health_grade']
        
        # Metadata
        enriched['processing_time_seconds'] = time.time() - start
        enriched['data_sources'] = 'DSBS,Internal_Analysis'
        
        return enriched
    
    def get_industry_sector(self, naics_2):
        """Map NAICS to industry sector"""
        sectors = {
            '11': 'Agriculture', '21': 'Mining', '22': 'Utilities',
            '23': 'Construction', '31': 'Manufacturing', '32': 'Manufacturing',
            '33': 'Manufacturing', '42': 'Wholesale Trade', '44': 'Retail Trade',
            '45': 'Retail Trade', '48': 'Transportation', '49': 'Transportation',
            '51': 'Information', '52': 'Finance', '53': 'Real Estate',
            '54': 'Professional Services', '55': 'Management', '56': 'Administrative',
            '61': 'Educational', '62': 'Healthcare', '71': 'Arts/Entertainment',
            '72': 'Accommodation/Food', '81': 'Other Services', '92': 'Public Admin'
        }
        return sectors.get(naics_2, 'Other')
    
    def calculate_industry_growth(self, naics_2):
        """Score industry growth potential"""
        high_growth = ['51', '52', '54', '62']  # Tech, Finance, Professional, Healthcare
        medium_growth = ['23', '31', '32', '33', '48', '49', '56']
        
        if naics_2 in high_growth:
            return 0.9
        elif naics_2 in medium_growth:
            return 0.6
        else:
            return 0.4
    
    def calculate_location_score(self, city, state):
        """Score location for business potential"""
        top_states = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
        major_cities = ['new york', 'los angeles', 'chicago', 'houston', 'phoenix',
                       'philadelphia', 'san antonio', 'san diego', 'dallas', 'san jose',
                       'austin', 'boston', 'seattle', 'denver', 'washington', 'atlanta']
        
        score = 0.5  # Base score
        
        if state in top_states:
            score += 0.2
        
        if city and any(major in str(city).lower() for major in major_cities):
            score += 0.3
            
        return min(score, 1.0)
    
    def identify_metro_area(self, city, state):
        """Identify metropolitan area"""
        if not city:
            return None
            
        city_lower = str(city).lower()
        
        # Simple metro mapping
        if any(x in city_lower for x in ['new york', 'brooklyn', 'queens']):
            return 'New York Metro'
        elif any(x in city_lower for x in ['los angeles', 'santa monica', 'pasadena']):
            return 'Los Angeles Metro'
        elif any(x in city_lower for x in ['chicago', 'evanston', 'naperville']):
            return 'Chicago Metro'
        elif any(x in city_lower for x in ['dallas', 'fort worth', 'arlington']):
            return 'Dallas-Fort Worth Metro'
        elif any(x in city_lower for x in ['houston', 'sugar land', 'the woodlands']):
            return 'Houston Metro'
        elif state == 'DC' or 'washington' in city_lower:
            return 'Washington DC Metro'
        else:
            return f'{city} Area'
    
    def assess_website_quality(self, website):
        """Assess website quality"""
        if not website:
            return 0.0
            
        website_str = str(website).lower()
        score = 0.5  # Has website
        
        # HTTPS
        if website_str.startswith('https://'):
            score += 0.2
        
        # Professional domain
        if not any(x in website_str for x in ['wix', 'weebly', 'wordpress.com', 'blogspot']):
            score += 0.2
        
        # .com domain
        if '.com' in website_str:
            score += 0.1
            
        return min(score, 1.0)
    
    def calculate_digital_maturity(self, company):
        """Calculate overall digital maturity"""
        score = 0.0
        
        if company.get('website'):
            score += 0.4
        if company.get('email'):
            score += 0.3
        if company.get('capabilities_statement_link'):
            score += 0.3
            
        return score
    
    def analyze_certifications(self, certifications):
        """Analyze SBA certifications"""
        if not certifications:
            return {
                'certification_count': 0,
                'certification_value_score': 0.0,
                'federal_contractor_potential': 0.3
            }
        
        cert_str = str(certifications).upper()
        cert_count = 0
        value_score = 0.0
        
        # High-value certifications
        high_value = {'8(A)': 0.9, 'HUBZONE': 0.8, 'SDVOSB': 0.8}
        medium_value = {'WOSB': 0.7, 'EDWOSB': 0.7, 'VOSB': 0.7}
        
        for cert, score in high_value.items():
            if cert in cert_str:
                cert_count += 1
                value_score = max(value_score, score)
        
        for cert, score in medium_value.items():
            if cert in cert_str:
                cert_count += 1
                value_score = max(value_score, score)
        
        federal_potential = min(0.3 + (cert_count * 0.2), 1.0)
        
        return {
            'certification_count': cert_count,
            'certification_value_score': value_score,
            'federal_contractor_potential': federal_potential
        }
    
    def calculate_completeness(self, company):
        """Calculate data completeness score"""
        important_fields = [
            'organization_name', 'primary_naics', 'state', 'city',
            'website', 'phone_number', 'email', 'capabilities_narrative'
        ]
        
        filled = sum(1 for field in important_fields if company.get(field))
        return filled / len(important_fields)
    
    def calculate_risk_score(self, company):
        """Calculate overall risk score (lower is better)"""
        risk = 0.5  # Base risk
        
        # Lower risk for better data
        risk -= company.get('data_completeness_score', 0) * 0.2
        
        # Lower risk for established structures
        if company.get('legal_structure') and 'LLC' in str(company.get('legal_structure')):
            risk -= 0.1
        elif company.get('legal_structure') and 'Corporation' in str(company.get('legal_structure')):
            risk -= 0.15
        
        # Lower risk for certified businesses
        risk -= company.get('certification_count', 0) * 0.05
        
        return max(0.1, min(risk, 1.0))
    
    def process_dataset(self, csv_path, limit=None):
        """Process the full dataset"""
        print(f"\n{'='*60}")
        print("KBI LABS MASTER ENRICHMENT")
        print(f"{'='*60}")
        print(f"Processing: {csv_path}")
        
        # Read CSV
        dtype_spec = {
            'Zipcode': str, 'Phone number': str, 
            'Primary NAICS code': str, 'First Name': str,
            'Last Name': str
        }
        
        if limit:
            df = pd.read_csv(csv_path, nrows=limit, dtype=dtype_spec)
            print(f"Processing limited to {limit} companies")
        else:
            # Count total rows first
            total_rows = sum(1 for _ in open(csv_path)) - 1
            print(f"Total companies to process: {total_rows:,}")
            df = pd.read_csv(csv_path, dtype=dtype_spec)
        
        # Process in batches
        batch_size = 1000
        conn = sqlite3.connect(self.db_path)
        processed = 0
        
        for i in range(0, len(df), batch_size):
            batch_start = time.time()
            batch = df.iloc[i:i+batch_size]
            enriched_batch = []
            
            for _, company in batch.iterrows():
                try:
                    enriched = self.enrich_company(company.to_dict())
                    enriched_batch.append(enriched)
                except Exception as e:
                    print(f"Error processing {company.get('Organization Name')}: {e}")
            
            # Save batch
            if enriched_batch:
                df_enriched = pd.DataFrame(enriched_batch)
                df_enriched.to_sql('companies_master', conn, 
                                 if_exists='append', index=False)
                processed += len(enriched_batch)
                
                # Progress update
                batch_time = time.time() - batch_start
                rate = len(enriched_batch) / batch_time
                eta = (len(df) - processed) / rate / 60  # minutes
                
                print(f"Progress: {processed:,}/{len(df):,} companies "
                      f"({processed/len(df)*100:.1f}%) - "
                      f"Rate: {rate:.1f} companies/sec - "
                      f"ETA: {eta:.1f} minutes")
        
        conn.close()
        total_time = (time.time() - self.start_time) / 60
        
        print(f"\n{'='*60}")
        print(f"✓ ENRICHMENT COMPLETE!")
        print(f"{'='*60}")
        print(f"Total companies processed: {processed:,}")
        print(f"Total time: {total_time:.1f} minutes")
        print(f"Average rate: {processed/total_time:.1f} companies/minute")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive summary"""
        conn = sqlite3.connect(self.db_path)
        
        # Overall statistics
        stats = pd.read_sql_query("""
            SELECT 
                COUNT(*) as total,
                AVG(pe_investment_score) as avg_pe_score,
                AVG(data_completeness_score) as avg_completeness,
                COUNT(CASE WHEN has_website = 1 THEN 1 END) as has_website_count,
                COUNT(CASE WHEN certification_count > 0 THEN 1 END) as certified_count,
                AVG(certification_count) as avg_certs
            FROM companies_master
        """, conn)
        
        print(f"\n{'='*60}")
        print("ENRICHMENT SUMMARY")
        print(f"{'='*60}")
        
        s = stats.iloc[0]
        print(f"\nOverall Statistics:")
        print(f"  Total companies: {s['total']:,.0f}")
        print(f"  Average PE score: {s['avg_pe_score']:.1f}")
        print(f"  Average data completeness: {s['avg_completeness']:.1%}")
        print(f"  Companies with websites: {s['has_website_count']:,.0f} ({s['has_website_count']/s['total']*100:.1f}%)")
        print(f"  Certified companies: {s['certified_count']:,.0f} ({s['certified_count']/s['total']*100:.1f}%)")
        print(f"  Average certifications: {s['avg_certs']:.1f}")
        
        # Grade distribution
        grades = pd.read_sql_query("""
            SELECT business_health_grade, COUNT(*) as count
            FROM companies_master
            GROUP BY business_health_grade
            ORDER BY business_health_grade
        """, conn)
        
        print("\nBusiness Health Grades:")
        for _, row in grades.iterrows():
            pct = row['count'] / s['total'] * 100
            print(f"  Grade {row['business_health_grade']}: {row['count']:,} ({pct:.1f}%)")
        
        # Top industries
        industries = pd.read_sql_query("""
            SELECT industry_sector, COUNT(*) as count, AVG(pe_investment_score) as avg_score
            FROM companies_master
            GROUP BY industry_sector
            ORDER BY count DESC
            LIMIT 10
        """, conn)
        
        print("\nTop Industries by Count:")
        for _, row in industries.iterrows():
            print(f"  {row['industry_sector']}: {row['count']:,} companies (avg score: {row['avg_score']:.1f})")
        
        # Top states
        states = pd.read_sql_query("""
            SELECT state, COUNT(*) as count, AVG(pe_investment_score) as avg_score
            FROM companies_master
            WHERE state IS NOT NULL
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """, conn)
        
        print("\nTop States by Count:")
        for _, row in states.iterrows():
            print(f"  {row['state']}: {row['count']:,} companies (avg score: {row['avg_score']:.1f})")
        
        # Top investment opportunities
        top_companies = pd.read_sql_query("""
            SELECT organization_name, city, state, pe_investment_score, 
                   business_health_grade, certification_count, has_website
            FROM companies_master
            ORDER BY pe_investment_score DESC
            LIMIT 20
        """, conn)
        
        print("\nTop 20 Investment Opportunities:")
        for i, row in top_companies.iterrows():
            print(f"\n  {i+1}. {row['organization_name']}")
            print(f"     Location: {row['city']}, {row['state']}")
            print(f"     PE Score: {row['pe_investment_score']:.1f} | Grade: {row['business_health_grade']}")
            print(f"     Certifications: {row['certification_count']} | Website: {'Yes' if row['has_website'] else 'No'}")
        
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='KBI Labs Master Enrichment')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    parser.add_argument('--full', action='store_true', help='Process full dataset')
    args = parser.parse_args()
    
    enricher = MasterEnrichment()
    
    if args.full:
        # Process full dataset
        csv_path = 'data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv'
        if os.path.exists(csv_path):
            response = input(f"\nThis will process all 64,799 companies. Continue? (y/n): ")
            if response.lower() == 'y':
                enricher.process_dataset(csv_path)
        else:
            print(f"Full dataset not found: {csv_path}")
    else:
        # Process sample or limited dataset
        sample_path = 'data/dsbs_raw/sample_50.csv'
        if os.path.exists(sample_path):
            enricher.process_dataset(sample_path, limit=args.limit)
        else:
            print("Sample file not found")
