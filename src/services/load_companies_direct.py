
#!/usr/bin/env python3
"""
Check API endpoints and load companies directly
"""

import sqlite3
import json
import requests
import os

def check_api_endpoints():
    """Check what API endpoints are available"""
    print("🔍 Checking API endpoints...")
    
    base_url = "http://localhost:8090"
    
    # Try different endpoints
    endpoints = [
        ("/api/companies", "GET"),
        ("/api/companies", "POST"),
        ("/api/company", "POST"),
        ("/api/add_company", "POST"),
        ("/api/health", "GET"),
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
            else:
                response = requests.post(f"{base_url}{endpoint}", json={}, timeout=2)
            print(f"{method} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"{method} {endpoint}: Error - {str(e)[:30]}")

def load_directly_to_json():
    """Load companies directly to companies.json file"""
    print("\n📂 Loading companies directly to JSON file...")
    
    # Connect to database
    conn = sqlite3.connect('kbi_complete_enriched.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get top companies
    query = """
    SELECT * FROM enriched_companies_full 
    WHERE pe_investment_score > 0
    ORDER BY pe_investment_score DESC
    LIMIT 100
    """
    
    companies = cursor.execute(query).fetchall()
    print(f"✅ Found {len(companies)} companies with PE scores")
    
    # Check if companies.json exists
    companies_file = "kbi_dashboard/companies.json"
    existing_companies = []
    
    if os.path.exists(companies_file):
        try:
            with open(companies_file, 'r') as f:
                existing_companies = json.load(f)
            print(f"📄 Found existing {len(existing_companies)} companies in JSON file")
        except:
            existing_companies = []
    
    # Create company list
    new_companies = []
    
    for company in companies[:50]:
        company_dict = dict(company)
        
        # Map to expected format
        mapped_company = {
            'uei': company_dict.get('uei', ''),
            'company_name': company_dict.get('organization_name', ''),
            'pe_investment_score': float(company_dict.get('pe_investment_score', 0)),
            'federal_contracts_value': 0,  # No contract data in DB
            'patent_count': int(company_dict.get('patent_count', 0)),
            'primary_naics': str(company_dict.get('primary_naics', '')).split('.')[0],
            'state': company_dict.get('state', ''),
            'city': company_dict.get('city', ''),
            'cage_code': company_dict.get('cage_code', ''),
            'sam_status': 'Active',
            'business_health_grade': company_dict.get('business_health_grade', 'B'),
            'website': company_dict.get('website', ''),
            'phone_number': str(company_dict.get('phone_number', '')).split('.')[0],
            'email': company_dict.get('email', ''),
            'capabilities_narrative': company_dict.get('capabilities_narrative', ''),
            'address_line_1': company_dict.get('address_line_1', ''),
            'zipcode': str(company_dict.get('zipcode', '')).split('.')[0],
            'legal_structure': company_dict.get('legal_structure', ''),
            'active_sba_certifications': company_dict.get('active_sba_certifications', ''),
            'nsf_awards_count': int(company_dict.get('nsf_awards_count', 0)),
            'nsf_total_funding': float(company_dict.get('nsf_total_funding', 0))
        }
        
        # Only add if has name and UEI
        if mapped_company['company_name'] and mapped_company['uei']:
            new_companies.append(mapped_company)
    
    # Merge with existing (remove duplicates)
    existing_ueis = {c.get('uei') for c in existing_companies if c.get('uei')}
    
    for company in new_companies:
        if company['uei'] not in existing_ueis:
            existing_companies.append(company)
    
    # Sort by score
    existing_companies.sort(key=lambda x: x.get('pe_investment_score', 0), reverse=True)
    
    # Save back to file
    with open(companies_file, 'w') as f:
        json.dump(existing_companies, f, indent=2)
    
    print(f"\n✅ Successfully saved {len(existing_companies)} companies to {companies_file}")
    
    # Show sample
    print("\n📋 Top 5 companies loaded:")
    for i, company in enumerate(existing_companies[:5]):
        print(f"{i+1}. {company['company_name']}")
        print(f"   Score: {company['pe_investment_score']}, Patents: {company['patent_count']}")
        print(f"   Location: {company['city']}, {company['state']}")
    
    conn.close()
    
    print("\n🎯 Next steps:")
    print("1. Restart the server to reload companies")
    print("2. Or reload the page to see new companies")
    
    return len(existing_companies)

def check_server_file():
    """Check what server file is running"""
    print("\n📄 Checking server configuration...")
    
    server_files = [
        "combined_server.py",
        "combined_server_v2.py", 
        "kbi_dashboard/app.py"
    ]
    
    for file in server_files:
        if os.path.exists(file):
            print(f"✅ Found: {file}")
            # Check if it has POST endpoint
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if "POST" in content and "/api/companies" in content:
                        print(f"   └─ Has POST /api/companies endpoint")
                    else:
                        print(f"   └─ No POST endpoint for companies")
            except:
                pass

def main():
    print("🚀 KBI Labs Company Loader")
    print("=" * 50)
    
    # Check API endpoints
    check_api_endpoints()
    
    # Check server files
    check_server_file()
    
    # Load directly to JSON
    total = load_directly_to_json()
    
    print(f"\n✅ Complete! {total} companies ready in the system")
    print("\n💡 To see the companies:")
    print("   1. Refresh your browser at http://3.143.232.123:8090")
    print("   2. Or restart the server: pkill -f combined_server && python3 combined_server_v2.py &")

if __name__ == "__main__":
    main()
