#!/usr/bin/env python3
"""Test data loading"""
import json

try:
    with open('companies.json', 'r') as f:
        data = json.load(f)
    print(f"✅ Successfully loaded {len(data)} companies")
    
    # Show first company
    if data:
        first_company = data[0]
        print(f"First company: {first_company['company_name']}")
        print(f"NAICS: {first_company.get('primary_naics')}")
        print(f"State: {first_company.get('state')}")
        
    # Calculate some metrics
    total_companies = len(data)
    companies_with_contracts = [c for c in data if c.get('federal_contracts_value', 0) > 0]
    
    print(f"Total companies: {total_companies}")
    print(f"Companies with federal contracts: {len(companies_with_contracts)}")
    
except Exception as e:
    print(f"❌ Error loading data: {e}")