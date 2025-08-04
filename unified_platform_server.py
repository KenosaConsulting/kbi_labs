#!/usr/bin/env python3
"""
KBI Labs - Unified Intelligence Platform Server
Comprehensive integration of all systems:
- Company Intelligence & Analytics
- Government Data Enrichment
- Agency Intelligence Mapping
- Strategic Advisory Automation
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add all paths
project_root = Path(__file__).parent
backend_path = project_root / "backend"
src_path = project_root / "src"

sys.path.extend([str(backend_path), str(src_path)])

# ============================================================================
# DATABASE MANAGERS - Unified database access
# ============================================================================

class UnifiedDatabaseManager:
    """Manages connections to both SQLite and PostgreSQL databases"""
    
    def __init__(self):
        self.sqlite_path = project_root / "backend" / "data" / "kbi_labs.db"
        self.pg_pool = None
        
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize PostgreSQL connection pool
            self.pg_pool = await asyncpg.create_pool(
                host=os.getenv("DATABASE_HOST", "localhost"),
                port=int(os.getenv("DATABASE_PORT", 5432)),
                database=os.getenv("DATABASE_NAME", "kbi_labs_enrichment"),
                user=os.getenv("DATABASE_USER", "kbi_user"),
                password=os.getenv("DATABASE_PASSWORD", "kbi_password"),
                min_size=5,
                max_size=20
            )
            logger.info("✅ PostgreSQL connection pool initialized")
            
            # Verify SQLite database exists
            if self.sqlite_path.exists():
                logger.info("✅ SQLite database found")
            else:
                logger.warning("⚠️ SQLite database not found - creating minimal schema")
                self._create_minimal_sqlite()
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _create_minimal_sqlite(self):
        """Create minimal SQLite schema for testing"""
        conn = sqlite3.connect(self.sqlite_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT,
                naics_code TEXT,
                revenue REAL,
                government_contracts_value REAL,
                created_at TEXT
            )
        """)
        
        # Insert sample data
        conn.execute("""
            INSERT OR REPLACE INTO companies VALUES 
            ('1', 'TechCorp Solutions', '541512', 5000000, 2000000, '2024-01-01'),
            ('2', 'DataMax Systems', '541511', 3500000, 1500000, '2024-01-02'),
            ('3', 'CyberGuard Inc', '541519', 8000000, 4000000, '2024-01-03')
        """)
        conn.commit()
        conn.close()
        logger.info("✅ Minimal SQLite database created")
    
    async def close(self):
        """Close database connections"""
        if self.pg_pool:
            await self.pg_pool.close()
            logger.info("Database connections closed")

# Global database manager
db_manager = UnifiedDatabaseManager()

# ============================================================================
# PYDANTIC MODELS - Unified data models
# ============================================================================

class CompanyIntelligence(BaseModel):
    id: str
    name: str
    naics_code: Optional[str] = None
    revenue: Optional[float] = None
    government_contracts_value: Optional[float] = None
    target_agencies: List[str] = []
    opportunity_score: Optional[float] = None

class AgencyIntelligence(BaseModel):
    agency_code: str
    agency_name: str
    budget_data: Optional[Dict[str, Any]] = None
    key_personnel: List[Dict[str, str]] = []
    upcoming_opportunities: List[Dict[str, Any]] = []
    strategic_recommendations: List[str] = []

class EnrichmentRequest(BaseModel):
    agency_code: str
    agency_name: Optional[str] = None
    data_types: List[str] = ["budget", "personnel", "contracts", "organizational"]
    enrichment_depth: str = "standard"
    priority: str = "normal"

class UnifiedIntelligenceReport(BaseModel):
    company: CompanyIntelligence
    target_agencies: List[AgencyIntelligence]
    strategic_recommendations: List[str]
    opportunity_score: float
    generated_at: str

# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 Starting KBI Labs Unified Intelligence Platform...")
    
    try:
        await db_manager.initialize()
        logger.info("✅ All database connections initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize databases: {e}")
        raise
    
    yield
    
    await db_manager.close()
    logger.info("🛑 KBI Labs Platform shutdown complete")

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="KBI Labs - Unified Intelligence Platform",
    description="Comprehensive SMB & Government Contractor Intelligence Platform",
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
    logger.info("✅ Static files mounted")
except Exception as e:
    logger.warning(f"⚠️ Static files not available: {e}")

# ============================================================================
# UNIFIED SERVICES - Business logic integration
# ============================================================================

