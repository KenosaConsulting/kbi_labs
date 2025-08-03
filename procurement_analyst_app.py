#!/usr/bin/env python3
"""
KBI Labs Procurement Analyst Platform - Main Application
Professional-grade procurement intelligence platform for government contractors
"""

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os
import json
import asyncio
from dataclasses import dataclass
import uuid

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KBI Labs Procurement Analyst Platform",
    description="AI-Powered Government Procurement Intelligence Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class OpportunityFilter(BaseModel):
    """Filters for opportunity search"""
    agencies: Optional[List[str]] = None
    naics_codes: Optional[List[str]] = None
    set_aside_types: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    states: Optional[List[str]] = None
    keywords: Optional[str] = None
    posted_after: Optional[datetime] = None

class OpportunityScore(BaseModel):
    """AI-generated opportunity scoring"""
    opportunity_id: str
    win_probability: float = Field(..., ge=0, le=1)
    confidence_level: str = Field(..., pattern="High|Medium|Low")
    competitive_score: float = Field(..., ge=0, le=100)
    strategic_fit: float = Field(..., ge=0, le=100)
    risk_assessment: str = Field(..., pattern="Low|Medium|High")
    recommended_action: str

class CompanyProfile(BaseModel):
    """Company profile for analysis"""
    company_name: str
    uei: Optional[str] = None
    duns: Optional[str] = None
    naics_codes: List[str] = []
    capabilities: List[str] = []
    past_performance: Dict[str, Any] = {}
    certifications: List[str] = []
    team_size: Optional[int] = None
    revenue_range: Optional[str] = None

class ProcurementOpportunity(BaseModel):
    """Government procurement opportunity"""
    id: str
    title: str
    description: str
    agency: str
    sub_agency: Optional[str] = None
    posted_date: datetime
    response_deadline: datetime
    estimated_value: Optional[float] = None
    naics_code: Optional[str] = None
    set_aside_type: Optional[str] = None
    place_of_performance: Optional[str] = None
    solicitation_number: str
    point_of_contact: Optional[Dict[str, str]] = None
    attachments: List[Dict[str, str]] = []
    
    # AI Analysis Results
    ai_score: Optional[OpportunityScore] = None
    competitive_analysis: Optional[Dict[str, Any]] = None
    market_intelligence: Optional[Dict[str, Any]] = None

class AnalysisRequest(BaseModel):
    """Request for AI analysis"""
    opportunity_id: str
    company_profile: CompanyProfile
    analysis_type: str = Field(..., pattern="quick|standard|deep")
    include_competitive: bool = True
    include_market_intel: bool = True

class DashboardMetrics(BaseModel):
    """Dashboard metrics and KPIs"""
    total_opportunities: int
    active_pursuits: int
    pipeline_value: float
    win_rate: float
    avg_opportunity_value: float
    upcoming_deadlines: int
    recent_wins: int
    market_trends: Dict[str, Any]

# In-memory data stores (replace with actual database in production)
opportunities_db = {}
companies_db = {}
analysis_cache = {}
user_pipelines = {}

# Mock data for demonstration
def initialize_mock_data():
    """Initialize sample data for demonstration"""
    
    # Sample opportunities
    sample_opportunities = [
        {
            "id": "DOD-2024-001",
            "title": "Advanced Cybersecurity Solutions for Defense Networks",
            "description": "The Department of Defense seeks comprehensive cybersecurity solutions...",
            "agency": "Department of Defense",
            "sub_agency": "Defense Information Systems Agency",
            "posted_date": datetime.now() - timedelta(days=2),
            "response_deadline": datetime.now() + timedelta(days=28),
            "estimated_value": 15000000.0,
            "naics_code": "541512",
            "set_aside_type": "Small Business",
            "place_of_performance": "Virginia",
            "solicitation_number": "HQ0034-24-R-0001"
        },
        {
            "id": "NASA-2024-002", 
            "title": "Satellite Data Analysis and Processing Services",
            "description": "NASA requires advanced data processing capabilities...",
            "agency": "National Aeronautics and Space Administration",
            "sub_agency": "Goddard Space Flight Center",
            "posted_date": datetime.now() - timedelta(days=1),
            "response_deadline": datetime.now() + timedelta(days=35),
            "estimated_value": 8500000.0,
            "naics_code": "541511",
            "set_aside_type": "Unrestricted",
            "place_of_performance": "Maryland",
            "solicitation_number": "GSFC-24-001"
        },
        {
            "id": "DHS-2024-003",
            "title": "Border Security Technology Integration",
            "description": "Department of Homeland Security needs integrated technology solutions...",
            "agency": "Department of Homeland Security",
            "sub_agency": "Customs and Border Protection",
            "posted_date": datetime.now() - timedelta(days=5),
            "response_deadline": datetime.now() + timedelta(days=21),
            "estimated_value": 25000000.0,
            "naics_code": "541330",
            "set_aside_type": "8(a)",
            "place_of_performance": "Texas",
            "solicitation_number": "CBP-2024-001"
        }
    ]
    
    for opp_data in sample_opportunities:
        opp = ProcurementOpportunity(**opp_data)
        opportunities_db[opp.id] = opp
    
    logger.info(f"Initialized {len(sample_opportunities)} sample opportunities")

