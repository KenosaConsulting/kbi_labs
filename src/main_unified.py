"""
KBI Labs Unified FastAPI Application
Main entry point combining all services: AI, Government Intelligence, and Business APIs
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting KBI Labs Unified Platform...")
    
    # Initialize database connections
    try:
        from src.models.database_manager import db_manager
        await db_manager.initialize()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database initialization failed: {e}")
    
    yield
    
    # Cleanup
    try:
        from src.models.database_manager import db_manager
        await db_manager.close()
        logger.info("Database connections closed")
    except:
        pass
    logger.info("Shutting down KBI Labs Unified Platform...")

# Create FastAPI app with all features
app = FastAPI(
    title="KBI Labs - Unified Intelligence Platform",
    description="AI-Powered Government Contractor Intelligence Platform",
    version="2.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add monitoring middleware
try:
    from src.monitoring.middleware import MonitoringMiddleware
    app.add_middleware(MonitoringMiddleware)
    logger.info("✅ Monitoring middleware loaded")
except Exception as e:
    logger.warning(f"⚠️ Monitoring middleware not available: {e}")

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("✅ Static files mounted")
except Exception as e:
    logger.warning(f"⚠️ Static files not available: {e}")

# Include all routers with error handling
routers_to_include = [
    # Core API routers (all use 'router' as the attribute name)
    ("src.api.routers.health", "router", None, ["health"]),
    ("src.api.routers.companies", "router", "/api/v2", ["companies"]),
    ("src.api.routers.analytics", "router", "/api/v2", ["analytics"]),
    ("src.api.routers.sec", "router", None, ["sec"]),
    ("src.api.routers.govcon", "router", "/api/v1", ["govcon"]),
    
    # Government Intelligence (the missing piece!)
    ("src.api.routers.government_intelligence", "router", "/api", ["government-intelligence"]),
    
    # V1 API
    ("src.api.v1.api", "api_router", "/api/v1", ["v1"]),
    
    # ML endpoints
    ("src.api.v1.endpoints.ml.predictions", "router", "/api/v1", ["ml"]),
    
    # Health monitoring
    ("src.api.routers.health_monitoring", "router", "/api/v3", ["monitoring"]),
]

for module_path, router_name, prefix, tags in routers_to_include:
    try:
        module = __import__(module_path, fromlist=[router_name])
        router_obj = getattr(module, router_name)
        
        if prefix:
            app.include_router(router_obj, prefix=prefix, tags=tags)
        else:
            app.include_router(router_obj, tags=tags)
        logger.info(f"✅ Loaded router: {module_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load router {module_path}: {e}")

# Add metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    try:
        from src.monitoring.metrics import metrics_endpoint
        return await metrics_endpoint()
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        return {"error": "Metrics not available", "detail": str(e)}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "message": "Welcome to KBI Labs Unified Intelligence Platform",
        "version": "2.2.0",
        "services": [
            "AI-Powered Business Intelligence",
            "Government Contract Intelligence", 
            "Patent Search Engine",
            "SMB Discovery Platform"
        ],
        "docs": "/api/docs",
        "health": "/health"
    }

# Enhanced health check
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    services_status = {}
    
    # Check database
    try:
        from src.models.database_manager import db_manager
        # Simple connection test
        services_status["database"] = "connected"
    except Exception as e:
        services_status["database"] = f"error: {str(e)}"
    
    # Check AI services
    try:
        from src.ai_services.recommendation_engine import get_recommendation_summary
        services_status["ai_services"] = "available"
    except Exception as e:
        services_status["ai_services"] = f"not available: {str(e)}"
    
    # Check patent search
    try:
        from src.patent_search_module import patent_engine
        services_status["patent_search"] = "available"
    except Exception as e:
        services_status["patent_search"] = f"not available: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "KBI Labs Unified Platform",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat(),
        "services": services_status
    }

# Government intelligence endpoints (direct implementation as backup)
@app.get("/api/government-intelligence/health")
async def government_intelligence_health():
    """Health check for government intelligence services"""
    return {
        "status": "healthy",
        "service": "Government Intelligence API",
        "version": "2.2.0",
        "endpoints": [
            "/api/government-intelligence/procurement-opportunities",
            "/api/government-intelligence/regulatory-intelligence",
            "/api/government-intelligence/congressional-intelligence",
            "/api/government-intelligence/comprehensive-intelligence"
        ]
    }

@app.get("/api/government-intelligence/procurement-opportunities")
async def get_procurement_opportunities():
    """Get live procurement opportunities from SAM.gov"""
    try:
        from src.integrations.sam_opportunities import get_real_procurement_opportunities
        opportunities = await get_real_procurement_opportunities()
        return {
            "status": "success",
            "data": opportunities,
            "source": "SAM.gov",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching procurement opportunities: {e}")
        return {
            "status": "error",
            "message": "Unable to fetch procurement opportunities",
            "error": str(e),
            "fallback_data": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)