class UnifiedIntelligenceService:
    """Core service integrating company and agency intelligence"""
    
    @staticmethod
    async def get_company_intelligence(company_id: str) -> CompanyIntelligence:
        """Get comprehensive company intelligence"""
        conn = sqlite3.connect(db_manager.sqlite_path)
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return CompanyIntelligence(
            id=row[0],
            name=row[1],
            naics_code=row[2],
            revenue=row[3],
            government_contracts_value=row[4],
            target_agencies=["9700", "7000"],  # Sample agencies
            opportunity_score=85.5
        )
    
    @staticmethod
    async def get_agency_intelligence(agency_code: str) -> AgencyIntelligence:
        """Get comprehensive agency intelligence"""
        async with db_manager.pg_pool.acquire() as conn:
            # Get cached agency data
            cached_data = await conn.fetch(
                "SELECT * FROM enriched_data_cache WHERE agency_code = $1",
                agency_code
            )
            
            # Get agency jobs
            jobs = await conn.fetch(
                "SELECT * FROM data_enrichment_jobs WHERE agency_code = $1 ORDER BY created_at DESC LIMIT 5",
                agency_code
            )
        
        agency_names = {
            "9700": "Department of Defense",
            "7000": "Department of Homeland Security",
            "7500": "Department of Health and Human Services",
            "4700": "General Services Administration"
        }
        
        return AgencyIntelligence(
            agency_code=agency_code,
            agency_name=agency_names.get(agency_code, f"Agency {agency_code}"),
            budget_data={"annual_budget": 500000000, "it_budget": 50000000},
            key_personnel=[
                {"name": "John Smith", "title": "CIO", "email": "john.smith@agency.gov"},
                {"name": "Sarah Johnson", "title": "Contracting Officer", "email": "sarah.johnson@agency.gov"}
            ],
            upcoming_opportunities=[
                {"title": "Cloud Migration", "value": 2500000, "due_date": "2025-09-15"},
                {"title": "Cybersecurity Enhancement", "value": 1800000, "due_date": "2025-08-30"}
            ],
            strategic_recommendations=[
                f"Target {agency_names.get(agency_code, 'this agency')} for IT modernization opportunities",
                "Focus on small business set-aside contracts",
                "Build relationships with key personnel before RFP release"
            ]
        )
    
    @staticmethod
    async def generate_unified_intelligence_report(company_id: str) -> UnifiedIntelligenceReport:
        """Generate comprehensive intelligence report combining company and agency data"""
        
        # Get company intelligence
        company = await UnifiedIntelligenceService.get_company_intelligence(company_id)
        
        # Get intelligence for target agencies
        target_agencies = []
        for agency_code in company.target_agencies:
            agency_intel = await UnifiedIntelligenceService.get_agency_intelligence(agency_code)
            target_agencies.append(agency_intel)
        
        # Generate strategic recommendations
        recommendations = [
            f"Based on {company.name}'s NAICS code {company.naics_code}, target IT modernization opportunities",
            f"With ${company.government_contracts_value:,.0f} in existing contracts, pursue larger opportunities",
            "Leverage small business status for set-aside opportunities",
            "Build relationships with agency contracting officers 6 months before opportunities"
        ]
        
        return UnifiedIntelligenceReport(
            company=company,
            target_agencies=target_agencies,
            strategic_recommendations=recommendations,
            opportunity_score=92.3,
            generated_at=datetime.now().isoformat()
        )

