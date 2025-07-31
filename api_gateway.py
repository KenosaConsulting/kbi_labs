#!/usr/bin/env python3
"""
Unified API Gateway for KBI Labs
Consolidates all API endpoints with proper structure
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json

# Models
from pydantic import BaseModel, Field
from enum import Enum

# Infrastructure
from database_manager import db_manager
from kafka_infrastructure import KafkaInfrastructure, EnrichmentRequest, AnalyticsEvent
from streaming_pipeline import RealTimeScoring

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

class CompanyCreate(CompanyBase):
    annual_revenue: Optional[float] = None
    federal_contracts_value: Optional[float] = None
    website: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: int
    pe_investment_score: Optional[float] = None
    business_health_grade: Optional[str] = None
    innovation_score: Optional[float] = None
    growth_potential_score: Optional[float] = None
    last_enriched_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EnrichmentRequestModel(BaseModel):
    uei: str
    company_name: str
    enrichment_sources: Optional[List[str]] = ["sam_gov", "usaspending", "patents"]
    priority: str = "normal"

class AnalyticsRequest(BaseModel):
    entity_id: str
    metrics: List[str] = ["all"]
    time_range: Optional[str] = "30d"

class PredictionRequest(BaseModel):
    uei: str
    prediction_types: List[str] = ["revenue", "growth", "risk"]
    horizon_months: int = 12

class SearchFilters(BaseModel):
    state: Optional[str] = None
    min_pe_score: Optional[float] = None
    max_pe_score: Optional[float] = None
    business_health_grade: Optional[str] = None
    min_revenue: Optional[float] = None
    max_revenue: Optional[float] = None
    has_federal_contracts: Optional[bool] = None
    industry_naics: Optional[str] = None


# ====================== Application ======================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting KBI Labs API Gateway...")
    
    # Initialize database
    await db_manager.initialize()
    
    # Initialize Kafka
    app.state.kafka = KafkaInfrastructure()
    app.state.kafka.initialize()
    
    # Initialize scoring engine
    app.state.scoring = RealTimeScoring()
    
    logger.info("All services initialized successfully")
    
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
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ====================== Middleware ======================

@app.middleware("http")
async def track_metrics(request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    duration = time.time() - start_time
    
    API_REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    API_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response


# ====================== Health & Monitoring ======================

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
    
    return {
        "status": "healthy",
        "services": {
            "database": db_health,
            "kafka": kafka_health
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ====================== Company Endpoints ======================

@app.get("/api/v3/companies", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    filters: SearchFilters = Depends()
):
    """List companies with filtering and pagination"""
    query = """
    SELECT * FROM companies WHERE 1=1
    """
    params = []
    param_count = 1
    
    # Build dynamic query based on filters
    if filters.state:
        query += f" AND state = ${param_count}"
        params.append(filters.state)
        param_count += 1
    
    if filters.min_pe_score is not None:
        query += f" AND pe_investment_score >= ${param_count}"
        params.append(filters.min_pe_score)
        param_count += 1
    
    if filters.max_pe_score is not None:
        query += f" AND pe_investment_score <= ${param_count}"
        params.append(filters.max_pe_score)
        param_count += 1
    
    if filters.business_health_grade:
        query += f" AND business_health_grade = ${param_count}"
        params.append(filters.business_health_grade)
        param_count += 1
    
    # Add ordering and pagination
    query += f" ORDER BY pe_investment_score DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
    params.extend([limit, skip])
    
    companies = await db_manager.execute_query(query, tuple(params))
    return companies

@app.get("/api/v3/companies/{uei}", response_model=CompanyResponse)
async def get_company(uei: str, background_tasks: BackgroundTasks):
    """Get company by UEI"""
    query = "SELECT * FROM companies WHERE uei = $1"
    result = await db_manager.execute_query(query, (uei,))
    
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = result[0]
    
    # Track analytics event
    event = AnalyticsEvent(
        event_type="company_viewed",
        entity_id=uei,
        data={"source": "api", "endpoint": f"/companies/{uei}"}
    )
    background_tasks.add_task(app.state.kafka.send_analytics_event, event)
    
    return company

@app.post("/api/v3/companies", response_model=CompanyResponse)
async def create_company(company: CompanyCreate):
    """Create new company"""
    success = await db_manager.upsert_company(company.dict())
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create company")
    
    # Trigger enrichment
    enrichment_req = EnrichmentRequest(
        uei=company.uei,
        company_name=company.organization_name,
        priority="high"
    )
    app.state.kafka.send_enrichment_request(enrichment_req)
    
    return await get_company(company.uei)


# ====================== Enrichment Endpoints ======================

@app.post("/api/v3/enrichment/enrich")
async def enrich_company(request: EnrichmentRequestModel):
    """Trigger company enrichment"""
    enrichment_req = EnrichmentRequest(**request.dict())
    
    success = app.state.kafka.send_enrichment_request(enrichment_req)
    
    if success:
        return {
            "status": "queued",
            "request_id": enrichment_req.request_id,
            "message": "Enrichment request queued successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to queue enrichment request")

@app.get("/api/v3/enrichment/status/{request_id}")
async def get_enrichment_status(request_id: str):
    """Get enrichment request status"""
    status = app.state.kafka.redis_client.get(f"enrichment:status:{request_id}")
    
    if not status:
        raise HTTPException(status_code=404, detail="Enrichment request not found")
    
    return JSONResponse(content=json.loads(status))

@app.post("/api/v3/enrichment/batch")
async def batch_enrichment(ueis: List[str]):
    """Trigger batch enrichment for multiple companies"""
    queued = 0
    
    for uei in ueis:
        # Get company info
        query = "SELECT organization_name FROM companies WHERE uei = $1"
        result = await db_manager.execute_query(query, (uei,))
        
        if result:
            enrichment_req = EnrichmentRequest(
                uei=uei,
                company_name=result[0]['organization_name']
            )
            if app.state.kafka.send_enrichment_request(enrichment_req):
                queued += 1
    
    return {
        "status": "success",
        "queued": queued,
        "total": len(ueis)
    }


# ====================== Analytics Endpoints ======================

@app.post("/api/v3/analytics/company")
async def get_company_analytics(request: AnalyticsRequest):
    """Get analytics for a specific company"""
    # Get real-time scores
    query = "SELECT * FROM companies WHERE uei = $1"
    result = await db_manager.execute_query(query, (request.entity_id,))
    
    if not result:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = result[0]
    
    # Calculate real-time scores
    scores = app.state.scoring.score_company(company)
    
    # Get historical metrics
    analytics = {
        "uei": request.entity_id,
        "current_scores": scores,
        "metrics": await self._get_company_metrics(request.entity_id, request.time_range),
        "peer_comparison": await self._get_peer_comparison(company),
        "growth_trajectory": await self._calculate_growth_trajectory(company),
        "risk_assessment": await self._perform_risk_assessment(company)
    }
    
    return analytics

@app.get("/api/v3/analytics/dashboard")
async def get_analytics_dashboard():
    """Get overall analytics dashboard"""
    summary = await db_manager.get_analytics_summary()
    
    # Add real-time metrics
    summary['real_time'] = {
        'active_enrichments': app.state.kafka.redis_client.dbsize(),
        'kafka_topics': app.state.kafka.get_topic_stats()
    }
    
    return summary

@app.get("/api/v3/analytics/trends")
async def get_market_trends(
    state: Optional[str] = None,
    industry: Optional[str] = None,
    days: int = Query(30, ge=1, le=365)
):
    """Get market trends and insights"""
    # This would connect to your time-series database
    trends = {
        "period": f"last_{days}_days",
        "filters": {
            "state": state,
            "industry": industry
        },
        "metrics": {
            "new_companies": 145,
            "avg_pe_score_change": 2.3,
            "top_growing_industries": [
                {"naics": "541512", "name": "Computer Systems Design", "growth": 15.2},
                {"naics": "541511", "name": "Custom Computer Programming", "growth": 12.8}
            ],
            "investment_opportunities": 28
        }
    }
    
    return trends


# ====================== Predictive Analytics ======================

@app.post("/api/v3/predictions/company")
async def get_company_predictions(request: PredictionRequest):
    """Get ML predictions for a company"""
    # This would call your ML models
    predictions = {
        "uei": request.uei,
        "horizon_months": request.horizon_months,
        "predictions": {},
        "confidence_intervals": {},
        "model_version": "2.1.0"
    }
    
    if "revenue" in request.prediction_types:
        predictions["predictions"]["revenue"] = {
            "current": 5000000,
            "predicted": 6500000,
            "growth_rate": 30.0,
            "confidence": 0.85
        }
    
    if "growth" in request.prediction_types:
        predictions["predictions"]["growth"] = {
            "employee_growth": 25.0,
            "market_share_growth": 2.5,
            "overall_growth_score": 82.0
        }
    
    if "risk" in request.prediction_types:
        predictions["predictions"]["risk"] = {
            "financial_risk": "low",
            "operational_risk": "medium",
            "market_risk": "low",
            "overall_risk_score": 28.0
        }
    
    return predictions

@app.post("/api/v3/predictions/simulate")
async def run_simulation(
    uei: str,
    scenarios: List[Dict[str, Any]],
    monte_carlo_runs: int = Query(1000, ge=100, le=10000)
):
    """Run Monte Carlo simulations for business scenarios"""
    # This would run actual simulations
    results = {
        "uei": uei,
        "scenarios_evaluated": len(scenarios),
        "monte_carlo_runs": monte_carlo_runs,
        "results": []
    }
    
    for scenario in scenarios:
        result = {
            "scenario_name": scenario.get("name", "Unnamed"),
            "probability_of_success": 0.73,
            "expected_value": 2500000,
            "value_at_risk_95": -500000,
            "best_case": 5000000,
            "worst_case": -1000000
        }
        results["results"].append(result)
    
    return results


# ====================== Reports & Visualizations ======================

@app.post("/api/v3/reports/generate")
async def generate_report(
    report_type: str,
    entity_ids: List[str],
    include_predictions: bool = True,
    format: str = Query("pdf", regex="^(pdf|html|json)$")
):
    """Generate decision-grade reports"""
    # Queue report generation
    report_id = f"report_{datetime.utcnow().timestamp()}"
    
    return {
        "report_id": report_id,
        "status": "generating",
        "estimated_time_seconds": 30,
        "download_url": f"/api/v3/reports/download/{report_id}"
    }

@app.get("/api/v3/visualizations/data")
async def get_visualization_data(
    chart_type: str,
    entity_ids: Optional[List[str]] = Query(None),
    metrics: List[str] = Query(["pe_score", "innovation_score"])
):
    """Get data formatted for visualizations"""
    # This would return data optimized for your frontend charts
    return {
        "chart_type": chart_type,
        "data": {
            "labels": ["Q1", "Q2", "Q3", "Q4"],
            "datasets": [
                {
                    "label": metric,
                    "data": [65, 70, 75, 82]
                }
                for metric in metrics
            ]
        }
    }


# ====================== Market Intelligence ======================

@app.get("/api/v3/market/opportunities")
async def find_market_opportunities(
    min_score: float = Query(70.0, ge=0, le=100),
    states: Optional[List[str]] = Query(None),
    industries: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """Find high-value market opportunities"""
    query = """
    SELECT c.*, 
           COUNT(eh.id) as enrichment_count,
           MAX(eh.created_at) as last_analysis
    FROM companies c
    LEFT JOIN enrichment_history eh ON c.uei = eh.uei
    WHERE c.pe_investment_score >= $1
    """
    
    params = [min_score]
    param_count = 2
    
    if states:
        query += f" AND c.state = ANY(${param_count})"
        params.append(states)
        param_count += 1
    
    query += """
    GROUP BY c.id
    ORDER BY c.pe_investment_score DESC, enrichment_count DESC
    LIMIT ${}
    """.format(param_count)
    params.append(limit)
    
    opportunities = await db_manager.execute_query(query, tuple(params))
    
    return {
        "total_found": len(opportunities),
        "opportunities": opportunities,
        "market_insights": {
            "avg_score": sum(o['pe_investment_score'] for o in opportunities) / len(opportunities) if opportunities else 0,
            "top_states": list(set(o['state'] for o in opportunities if o.get('state')))[:5]
        }
    }


# ====================== Helper Functions ======================

async def _get_company_metrics(uei: str, time_range: str) -> Dict[str, Any]:
    """Get company metrics for specified time range"""
    # Implement actual metrics retrieval
    return {
        "revenue_growth": 15.2,
        "contract_win_rate": 0.65,
        "innovation_index": 78.5,
        "market_share": 2.3
    }

async def _get_peer_comparison(company: Dict[str, Any]) -> Dict[str, Any]:
    """Compare company against peers"""
    # Implement peer comparison logic
    return {
        "peer_group_size": 145,
        "percentile_rank": 85,
        "strengths": ["innovation", "federal_presence"],
        "improvement_areas": ["market_expansion"]
    }

async def _calculate_growth_trajectory(company: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate growth trajectory"""
    return {
        "current_trajectory": "accelerating",
        "growth_rate": 22.5,
        "sustainability_score": 0.78
    }

async def _perform_risk_assessment(company: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive risk assessment"""
    return {
        "overall_risk": "medium",
        "risk_factors": {
            "market": "low",
            "financial": "medium",
            "operational": "low",
            "regulatory": "medium"
        },
        "mitigation_recommendations": [
            "Diversify revenue streams",
            "Strengthen cash reserves"
        ]
    }


# ====================== Admin Endpoints ======================

@app.post("/api/v3/admin/reindex")
async def trigger_reindex(background_tasks: BackgroundTasks):
    """Trigger database reindexing"""
    background_tasks.add_task(db_manager.create_indexes)
    background_tasks.add_task(db_manager.optimize_database)
    
    return {"status": "reindexing started", "message": "Database optimization in progress"}

@app.post("/api/v3/admin/migrate")
async def migrate_from_sqlite(
    sqlite_path: str = Query("kbi_production.db"),
    background_tasks: BackgroundTasks = None
):
    """Migrate data from SQLite to PostgreSQL"""
    background_tasks.add_task(db_manager.migrate_from_sqlite, sqlite_path)
    
    return {"status": "migration started", "message": "Data migration in progress"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
