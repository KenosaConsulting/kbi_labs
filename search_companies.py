#!/usr/bin/env python3
"""Search for companies in the DSBS dataset"""

import json
import sys
from pathlib import Path

def search_companies(query=None, state=None, limit=10):
    """Search companies by name or state"""
    
    # Load the index
    with open('data/company_index.json', 'r') as f:
        index = json.load(f)
    
    results = []
    
    for uei, data in index.items():
        # Filter by state (handle NaN/float values)
        if state:
            company_state = data.get('state', '')
            # Convert to string and handle float/NaN cases
            if isinstance(company_state, float):
                continue
            if str(company_state).lower() != state.lower():
                continue
        
        # Filter by name (case-insensitive partial match)
        if query:
            company_name = data.get('name', '')
            if isinstance(company_name, float) or query.lower() not in str(company_name).lower():
                continue
        
        results.append({
            'uei': uei,
            'name': data['name'],
            'city': data.get('city', 'Unknown'),
            'state': data.get('state', 'Unknown')
        })
        
        if len(results) >= limit:
            break
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Search DSBS companies')
    parser.add_argument('--name', help='Search by company name (partial match)')
    parser.add_argument('--state', help='Filter by state')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results')
    
    args = parser.parse_args()
    
    results = search_companies(query=args.name, state=args.state, limit=args.limit)
    
    print(f"\nFound {len(results)} companies:")
    for i, company in enumerate(results):
        print(f"{i+1}. {company['name']}")
        print(f"   Location: {company['city']}, {company['state']}")
        print(f"   UEI: {company['uei']}")
        print()