# ============================================================================
# API ENDPOINTS - Unified intelligence endpoints
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Test SQLite
        conn = sqlite3.connect(db_manager.sqlite_path)
        sqlite_test = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        conn.close()
        
        # Test PostgreSQL
        async with db_manager.pg_pool.acquire() as pg_conn:
            pg_test = await pg_conn.fetchval("SELECT COUNT(*) FROM data_enrichment_jobs")
        
        return {
            "status": "healthy",
            "platform": "KBI Labs Unified Intelligence",
            "version": "4.0.0",
            "databases": {
                "sqlite": {"status": "connected", "companies": sqlite_test},
                "postgresql": {"status": "connected", "jobs": pg_test}
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# COMPANY INTELLIGENCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/companies")
async def get_companies():
    """Get all companies with intelligence scores"""
    conn = sqlite3.connect(db_manager.sqlite_path)
    rows = conn.execute("SELECT * FROM companies").fetchall()
    conn.close()
    
    companies = []
    for row in rows:
        companies.append({
            "id": row[0],
            "name": row[1],
            "naics_code": row[2],
            "revenue": row[3],
            "government_contracts_value": row[4],
            "opportunity_score": 85.0 + (int(row[0]) * 3.2)  # Dynamic scoring
        })
    
    return {"companies": companies, "total": len(companies)}

@app.get("/api/v1/companies/{company_id}")
async def get_company_details(company_id: str):
    """Get detailed company intelligence"""
    return await UnifiedIntelligenceService.get_company_intelligence(company_id)

@app.get("/api/v1/companies/{company_id}/intelligence-report")
async def get_company_intelligence_report(company_id: str):
    """Get comprehensive intelligence report for a company"""
    return await UnifiedIntelligenceService.generate_unified_intelligence_report(company_id)

# ============================================================================
# AGENCY INTELLIGENCE ENDPOINTS (from data enrichment system)
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
        {"code": "3600", "name": "Department of Veterans Affairs", "category": "Veterans"}
    ]
    
    return {
        "success": True,
        "agencies": agencies,
        "total_count": len(agencies)
    }

@app.post("/api/data-enrichment/enrich")
async def request_agency_enrichment(request: EnrichmentRequest, background_tasks: BackgroundTasks):
    """Request data enrichment for a government agency"""
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # Store enrichment job in PostgreSQL
    async with db_manager.pg_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO data_enrichment_jobs 
            (id, agency_code, agency_name, data_types, enrichment_depth, priority, status, progress, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, 
        uuid.UUID(job_id), request.agency_code, request.agency_name, request.data_types,
        request.enrichment_depth, request.priority, "queued", 0, datetime.now())
    
    # Add background task to process enrichment
    background_tasks.add_task(process_enrichment_job, job_id, request)
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "message": f"Enrichment job queued for agency {request.agency_code}",
        "estimated_duration_minutes": 5
    }

@app.get("/api/data-enrichment/job/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status of an enrichment job"""
    async with db_manager.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM data_enrichment_jobs WHERE id = $1",
            uuid.UUID(job_id)
        )
    
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

@app.get("/api/data-enrichment/agency/{agency_code}/intelligence")
async def get_agency_intelligence_endpoint(agency_code: str):
    """Get comprehensive agency intelligence"""
    return await UnifiedIntelligenceService.get_agency_intelligence(agency_code)

# ============================================================================
# STRATEGIC ADVISORY ENDPOINTS
# ============================================================================

