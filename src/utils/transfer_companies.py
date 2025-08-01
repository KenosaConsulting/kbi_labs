import sqlite3
import json
import requests

# Connect to source database
source_conn = sqlite3.connect('kbi_complete_enriched.db')
source_conn.row_factory = sqlite3.Row
source_cursor = source_conn.cursor()

# Get top 100 companies by PE score
companies = source_cursor.execute("""
    SELECT * FROM enriched_companies_full 
    WHERE pe_investment_score > 0
    ORDER BY pe_investment_score DESC, federal_contracts_value DESC
    LIMIT 100
""").fetchall()

print(f"Found {len(companies)} high-scoring companies")

# Convert to dict format
for company in companies:
    company_dict = dict(company)
    
    # Post to API
    try:
        response = requests.post('http://localhost:8090/api/companies', 
                                json=company_dict,
                                timeout=5)
        if response.status_code == 200:
            print(f"✓ Loaded: {company_dict.get('company_name', 'Unknown')}")
        else:
            print(f"✗ Failed: {company_dict.get('company_name', 'Unknown')}")
    except Exception as e:
        print(f"Error loading company: {e}")
        
source_conn.close()
print("\n✅ Transfer complete!")
