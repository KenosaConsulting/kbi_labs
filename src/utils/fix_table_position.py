with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Find the table HTML
import re
table_match = re.search(r'<!-- Top Companies Table -->.*?</div>\s*</div>', content, re.DOTALL)

if table_match:
    table_html = table_match.group(0)
    
    # Remove table from current position
    content = content.replace(table_html, '')
    
    # Find a better position - after the geographic distribution section
    # Look for the end of the geographic distribution div
    geo_end = content.find('<!-- Geographic Distribution end -->')
    if geo_end == -1:
        # Try to find after "Geographic Distribution" section
        geo_pattern = r'(Geographic Distribution.*?</div>\s*</div>\s*</div>)'
        geo_match = re.search(geo_pattern, content, re.DOTALL)
        if geo_match:
            insert_pos = geo_match.end()
        else:
            # Find before Risk/Return Analysis
            risk_pos = content.find('<h3 class="text-lg font-semibold mb-4">Risk/Return Analysis</h3>')
            if risk_pos > 0:
                # Go back to find the containing div
                insert_pos = content.rfind('<div', 0, risk_pos)
            else:
                insert_pos = content.find('</main>') - 100
    else:
        insert_pos = geo_end
    
    # Insert the table
    content = content[:insert_pos] + '\n\n' + table_html + '\n\n' + content[insert_pos:]
    
    # Save
    with open('kbi_dashboard/portfolio.html', 'w') as f:
        f.write(content)
    
    print("✅ Moved table to proper position inside main content")
    
    # Verify
    main_end = content.find('</main>')
    table_pos = content.find('id="topCompaniesTable"')
    if table_pos < main_end:
        print("✅ Table is now inside <main> tag")
    else:
        print("❌ Table is still outside <main> tag")
else:
    print("❌ Could not find table HTML")

