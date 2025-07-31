#!/usr/bin/env python3
"""Find companies with federal contracts from your database"""
import requests
import json
import time
import sys

def test_uei_batch(ueis):
    """Test a batch of UEIs and return those with contracts"""
    contractors = []
    
    for uei, name in ueis:
        if not uei or len(uei) < 9:  # Skip invalid UEIs
            continue
            
        try:
            response = requests.get(f"http://localhost:8001/api/v3/usaspending/search/{uei}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data"):
                    summary = data["data"]
                    if isinstance(summary, dict) and summary.get("total_awards", 0) > 0:
                        contractors.append({
                            "uei": uei,
                            "name": name,
                            "total_awards": summary.get("total_awards", 0),
                            "total_amount": summary.get("total_amount", 0)
                        })
                        print(f"✅ Found contractor: {name} - {summary.get('total_awards', 0)} awards, ${summary.get('total_amount', 0):,.2f}")
                    else:
                        print(f"❌ No contracts: {name}")
            time.sleep(0.5)  # Be nice to the API
        except Exception as e:
            print(f"Error testing {uei}: {str(e)}")
    
    return contractors

# Test with some known contractor UEIs
print("Testing with known federal contractor UEIs...")
known_contractors = [
    ("SAM0000000001", "Lockheed Martin"),
    ("M67WJSTEVKP3", "Microsoft Corporation"),
    ("NNM4FKDEDJU1", "Amazon Web Services"),
    ("UUQTCGFFARJ7", "General Dynamics"),
    ("HWEBEH4ZXKH5", "Boeing Company"),
]

# Test these
found = test_uei_batch(known_contractors)

print(f"\nFound {len(found)} contractors with federal awards")
for contractor in found:
    print(f"  {contractor['name']}: {contractor['total_awards']} awards totaling ${contractor['total_amount']:,.2f}")
