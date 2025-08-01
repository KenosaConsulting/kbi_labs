#!/usr/bin/env python3
"""KBI Labs API with monitoring and all routes"""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import psutil
import logging

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

app = FastAPI(
    title="KBI Labs API with Monitoring",
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

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Health endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KBI Labs API"}

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

# Enrichment endpoints (simplified for now)
@app.get("/api/v3/enrichment/health")
async def enrichment_health():
    return {"status": "healthy", "service": "enrichment"}

@app.post("/api/v3/enrichment/enrich")
async def enrich_company(data: dict):
    uei = data.get("uei")
    return {
        "status": "company_not_found",
        "uei": uei,
        "message": "Company not found in database (this is a test response)"
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
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
