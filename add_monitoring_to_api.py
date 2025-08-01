import sys

# Read the current main.py
with open('src/api/main.py', 'r') as f:
    content = f.read()

# Add imports if not present
monitoring_imports = """from src.monitoring.metrics import metrics_endpoint
from src.monitoring.middleware import MonitoringMiddleware
from src.api.routers import health_monitoring
"""

# Add monitoring setup after app creation
monitoring_setup = """
# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return await metrics_endpoint()

# Include health monitoring router
app.include_router(health_monitoring.router, prefix="/api/v3", tags=["monitoring"])
"""

# Find where to insert imports
import_pos = content.find('from fastapi import')
if import_pos != -1:
    # Insert after the last import
    last_import = content.rfind('\n\n', 0, content.find('app = FastAPI'))
    content = content[:last_import] + '\n' + monitoring_imports + content[last_import:]

# Find where to insert monitoring setup
app_creation = content.find('app = FastAPI')
if app_creation != -1:
    # Find the next empty line after app creation and CORS setup
    cors_end = content.find('allow_headers=["*"],\n)', app_creation)
    if cors_end != -1:
        insert_pos = content.find('\n\n', cors_end) + 2
    else:
        insert_pos = content.find('\n\n', app_creation) + 2
    
    content = content[:insert_pos] + monitoring_setup + '\n' + content[insert_pos:]

# Write the updated content
with open('src/api/main.py', 'w') as f:
    f.write(content)

print("✅ Monitoring added to main.py")
