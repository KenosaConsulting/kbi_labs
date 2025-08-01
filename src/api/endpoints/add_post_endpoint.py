
#!/usr/bin/env python3
"""
Add POST endpoint to combined_server_v2.py
"""

import os

def add_post_endpoint():
    """Add POST endpoint for adding companies"""
    
    server_file = "combined_server_v2.py"
    
    if not os.path.exists(server_file):
        print(f"❌ {server_file} not found!")
        return
    
    # Read current content
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Check if POST endpoint already exists
    if "methods=['GET', 'POST']" in content and "/api/companies" in content:
        print("✅ POST endpoint already exists!")
        return
    
    # Find where to insert the new code
    api_companies_line = "@app.route('/api/companies')"
    
    if api_companies_line in content:
        # Replace GET-only with GET and POST
        new_content = content.replace(
            "@app.route('/api/companies')",
            "@app.route('/api/companies', methods=['GET', 'POST'])"
        )
        
        # Find the function and modify it
        lines = new_content.split('\n')
        new_lines = []
        in_companies_func = False
        indent_found = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            if "def api_companies():" in line:
                in_companies_func = True
            elif in_companies_func and not indent_found and line.strip() and not line.startswith('def'):
                # Found first line of function body
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                
                # Insert POST handling code
                new_lines.append(f"{indent_str}if request.method == 'POST':")
                new_lines.append(f"{indent_str}    # Add new company")
                new_lines.append(f"{indent_str}    new_company = request.json")
                new_lines.append(f"{indent_str}    companies = load_companies()")
                new_lines.append(f"{indent_str}    ")
                new_lines.append(f"{indent_str}    # Check if company already exists")
                new_lines.append(f"{indent_str}    if any(c.get('uei') == new_company.get('uei') for c in companies):")
                new_lines.append(f"{indent_str}        return jsonify({{'error': 'Company already exists'}}), 409")
                new_lines.append(f"{indent_str}    ")
                new_lines.append(f"{indent_str}    # Add company")
                new_lines.append(f"{indent_str}    companies.append(new_company)")
                new_lines.append(f"{indent_str}    ")
                new_lines.append(f"{indent_str}    # Save back to file")
                new_lines.append(f"{indent_str}    with open(COMPANIES_FILE, 'w') as f:")
                new_lines.append(f"{indent_str}        json.dump(companies, f, indent=2)")
                new_lines.append(f"{indent_str}    ")
                new_lines.append(f"{indent_str}    return jsonify({{'message': 'Company added successfully'}}), 200")
                new_lines.append(f"{indent_str}")
                new_lines.append(f"{indent_str}# GET request - return all companies")
                
                indent_found = True
        
        # Save modified file
        with open("combined_server_v2_with_post.py", 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Created combined_server_v2_with_post.py with POST endpoint")
        print("\n📝 To use it:")
        print("   1. Stop current server: pkill -f combined_server")
        print("   2. Backup current: cp combined_server_v2.py combined_server_v2_backup.py")
        print("   3. Replace: mv combined_server_v2_with_post.py combined_server_v2.py")
        print("   4. Start new: python3 combined_server_v2.py &")
    else:
        print("❌ Could not find /api/companies route in server file")

if __name__ == "__main__":
    add_post_endpoint()
