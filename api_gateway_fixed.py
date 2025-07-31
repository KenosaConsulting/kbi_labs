#!/usr/bin/env python3
"""
Unified API Gateway for KBI Labs - Fixed Version
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import os

# Models
from pydantic import BaseModel, Field
from enum import Enum

# Monitoring
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
API_LATENCY = Histogram('api_request_duration_seconds', 'API request latency', ['method', 'endpoint'])


# ====================== Models ======================

class CompanyBase(BaseModel):
    uei: str = Field(..., description="Unique Entity Identifier")
    organization_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: Optional[int] = None
    pe_investment_score: Optional[float] = None
    business_health_grade: Optional[str] = None
    innovation_score: Optional[float] = None
    growth_potential_score: Optional[float] = None
    last_enriched_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EnrichmentRequest(BaseModel):
    uei: str
    company_name: str
    enrichment_sources: Optional[List[str]] = ["sam_gov", "usaspending", "patents"]
    priority: str = "normal"


# ====================== Simple Database Manager ======================

class SimpleDatabaseManager:
    """Simple database manager for testing"""
    
    def __init__(self):
        self.initialized = False
        
    async def initialize(self):
        """Initialize database connection"""
        self.initialized = True
        logger.info("Database manager initialized (mock)")
        
    async def health_check(self):
        """Simple health check"""
        return {"status": "healthy", "mock": True}
        
    async def close(self):
        """Close connections"""
        logger.info("Database connections closed (mock)")

# Create instance
db_manager = SimpleDatabaseManager()


# ====================== Simple Kafka Manager ======================

class SimpleKafkaManager:
    """Simple Kafka manager for testing"""
    
    def __init__(self):
        self.initialized = False
        
    def initialize(self):
        """Initialize Kafka connection"""
        try:
            from kafka import KafkaProducer
            self.producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.initialized = True
            logger.info("Kafka manager initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kafka: {e}")
            return False
            
    def send_enrichment_request(self, request: EnrichmentRequest):
        """Send enrichment request"""
        try:
            if hasattr(self, 'producer'):
                self.producer.send('company-enrichment', value=request.dict())
                return True
        except:
            pass
        return False
        
    def health_check(self):
        """Simple health check"""
        return {"status": "healthy" if self.initialized else "unhealthy"}
        
    def close(self):
        """Close connections"""
        if hasattr(self, 'producer'):
            self.producer.close()


# ====================== Application ======================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting KBI Labs API Gateway...")
    
    # Initialize database
    await db_manager.initialize()
    
    # Initialize Kafka
    app.state.kafka = SimpleKafkaManager()
    app.state.kafka.initialize()
    
    logger.info("All services initialized")
    
    yield
    
    # Cleanup
    await db_manager.close()
    app.state.kafka.close()
    logger.info("Shutting down KBI Labs API Gateway...")


app = FastAPI(
    title="KBI Labs API Gateway",
    description="Unified API for predictive analytics and business intelligence",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ====================== Health Endpoints ======================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to KBI Labs API Gateway",
        "version": "3.0.0",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "KBI Labs API Gateway",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check"""
    db_health = await db_manager.health_check()
    kafka_health = app.state.kafka.health_check()
    
    # Test actual connections
    redis_ok = False
    postgres_ok = False
    kafka_ok = kafka_health["status"] == "healthy"
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        redis_ok = True
    except:
        pass
        
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='kbi_labs',
            user='kbi_user',
            password=os.getenv('POSTGRES_PASSWORD', 'change-this-password')
        )
        conn.close()
        postgres_ok = True
    except:
        pass
    
    return {
        "status": "healthy" if all([redis_ok, postgres_ok, kafka_ok]) else "degraded",
        "services": {
            "database": {"postgres": postgres_ok, "mock": True},
            "kafka": kafka_health,
            "redis": redis_ok
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ====================== Company Endpoints ======================

@app.get("/api/v3/companies")
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    state: Optional[str] = None
):
    """List companies - mock implementation"""
    mock_companies = [
        {
            "uei": "TEST123456789",
            "organization_name": "Test Corp Alpha",
            "city": "San Francisco",
            "state": "CA",
            "pe_investment_score": 85.5,
            "business_health_grade": "A"
        },
        {
            "uei": "TEST987654321",
            "organization_name": "Test Corp Beta",
            "city": "New York",
            "state": "NY",
            "pe_investment_score": 92.3,
            "business_health_grade": "A+"
        }
    ]
    
    # Filter by state if provided
    if state:
        mock_companies = [c for c in mock_companies if c.get("state") == state]
    
    return mock_companies[skip:skip+limit]

@app.get("/api/v3/companies/{uei}")
async def get_company(uei: str):
    """Get company by UEI"""
    if uei == "TEST123456789":
        return {
            "uei": "TEST123456789",
            "organization_name": "Test Corp Alpha",
            "city": "San Francisco",
            "state": "CA",
            "pe_investment_score": 85.5,
            "business_health_grade": "A",
            "innovation_score": 78.2,
            "growth_potential_score": 81.0
        }
    else:
        raise HTTPException(status_code=404, detail="Company not found")


# ====================== Enrichment Endpoints ======================

@app.post("/api/v3/enrichment/enrich")
async def enrich_company(request: EnrichmentRequest):
    """Trigger company enrichment"""
    success = app.state.kafka.send_enrichment_request(request)
    
    if success:
        return {
            "status": "queued",
            "request_id": f"req_{datetime.utcnow().timestamp()}",
            "message": "Enrichment request queued successfully"
        }
    else:
        return {
            "status": "mock_mode",
            "message": "Running in mock mode - enrichment simulated"
        }


# ====================== Analytics Endpoints ======================

@app.get("/api/v3/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard - mock data"""
    return {
        "total_companies": 54799,
        "enriched_companies": 12543,
        "top_states": [
            {"state": "CA", "count": 8234},
            {"state": "TX", "count": 6521},
            {"state": "NY", "count": 5123}
        ],
        "grade_distribution": {
            "A+": 2341,
            "A": 5432,
            "B": 8765,
            "C": 3210
        },
        "avg_scores": {
            "pe_score": 72.5,
            "innovation_score": 68.3,
            "growth_score": 74.1
        }
    }


# ====================== Test Endpoints ======================

@app.get("/api/test/services")
async def test_services():
    """Test all service connections"""
    results = {}
    
    # Test Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        results["redis"] = "✅ Connected"
    except Exception as e:
        results["redis"] = f"❌ {str(e)}"
    
    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='kbi_labs',
            user='kbi_user',
            password=os.getenv('POSTGRES_PASSWORD', 'change-this-password')
        )
        conn.close()
        results["postgresql"] = "✅ Connected"
    except Exception as e:
        results["postgresql"] = f"❌ {str(e)}"
    
    # Test Kafka
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
        producer.close()
        results["kafka"] = "✅ Connected"
    except Exception as e:
        results["kafka"] = f"❌ {str(e)}"
    
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
