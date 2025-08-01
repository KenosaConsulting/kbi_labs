#!/usr/bin/env python3
"""KBI Labs API with USASpending Integration"""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import psutil
import logging
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import routers
from src.api.routers import usaspending

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# USASpending specific metrics
usaspending_requests_total = Counter(
    'usaspending_requests_total',
    'Total USASpending API requests',
    ['endpoint', 'status']
)

usaspending_request_duration_seconds = Histogram(
    'usaspending_request_duration_seconds',
    'USASpending API request duration',
    ['endpoint']
)

# System metrics
cpu_usage_percent = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage_percent = Gauge('memory_usage_percent', 'Memory usage percentage')

app = FastAPI(
    title="KBI Labs API with USASpending",
    version="2.0.0",
    docs_url="/docs"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task to update system metrics
async def update_system_metrics():
    while True:
        cpu_usage_percent.set(psutil.cpu_percent(interval=1))
        memory = psutil.virtual_memory()
        memory_usage_percent.set(memory.percent)
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_system_metrics())

# Include routers
app.include_router(usaspending.router, prefix="/api/v3/usaspending", tags=["usaspending"])

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Health endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KBI Labs API", "version": "2.0.0"}

@app.get("/api/v3/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "service": "KBI Labs API",
        "version": "2.0.0",
        "features": ["enrichment", "usaspending"],
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }

# Original enrichment endpoints
@app.get("/api/v3/enrichment/health")
async def enrichment_health():
    return {"status": "healthy", "service": "enrichment"}

@app.post("/api/v3/enrichment/enrich")
async def enrich_company(data: dict):
    uei = data.get("uei")
    # Now also check USASpending
    return {
        "status": "success",
        "uei": uei,
        "message": "Enrichment available - use /api/v3/usaspending/search/{uei} for federal spending data"
    }

# Middleware to track requests
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Track metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    # Track USASpending specific metrics
    if "usaspending" in request.url.path:
        usaspending_requests_total.labels(
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        usaspending_request_duration_seconds.labels(
            endpoint=request.url.path
        ).observe(duration)
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
