#!/usr/bin/env python3
"""Test the new API structure"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.api.main import app
    from src.config.settings import settings
    print("✅ Successfully imported API and settings")
    print(f"   App: {app.title}")
    print(f"   Port: {settings.port}")
    print(f"   Debug: {settings.debug}")
except Exception as e:
    print(f"❌ Import error: {e}")
    
# List available endpoints
try:
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append(route.path)
    print(f"\n📌 Available routes: {len(routes)}")
    for route in sorted(routes)[:10]:  # Show first 10
        print(f"   {route}")
except Exception as e:
    print(f"❌ Error listing routes: {e}")
