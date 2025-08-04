#!/usr/bin/env python3
"""
Simple KBI Labs Data Enrichment API Server
Simplified version for testing without complex imports
"""

import uvicorn
import os
import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(
    title="KBI Labs Data Enrichment API",
    description="Government data enrichment system for SMB government contractors",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
async def get_db_connection():
    return await asyncpg.connect(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", 5432)),
        database=os.getenv("DATABASE_NAME", "kbi_labs_enrichment"),
        user=os.getenv("DATABASE_USER", "kbi_user"),
        password=os.getenv("DATABASE_PASSWORD", "kbi_password")
    )

# Pydantic models
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

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        conn = await get_db_connection()
        await conn.execute("SELECT 1")
        await conn.close()
        
        return {
            "status": "healthy",
            "service": "kbi-enrichment-api",
            "version": "1.0.0",
            "database": "connected",
            "enrichment_system": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected",
            "enrichment_system": False
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
            "enrichment": "/api/data-enrichment/",
            "docs": "/docs",
            "test_page": "/test"
        }
    }

# Supported agencies endpoint
@app.get("/api/data-enrichment/agencies")
async def get_supported_agencies():
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

# Data types endpoint
@app.get("/api/data-enrichment/data-types")
async def get_supported_data_types():
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

# Enrichment request endpoint
@app.post("/api/data-enrichment/enrich", response_model=EnrichmentResponse)
async def request_agency_enrichment(request: EnrichmentRequest):
    try:
        # Generate a test job ID
        job_id = str(uuid.uuid4())
        
        # Insert into database
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

# Job status endpoint
@app.get("/api/data-enrichment/job/{job_id}/status")
async def get_job_status(job_id: str):
    try:
        conn = await get_db_connection()
        row = await conn.fetchrow(
            "SELECT * FROM data_enrichment_jobs WHERE id = $1",
            uuid.UUID(job_id)
        )
        await conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job_id,
            "agency_code": row["agency_code"],
            "data_types": row["data_types"],
            "status": row["status"],
            "progress": row["progress"],
            "created_at": row["created_at"].isoformat(),
            "started_at": row["started_at"].isoformat() if row["started_at"] else None,
            "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

