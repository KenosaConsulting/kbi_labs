import re

with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Check if table already exists
if 'topCompaniesTable' not in content:
    # Find where to insert (before Risk/Return Analysis)
    insert_point = content.find('Risk/Return Analysis')
    if insert_point == -1:
        insert_point = content.find('</main>')
    
    if insert_point != -1:
        # Create the table HTML
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
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"></th>
                        </tr>
                    </thead>
                    <tbody id="topCompaniesTable" class="bg-white divide-y divide-gray-200">
                        <!-- Companies will be loaded here by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
        
        '''
        
        # Insert the table
        content = content[:insert_point] + table_html + content[insert_point:]
        
        # Save the updated file
        with open('kbi_dashboard/portfolio.html', 'w') as f:
            f.write(content)
        
        print("✅ Added portfolio table to HTML")
    else:
        print("❌ Could not find insertion point")
else:
    print("✅ Table already exists in HTML")

