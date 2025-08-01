with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Find where to insert - right after the title
title_pos = content.find('<h1 class="text-3xl font-bold text-gray-900">KBI Labs - Portfolio Analysis</h1>')
if title_pos > 0:
    # Find the end of the header section
    header_end = content.find('</header>', title_pos)
    if header_end > 0:
        insert_pos = content.find('<main', header_end)
        if insert_pos > 0:
            # Find the first good spot after main
            insert_pos = content.find('>', insert_pos) + 1
            
            # Check if table already exists there
            if 'Top Portfolio Companies' not in content[insert_pos:insert_pos+1000]:
                table_html = '''
    <!-- Top Companies Section -->
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="bg-white rounded-lg shadow p-6">
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
                        <!-- Companies will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
'''
                content = content[:insert_pos] + table_html + content[insert_pos:]
                
                with open('kbi_dashboard/portfolio.html', 'w') as f:
                    f.write(content)
                
                print("✅ Added table right after main tag")
            else:
                print("✅ Table already exists in that location")

