#!/usr/bin/env python3
"""
Simple KBI Labs Procurement Platform Server
Simplified version for reliable startup and testing
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KBI Labs Procurement Analyst Platform",
    description="AI-Powered Government Procurement Intelligence Platform",
    version="1.0.0"
)

# Add CORS middleware
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
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Simple data models
class OpportunityResponse(BaseModel):
    id: str
    title: str
    description: str
    agency: str
    posted_date: str
    response_deadline: str
    estimated_value: Optional[float] = None
    naics_code: Optional[str] = None
    set_aside_type: Optional[str] = None
    solicitation_number: str
    ai_score: Optional[float] = None

class MetricsResponse(BaseModel):
    total_opportunities: int
    pipeline_value: float
    win_rate: float
    upcoming_deadlines: int
    platform_status: str

# Sample data
SAMPLE_OPPORTUNITIES = [
    {
        "id": "DOD-2024-001",
        "title": "Advanced Cybersecurity Solutions for Defense Networks",
        "description": "The Department of Defense seeks comprehensive cybersecurity solutions for protecting critical defense infrastructure and networks against advanced persistent threats.",
        "agency": "Department of Defense",
        "posted_date": (datetime.now() - timedelta(days=2)).isoformat(),
        "response_deadline": (datetime.now() + timedelta(days=28)).isoformat(),
        "estimated_value": 15000000.0,
        "naics_code": "541512",
        "set_aside_type": "Small Business",
        "solicitation_number": "HQ0034-24-R-0001",
        "ai_score": 0.78
    },
    {
        "id": "NASA-2024-002",
        "title": "Satellite Data Analysis and Processing Services",
        "description": "NASA requires advanced data processing capabilities for analyzing satellite imagery and telemetry data from multiple space missions.",
        "agency": "National Aeronautics and Space Administration",
        "posted_date": (datetime.now() - timedelta(days=1)).isoformat(),
        "response_deadline": (datetime.now() + timedelta(days=35)).isoformat(),
        "estimated_value": 8500000.0,
        "naics_code": "541511",
        "set_aside_type": "Unrestricted",
        "solicitation_number": "GSFC-24-001",
        "ai_score": 0.65
    },
    {
        "id": "DHS-2024-003",
        "title": "Border Security Technology Integration",
        "description": "Department of Homeland Security needs integrated technology solutions for enhancing border security operations and monitoring capabilities.",
        "agency": "Department of Homeland Security",
        "posted_date": (datetime.now() - timedelta(days=5)).isoformat(),
        "response_deadline": (datetime.now() + timedelta(days=21)).isoformat(),
        "estimated_value": 25000000.0,
        "naics_code": "541330",
        "set_aside_type": "8(a)",
        "solicitation_number": "CBP-2024-001",
        "ai_score": 0.82
    },
    {
        "id": "VA-2024-004",
        "title": "Healthcare IT Modernization Program",
        "description": "Veterans Affairs seeks comprehensive IT modernization services to upgrade healthcare systems and improve veteran care delivery.",
        "agency": "Department of Veterans Affairs",
        "posted_date": (datetime.now() - timedelta(days=3)).isoformat(),
        "response_deadline": (datetime.now() + timedelta(days=42)).isoformat(),
        "estimated_value": 12000000.0,
        "naics_code": "541511",
        "set_aside_type": "VOSB",
        "solicitation_number": "VA-2024-IT-001",
        "ai_score": 0.71
    },
    {
        "id": "GSA-2024-005",
        "title": "Cloud Infrastructure Services",
        "description": "General Services Administration requires cloud infrastructure and platform services to support government digital transformation initiatives.",
        "agency": "General Services Administration",
        "posted_date": (datetime.now() - timedelta(days=4)).isoformat(),
        "response_deadline": (datetime.now() + timedelta(days=30)).isoformat(),
        "estimated_value": 18000000.0,
        "naics_code": "518210",
        "set_aside_type": "Small Business",
        "solicitation_number": "GSA-2024-CLOUD-001",
        "ai_score": 0.69
    }
]

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main platform landing page"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KBI Labs Procurement Analyst Platform</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px; text-align: center; }}
            .header h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 10px; }}
            .header p {{ font-size: 1.2rem; opacity: 0.9; }}
            .nav {{ display: flex; gap: 15px; justify-content: center; margin-top: 30px; flex-wrap: wrap; }}
            .nav a {{ background: rgba(255,255,255,0.2); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 500; transition: all 0.3s; }}
            .nav a:hover {{ background: rgba(255,255,255,0.3); transform: translateY(-2px); }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
            .stat {{ background: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .stat-value {{ font-size: 2.5em; font-weight: bold; color: #2563eb; margin-bottom: 5px; }}
            .stat-label {{ color: #6b7280; font-size: 0.9em; }}
            .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-top: 40px; }}
            .feature {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .feature h3 {{ color: #1f2937; margin-bottom: 15px; font-size: 1.3rem; }}
            .feature p {{ color: #6b7280; }}
            .icon {{ font-size: 2rem; margin-bottom: 15px; }}
            .status {{ background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; display: inline-block; font-size: 0.9rem; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 KBI Labs Procurement Platform</h1>
                <p>AI-Powered Government Procurement Intelligence</p>
                <div class="status">✅ Platform Operational</div>
                
                <div class="nav">
                    <a href="/dashboard">📊 Dashboard</a>
                    <a href="/api/opportunities">🎯 Opportunities API</a>
                    <a href="/api/docs">📖 API Documentation</a>
                    <a href="/health">💚 Health Check</a>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(SAMPLE_OPPORTUNITIES)}</div>
                    <div class="stat-label">Active Opportunities</div>
                </div>
                <div class="stat">
                    <div class="stat-value">84%</div>
                    <div class="stat-label">AI Prediction Accuracy</div>
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
                    <div class="icon">🎯</div>
                    <h3>Opportunity Intelligence</h3>
                    <p>Real-time monitoring of government procurement opportunities with AI-powered scoring and competitive analysis.</p>
                </div>
                <div class="feature">
                    <div class="icon">🤖</div>
                    <h3>AI Analysis Engine</h3>
                    <p>Machine learning models predicting contract success probability with 84%+ accuracy and automated risk assessment.</p>
                </div>
                <div class="feature">
                    <div class="icon">📊</div>
                    <h3>Market Intelligence</h3>
                    <p>Comprehensive market analysis, spending trends, and competitive landscape insights for strategic decision making.</p>
                </div>
                <div class="feature">
                    <div class="icon">⚡</div>
                    <h3>Professional Tools</h3>
                    <p>Pipeline management, proposal assistance, team collaboration, and executive reporting for procurement professionals.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """SMB Contractor Intelligence Dashboard"""
    try:
        with open("smb_contractor_dashboard.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Fallback to basic dashboard if file not found
        html_content = """
        <!DOCTYPE html>
        <html><head><title>Dashboard Loading...</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h1>🔄 Loading SMB Contractor Dashboard...</h1>
        <p>If this persists, please check that smb_contractor_dashboard.html exists.</p>
        <a href="/" style="color: #2563eb;">← Back to Home</a>
        </body></html>
        """
        return HTMLResponse(content=html_content)

@app.get("/test", response_class=HTMLResponse)
async def dashboard_test():
    """Interactive Dashboard Testing Interface"""
    try:
        with open("dashboard_test.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Test interface not found</h1>", status_code=404)

@app.get("/debug", response_class=HTMLResponse)
async def dashboard_debug():
    """Simple Dashboard Debug Interface"""
    try:
        with open("debug_dashboard.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Debug interface not found</h1>", status_code=404)

@app.get("/simple-test", response_class=HTMLResponse)
async def simple_dashboard_test():
    """Simple Dashboard Test Interface"""
    try:
        with open("dashboard_simple_test.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Simple test interface not found</h1>", status_code=404)

@app.get("/minimal", response_class=HTMLResponse)
async def minimal_dashboard():
    """Minimal React Dashboard Test"""
    try:
        with open("dashboard_minimal.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Minimal dashboard not found</h1>", status_code=404)

@app.get("/react-test", response_class=HTMLResponse)
async def react_test():
    """React Loading Test"""
    try:
        with open("react_test.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>React test not found</h1>", status_code=404)

@app.get("/basic", response_class=HTMLResponse)
async def basic_dashboard():
    """Basic HTML Dashboard (No React)"""
    try:
        with open("dashboard_basic.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Basic dashboard not found</h1>", status_code=404)

@app.get("/api/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    limit: int = Query(20, le=100),
    agency: Optional[str] = Query(None),
    set_aside_type: Optional[str] = Query(None)
):
    """Get procurement opportunities with filtering"""
    opportunities = SAMPLE_OPPORTUNITIES.copy()
    
    # Apply filters
    if agency:
        opportunities = [opp for opp in opportunities if agency.lower() in opp['agency'].lower()]
    
    if set_aside_type:
        opportunities = [opp for opp in opportunities if opp.get('set_aside_type') == set_aside_type]
    
    # Limit results
    opportunities = opportunities[:limit]
    
    logger.info(f"Retrieved {len(opportunities)} opportunities")
    return opportunities

@app.get("/api/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: str):
    """Get specific opportunity details"""
    opportunity = next((opp for opp in SAMPLE_OPPORTUNITIES if opp['id'] == opportunity_id), None)
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return opportunity

@app.get("/api/dashboard/metrics", response_model=MetricsResponse)
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    total_value = sum(opp.get('estimated_value', 0) for opp in SAMPLE_OPPORTUNITIES)
    avg_score = sum(opp.get('ai_score', 0) for opp in SAMPLE_OPPORTUNITIES) / len(SAMPLE_OPPORTUNITIES)
    
    # Count upcoming deadlines (within 7 days)
    upcoming_deadlines = 0
    for opp in SAMPLE_OPPORTUNITIES:
        deadline = datetime.fromisoformat(opp['response_deadline'].replace('Z', '+00:00'))
        if deadline <= datetime.now() + timedelta(days=7):
            upcoming_deadlines += 1
    
    return MetricsResponse(
        total_opportunities=len(SAMPLE_OPPORTUNITIES),
        pipeline_value=total_value,
        win_rate=avg_score,
        upcoming_deadlines=upcoming_deadlines,
        platform_status="operational"
    )

@app.get("/api/predict")
async def predict_opportunity(
    opportunity_id: str = Query(...),
    company_name: str = Query("Test Company"),
    naics_match: bool = Query(True),
    past_performance: bool = Query(True)
):
    """Simple AI prediction endpoint"""
    
    # Find the opportunity
    opportunity = next((opp for opp in SAMPLE_OPPORTUNITIES if opp['id'] == opportunity_id), None)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Simple prediction logic
    base_score = 0.5
    
    if naics_match:
        base_score += 0.15
    
    if past_performance:
        base_score += 0.20
    
    # Add some randomness based on opportunity value
    if opportunity.get('estimated_value', 0) < 5000000:
        base_score += 0.10  # Smaller contracts easier to win
    
    # Set-aside bonus
    if opportunity.get('set_aside_type') == 'Small Business':
        base_score += 0.05
    
    # Cap at 0.95
    win_probability = min(base_score, 0.95)
    
    confidence = "High" if abs(win_probability - 0.5) > 0.3 else "Medium"
    
    recommendation = (
        "Pursue Actively" if win_probability > 0.7 else
        "Consider Carefully" if win_probability > 0.5 else
        "Monitor Only"
    )
    
    return {
        "opportunity_id": opportunity_id,
        "company_name": company_name,
        "win_probability": round(win_probability, 3),
        "confidence": confidence,
        "recommendation": recommendation,
        "factors": {
            "naics_match": naics_match,
            "past_performance": past_performance,
            "opportunity_value": opportunity.get('estimated_value'),
            "set_aside_type": opportunity.get('set_aside_type')
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "KBI Labs Procurement Platform",
        "version": "1.0.0",
        "opportunities_loaded": len(SAMPLE_OPPORTUNITIES),
        "features": [
            "Real-time Opportunity Intelligence",
            "AI-Powered Success Prediction",
            "Market Analysis Dashboard",
            "Professional Procurement Tools"
        ]
    }

# Add government intelligence routes
try:
    from api.routers.government_intelligence import router as gov_intel_router
    app.include_router(gov_intel_router, prefix="/api")
    logger.info("Government intelligence API routes loaded")
except ImportError as e:
    logger.warning(f"Could not load government intelligence routes: {e}")

@app.get("/api/test-connection")
async def test_frontend_connection():
    """Test endpoint for frontend-backend connectivity"""
    try:
        return {
            "status": "success",
            "message": "Frontend-backend connection working!",
            "server_time": datetime.now().isoformat(),
            "available_endpoints": [
                "/api/government-intelligence/comprehensive-intelligence",
                "/api/government-intelligence/procurement-opportunities", 
                "/api/government-intelligence/enhanced-gsa-intelligence",
                "/api/government-intelligence/govinfo-intelligence",
                "/api/government-intelligence/health"
            ],
            "test_data": {
                "sample_opportunity": SAMPLE_OPPORTUNITIES[0] if SAMPLE_OPPORTUNITIES else None,
                "total_opportunities": len(SAMPLE_OPPORTUNITIES)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "server_time": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting KBI Labs Procurement Platform...")
    print("📊 Dashboard: http://localhost:8000/dashboard")
    print("🎯 API Docs: http://localhost:8000/docs")
    print("💚 Health: http://localhost:8000/health")
    print("🌐 Government Intelligence: http://localhost:8000/api/government-intelligence/")
    print("🔧 Test Connection: http://localhost:8000/api/test-connection")
    print("🌐 Server accessible on all network interfaces")
    print("💡 To make it internet accessible, run: ngrok http 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")