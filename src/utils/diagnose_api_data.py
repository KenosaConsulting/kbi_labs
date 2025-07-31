#!/usr/bin/env python3
"""
Diagnostic script to test SAM.gov API and check NSF data
"""
import os
import requests
import pandas as pd
from dotenv import load_dotenv
import json
import glob

# Load environment variables
load_dotenv()

def test_sam_gov_api():
    """Test SAM.gov API with various endpoints"""
    print("\n" + "="*60)
    print("TESTING SAM.GOV API")
    print("="*60)
    
    api_key = os.getenv('SAM_GOV_API_KEY')
    
    if not api_key:
        print("❌ No SAM.gov API key found in .env file")
        return False
    
    print(f"✓ API Key found: {api_key[:10]}...")
    
    # Test different endpoints
    test_cases = [
        {
            'name': 'Entity Information API v3',
            'url': 'https://api.sam.gov/entity-information/v3/entities',
            'params': {
                'api_key': api_key,
                'ueiSAM': 'ZQGGHJH74DW7',  # Example UEI
                'includeSections': 'entityRegistration'
            }
        },
        {
            'name': 'Entity Information API v2',
            'url': 'https://api.sam.gov/entity-information/v2/entities',
            'params': {
                'api_key': api_key,
                'ueiSAM': 'ZQGGHJH74DW7'
            }
        },
        {
            'name': 'Opportunities API',
            'url': 'https://api.sam.gov/opportunities/v2/search',
            'params': {
                'api_key': api_key,
                'limit': 1
            }
        }
    ]
    
    working_endpoint = None
    
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            response = requests.get(test['url'], params=test['params'], timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ SUCCESS! This endpoint works")
                working_endpoint = test
                data = response.json()
                print(f"Response preview: {json.dumps(data, indent=2)[:500]}...")
            elif response.status_code == 401:
                print("❌ Authentication failed - API key may be invalid")
            elif response.status_code == 403:
                print("❌ Forbidden - API key may not have access to this endpoint")
            elif response.status_code == 404:
                print("❌ Not found - Endpoint or UEI doesn't exist")
            elif response.status_code == 429:
                print("⚠️  Rate limited - too many requests")
            else:
                print(f"❌ Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    return working_endpoint

def check_nsf_data():
    """Check what NSF data files we have"""
    print("\n" + "="*60)
    print("CHECKING NSF DATA")
    print("="*60)
    
    # Check common locations for NSF data
    nsf_paths = [
        'nsf_data/',
        'data/nsf/',
        'NSF_data/',
        './',
        'data/'
    ]
    
    found_files = []
    
    for path in nsf_paths:
        if os.path.exists(path):
            print(f"\nChecking {path}...")
            
            # Look for CSV and Excel files
            patterns = ['*.csv', '*.xlsx', '*.xls', '*nsf*', '*NSF*', '*grant*']
            
            for pattern in patterns:
                files = glob.glob(os.path.join(path, pattern))
                for file in files:
                    if 'nsf' in file.lower() or 'grant' in file.lower():
                        found_files.append(file)
                        print(f"  Found: {file}")
    
    if not found_files:
        print("\n❌ No NSF data files found")
        print("\nTo get NSF data:")
        print("1. Go to: https://www.nsf.gov/awardsearch/download.jsp")
        print("2. Download award data (CSV format)")
        print("3. Save to: nsf_data/ directory")
        return None
    
    # Analyze the first NSF file found
    print(f"\n📊 Analyzing NSF file: {found_files[0]}")
    
    try:
        if found_files[0].endswith('.csv'):
            df = pd.read_csv(found_files[0], nrows=5)
        else:
            df = pd.read_excel(found_files[0], nrows=5)
            
        print(f"Columns found: {list(df.columns)}")
        print(f"Total rows: {len(pd.read_csv(found_files[0])) if found_files[0].endswith('.csv') else 'Unknown'}")
        
        # Look for important columns
        important_cols = ['AwardAmount', 'AwardTitle', 'Organization', 'Institution', 
                         'AwardeeCity', 'AwardeeState', 'AwardEffectiveDate']
        
        print("\nImportant columns present:")
        for col in important_cols:
            if col in df.columns:
                print(f"  ✓ {col}")
            else:
                # Check case-insensitive
                matches = [c for c in df.columns if col.lower() in c.lower()]
                if matches:
                    print(f"  ✓ {col} (found as: {matches[0]})")
                else:
                    print(f"  ❌ {col}")
        
        return found_files[0]
        
    except Exception as e:
        print(f"❌ Error reading NSF file: {e}")
        return None

def test_with_real_uei():
    """Test SAM.gov with a real UEI from your data"""
    print("\n" + "="*60)
    print("TESTING WITH REAL UEI FROM YOUR DATA")
    print("="*60)
    
    # Get a real UEI from your data
    try:
        df = pd.read_csv('data/dsbs_raw/All_DSBS_processed_chunk_full_20250728.csv', nrows=10)
        
        # Find companies with valid UEIs
        valid_ueis = []
        for _, row in df.iterrows():
            uei = row.get('UEI (Unique Entity Identifier)')
            if pd.notna(uei) and len(str(uei)) == 12:
                valid_ueis.append({
                    'uei': uei,
                    'name': row.get('Organization Name')
                })
        
        if not valid_ueis:
            print("❌ No valid UEIs found in sample data")
            return
            
        print(f"Found {len(valid_ueis)} valid UEIs to test:")
        
        api_key = os.getenv('SAM_GOV_API_KEY')
        if not api_key:
            print("❌ No API key to test with")
            return
            
        # Test each UEI
        for company in valid_ueis[:3]:  # Test first 3
            print(f"\nTesting: {company['name']}")
            print(f"UEI: {company['uei']}")
            
            # Try v3 API
            url = 'https://api.sam.gov/entity-information/v3/entities'
            params = {
                'api_key': api_key,
                'ueiSAM': company['uei']
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if 'entityData' in data and data['entityData']:
                        entity = data['entityData'][0]
                        print(f"✓ Found in SAM.gov!")
                        print(f"  Registration Status: {entity.get('entityRegistration', {}).get('registrationStatus')}")
                        print(f"  Expiration Date: {entity.get('entityRegistration', {}).get('expirationDate')}")
                    else:
                        print("❌ Not found in SAM.gov")
                else:
                    print(f"❌ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Error reading data file: {e}")

def suggest_alternatives():
    """Suggest alternative approaches if APIs aren't working"""
    print("\n" + "="*60)
    print("ALTERNATIVE DATA SOURCES")
    print("="*60)
    
    print("\n📊 If SAM.gov API isn't working:")
    print("1. Check if your API key has the right permissions")
    print("2. Try the SAM.gov Entity Management API instead")
    print("3. Use the bulk data download:")
    print("   - Go to: https://sam.gov/data-services/Entity-Registration")
    print("   - Download the public data extract (updated daily)")
    print("   - Save as: sam_data/SAM_PUBLIC_EXTRACT.csv")
    
    print("\n📊 For NSF data:")
    print("1. Download from: https://www.nsf.gov/awardsearch/download.jsp")
    print("2. Select 'Download All' or specific years")
    print("3. Choose CSV format")
    print("4. Save to: nsf_data/ directory")
    
    print("\n📊 Additional enrichment sources:")
    print("1. Federal Spending:")
    print("   - https://www.usaspending.gov/download_center/award_data_archive")
    print("2. SBA Dynamic Small Business Search:")
    print("   - https://data.sba.gov/dataset/dynamic-small-business-search-dsbs")
    print("3. D&B Hoovers (paid):")
    print("   - Company financials and credit ratings")

def create_mock_enrichment():
    """Create a version that works without APIs"""
    print("\n" + "="*60)
    print("CREATING MOCK ENRICHMENT SCRIPT")
    print("="*60)
    
    code = '''#!/usr/bin/env python3
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
        
        print(f"\\nEnrichment complete!")
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
'''
    
    with open('local_enrichment_pipeline.py', 'w') as f:
        f.write(code)
    
    print("✓ Created local_enrichment_pipeline.py")
    print("This version works without any external APIs")
    print("Run with: python3 local_enrichment_pipeline.py")

if __name__ == "__main__":
    # Run all diagnostics
    
    # 1. Test SAM.gov API
    working_endpoint = test_sam_gov_api()
    
    # 2. Check NSF data
    nsf_file = check_nsf_data()
    
    # 3. Test with real UEI
    test_with_real_uei()
    
    # 4. Suggest alternatives
    suggest_alternatives()
    
    # 5. Create mock enrichment
    create_mock_enrichment()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    
    if working_endpoint:
        print("✓ SAM.gov API is accessible")
    else:
        print("❌ SAM.gov API issues detected")
        
    if nsf_file:
        print(f"✓ NSF data found: {nsf_file}")
    else:
        print("❌ NSF data not found")
        
    print("\nNext steps:")
    print("1. Fix any API issues identified above")
    print("2. Download missing data files")
    print("3. Run local_enrichment_pipeline.py for immediate results")
