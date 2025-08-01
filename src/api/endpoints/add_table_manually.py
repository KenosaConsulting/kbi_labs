with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Find where to insert the table
# Look for the end of the geographic distribution section
insert_marker = "<!-- Risk/Return Analysis -->"
if insert_marker not in content:
    # Try to find before the closing main tag
    insert_marker = "</main>"

if insert_marker in content:
    table_html = '''
    <!-- Top Companies Table -->
    <div class="bg-white rounded-lg shadow p-6 mb-8">
        <h3 class="text-lg font-semibold mb-4">Top Portfolio Companies</h3>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Company</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PE Score</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patents</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contract Value</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                    </tr>
                </thead>
                <tbody id="topCompaniesTable" class="bg-white divide-y divide-gray-200">
                    <!-- Companies will be loaded here by JavaScript -->
                </tbody>
            </table>
        </div>
    </div>
    
    '''
    
    # Insert before the marker
    insert_pos = content.find(insert_marker)
    content = content[:insert_pos] + table_html + content[insert_pos:]
    
    # Save
    with open('kbi_dashboard/portfolio.html', 'w') as f:
        f.write(content)
    
    print(f"✅ Added table before '{insert_marker}'")
    
    # Verify
    if 'id="topCompaniesTable"' in content:
        print("✅ Table element confirmed in HTML")
else:
    print("❌ Could not find insertion point")
    # Let's see what the structure looks like
    print("\nHTML structure preview:")
    lines = content.split('\n')
    for i, line in enumerate(lines[-50:]):
        if 'main' in line or 'body' in line or 'script' in line:
            print(f"Line {len(lines)-50+i}: {line.strip()}")

