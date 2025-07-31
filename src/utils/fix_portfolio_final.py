import re

# Read the portfolio file
with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Find and comment out any hardcoded company data
# Look for the section that's creating these undefined rows
pattern = r'(<tbody id="topCompaniesTable">[\s\S]*?</tbody>)'
match = re.search(pattern, content)

if match:
    # Replace the tbody content with empty
    content = re.sub(pattern, '<tbody id="topCompaniesTable">\n<!-- Table will be populated by JavaScript -->\n</tbody>', content)
    print("✅ Removed hardcoded table data")

# Also remove any JavaScript that's populating with hardcoded data
# Look for loadPortfolioData or similar functions
if 'loadPortfolioData' in content:
    # Comment out the function call
    content = re.sub(r'loadPortfolioData\(\);?', '// loadPortfolioData(); // Disabled - using dynamic loading', content)
    print("✅ Disabled hardcoded data loading")

# Make sure our updatePortfolioTable is called
if 'updatePortfolioTable' in content:
    print("✅ updatePortfolioTable function found")
else:
    # Add it if missing
    content = content.replace('</body>', '''
<script>
// Dynamic portfolio loading
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/companies')
        .then(response => response.json())
        .then(companies => {
            const tbody = document.getElementById('topCompaniesTable');
            tbody.innerHTML = '';
            
            companies.sort((a, b) => (b.pe_investment_score || 0) - (a.pe_investment_score || 0));
            
            companies.slice(0, 25).forEach(company => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium text-gray-900">${company.company_name}</div>
                        <div class="text-sm text-gray-500">${company.uei}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900">${company.city}, ${company.state}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            ${company.pe_investment_score}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${company.business_health_grade}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${company.patent_count}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${(company.federal_contracts_value / 1000000).toFixed(2)}M</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <a href="company-details.html?uei=${company.uei}" class="text-indigo-600 hover:text-indigo-900">View Details</a>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
});
</script>
</body>''')
    print("✅ Added dynamic loading script")

# Save the fixed file
with open('kbi_dashboard/portfolio_fixed.html', 'w') as f:
    f.write(content)

print("\n✅ Created portfolio_fixed.html")
print("Replace the original with: mv kbi_dashboard/portfolio_fixed.html kbi_dashboard/portfolio.html")
