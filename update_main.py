#!/usr/bin/env python3
import re

# Read the current main.py
with open('src/main.py', 'r') as f:
    content = f.read()

# Check if already updated
if 'intelligence_router' in content:
    print("✅ main.py already includes intelligence router")
    exit(0)

# Add the import after other imports
import_line = "from src.api.v2.intelligence import router as intelligence_router"
import_pattern = r'(from fastapi import .*\n)'
content = re.sub(import_pattern, r'\1' + import_line + '\n', content)

# Find where routers are included and add ours
router_pattern = r'(app\.include_router\([^)]+\))'
last_router = list(re.finditer(router_pattern, content))[-1]
insert_pos = last_router.end()

# Insert our router inclusion
content = content[:insert_pos] + '\napp.include_router(intelligence_router)' + content[insert_pos:]

# Write the updated content
with open('src/main.py', 'w') as f:
    f.write(content)

print("✅ Updated main.py with intelligence router")
