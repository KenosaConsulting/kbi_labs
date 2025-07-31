
#!/usr/bin/env python3
"""
Load companies from enriched database with ACTUAL column names
"""

import sqlite3
import json
import requests

def load_top_companies():
    """Load top companies with correct column mapping"""
    conn = sqlite3.connect('kbi_complete_enriched.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🔍 Loading companies from enriched database...")
    
    # Get companies with investment scores - we know pe_investment_score exists!
    query = """
    SELECT * FROM enriched_companies_full 
    WHERE pe_investment_score > 0
    ORDER BY pe_investment_score DESC
    LIMIT 100
    """
    
    companies = cursor.execute(query).fetchall()
    print(f"✅ Found {len(companies)} companies with PE scores")
    
    # Process companies
    loaded_count = 0
    companies_data = []
    
    for i, company in enumerate(companies[:50]):  # Load first 50
        company_dict = dict(company)
        
        # Calculate contract value from scoring factors if available
        contract_value = 0
        try:
            if company_dict.get('scoring_factors'):
                import ast
                factors = ast.literal_eval(company_dict['scoring_factors'])
                # Extract any contract/revenue data from scoring factors
                contract_value = int(factors.get('contract_value', 0))
        except:
            contract_value = 0
        
        # Map database fields to API expected fields
        mapped_company = {
            'uei': company_dict.get('uei', ''),
            'company_name': company_dict.get('organization_name', ''),
            'pe_investment_score': float(company_dict.get('pe_investment_score', 0)),
            'federal_contracts_value': contract_value,  # Will be 0 for now
            'patent_count': int(company_dict.get('patent_count', 0)),
            'primary_naics': str(company_dict.get('primary_naics', '')).split('.')[0],  # Remove decimal
            'state': company_dict.get('state', ''),
            'city': company_dict.get('city', ''),
            'cage_code': company_dict.get('cage_code', ''),
            'sam_status': 'Active',  # Default since not in data
            'business_health_grade': company_dict.get('business_health_grade', 'B'),
            'website': company_dict.get('website', ''),
            'phone_number': str(company_dict.get('phone_number', '')).split('.')[0],  # Remove decimal
            'email': company_dict.get('email', ''),
            'capabilities_narrative': company_dict.get('capabilities_narrative', ''),
            'address_line_1': company_dict.get('address_line_1', ''),
            'zipcode': str(company_dict.get('zipcode', '')).split('.')[0],  # Remove decimal
            'legal_structure': company_dict.get('legal_structure', ''),
            'active_sba_certifications': company_dict.get('active_sba_certifications', ''),
            'nsf_awards_count': int(company_dict.get('nsf_awards_count', 0)),
            'nsf_total_funding': float(company_dict.get('nsf_total_funding', 0))
        }
        
        # Only load companies with names
        if mapped_company['company_name'] and mapped_company['uei']:
            if i < 5:  # Show details for first 5
                print(f"\n📦 Company #{i+1}: {mapped_company['company_name'][:50]}")
                print(f"   UEI: {mapped_company['uei']}")
                print(f"   Score: {mapped_company['pe_investment_score']:.1f}")
                print(f"   Patents: {mapped_company['patent_count']}")
                print(f"   Grade: {mapped_company['business_health_grade']}")
                print(f"   Location: {mapped_company['city']}, {mapped_company['state']}")
            
            companies_data.append(mapped_company)
            
            # Try to post to API
            try:
                response = requests.post('http://localhost:8090/api/companies', 
                                       json=mapped_company,
                                       timeout=5)
                if response.status_code == 200:
                    if i < 5:
                        print("   ✅ Loaded successfully")
                    loaded_count += 1
                elif response.status_code == 409:
                    if i < 5:
                        print("   ⚠️  Already exists")
                else:
                    if i < 5:
                        print(f"   ❌ Error: {response.status_code}")
            except Exception as e:
                if i < 5:
                    print(f"   ❌ Connection error: {e}")
    
    # Show progress dots for remaining companies
    if len(companies_data) > 5:
        print(f"\n... loading {len(companies_data) - 5} more companies ...")
    
    # Save to file for backup
    with open('companies_loaded.json', 'w') as f:
        json.dump(companies_data[:10], f, indent=2)  # Save sample
    
    print(f"\n📊 Loading Summary:")
    print(f"   Total found in DB: {len(companies)}")
    print(f"   Processed: {len(companies_data)}")
    print(f"   Successfully loaded: {loaded_count}")
    print(f"   Sample saved to: companies_loaded.json")
    
    conn.close()
    
    # Check final count
    try:
        response = requests.get('http://localhost:8090/api/companies')
        if response.status_code == 200:
            current_companies = response.json()
            print(f"\n✅ Total companies now in system: {len(current_companies)}")
            
            # Show a few examples
            if current_companies:
                print("\n📋 Sample companies in system:")
                for c in current_companies[:3]:
                    print(f"   - {c.get('company_name', 'Unknown')} (Score: {c.get('pe_investment_score', 0)})")
    except:
        pass

if __name__ == "__main__":
    load_top_companies()
