"""Main API Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.api.routers import companies, analytics, health, sec, govcon
from src.models.database_manager import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting KBI Labs API Gateway...")
    # Initialize database
    await db_manager.initialize()
    yield
    # Cleanup
    await db_manager.close()
    logger.info("Shutting down KBI Labs API Gateway...")
from src.monitoring.metrics import metrics_endpoint
from src.monitoring.middleware import MonitoringMiddleware
from src.api.routers import health_monitoring


# Create FastAPI app
app = FastAPI(
    title="KBI Labs API",
    description="Enterprise Intelligence Platform API",
    version="2.0.1",
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
app.add_middleware(MonitoringMiddleware)

# Add metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return await metrics_endpoint()

# Include health monitoring router
app.include_router(health_monitoring.router, prefix="/api/v3", tags=["monitoring"])

# Include routers
app.include_router(health.router)
app.include_router(companies.router, prefix="/api/v2")
app.include_router(analytics.router, prefix="/api/v2")
app.include_router(sec.router)
app.include_router(govcon.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to KBI Labs API",
        "version": "2.0.0",
        "docs": "/api/docs"
    }

# Health check at root level
@app.get("/health/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "KBI Labs API Gateway",
        "database": "connected"
    }
