#!/usr/bin/env python3
"""
KBI Labs Data Enrichment API Server
Test server for the government data enrichment system
"""

import asyncio
import uvicorn
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Load environment variables
load_dotenv()

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

try:
    from api.data_enrichment_routes import router as enrichment_router
    ENRICHMENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import enrichment routes: {e}")
    ENRICHMENT_AVAILABLE = False

app = FastAPI(
    title="KBI Labs Data Enrichment API",
    description="Government data enrichment system for SMB government contractors",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include enrichment routes if available
if ENRICHMENT_AVAILABLE:
    app.include_router(enrichment_router)
    print("✅ Enrichment routes loaded successfully")
else:
    print("⚠️  Enrichment routes not available - check backend imports")

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        # Test database connection if available
        if ENRICHMENT_AVAILABLE:
            # This would test the actual database connection
            status = "healthy"
            db_status = "connected"
        else:
            status = "partial"
            db_status = "unavailable"
        
        return {
            "status": status,
            "service": "kbi-enrichment-api",
            "version": "1.0.0",
            "database": db_status,
            "enrichment_system": ENRICHMENT_AVAILABLE
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "KBI Labs Data Enrichment API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "enrichment": "/api/data-enrichment/" if ENRICHMENT_AVAILABLE else "unavailable",
            "docs": "/docs",
            "test_page": "/test"
        }
    }

# Test page endpoint
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KBI Labs Data Enrichment - Test Page</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold text-center mb-8">KBI Labs Data Enrichment System</h1>
        
        <div class="max-w-2xl mx-auto">
            <!-- System Status -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">System Status</h2>
                <div id="system-status" class="space-y-2">
                    <div class="flex justify-between">
                        <span>API Server:</span>
                        <span id="api-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Database:</span>
                        <span id="db-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Enrichment System:</span>
                        <span id="enrichment-status" class="text-yellow-600">Checking...</span>
                    </div>
                </div>
            </div>
            
            <!-- Quick Test -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">Quick Test</h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Agency Code:</label>
                        <input type="text" id="agency-code" value="9700" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md">
                    </div>
                    <button id="test-enrichment" 
                            class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                        Test Agency Enrichment
                    </button>
                    <button id="test-agencies" 
                            class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700">
                        Get Supported Agencies
                    </button>
                </div>
            </div>
            
            <!-- Results -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">Test Results</h2>
                <pre id="test-results" class="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">Ready to test...</pre>
            </div>
            
            <!-- Links -->
            <div class="bg-white rounded-lg shadow-md p-6 mt-6">
                <h2 class="text-xl font-semibold mb-4">API Documentation</h2>
                <div class="space-y-2">
                    <a href="/docs" class="block text-blue-600 hover:text-blue-800">📚 OpenAPI Documentation (Swagger)</a>
                    <a href="/redoc" class="block text-blue-600 hover:text-blue-800">📖 ReDoc Documentation</a>
                    <a href="/health" class="block text-blue-600 hover:text-blue-800">❤️ Health Check</a>
                </div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        
        // Check system status
        async function checkSystemStatus() {
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();
                
                document.getElementById('api-status').textContent = 'Online';
                document.getElementById('api-status').className = 'text-green-600';
                
                document.getElementById('db-status').textContent = data.database === 'connected' ? 'Connected' : 'Disconnected';
                document.getElementById('db-status').className = data.database === 'connected' ? 'text-green-600' : 'text-red-600';
                
                document.getElementById('enrichment-status').textContent = data.enrichment_system ? 'Available' : 'Unavailable';
                document.getElementById('enrichment-status').className = data.enrichment_system ? 'text-green-600' : 'text-red-600';
                
            } catch (error) {
                document.getElementById('api-status').textContent = 'Offline';
                document.getElementById('api-status').className = 'text-red-600';
                document.getElementById('db-status').textContent = 'Disconnected';
                document.getElementById('db-status').className = 'text-red-600';
                document.getElementById('enrichment-status').textContent = 'Unavailable';
                document.getElementById('enrichment-status').className = 'text-red-600';
            }
        }
        
        // Test supported agencies
        document.getElementById('test-agencies').addEventListener('click', async () => {
            const resultsElement = document.getElementById('test-results');
            resultsElement.textContent = 'Getting supported agencies...\\n';
            
            try {
                const response = await fetch(`${API_BASE}/api/data-enrichment/agencies`);
                const data = await response.json();
                resultsElement.textContent += `Response (${response.status}): \\n${JSON.stringify(data, null, 2)}`;
                
            } catch (error) {
                resultsElement.textContent += `Error: ${error.message}`;
            }
        });
        
        // Test enrichment
        document.getElementById('test-enrichment').addEventListener('click', async () => {
            const agencyCode = document.getElementById('agency-code').value;
            const resultsElement = document.getElementById('test-results');
            
            resultsElement.textContent = 'Testing enrichment request...\\n';
            
            try {
                const response = await fetch(`${API_BASE}/api/data-enrichment/enrich`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        agency_code: agencyCode,
                        agency_name: `Test Agency ${agencyCode}`,
                        data_types: ['budget', 'personnel'],
                        enrichment_depth: 'basic',
                        priority: 'normal'
                    })
                });
                
                const data = await response.json();
                resultsElement.textContent += `Response (${response.status}): \\n${JSON.stringify(data, null, 2)}`;
                
            } catch (error) {
                resultsElement.textContent += `Error: ${error.message}`;
            }
        });
        
        // Check status on page load
        checkSystemStatus();
        
        // Refresh status every 30 seconds
        setInterval(checkSystemStatus, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# Serve frontend static files if available
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")

if __name__ == "__main__":
    print("🚀 Starting KBI Labs Data Enrichment API Server")
    print("=" * 50)
    print(f"📊 Database: {os.getenv('DATABASE_NAME', 'kbi_labs_enrichment')}")
    print(f"🔌 Host: {os.getenv('API_HOST', '0.0.0.0')}")
    print(f"🚪 Port: {os.getenv('API_PORT', '8000')}")
    print(f"🔍 Docs: http://localhost:{os.getenv('API_PORT', '8000')}/docs")
    print(f"🧪 Test: http://localhost:{os.getenv('API_PORT', '8000')}/test")
    print("=" * 50)
    
    uvicorn.run(
        "test_server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level="info"
    )