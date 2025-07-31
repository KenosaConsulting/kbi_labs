import re

# Read the file
with open('company-details.html', 'r') as f:
    content = f.read()

# Update API endpoints
content = re.sub(r"const API_BASE = '[^']*'", "const API_BASE = 'http://localhost:5000/api'", content)
content = re.sub(r"const AI_API_BASE = '[^']*'", "const AI_API_BASE = 'http://localhost:5001/api'", content)

# For external access (your browser), use the EC2 IP
content = content.replace("http://localhost:5000/api", "http://3.143.232.123:5000/api")
content = content.replace("http://localhost:5001/api", "http://3.143.232.123:5001/api")

# Write back
with open('company-details.html', 'w') as f:
    f.write(content)

print("✅ Updated endpoints for external access")
