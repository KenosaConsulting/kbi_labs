import os

# Read the current main.py
with open('src/main.py', 'r') as f:
    content = f.read()

# Check if enrichment router is already imported
if 'enrichment' not in content:
    # Add import
    import_line = "from src.api.routers import health, companies, analytics"
    new_import = "from src.api.routers import health, companies, analytics, enrichment"
    content = content.replace(import_line, new_import)
    
    # Add router inclusion
    router_section = 'app.include_router(analytics.router, prefix="/api/v2")'
    new_router = '''app.include_router(analytics.router, prefix="/api/v2")
app.include_router(enrichment.router, prefix="/api/v3")'''
    content = content.replace(router_section, new_router)
    
    # Write back
    with open('src/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Added enrichment routes to main.py")
else:
    print("✅ Enrichment routes already in main.py")
