
#!/usr/bin/env python3
"""
Quick fix to ensure companies display correctly
"""

import json
import os
import shutil

def fix_companies_display():
    """Fix the companies.json file location and format"""
    
    print("🔧 Fixing companies display...")
    
    # Check all possible locations
    possible_files = [
        "companies.json",
        "kbi_dashboard/companies.json",
        "data/companies.json"
    ]
    
    # Find which file exists
    source_file = None
    for f in possible_files:
        if os.path.exists(f):
            print(f"✅ Found companies file at: {f}")
            with open(f, 'r') as file:
                data = json.load(file)
                print(f"   Contains {len(data)} companies")
                if len(data) > 4:  # This is our new file
                    source_file = f
                    break
    
    if not source_file:
        print("❌ No companies file found with new data!")
        return
    
    # Load the good data
    with open(source_file, 'r') as f:
        companies = json.load(f)
    
    print(f"\n📊 Loaded {len(companies)} companies")
    print("Sample companies:")
    for i, c in enumerate(companies[:3]):
        print(f"  {i+1}. {c.get('company_name', 'Unknown')}")
    
    # Find where the server expects the file
    if os.path.exists("combined_server_v2.py"):
        with open("combined_server_v2.py", 'r') as f:
            content = f.read()
            if "companies.json" in content:
                # Extract the path
                import re
                matches = re.findall(r'["\']([^"\']*companies\.json)["\']', content)
                if matches:
                    expected_path = matches[0]
                    print(f"\n📁 Server expects companies at: {expected_path}")
                    
                    # Create directory if needed
                    dir_path = os.path.dirname(expected_path)
                    if dir_path and not os.path.exists(dir_path):
                        os.makedirs(dir_path)
                        print(f"✅ Created directory: {dir_path}")
                    
                    # Copy the file to where server expects it
                    if expected_path != source_file:
                        shutil.copy2(source_file, expected_path)
                        print(f"✅ Copied companies to: {expected_path}")
    
    # Also check for a simple companies.json in root
    if not os.path.exists("companies.json") and source_file != "companies.json":
        shutil.copy2(source_file, "companies.json")
        print("✅ Created companies.json in root directory")
    
    print("\n✅ Fix complete! Now restart the server:")
    print("   pkill -f combined_server")
    print("   python3 combined_server_v2.py &")

if __name__ == "__main__":
    fix_companies_display()
