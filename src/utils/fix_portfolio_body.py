with open('kbi_dashboard/portfolio.html', 'r') as f:
    content = f.read()

# Count body tags before
open_before = content.count('<body')
close_before = content.count('</body>')
print(f"Before - <body>: {open_before}, </body>: {close_before}")

# Remove extra </body> tags, keeping only the last one
# Find all positions of </body>
import re
body_closes = list(re.finditer(r'</body>', content))

if len(body_closes) > 1:
    # Remove all but the last one
    for match in body_closes[:-1]:
        content = content[:match.start()] + '<!-- removed extra body close -->' + content[match.end():]
    print(f"Removed {len(body_closes)-1} extra </body> tags")

# Also remove extra </html> tags if any
html_closes = list(re.finditer(r'</html>', content))
if len(html_closes) > 1:
    for match in html_closes[:-1]:
        content = content[:match.start()] + '<!-- removed extra html close -->' + content[match.end():]
    print(f"Removed {len(html_closes)-1} extra </html> tags")

# Save the fixed file
with open('kbi_dashboard/portfolio.html', 'w') as f:
    f.write(content)

# Count after
open_after = content.count('<body')
close_after = content.count('</body>')
print(f"After - <body>: {open_after}, </body>: {close_after}")

# Check if table still exists
if 'id="topCompaniesTable"' in content:
    print("✅ Table element still present in HTML")
else:
    print("❌ Table element missing!")

