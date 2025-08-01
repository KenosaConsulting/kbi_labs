#!/usr/bin/env python3
"""
Load companies from enriched database with correct column names
"""

import sqlite3
import json
import requests

def check_database_schema():
    """First check what columns we actually have"""
    conn = sqlite3.connect('kbi_complete_enriched.db')
    cursor = conn.cursor()
    
    # Get column info
    cursor.execute("PRAGMA table_info(enriched_companies_full)")
    columns = cursor.fetchall()
    
    print("Available columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    return [col[1] for col in columns]

def load_top_companies():
    """Load top companies with available columns"""
    # First check schema
    available_columns = check_database_schema()
    
    # Connect to source database
    conn = sqlite3.connect('kbi_complete_enriched.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Build query based on available columns
    score_column = 'pe_investment_score' if 'pe_investment_score' in available_columns else 'investment_score'
    contract_column = 'total_contract_value' if 'total_contract_value' in available_columns else 'federal_contracts_value'
    
    # Get top companies
    query = f"""
    SELECT * FROM enriched_companies_full 
    WHERE {score_column} > 0
    ORDER BY {score_column} DESC
    LIMIT 100
    """
    
    companies = cursor.execute(query).fetchall()
    print(f"\nFound {len(companies)} high-scoring companies")
    
    # Save to JSON for manual loading if API fails
    companies_list = []
    for company in companies[:10]:  # First 10 for testing
        company_dict = dict(company)
        companies_list.append(company_dict)
        
        # Map to expected field names
        mapped_company = {
            'uei': company_dict.get('uei', company_dict.get('unique_entity_id', '')),
            'company_name': company_dict.get('company_name', company_dict.get('entity_name', '')),
            'pe_investment_score': company_dict.get(score_column, 0),
            'federal_contracts_value': company_dict.get(contract_column, 0),
            'patent_count': company_dict.get('patent_count', 0),
            'primary_naics': company_dict.get('primary_naics', company_dict.get('naics_code', '')),
            'state': company_dict.get('state', ''),
            'city': company_dict.get('city', ''),
            'cage_code': company_dict.get('cage_code', ''),
            'sam_status': company_dict.get('registration_status', 'Active'),
            'business_health_grade': company_dict.get('business_health_grade', 'B')
        }
        
        print(f"\nCompany: {mapped_company['company_name']}")
        print(f"  Score: {mapped_company['pe_investment_score']}")
        print(f"  Contracts: ${mapped_company['federal_contracts_value']:,.0f}")
        
        # Try to post to API
        try:
            response = requests.post('http://localhost:8090/api/companies', 
                                    json=mapped_company,
                                    timeout=5)
            if response.status_code == 200:
                print(f"  ✓ Loaded successfully")
            else:
                print(f"  ✗ API error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Connection error: {e}")
    
    # Save companies to file
    with open('top_companies.json', 'w') as f:
        json.dump(companies_list, f, indent=2, default=str)
    
    print(f"\n💾 Saved {len(companies_list)} companies to top_companies.json")
    
    conn.close()

if __name__ == "__main__":
    load_top_companies()