# Initialize mock data on startup
initialize_mock_data()

# Data pipeline integration
from procurement_data_pipeline import initialize_pipeline, data_pipeline

@app.on_event("startup")
async def startup_event():
    """Initialize data pipeline on startup"""
    global data_pipeline
    data_pipeline = await initialize_pipeline()
    logger.info("Procurement Analyst Platform started successfully")

# Core Services

class ProcurementAnalysisService:
    """Core service for procurement analysis and intelligence"""
    
    def __init__(self):
        self.ml_models = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for analysis"""
        try:
            from quick_start_ml_prototype import KBIProcurementMLPrototype
            self.ml_models = KBIProcurementMLPrototype()
            self.ml_models.load_models()
            logger.info("ML models loaded successfully")
        except Exception as e:
            logger.warning(f"ML models not available: {e}")
            self.ml_models = None
    
    async def analyze_opportunity(self, opportunity: ProcurementOpportunity, 
                                company: CompanyProfile, analysis_type: str = "standard") -> OpportunityScore:
        """Analyze an opportunity for a specific company"""
        
        # Calculate base scores
        strategic_fit = self._calculate_strategic_fit(opportunity, company)
        competitive_score = self._calculate_competitive_score(opportunity)
        
        # Use ML models if available
        win_probability = 0.5  # Default
        if self.ml_models:
            try:
                # Prepare data for ML model
                ml_data = {
                    'procurement_intelligence_score': strategic_fit,
                    'gsa_calc_found': 'GSA' in company.certifications,
                    'fpds_found': len(company.past_performance) > 0,
                    'sam_opportunities_found': True,
                    'sam_entity_found': company.uei is not None,
                    'gsa_avg_rate': 150.0,
                    'fpds_total_value': sum(company.past_performance.values()) if company.past_performance else 0,
                    'fpds_total_contracts': len(company.past_performance),
                    'sam_total_matches': 5,
                    'agency_diversity': 3,
                    'contractor_network_size': company.team_size or 10,
                    'years_in_business': 10,
                    'small_business': 'Small Business' in company.certifications,
                    'veteran_owned': 'VOSB' in company.certifications,
                    'woman_owned': 'WOSB' in company.certifications,
                    'state': 'VA',
                    'primary_naics': int(opportunity.naics_code) if opportunity.naics_code else 541511
                }
                
                prediction = self.ml_models.predict_contract_success(ml_data)
                win_probability = prediction['success_probability']
                
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
        
        # Determine confidence and risk
        confidence = "High" if abs(win_probability - 0.5) > 0.3 else "Medium" if abs(win_probability - 0.5) > 0.15 else "Low"
        risk = "Low" if win_probability > 0.7 else "Medium" if win_probability > 0.4 else "High"
        
        # Generate recommendation
        if win_probability > 0.7:
            recommendation = "Pursue Actively - High probability of success"
        elif win_probability > 0.4:
            recommendation = "Consider Carefully - Moderate probability with strategic value"
        else:
            recommendation = "Monitor Only - Low probability, consider team partnerships"
        
        return OpportunityScore(
            opportunity_id=opportunity.id,
            win_probability=win_probability,
            confidence_level=confidence,
            competitive_score=competitive_score,
            strategic_fit=strategic_fit,
            risk_assessment=risk,
            recommended_action=recommendation
        )
    
    def _calculate_strategic_fit(self, opportunity: ProcurementOpportunity, company: CompanyProfile) -> float:
        """Calculate strategic fit score"""
        score = 50.0  # Base score
        
        # NAICS alignment
        if opportunity.naics_code in company.naics_codes:
            score += 20.0
        
        # Capability match (simplified)
        relevant_keywords = ['cybersecurity', 'data', 'technology', 'software', 'analysis']
        opp_text = f"{opportunity.title} {opportunity.description}".lower()
        
        for capability in company.capabilities:
            if any(keyword in capability.lower() for keyword in relevant_keywords):
                if any(keyword in opp_text for keyword in relevant_keywords):
                    score += 10.0
        
        # Past performance
        if company.past_performance and len(company.past_performance) > 0:
            score += 15.0
        
        # Certifications
        if opportunity.set_aside_type and opportunity.set_aside_type in company.certifications:
            score += 15.0
        
        return min(score, 100.0)
    
    def _calculate_competitive_score(self, opportunity: ProcurementOpportunity) -> float:
        """Calculate competitive landscape score"""
        # Simplified competitive analysis
        base_score = 60.0
        
        # Adjust based on opportunity characteristics
        if opportunity.set_aside_type == "Small Business":
            base_score += 10.0
        elif opportunity.set_aside_type in ["8(a)", "HUBZone", "WOSB", "VOSB"]:
            base_score += 20.0
        
        # Value-based adjustment
        if opportunity.estimated_value and opportunity.estimated_value < 1000000:
            base_score += 15.0  # Less competition for smaller contracts
        elif opportunity.estimated_value and opportunity.estimated_value > 10000000:
            base_score -= 10.0  # More competition for larger contracts
        
        return min(base_score, 100.0)

# Initialize services
analysis_service = ProcurementAnalysisService()

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main application landing page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>KBI Labs Procurement Analyst Platform</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .nav { display: flex; gap: 20px; margin-top: 20px; }
            .nav a { background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 500; }
            .nav a:hover { background: #1d4ed8; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
            .feature { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .feature h3 { color: #1f2937; margin-top: 0; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 30px 0; }
            .stat { background: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .stat-value { font-size: 2em; font-weight: bold; color: #2563eb; }
            .stat-label { color: #6b7280; font-size: 0.9em; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 KBI Labs Procurement Analyst Platform</h1>
                <p>AI-Powered Government Procurement Intelligence Platform</p>
                <div class="nav">
                    <a href="/api/docs">API Documentation</a>
                    <a href="/dashboard">Analytics Dashboard</a>
                    <a href="/opportunities">View Opportunities</a>
                    <a href="/analysis">AI Analysis</a>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">""" + str(len(opportunities_db)) + """</div>
                    <div class="stat-label">Active Opportunities</div>
                </div>
                <div class="stat">
                    <div class="stat-value">84%</div>
                    <div class="stat-label">ML Prediction Accuracy</div>
                </div>
                <div class="stat">
                    <div class="stat-value">70+</div>
                    <div class="stat-label">Government Data Sources</div>
                </div>
                <div class="stat">
                    <div class="stat-value">24/7</div>
                    <div class="stat-label">Opportunity Monitoring</div>
                </div>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>🎯 Opportunity Intelligence</h3>
                    <p>Real-time monitoring of 70+ government data sources with AI-powered opportunity scoring and competitive analysis.</p>
                </div>
                <div class="feature">
                    <h3>🤖 AI Analysis Engine</h3>
                    <p>Machine learning models predicting contract success probability with 84%+ accuracy and automated risk assessment.</p>
                </div>
                <div class="feature">
                    <h3>📊 Market Intelligence</h3>
                    <p>Comprehensive market analysis, spending trends, and competitive landscape insights for strategic decision making.</p>
                </div>
                <div class="feature">
                    <h3>⚡ Professional Tools</h3>
                    <p>Pipeline management, proposal assistance, team collaboration, and executive reporting for procurement professionals.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/opportunities", response_model=List[ProcurementOpportunity])
async def get_opportunities(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    agency: Optional[str] = Query(None),
    naics_code: Optional[str] = Query(None),
    set_aside_type: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    live_data: bool = Query(False, description="Use live data from pipeline")
):
    """Get procurement opportunities with filtering"""
    
    if live_data and data_pipeline:
        # Get live data from pipeline
        filters = {}
        if agency: filters['agency'] = agency
        if naics_code: filters['naics_code'] = naics_code
        if set_aside_type: filters['set_aside_type'] = set_aside_type
        if min_value: filters['min_value'] = min_value
        if max_value: filters['max_value'] = max_value
        
        pipeline_opportunities = data_pipeline.get_opportunities(filters)
        
        # Convert to our data model format
        opportunities = []
        for opp in pipeline_opportunities[offset:offset + limit]:
            # Convert pipeline opportunity to API opportunity
            api_opp = ProcurementOpportunity(
                id=opp.opportunity_id,
                title=opp.title,
                description=opp.description,
                agency=opp.agency,
                sub_agency=opp.sub_agency,
                posted_date=opp.posted_date,
                response_deadline=opp.response_deadline,
                estimated_value=opp.estimated_value,
                naics_code=opp.naics_code,
                set_aside_type=opp.set_aside_type,
                place_of_performance=opp.place_of_performance,
                solicitation_number=opp.solicitation_number
            )
            opportunities.append(api_opp)
        
        logger.info(f"Retrieved {len(opportunities)} live opportunities from pipeline")
        return opportunities
    
    else:
        # Use mock data
        opportunities = list(opportunities_db.values())
        
        # Apply filters
        if agency:
            opportunities = [opp for opp in opportunities if agency.lower() in opp.agency.lower()]
        
        if naics_code:
            opportunities = [opp for opp in opportunities if opp.naics_code == naics_code]
        
        if set_aside_type:
            opportunities = [opp for opp in opportunities if opp.set_aside_type == set_aside_type]
        
        if min_value:
            opportunities = [opp for opp in opportunities if opp.estimated_value and opp.estimated_value >= min_value]
        
        if max_value:
            opportunities = [opp for opp in opportunities if opp.estimated_value and opp.estimated_value <= max_value]
        
        # Sort by posted date (newest first)
        opportunities.sort(key=lambda x: x.posted_date, reverse=True)
        
        # Apply pagination
        paginated = opportunities[offset:offset + limit]
        
        logger.info(f"Retrieved {len(paginated)} opportunities (filtered from {len(opportunities_db)})")
        
        return paginated

@app.get("/api/opportunities/{opportunity_id}", response_model=ProcurementOpportunity)
async def get_opportunity(opportunity_id: str):
    """Get specific opportunity details"""
    
    if opportunity_id not in opportunities_db:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return opportunities_db[opportunity_id]

@app.post("/api/analysis/opportunity", response_model=OpportunityScore)
async def analyze_opportunity(request: AnalysisRequest):
    """Analyze opportunity for a specific company"""
    
    if request.opportunity_id not in opportunities_db:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opportunity = opportunities_db[request.opportunity_id]
    
    # Check cache first
    cache_key = f"{request.opportunity_id}_{hash(str(request.company_profile))}"
    if cache_key in analysis_cache:
        logger.info(f"Returning cached analysis for {request.opportunity_id}")
        return analysis_cache[cache_key]
    
    # Perform analysis
    logger.info(f"Analyzing opportunity {request.opportunity_id} for {request.company_profile.company_name}")
    
    analysis_result = await analysis_service.analyze_opportunity(
        opportunity=opportunity,
        company=request.company_profile,
        analysis_type=request.analysis_type
    )
    
    # Cache result
    analysis_cache[cache_key] = analysis_result
    
    # Update opportunity with analysis
    opportunities_db[request.opportunity_id].ai_score = analysis_result
    
    return analysis_result

@app.get("/api/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get dashboard metrics and KPIs"""
    
    opportunities = list(opportunities_db.values())
    
    # Calculate metrics
    total_opportunities = len(opportunities)
    pipeline_value = sum(opp.estimated_value or 0 for opp in opportunities)
    avg_value = pipeline_value / total_opportunities if total_opportunities > 0 else 0
    
    # Upcoming deadlines (within 7 days)
    upcoming_deadlines = len([
        opp for opp in opportunities 
        if opp.response_deadline <= datetime.now() + timedelta(days=7)
    ])
    
    metrics = DashboardMetrics(
        total_opportunities=total_opportunities,
        active_pursuits=len([opp for opp in opportunities if opp.ai_score]),
        pipeline_value=pipeline_value,
        win_rate=0.65,  # Mock data
        avg_opportunity_value=avg_value,
        upcoming_deadlines=upcoming_deadlines,
        recent_wins=12,  # Mock data
        market_trends={
            "cybersecurity_growth": 0.23,
            "ai_ml_growth": 0.45,
            "cloud_growth": 0.31,
            "top_agencies": ["DOD", "DHS", "NASA", "VA", "GSA"]
        }
    )
    
    return metrics

