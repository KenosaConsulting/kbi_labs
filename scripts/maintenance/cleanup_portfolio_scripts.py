with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Remove any calls to updatePortfolioTable() since tryLoadTable is handling it
content = content.replace('updatePortfolioTable();', '// updatePortfolioTable(); // Handled by tryLoadTable')

# Also comment out any standalone updatePortfolioTable calls
import re
content = re.sub(r'^\s*updatePortfolioTable\(\);?\s*$', '// updatePortfolioTable(); // Handled by tryLoadTable', content, flags=re.MULTILINE)

with open('kbi_dashboard/portfolio.html', 'w') as f:
    f.write(content)

print("✅ Cleaned up duplicate function calls")
