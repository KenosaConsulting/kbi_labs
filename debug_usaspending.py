#!/usr/bin/env python3
"""Debug USASpending API calls"""
import requests
import json

# Test with a known UEI
uei = "M67WJSTEVKP3"  # Microsoft
url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

payload = {
    "filters": {
        "recipient_unique_id": uei,
        "award_type_codes": ["A", "B", "C", "D"]
    },
    "fields": ["Award ID", "Recipient Name", "Award Amount"],
    "page": 1,
    "limit": 5,
    "sort": "Award Amount",
    "order": "desc"
}

print(f"Testing UEI: {uei}")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(url, json=payload, timeout=30)
print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Total Results: {data.get('total', 0)}")
    print(f"Results Returned: {len(data.get('results', []))}")
    
    for i, result in enumerate(data.get('results', [])[:3]):
        print(f"\nResult {i+1}:")
        print(f"  Award ID: {result.get('Award ID')}")
        print(f"  Recipient: {result.get('Recipient Name')}")
        print(f"  Amount: ${result.get('Award Amount', 0):,.2f}")
else:
    print(f"Error: {response.text[:500]}")