@app.get("/api/agencies", response_model=List[str])
async def get_agencies():
    """Get list of agencies with active opportunities"""
    
    agencies = set(opp.agency for opp in opportunities_db.values())
    return sorted(list(agencies))

@app.get("/api/naics-codes", response_model=List[Dict[str, str]])
async def get_naics_codes():
    """Get list of NAICS codes with descriptions"""
    
    # Mock NAICS codes for demonstration
    naics_codes = [
        {"code": "541511", "description": "Custom Computer Programming Services"},
        {"code": "541512", "description": "Computer Systems Design Services"},
        {"code": "541513", "description": "Computer Facilities Management Services"},
        {"code": "541519", "description": "Other Computer Related Services"},
        {"code": "541330", "description": "Engineering Services"},
        {"code": "541690", "description": "Other Scientific and Technical Consulting Services"}
    ]
    
    return naics_codes

@app.get("/api/set-aside-types", response_model=List[str])
async def get_set_aside_types():
    """Get list of set-aside types"""
    
    return [
        "Small Business",
        "8(a)",
        "HUBZone", 
        "WOSB",
        "VOSB",
        "SDVOSB",
        "Unrestricted"
    ]

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get data pipeline status"""
    if data_pipeline:
        return data_pipeline.get_status()
    else:
        return {
            "is_running": False,
            "error": "Data pipeline not initialized"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "KBI Labs Procurement Analyst Platform",
        "version": "1.0.0",
        "ml_models_loaded": analysis_service.ml_models is not None,
        "opportunities_count": len(opportunities_db),
        "data_pipeline_running": data_pipeline.is_running if data_pipeline else False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)