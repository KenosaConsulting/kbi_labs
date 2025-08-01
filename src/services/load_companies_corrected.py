
#!/usr/bin/env python3
"""
Load companies from enriched database with CORRECT column names
"""

import sqlite3
import json
import requests

def load_top_companies():
    """Load top companies with correct column mapping"""
    conn = sqlite3.connect('kbi_complete_enriched.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # First, let's see what data we have
    print("🔍 Checking database content...")
    
    # Get a sample company to see the data
    sample = cursor.execute("SELECT * FROM enriched_companies_full LIMIT 1").fetchone()
    if sample:
        print("\nSample company fields:")
        for key in sample.keys():
            value = sample[key]
            if value is not None and value != '':
                print(f"  {key}: {str(value)[:50]}...")
    
    # Get companies with investment scores
    query = """
    SELECT * FROM enriched_companies_full 
    WHERE pe_investment_score > 0
    ORDER BY pe_investment_score DESC, total_contract_value DESC
    LIMIT 100
    """
    
    try:
        companies = cursor.execute(query).fetchall()
        print(f"\n✅ Found {len(companies)} companies with PE scores")
    except sqlite3.OperationalError:
        # Try without PE score filter if column doesn't exist
        print("⚠️  No pe_investment_score column, getting all companies...")
        query = """
        SELECT * FROM enriched_companies_full 
        WHERE total_contract_value > 0 OR patent_count > 0
        ORDER BY total_contract_value DESC
        LIMIT 100
        """
        companies = cursor.execute(query).fetchall()
        print(f"✅ Found {len(companies)} companies with contracts or patents")
    
    # Process companies
    loaded_count = 0
    companies_data = []
    
    for company in companies[:20]:  # Load first 20
        company_dict = dict(company)
        
        # Map database fields to API expected fields
        mapped_company = {
            'uei': company_dict.get('uei', ''),
            'company_name': company_dict.get('organization_name', ''),  # Correct field name!
            'pe_investment_score': company_dict.get('pe_investment_score', 75),  # Default if missing
            'federal_contracts_value': company_dict.get('total_contract_value', 0),
            'patent_count': company_dict.get('patent_count', 0),
            'primary_naics': company_dict.get('primary_naics', ''),
            'state': company_dict.get('state', ''),
            'city': company_dict.get('city', ''),
            'cage_code': company_dict.get('cage_code', ''),
            'sam_status': company_dict.get('sam_registration_status', 'Active'),
            'business_health_grade': company_dict.get('business_health_grade', 'B'),
            'website': company_dict.get('website', ''),
            'phone_number': company_dict.get('phone_number', ''),
            'email': company_dict.get('email', ''),
            'capabilities_narrative': company_dict.get('capabilities_narrative', ''),
            'address_line_1': company_dict.get('address_line_1', ''),
            'zipcode': company_dict.get('zipcode', '')
        }
        
        # Only load companies with names
        if mapped_company['company_name']:
            print(f"\n📦 Loading: {mapped_company['company_name'][:50]}")
            print(f"   UEI: {mapped_company['uei']}")
            print(f"   Score: {mapped_company['pe_investment_score']}")
            print(f"   Contracts: ${mapped_company['federal_contracts_value']:,.0f}")
            print(f"   Patents: {mapped_company['patent_count']}")
            
            companies_data.append(mapped_company)
            
            # Try to post to API
            try:
                response = requests.post('http://localhost:8090/api/companies', 
                                       json=mapped_company,
                                       timeout=5)
                if response.status_code == 200:
                    print("   ✅ Loaded successfully")
                    loaded_count += 1
                elif response.status_code == 409:
                    print("   ⚠️  Already exists")
                else:
                    print(f"   ❌ Error: {response.status_code}")
                    if response.text:
                        print(f"   Response: {response.text[:100]}")
            except Exception as e:
                print(f"   ❌ Connection error: {e}")
    
    # Save to file for backup/manual loading
    with open('companies_to_load.json', 'w') as f:
        json.dump(companies_data, f, indent=2)
    
    print(f"\n📊 Summary:")
    print(f"   Companies found: {len(companies)}")
    print(f"   Companies processed: {len(companies_data)}")
    print(f"   Successfully loaded: {loaded_count}")
    print(f"   Data saved to: companies_to_load.json")
    
    conn.close()
    
    # Check what's now in the system
    try:
        response = requests.get('http://localhost:8090/api/companies')
        if response.status_code == 200:
            current_companies = response.json()
            print(f"\n✅ Total companies in system: {len(current_companies)}")
    except:
        pass

if __name__ == "__main__":
    load_top_companies()
