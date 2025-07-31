#!/usr/bin/env python3
"""Test USASpending integration with various UEIs"""
import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_uei(uei: str, description: str = ""):
    """Test a single UEI"""
    print(f"\n{'='*60}")
    print(f"Testing UEI: {uei}")
    if description:
        print(f"Description: {description}")
    print(f"{'='*60}")
    
    # Test search endpoint
    start = time.time()
    response = requests.get(f"{API_BASE}/api/v3/usaspending/search/{uei}")
    elapsed = time.time() - start
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Result: {data['status']}")
        
        if data['status'] == 'success' and 'data' in data:
            summary = data['data'].get('summary', data['data'])
            if 'total_awards' in summary:
                print(f"Total Awards: {summary['total_awards']}")
                print(f"Total Amount: ${summary.get('total_amount', 0):,.2f}")
                
                # Show top agencies
                agencies = summary.get('agencies', {})
                if agencies:
                    print("\nTop Agencies:")
                    for agency, info in list(agencies.items())[:3]:
                        print(f"  - {agency}: {info['count']} awards, ${info['total_amount']:,.2f}")
    else:
        print(f"Error: {response.text}")

def main():
    print("🔍 USASpending Integration Test")
    
    # Test cases - replace with actual UEIs from your data
    test_cases = [
        ("ABCDEF123456", "Test UEI - Valid Format"),
        ("123456789012", "Numeric UEI Test"),
        # Add real UEIs here from your enriched_companies table
    ]
    
    for uei, desc in test_cases:
        test_uei(uei, desc)
        time.sleep(1)  # Be nice to the API
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
