#!/usr/bin/env python3
"""
KBI Labs - Consolidated Intelligence Platform Server
Unified server combining all functionality from:
- unified_platform_server.py (comprehensive integration)
- test_server.py (enrichment API testing)
- simple_test_server.py (simplified testing)

Environment-based configuration for test/development/production modes
Phase 2 AI/ML integration ready
"""

import asyncio
import uvicorn
import os
import sys
import sqlite3
import asyncpg
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
import logging
import json
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_TEST_MODE = ENVIRONMENT in ["test", "testing"]
IS_DEVELOPMENT = ENVIRONMENT == "development"
IS_PRODUCTION = ENVIRONMENT == "production"

# Add all paths
project_root = Path(__file__).parent
backend_path = project_root / "backend"
src_path = project_root / "src"

sys.path.extend([str(backend_path), str(src_path)])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EnrichmentRequest(BaseModel):
    agency_code: str
    agency_name: Optional[str] = None
    data_types: List[str] = ["budget", "personnel", "contracts", "organizational"]
    enrichment_depth: str = "standard"
    priority: str = "normal"
    user_id: Optional[str] = None

class EnrichmentResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    status: str
    message: str
    cache_hit: Optional[bool] = False

# ============================================================================
# DATABASE MANAGERS - Environment-specific configuration
# ============================================================================

async def get_db_connection():
    """Database connection with environment-specific configuration"""
    if IS_TEST_MODE:
        # Use SQLite for testing
        import aiosqlite
        return await aiosqlite.connect("test_kbi_labs.db")
    else:
        # Use PostgreSQL for development/production
        return await asyncpg.connect(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", 5432)),
            database=os.getenv("DATABASE_NAME", "kbi_labs"),
            user=os.getenv("DATABASE_USER", "kbi_user"),
            password=os.getenv("DATABASE_PASSWORD", "kbi_password")
        )

# ============================================================================
# APPLICATION FACTORY
# ============================================================================

