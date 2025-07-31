#!/usr/bin/env python3
"""
Diagnose and fix patent data loading issue
"""
import os
import pandas as pd
import glob

def check_patent_data():
    """Check what patent data files we have and their structure"""
    print("="*60)
    print("PATENT DATA DIAGNOSTIC")
    print("="*60)
    
    patent_path = 'patent_data/'
    
    if not os.path.exists(patent_path):
        print(f"❌ Patent data directory not found: {patent_path}")
        print("\nTo fix:")
        print("1. Create the directory: mkdir -p patent_data")
        print("2. Download patent data from USPTO")
        return
    
    print(f"✓ Found patent data directory: {patent_path}")
    
    # List all files
    all_files = os.listdir(patent_path)
    tsv_files = [f for f in all_files if f.endswith('.tsv')]
    
    print(f"\nTotal files in directory: {len(all_files)}")
    print(f"TSV files found: {len(tsv_files)}")
    
    if not tsv_files:
        print("❌ No TSV files found!")
        return
    
    print("\nAnalyzing patent files...")
    print("-" * 60)
    
    # Check each TSV file
    total_orgs = 0
    org_column_mapping = {}
    
    for i, file in enumerate(tsv_files[:10]):  # Check first 10 files
        filepath = os.path.join(patent_path, file)
        print(f"\n{i+1}. {file}")
        
        try:
            # Read first few rows to check structure
            df_sample = pd.read_csv(filepath, sep='\t', nrows=5)
            print(f"   Columns: {list(df_sample.columns)}")
            
            # Look for organization-related columns
            org_columns = []
            for col in df_sample.columns:
                col_lower = col.lower()
                if any(term in col_lower for term in ['org', 'assignee', 'company', 'firm', 'corp']):
                    org_columns.append(col)
            
            if org_columns:
                print(f"   Found org columns: {org_columns}")
                org_column_mapping[file] = org_columns
                
                # Count unique organizations in this file
                df_full = pd.read_csv(filepath, sep='\t', usecols=org_columns[:1], nrows=100000)
                org_col = org_columns[0]
                unique_orgs = df_full[org_col].dropna().nunique()
                total_orgs += unique_orgs
                print(f"   Unique organizations: {unique_orgs:,}")
                
                # Show sample organizations
                sample_orgs = df_full[org_col].dropna().unique()[:5]
                print(f"   Sample orgs: {list(sample_orgs)}")
            else:
                print(f"   ⚠️  No organization columns found")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    
    print("\n" + "="*60)
    print(f"SUMMARY: Found {total_orgs:,} organizations across sampled files")
    
    # Create a fixed patent loader
    if org_column_mapping:
        print("\nCreating fixed patent loader...")
        create_fixed_patent_loader(org_column_mapping)

def create_fixed_patent_loader(org_mapping):
    """Create a fixed version of the patent data loader"""
    
    code = '''def _load_patent_data(self):
    """Load patent data from local files - FIXED VERSION"""
    self.patent_lookup = {}
    patent_path = 'patent_data/'
    
    if os.path.exists(patent_path):
        try:
            logger.info("Loading patent data...")
            patent_files = glob.glob(os.path.join(patent_path, '*.tsv'))
            
            # Mapping of files to their organization columns
            org_columns = {
'''
    
    # Add the mapping
    for file, cols in org_mapping.items():
        code += f"                '{file}': {cols},\n"
    
    code += '''            }
            
            organizations_loaded = 0
            
            for file in patent_files[:10]:  # Process more files
                filename = os.path.basename(file)
                
                if filename in org_columns:
                    try:
                        cols = org_columns[filename]
                        org_col = cols[0]  # Use first org column
                        
                        # Read the file
                        df = pd.read_csv(file, sep='\\t', usecols=[org_col], nrows=500000)
                        
                        # Process organizations
                        for org in df[org_col].dropna().unique():
                            org_clean = str(org).lower().strip()
                            if org_clean and len(org_clean) > 3:
                                if org_clean not in self.patent_lookup:
                                    self.patent_lookup[org_clean] = 0
                                self.patent_lookup[org_clean] += 1
                                organizations_loaded += 1
                                
                    except Exception as e:
                        logger.debug(f"Error loading {filename}: {e}")
                        
            logger.info(f"Loaded patent data for {len(self.patent_lookup):,} unique organizations")
            
        except Exception as e:
            logger.error(f"Error loading patent data: {e}")
'''
    
    with open('patent_loader_fix.py', 'w') as f:
        f.write(code)
    
    print("✓ Created patent_loader_fix.py with the correct column mappings")
    print("\nTo apply the fix:")
    print("1. Copy this function into fixed_pipeline_final.py")
    print("2. Replace the existing _load_patent_data method")

def test_patent_search():
    """Test searching for a known company in patent data"""
    print("\n" + "="*60)
    print("TESTING PATENT SEARCH")
    print("="*60)
    
    test_companies = [
        "IBM",
        "Microsoft Corporation", 
        "Apple Inc",
        "Google LLC",
        "Amazon Technologies"
    ]
    
    # Load patent data similar to pipeline
    patent_lookup = {}
    patent_path = 'patent_data/'
    
    if os.path.exists(patent_path):
        files = glob.glob(os.path.join(patent_path, '*.tsv'))[:3]
        
        for file in files:
            try:
                # Try to find assignee columns
                df = pd.read_csv(file, sep='\t', nrows=10000)
                
                for col in df.columns:
                    if 'assignee' in col.lower() and 'org' in col.lower():
                        orgs = df[col].dropna().unique()
                        for org in orgs:
                            org_lower = str(org).lower()
                            if org_lower not in patent_lookup:
                                patent_lookup[org_lower] = 0
                            patent_lookup[org_lower] += 1
                        break
                        
            except Exception as e:
                pass
    
    print(f"Loaded {len(patent_lookup)} organizations")
    
    print("\nSearching for test companies:")
    for company in test_companies:
        company_lower = company.lower()
        found = False
        
        for patent_org in patent_lookup:
            if company_lower in patent_org or patent_org in company_lower:
                print(f"✓ Found '{company}' as '{patent_org}' with {patent_lookup[patent_org]} patents")
                found = True
                break
                
        if not found:
            print(f"❌ Not found: {company}")

if __name__ == "__main__":
    # Run diagnostics
    check_patent_data()
    test_patent_search()