# Active jobs endpoint
@app.get("/api/data-enrichment/jobs/active")
async def get_active_jobs():
    try:
        conn = await get_db_connection()
        rows = await conn.fetch("""
            SELECT id, agency_code, agency_name, data_types, status, progress, created_at, priority
            FROM data_enrichment_jobs 
            WHERE status IN ('queued', 'running')
            ORDER BY priority DESC, created_at ASC
            LIMIT 20
        """)
        await conn.close()
        
        jobs = []
        for row in rows:
            jobs.append({
                "job_id": str(row["id"]),
                "agency_code": row["agency_code"],
                "agency_name": row["agency_name"],
                "data_types": row["data_types"],
                "status": row["status"],
                "progress": row["progress"],
                "priority": row["priority"],
                "created_at": row["created_at"].isoformat()
            })
        
        return {
            "success": True,
            "active_jobs": jobs,
            "total_count": len(jobs)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active jobs: {str(e)}"
        )

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
        <h1 class="text-3xl font-bold text-center mb-8">🚀 KBI Labs Data Enrichment System</h1>
        
        <div class="max-w-4xl mx-auto">
            <!-- System Status -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">📊 System Status</h2>
                <div id="system-status" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="flex justify-between">
                        <span class="font-medium">API Server:</span>
                        <span id="api-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="font-medium">Database:</span>
                        <span id="db-status" class="text-yellow-600">Checking...</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="font-medium">Enrichment:</span>
                        <span id="enrichment-status" class="text-yellow-600">Checking...</span>
                    </div>
                </div>
            </div>
            
            <!-- Quick Test -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">🧪 Quick Test</h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Agency Code:</label>
                            <input type="text" id="agency-code" value="9700" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Data Types:</label>
                            <select multiple id="data-types" class="w-full px-3 py-2 border border-gray-300 rounded-md">
                                <option value="budget" selected>Budget</option>
                                <option value="personnel" selected>Personnel</option>
                                <option value="contracts">Contracts</option>
                                <option value="organizational">Organizational</option>
                            </select>
                        </div>
                    </div>
                    <div class="space-y-4">
                        <button id="test-agencies" 
                                class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700">
                            📋 Get Supported Agencies
                        </button>
                        <button id="test-enrichment" 
                                class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                            ⚡ Test Agency Enrichment
                        </button>
                        <button id="test-active-jobs" 
                                class="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700">
                            📈 Get Active Jobs
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Results -->
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">📄 Test Results</h2>
                <pre id="test-results" class="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">Ready to test...</pre>
            </div>
            
            <!-- Links -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">🔗 API Documentation</h2>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <a href="/docs" class="block text-center bg-blue-50 hover:bg-blue-100 p-4 rounded-lg text-blue-600 hover:text-blue-800">
                        📚 OpenAPI (Swagger)
                    </a>
                    <a href="/redoc" class="block text-center bg-green-50 hover:bg-green-100 p-4 rounded-lg text-green-600 hover:text-green-800">
                        📖 ReDoc Documentation
                    </a>
                    <a href="/health" class="block text-center bg-red-50 hover:bg-red-100 p-4 rounded-lg text-red-600 hover:text-red-800">
                        ❤️ Health Check
                    </a>
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
                
                document.getElementById('api-status').textContent = '🟢 Online';
                document.getElementById('api-status').className = 'text-green-600';
                
                document.getElementById('db-status').textContent = data.database === 'connected' ? '🟢 Connected' : '🔴 Disconnected';
                document.getElementById('db-status').className = data.database === 'connected' ? 'text-green-600' : 'text-red-600';
                
                document.getElementById('enrichment-status').textContent = data.enrichment_system ? '🟢 Available' : '🔴 Unavailable';
                document.getElementById('enrichment-status').className = data.enrichment_system ? 'text-green-600' : 'text-red-600';
                
            } catch (error) {
                document.getElementById('api-status').textContent = '🔴 Offline';
                document.getElementById('api-status').className = 'text-red-600';
                document.getElementById('db-status').textContent = '🔴 Disconnected';
                document.getElementById('db-status').className = 'text-red-600';
                document.getElementById('enrichment-status').textContent = '🔴 Unavailable';
                document.getElementById('enrichment-status').className = 'text-red-600';
            }
        }
        
        // Get selected data types
        function getSelectedDataTypes() {
            const select = document.getElementById('data-types');
            return Array.from(select.selectedOptions).map(option => option.value);
        }
        
        // Test supported agencies
        document.getElementById('test-agencies').addEventListener('click', async () => {
            const resultsElement = document.getElementById('test-results');
            resultsElement.textContent = '🔍 Getting supported agencies...\\n';
            
            try {
                const response = await fetch(`${API_BASE}/api/data-enrichment/agencies`);
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${response.status}): \\n${JSON.stringify(data, null, 2)}`;
                
            } catch (error) {
                resultsElement.textContent += `❌ Error: ${error.message}`;
            }
        });
        
        // Test enrichment
        document.getElementById('test-enrichment').addEventListener('click', async () => {
            const agencyCode = document.getElementById('agency-code').value;
            const dataTypes = getSelectedDataTypes();
            const resultsElement = document.getElementById('test-results');
            
            resultsElement.textContent = '⚡ Testing enrichment request...\\n';
            
            try {
                const response = await fetch(`${API_BASE}/api/data-enrichment/enrich`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        agency_code: agencyCode,
                        agency_name: `Test Agency ${agencyCode}`,
                        data_types: dataTypes,
                        enrichment_depth: 'basic',
                        priority: 'normal'
                    })
                });
                
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${response.status}): \\n${JSON.stringify(data, null, 2)}`;
                
            } catch (error) {
                resultsElement.textContent += `❌ Error: ${error.message}`;
            }
        });
        
        // Test active jobs
        document.getElementById('test-active-jobs').addEventListener('click', async () => {
            const resultsElement = document.getElementById('test-results');
            resultsElement.textContent = '📈 Getting active jobs...\\n';
            
            try {
                const response = await fetch(`${API_BASE}/api/data-enrichment/jobs/active`);
                const data = await response.json();
                resultsElement.textContent += `✅ Response (${response.status}): \\n${JSON.stringify(data, null, 2)}`;
                
            } catch (error) {
                resultsElement.textContent += `❌ Error: ${error.message}`;
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
        "simple_test_server:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
        log_level="info"
    )