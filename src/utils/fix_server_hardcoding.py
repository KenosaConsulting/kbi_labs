
#!/usr/bin/env python3
"""
Fix hardcoded test companies in server
"""

import re
import shutil

def fix_server():
    print("🔧 Fixing hardcoded companies in server...")
    
    # Backup original
    shutil.copy2('combined_server_v2.py', 'combined_server_v2_backup.py')
    print("✅ Created backup: combined_server_v2_backup.py")
    
    # Read server file
    with open('combined_server_v2.py', 'r') as f:
        content = f.read()
    
    # Pattern 1: Replace hardcoded return with file loading
    if 'return [' in content and '"uei": "TEST' in content:
        print("🔍 Found hardcoded TEST companies...")
        
        # Replace the hardcoded return statement
        # This pattern matches return [...] with TEST companies
        pattern = r'return \[\s*\{[^}]*"uei":\s*"TEST[^}]+\}[^\]]*\]'
        
        replacement = '''try:
        with open(COMPANIES_FILE, 'r') as f:
            companies = json.load(f)
        return companies
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []'''
        
        content = re.sub(pattern, replacement, content)
        print("✅ Replaced hardcoded return with file loading")
    
    # Pattern 2: Fix load_companies if it's not loading from file
    load_func_match = re.search(r'(def load_companies\(\):.*?)(?=\ndef|\Z)', content, re.DOTALL)
    if load_func_match:
        func_content = load_func_match.group(0)
        if 'companies.json' not in func_content and 'COMPANIES_FILE' not in func_content:
            print("🔍 load_companies() not loading from file...")
            
            # Replace the entire function
            new_func = '''def load_companies():
    """Load companies from JSON file"""
    try:
        with open(COMPANIES_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []'''
            
            content = content.replace(func_content, new_func)
            print("✅ Fixed load_companies function")
    
    # Make sure COMPANIES_FILE is defined
    if 'COMPANIES_FILE' not in content:
        # Add it after imports
        import_end = content.rfind('import')
        import_end = content.find('\n', import_end) + 1
        content = content[:import_end] + "\nCOMPANIES_FILE = 'companies.json'\n" + content[import_end:]
        print("✅ Added COMPANIES_FILE constant")
    
    # Write fixed file
    with open('combined_server_v2.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Server fixed! The server will now load from companies.json")
    print("\n🚀 Next steps:")
    print("   1. pkill -f combined_server")
    print("   2. python3 combined_server_v2.py &")
    print("   3. curl http://localhost:8090/api/companies")

if __name__ == "__main__":
    fix_server()