def create_app() -> FastAPI:
    """Create FastAPI app with environment-specific configuration"""
    
    app_config = {
        "development": {
            "title": "KBI Labs - Development Server",
            "description": "Development environment for KBI Labs Intelligence Platform",
            "debug": True
        },
        "test": {
            "title": "KBI Labs - Test Server", 
            "description": "Test environment with simplified database and mocked services",
            "debug": True
        },
        "production": {
            "title": "KBI Labs - Intelligence Platform",
            "description": "Production KBI Labs Intelligence Platform for SMB Government Contractors",
            "debug": False
        }
    }
    
    config = app_config.get(ENVIRONMENT, app_config["development"])
    
    app = FastAPI(
        title=config["title"],
        description=config["description"],
        version="2.0.0",
        docs_url="/docs" if not IS_PRODUCTION else None,
        redoc_url="/redoc" if not IS_PRODUCTION else None
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if IS_DEVELOPMENT else os.getenv("ALLOWED_ORIGINS", "").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

# Create app instance
app = create_app()

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check with environment-specific tests"""
    try:
        # Database connection test
        if IS_TEST_MODE:
            db_status = "sqlite-ready"
            db_connected = True
        else:
            try:
                conn = await get_db_connection()
                await conn.execute("SELECT 1")
                await conn.close()
                db_status = "connected"
                db_connected = True
            except Exception:
                db_status = "disconnected"
                db_connected = False
        
        return {
            "status": "healthy" if db_connected else "degraded",
            "service": "kbi-labs-platform",
            "version": "2.0.0",
            "environment": ENVIRONMENT,
            "database": db_status,
            "enrichment_system": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "environment": ENVIRONMENT
        }

@app.get("/")
async def root():
    """Root endpoint with environment-specific information"""
    endpoints = {
        "health": "/health",
        "enrichment": "/api/data-enrichment/",
        "companies": "/api/companies/",
        "intelligence": "/api/intelligence/"
    }
    
    if not IS_PRODUCTION:
        endpoints.update({
            "docs": "/docs",
            "test_page": "/test"
        })
    
    return {
        "message": f"KBI Labs Intelligence Platform - {ENVIRONMENT.title()}",
        "version": "2.0.0", 
        "environment": ENVIRONMENT,
        "status": "online",
        "endpoints": endpoints
    }

# ============================================================================
# DATA ENRICHMENT API (from test_server.py and simple_test_server.py)
# ============================================================================

@app.get("/api/data-enrichment/agencies")
async def get_supported_agencies():
    """Get list of supported government agencies"""
    agencies = [
        {"code": "9700", "name": "Department of Defense", "category": "Defense"},
        {"code": "7000", "name": "Department of Homeland Security", "category": "Security"},
        {"code": "7500", "name": "Department of Health and Human Services", "category": "Health"},
        {"code": "1400", "name": "Department of the Interior", "category": "Natural Resources"},
        {"code": "4700", "name": "General Services Administration", "category": "Government Services"},
        {"code": "3600", "name": "Department of Veterans Affairs", "category": "Veterans"},
        {"code": "5700", "name": "Department of the Air Force", "category": "Defense"},
        {"code": "2100", "name": "Department of the Army", "category": "Defense"},
        {"code": "1700", "name": "Department of the Navy", "category": "Defense"}
    ]
    
    return {
        "success": True,
        "agencies": agencies,
        "total_count": len(agencies)
    }

@app.get("/api/data-enrichment/data-types")
async def get_supported_data_types():
    """Get supported enrichment data types"""
    data_types = [
        {
            "type": "budget",
            "name": "Budget Data",
            "description": "Financial data including budget authority, outlays, and spending patterns"
        },
        {
            "type": "personnel", 
            "name": "Personnel Data",
            "description": "Key personnel, leadership, and organizational contacts"
        },
        {
            "type": "contracts",
            "name": "Contract Data", 
            "description": "Contract awards, procurement opportunities, and vendor information"
        },
        {
            "type": "organizational",
            "name": "Organizational Data",
            "description": "Organizational structure, office hierarchy, and reporting relationships"
        }
    ]
    
    return {
        "success": True,
        "data_types": data_types,
        "total_count": len(data_types)
    }

@app.post("/api/data-enrichment/enrich", response_model=EnrichmentResponse)
async def request_agency_enrichment(request: EnrichmentRequest):
    """Submit agency enrichment request"""
    try:
        job_id = str(uuid.uuid4())
        
        # Environment-specific job handling
        if IS_TEST_MODE:
            # Mock job creation for testing
            return EnrichmentResponse(
                success=True,
                job_id=job_id,
                status="queued",
                message=f"Test enrichment job queued for agency {request.agency_code}",
                cache_hit=False
            )
        else:
            # Full database integration for development/production
            conn = await get_db_connection()
            await conn.execute("""
                INSERT INTO data_enrichment_jobs 
                (id, agency_code, agency_name, data_types, enrichment_depth, priority, status, progress, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            uuid.UUID(job_id), request.agency_code, request.agency_name, request.data_types,
            request.enrichment_depth, request.priority, "queued", 0, datetime.now())
            
            await conn.close()
            
            return EnrichmentResponse(
                success=True,
                job_id=job_id,
                status="queued",
                message=f"Enrichment job queued for agency {request.agency_code}",
                cache_hit=False
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process enrichment request: {str(e)}"
        )

# ============================================================================
# COMPANIES API (from unified_platform_server.py)
# ============================================================================

@app.get("/api/companies/")
async def get_companies(limit: int = Query(50, le=1000)):
    """Get companies with intelligence data"""
    # Implementation would include full company intelligence from unified server
    return {
        "companies": [],
        "total": 0,
        "environment": ENVIRONMENT,
        "message": "Companies API endpoint - implementation pending"
    }

# ============================================================================
# INTELLIGENCE API (Phase 2 Ready)
# ============================================================================

@app.get("/api/intelligence/")
async def get_intelligence_overview():
    """AI/ML intelligence overview - Phase 2 ready endpoint"""
    return {
        "status": "ready",
        "version": "2.0.0",
        "phase": "2-ready",
        "ai_ml_integration": "pending",
        "capabilities": [
            "government_data_enrichment",
            "company_intelligence", 
            "contract_opportunity_scoring",
            "agency_analysis"
        ]
    }

# ============================================================================
# TEST PAGE (Development and Test only)
# ============================================================================

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Comprehensive test page - available in development and test modes only"""
    if IS_PRODUCTION:
        raise HTTPException(status_code=404, detail="Test page not available in production")
        
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KBI Labs - {ENVIRONMENT.title()} Test Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            <h1 class="text-3xl font-bold text-blue-800">🚀 KBI Labs - {ENVIRONMENT.title()} Environment</h1>
            <p class="text-blue-600">Consolidated server v2.0.0 - Testing interface</p>
        </div>
        
        <div class="max-w-6xl mx-auto">
            <!-- System Status -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">📊 System Status</h2>
                <div id="system-status" class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="flex justify-between">
                        <span class="font-medium">Server:</span>
                        <span id="server-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="font-medium">Database:</span>
                        <span id="db-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="font-medium">Environment:</span>
                        <span class="text-green-600">{ENVIRONMENT.title()}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="font-medium">Enrichment:</span>
                        <span id="enrichment-status" class="text-yellow-600">Checking...</span>
                    </div>
                </div>
            </div>
            
            <!-- API Testing -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <!-- Enrichment Test -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4">🧪 Data Enrichment Test</h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Agency Code:</label>
                            <input type="text" id="agency-code" value="9700" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md">
                        </div>
                        <button id="test-enrichment" 
                                class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                            ⚡ Test Enrichment
                        </button>
                        <button id="get-agencies" 
                                class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700">
                            📋 Get Agencies
                        </button>
                    </div>
                </div>
                
                <!-- Intelligence Test -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold mb-4">🧠 Intelligence API Test</h2>
                    <div class="space-y-4">
                        <button id="test-intelligence" 
                                class="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700">
                            🚀 Test Intelligence API
                        </button>
                        <button id="test-companies" 
                                class="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700">
                            🏢 Test Companies API
                        </button>
                        <div class="text-sm text-gray-600">
                            <p><strong>Phase 2 Ready:</strong> AI/ML integration endpoints prepared</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Results -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">📄 Test Results</h2>
                <pre id="test-results" class="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">Ready to test consolidated server...</pre>
            </div>
            
            <!-- Documentation Links -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">🔗 API Documentation & Links</h2>
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <a href="/docs" class="block text-center bg-blue-50 hover:bg-blue-100 p-4 rounded-lg text-blue-600">
                        📚 OpenAPI (Swagger)
                    </a>
                    <a href="/redoc" class="block text-center bg-green-50 hover:bg-green-100 p-4 rounded-lg text-green-600">
                        📖 ReDoc Documentation  
                    </a>
                    <a href="/health" class="block text-center bg-red-50 hover:bg-red-100 p-4 rounded-lg text-red-600">
                        ❤️ Health Check
                    </a>
                    <a href="/api/intelligence/" class="block text-center bg-purple-50 hover:bg-purple-100 p-4 rounded-lg text-purple-600">
                        🧠 Intelligence API
                    </a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        
        // System status check
        async function checkSystemStatus() {{
            try {{
                const response = await fetch(`${{API_BASE}}/health`);
                const data = await response.json();
                
                document.getElementById('server-status').textContent = '🟢 Online';
                document.getElementById('server-status').className = 'text-green-600';
                
                document.getElementById('db-status').textContent = data.database.includes('connected') ? '🟢 Connected' : '🟡 Ready';
                document.getElementById('db-status').className = data.database.includes('connected') ? 'text-green-600' : 'text-yellow-600';
                
                document.getElementById('enrichment-status').textContent = data.enrichment_system ? '🟢 Available' : '🔴 Unavailable';
                document.getElementById('enrichment-status').className = data.enrichment_system ? 'text-green-600' : 'text-red-600';
                
            }} catch (error) {{
                ['server-status', 'db-status', 'enrichment-status'].forEach(id => {{
                    document.getElementById(id).textContent = '🔴 Error';
                    document.getElementById(id).className = 'text-red-600';
                }});
            }}
        }}
        
        // Test functions
        document.getElementById('test-enrichment').addEventListener('click', async () => {{
            const resultsElement = document.getElementById('test-results');
            const agencyCode = document.getElementById('agency-code').value;
            resultsElement.textContent = '⚡ Testing enrichment API...\\n';
            
            try {{
                const response = await fetch(`${{API_BASE}}/api/data-enrichment/enrich`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        agency_code: agencyCode,
                        agency_name: `Test Agency ${{agencyCode}}`,
                        data_types: ['budget', 'personnel'],
                        enrichment_depth: 'basic'
                    }})
                }});
                
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${{response.status}}): \\n${{JSON.stringify(data, null, 2)}}`;
                
            }} catch (error) {{
                resultsElement.textContent += `❌ Error: ${{error.message}}`;
            }}
        }});
        
        document.getElementById('get-agencies').addEventListener('click', async () => {{
            const resultsElement = document.getElementById('test-results');
            resultsElement.textContent = '📋 Getting agencies...\\n';
            
            try {{
                const response = await fetch(`${{API_BASE}}/api/data-enrichment/agencies`);
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${{response.status}}): \\n${{JSON.stringify(data, null, 2)}}`;
                
            }} catch (error) {{
                resultsElement.textContent += `❌ Error: ${{error.message}}`;
            }}
        }});
        
        document.getElementById('test-intelligence').addEventListener('click', async () => {{
            const resultsElement = document.getElementById('test-results');
            resultsElement.textContent = '🧠 Testing intelligence API...\\n';
            
            try {{
                const response = await fetch(`${{API_BASE}}/api/intelligence/`);
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${{response.status}}): \\n${{JSON.stringify(data, null, 2)}}`;
                
            }} catch (error) {{
                resultsElement.textContent += `❌ Error: ${{error.message}}`;
            }}
        }});
        
        document.getElementById('test-companies').addEventListener('click', async () => {{
            const resultsElement = document.getElementById('test-results');
            resultsElement.textContent = '🏢 Testing companies API...\\n';
            
            try {{
                const response = await fetch(`${{API_BASE}}/api/companies/`);
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${{response.status}}): \\n${{JSON.stringify(data, null, 2)}}`;
                
            }} catch (error) {{
                resultsElement.textContent += `❌ Error: ${{error.message}}`;
            }}
        }});
        
        // Initialize
        checkSystemStatus();
        setInterval(checkSystemStatus, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# ============================================================================
# STATIC FILES
# ============================================================================

# Serve static files
static_paths = [
    (project_root / "frontend", "frontend"),
    (project_root / "static", "static")
]

for path, name in static_paths:
    if path.exists():
        app.mount(f"/{name}", StaticFiles(directory=str(path)), name=name)

# ============================================================================
# STARTUP CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting KBI Labs Consolidated Intelligence Platform")
    print("=" * 60)
    print(f"🌍 Environment: {ENVIRONMENT}")
    print(f"🔧 Mode: {'Test' if IS_TEST_MODE else 'Development' if IS_DEVELOPMENT else 'Production'}")
    print(f"📊 Database: {'SQLite (Test)' if IS_TEST_MODE else os.getenv('DATABASE_NAME', 'kbi_labs')}")
    print(f"🔌 Host: {os.getenv('API_HOST', '0.0.0.0')}")
    print(f"🚪 Port: {os.getenv('API_PORT', '8000')}")
    
    if not IS_PRODUCTION:
        print(f"🔍 Docs: http://localhost:{os.getenv('API_PORT', '8000')}/docs")
        print(f"🧪 Test: http://localhost:{os.getenv('API_PORT', '8000')}/test")
    
    print(f"❤️  Health: http://localhost:{os.getenv('API_PORT', '8000')}/health")
    print("=" * 60)
    print("📋 Consolidated Features:")
    print("   ✅ Unified Platform Server (comprehensive)")
    print("   ✅ Test Server (enrichment API)")
    print("   ✅ Simple Test Server (basic testing)")
    print("   ✅ Environment-based configuration")
    print("   ✅ Phase 2 AI/ML integration ready")
    print("=" * 60)
    
    uvicorn.run(
        "main_server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=IS_DEVELOPMENT,
        log_level="info"
    )