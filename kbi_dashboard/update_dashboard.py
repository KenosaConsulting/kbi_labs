import re

with open('index.html', 'r') as f:
    content = f.read()

# Add portfolio button if not already there
if 'portfolio.html' not in content:
    # Find the header section and add the portfolio button
    pattern = r'(<h1[^>]*>KBI Labs[^<]*</h1>)'
    replacement = r'\1\n                <a href="portfolio.html" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 ml-4">Portfolio Analysis</a>'
    content = re.sub(pattern, replacement, content)
    
    with open('index.html', 'w') as f:
        f.write(content)
    
    print("✅ Portfolio button added to dashboard")
else:
    print("✅ Portfolio button already exists")
