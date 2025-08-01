#!/usr/bin/env python3
"""Run the KBI Labs API"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from src.config.settings import settings
    
    print(f"🚀 Starting KBI Labs API on port {settings.port}...")
    print(f"📚 API Documentation will be available at: http://localhost:{settings.port}/api/docs")
    print(f"🔍 Interactive API testing at: http://localhost:{settings.port}/api/redoc")
    print(f"")
    print(f"Available endpoints:")
    print(f"  - Health check: http://localhost:{settings.port}/health/")
    print(f"  - Companies: http://localhost:{settings.port}/api/v2/companies/")
    print(f"  - Analytics: http://localhost:{settings.port}/api/v2/analytics/overview")
    print(f"")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )
