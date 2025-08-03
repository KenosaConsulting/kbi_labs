#!/usr/bin/env python3
"""
Test fixed USASpending.gov API integration
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_award_search():
    """Test the corrected award search"""
    print("🔍 Testing Fixed Award Search")
    
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award"
    
    # Corrected payload based on API requirements
    payload = {
        "filters": {
            "keywords": ["artificial intelligence"],
            "award_type_codes": ["A", "B", "C", "D"],  # Required field
            "time_period": [
                {
                    "start_date": "2023-10-01",
                    "end_date": "2024-09-30"
                }
            ]
        },
        "fields": [  # Required field
            "Award ID",
            "Recipient Name", 
            "Award Amount",
            "Awarding Agency",
            "Award Description"
        ],
        "page": 1,
        "limit": 5,
        "sort": "Award Amount",
        "order": "desc"
    }
    
    try:
        response = requests.post(
            url, 
            json=payload, 
            timeout=30, 
            verify=False,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Found {len(data.get('results', []))} awards")
            
            if data.get('results'):
                for i, award in enumerate(data['results'][:3], 1):
                    print(f"{i}. {award.get('Award Description', 'N/A')[:70]}...")
                    print(f"   Amount: ${award.get('Award Amount', 0):,.0f}")
                    print(f"   Agency: {award.get('Awarding Agency', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_agency_spending():
    """Test the corrected agency spending"""
    print("\n💰 Testing Fixed Agency Spending")
    
    url = "https://api.usaspending.gov/api/v2/financial_balances/agencies"
    params = {
        'fiscal_year': 2024,
        'funding_agency_id': 'all'  # This should fix the 400 error
    }
    
    try:
        response = requests.get(url, params=params, timeout=15, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            agencies = data.get('results', [])
            print(f"✅ SUCCESS! Found {len(agencies)} agencies")
            
            if agencies:
                for i, agency in enumerate(agencies[:3], 1):
                    budget = agency.get('total_budgetary_resources', 0)
                    budget_str = f"${budget/1000000000:.1f}B" if budget > 1000000000 else f"${budget/1000000:.1f}M"
                    print(f"{i}. {agency.get('agency_name', 'N/A')}: {budget_str}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🚀 TESTING FIXED USASPENDING API")
    print("=" * 50)
    
    test_award_search()
    test_agency_spending()
    
    print("\n✅ USASpending API fix test complete!")