#!/usr/bin/env python3
"""Minimal KBI Labs API with monitoring"""
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import sys
import os
import time
import psutil

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our routers
from src.api.routers import enrichment

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

app = FastAPI(
    title="KBI Labs API (Minimal with Monitoring)",
    version="1.0.0",
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

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Add basic health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KBI Labs API"}

# Add detailed health check
@app.get("/api/v3/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "service": "KBI Labs API",
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }

# Include the enrichment router
app.include_router(enrichment.router, prefix="/api/v3/enrichment", tags=["enrichment"])

# Middleware to track requests
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