@app.get("/api/v1/strategic-advisory/company/{company_id}/agency-recommendations")
async def get_agency_recommendations(company_id: str):
    """Get agency targeting recommendations for a company"""
    
    company = await UnifiedIntelligenceService.get_company_intelligence(company_id)
    
    # Generate recommendations based on company profile
    recommendations = []
    
    if company.naics_code and company.naics_code.startswith("541"):  # Professional services
        recommendations.extend([
            {
                "agency_code": "9700",
                "agency_name": "Department of Defense",
                "recommendation": "High priority - large IT services budget",
                "estimated_value": 25000000,
                "confidence": 92.5
            },
            {
                "agency_code": "7000", 
                "agency_name": "Department of Homeland Security",
                "recommendation": "Medium priority - cybersecurity focus",
                "estimated_value": 15000000,
                "confidence": 78.3
            }
        ])
    
    return {
        "company_id": company_id,
        "company_name": company.name,
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/v1/strategic-advisory/generate-agency-plan")
async def generate_agency_plan(agency_code: str, company_id: str):
    """Generate comprehensive agency targeting plan"""
    
    company = await UnifiedIntelligenceService.get_company_intelligence(company_id)
    agency = await UnifiedIntelligenceService.get_agency_intelligence(agency_code)
    
    plan = {
        "company": company.dict(),
        "target_agency": agency.dict(),
        "strategic_plan": {
            "phase_1": "Research and relationship building (Months 1-3)",
            "phase_2": "Capability positioning and teaming (Months 4-6)", 
            "phase_3": "Opportunity pursuit and proposal (Months 7-9)",
            "key_contacts": agency.key_personnel,
            "budget_targets": agency.budget_data,
            "success_probability": 76.8
        },
        "generated_at": datetime.now().isoformat()
    }
    
    return plan

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def process_enrichment_job(job_id: str, request: EnrichmentRequest):
    """Background task to process enrichment jobs"""
    await asyncio.sleep(2)  # Simulate processing time
    
    # Update job status to completed
    async with db_manager.pg_pool.acquire() as conn:
        await conn.execute("""
            UPDATE data_enrichment_jobs 
            SET status = 'completed', progress = 100, completed_at = $2
            WHERE id = $1
        """, uuid.UUID(job_id), datetime.now())
    
    logger.info(f"✅ Completed enrichment job {job_id} for agency {request.agency_code}")

# ============================================================================
# UNIFIED DASHBOARD
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def unified_dashboard():
    """Unified dashboard homepage"""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KBI Labs - Unified Intelligence Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <h1 class="text-2xl font-bold text-indigo-600">KBI Labs</h1>
                        <span class="ml-2 text-sm text-gray-500">Unified Intelligence Platform v4.0</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <a href="/api/docs" class="text-indigo-600 hover:text-indigo-900">API Docs</a>
                        <a href="/api/health" class="text-green-600 hover:text-green-900">Health</a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="px-4 py-6 sm:px-0">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    
                    <!-- Company Intelligence -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <span class="text-3xl">🏢</span>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Company Intelligence</dt>
                                        <dd class="text-lg font-medium text-gray-900">SMB Analysis & Scoring</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <a href="/api/v1/companies" class="font-medium text-indigo-700 hover:text-indigo-900">
                                    View Companies →
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- Agency Intelligence -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <span class="text-3xl">🏛️</span>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Agency Intelligence</dt>
                                        <dd class="text-lg font-medium text-gray-900">Government Data Mapping</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <a href="/api/data-enrichment/agencies" class="font-medium text-indigo-700 hover:text-indigo-900">
                                    View Agencies →
                                </a>
                            </div>
                        </div>
                    </div>

                    <!-- Strategic Advisory -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <span class="text-3xl">🎯</span>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">Strategic Advisory</dt>
                                        <dd class="text-lg font-medium text-gray-900">Automated Agency Plans</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <a href="#" onclick="generateSampleReport()" class="font-medium text-indigo-700 hover:text-indigo-900">
                                    Generate Report →
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="mt-8">
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900">Quick Actions</h3>
                            <div class="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                                <button onclick="testCompanyIntelligence()" class="bg-blue-50 hover:bg-blue-100 p-3 rounded-lg text-center">
                                    <div class="text-blue-600 font-medium">Test Company Intelligence</div>
                                </button>
                                <button onclick="testAgencyEnrichment()" class="bg-green-50 hover:bg-green-100 p-3 rounded-lg text-center">
                                    <div class="text-green-600 font-medium">Test Agency Enrichment</div>
                                </button>
                                <button onclick="generateStrategicPlan()" class="bg-purple-50 hover:bg-purple-100 p-3 rounded-lg text-center">
                                    <div class="text-purple-600 font-medium">Generate Strategic Plan</div>
                                </button>
                                <button onclick="viewSystemHealth()" class="bg-red-50 hover:bg-red-100 p-3 rounded-lg text-center">
                                    <div class="text-red-600 font-medium">System Health</div>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Results Area -->
                <div class="mt-8">
                    <div class="bg-white shadow rounded-lg">
                        <div class="px-4 py-5 sm:p-6">
                            <h3 class="text-lg leading-6 font-medium text-gray-900">Results</h3>
                            <div class="mt-2">
                                <pre id="results" class="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-96">Click any action above to see results...</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        async function makeRequest(url, options = {}) {
            try {
                const response = await fetch(url, options);
                const data = await response.json();
                document.getElementById('results').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                document.getElementById('results').textContent = `Error: ${error.message}`;
            }
        }

        function testCompanyIntelligence() {
            makeRequest('/api/v1/companies');
        }

        function testAgencyEnrichment() {
            makeRequest('/api/data-enrichment/agencies');
        }

        function generateStrategicPlan() {
            makeRequest('/api/v1/companies/1/intelligence-report');
        }

        function viewSystemHealth() {
            makeRequest('/api/health');
        }

        function generateSampleReport() {
            makeRequest('/api/v1/strategic-advisory/company/1/agency-recommendations');
        }
    </script>
</body>
</html>"""
    return html

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting KBI Labs Unified Intelligence Platform")
    print("=" * 60)
    print("🏢 Company Intelligence: /api/v1/companies")
    print("🏛️ Agency Intelligence: /api/data-enrichment/agencies") 
    print("🎯 Strategic Advisory: /api/v1/strategic-advisory")
    print("📊 Unified Dashboard: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/api/docs")
    print("❤️ Health Check: http://localhost:8000/api/health")
    print("=" * 60)
    
    uvicorn.run(
        "unified_platform_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )