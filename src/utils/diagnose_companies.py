
#!/usr/bin/env python3
"""
Diagnose why companies aren't loading
"""

import json
import os
import requests

def diagnose_issue():
    print("🔍 Diagnosing KBI Labs Companies Loading Issue")
    print("=" * 50)
    
    # 1. Check JSON files
    print("\n1️⃣ Checking JSON files:")
    json_files = [
        "companies.json",
        "kbi_dashboard/companies.json",
        "companies_loaded.json"
    ]
    
    valid_file = None
    for file in json_files:
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                print(f"✅ {file}: Valid JSON with {len(data)} companies")
                if len(data) > 4 and valid_file is None:
                    valid_file = file
                    # Show sample
                    if data and isinstance(data, list) and isinstance(data[0], dict):
                        print(f"   Sample: {data[0].get('company_name', 'No name field')}")
            except Exception as e:
                print(f"❌ {file}: Invalid JSON - {str(e)[:50]}")
        else:
            print(f"⚠️  {file}: Not found")
    
    # 2. Check server code
    print("\n2️⃣ Checking server code:")
    if os.path.exists("combined_server_v2.py"):
        with open("combined_server_v2.py", 'r') as f:
            content = f.read()
        
        # Look for hardcoded data
        if 'TEST001' in content or '"uei": "TEST' in content:
            print("⚠️  Found hardcoded TEST companies in server")
            
            # Find the specific location
            import re
            test_pattern = re.search(r'(return \[[\s\S]*?"uei":\s*"TEST[\s\S]*?\])', content)
            if test_pattern:
                print("   Location: Inside a return statement")
                print("   This is overriding any JSON file!")
        
        # Check load_companies function
        if 'def load_companies' in content:
            load_func_start = content.find('def load_companies')
            load_func_end = content.find('\ndef', load_func_start + 1)
            if load_func_end == -1:
                load_func_end = len(content)
            load_func = content[load_func_start:load_func_end]
            
            if 'companies.json' in load_func:
                print("✅ load_companies() references companies.json")
            else:
                print("⚠️  load_companies() doesn't seem to load from JSON")
    
    # 3. Test API
    print("\n3️⃣ Testing API:")
    try:
        response = requests.get('http://localhost:8090/api/companies')
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ API returned {len(companies)} companies")
            if companies:
                first = companies[0]
                print(f"   First company UEI: {first.get('uei', 'No UEI')}")
                print(f"   First company name: {first.get('company_name', 'No name')}")
                if first.get('uei', '').startswith('TEST'):
                    print("   ⚠️  These are hardcoded test companies!")
        else:
            print(f"❌ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ API error: {e}")
    
    # 4. Solution
    print("\n4️⃣ SOLUTION:")
    if valid_file:
        print(f"✅ Use valid data from: {valid_file}")
        print("\nRun these commands to fix:")
        print(f"   cp {valid_file} companies.json")
        print("   python3 fix_server_hardcoding.py")
        print("   pkill -f combined_server")
        print("   python3 combined_server_v2.py &")
    else:
        print("❌ No valid companies data found!")
        print("   Re-run: python3 load_companies_direct.py")

if __name__ == "__main__":
    diagnose_issue()
