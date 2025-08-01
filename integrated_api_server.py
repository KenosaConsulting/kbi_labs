#!/usr/bin/env python3
"""
SMB Intelligence API with SAM.gov Integration
Now includes live federal contract opportunities
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, List
import json
from datetime import datetime
import uvicorn
import os

# Import our SAM.gov integration
from sam_api_enhanced import EnhancedSAMAPI

app = FastAPI(title="SMB Intelligence API", version="3.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global data storage
company_index = {}
market_insights = {}
sam_api = None

@app.on_event("startup")
async def load_data():
    """Load company data and initialize SAM API"""
    global company_index, market_insights, sam_api
    
    # Load company index
    with open('data/company_index.json', 'r') as f:
        company_index = json.load(f)
    
    # Load market insights
    try:
        with open('data/market_insights.json', 'r') as f:
            market_insights = json.load(f)
    except:
        market_insights = {}
    
    # Initialize SAM.gov API
    api_key = os.environ.get("SAM_GOV_API_KEY")
    if api_key:
        sam_api = EnhancedSAMAPI(api_key)
        if sam_api.test_api_key():
            print("✅ SAM.gov API connected")
        else:
            sam_api = None
            print("❌ SAM.gov API key invalid")
    else:
        print("⚠️  No SAM.gov API key found")
    
    print(f"✅ Loaded {len(company_index):,} companies")

# Keep your existing auth and endpoints...
VALID_TOKENS = {
    "pe_firm_token_2024": "pe_firm",
    "smb_owner_token_2024": "smb_owner"
}

def get_user_context(authorization: str = Header(None)) -> str:
    """Get user context from auth token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    token = authorization.replace("Bearer ", "")
    user_type = VALID_TOKENS.get(token)
    
    if not user_type:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user_type

# NEW ENDPOINT: Federal Opportunities
@app.get("/api/v3/opportunities/{state}")
async def get_opportunities(state: str, user_type: str = Depends(get_user_context)):
    """Get federal contract opportunities by state"""
    if not sam_api:
        raise HTTPException(status_code=503, detail="SAM.gov API not available")
    
    opportunities = sam_api.search_opportunities_by_state(state.upper(), limit=20)
    
    # Add context based on user type
    if user_type == "pe_firm":
        # For PE firms, emphasize revenue potential
        for opp in opportunities:
            opp["intelligence"] = {
                "revenue_potential": "High" if opp.get("set_aside") != "Open" else "Medium",
                "competition_level": "Limited" if "8(a)" in opp.get("set_aside", "") else "High",
                "portfolio_fit": "Analyze NAICS match with portfolio companies"
            }
    else:
        # For SMB owners, emphasize actionability
        for opp in opportunities:
            opp["intelligence"] = {
                "eligibility": "Check certifications required",
                "deadline_urgency": "Critical" if opp.get("days_left", 0) < 7 else "Normal",
                "next_steps": "Review requirements and register interest"
            }
    
    return {
        "state": state.upper(),
        "count": len(opportunities),
        "opportunities": opportunities,
        "generated_at": datetime.now().isoformat()
    }

# NEW ENDPOINT: Opportunity Statistics
@app.get("/api/v3/opportunity-stats")
async def get_opportunity_stats(state: Optional[str] = None):
    """Get statistics about federal opportunities"""
    if not sam_api:
        raise HTTPException(status_code=503, detail="SAM.gov API not available")
    
    stats = sam_api.get_opportunity_stats(state)
    return stats

# Enhanced company intelligence with opportunities
@app.get("/api/v3/companies/{uei}/intelligence")
async def get_enhanced_company_intelligence(uei: str, user_type: str = Depends(get_user_context)):
    """Get company intelligence with matching opportunities"""
    
    # Get basic company data
    company_data = company_index.get(uei)
    if not company_data:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get your existing intelligence...
    base_info = {
        "uei": uei,
        "company_name": company_data["name"],
        "location": {
            "city": company_data.get("city", "Unknown"),
            "state": company_data.get("state", "Unknown")
        }
    }
    
    # Add matching opportunities if available
    if sam_api and company_data.get("state"):
        opportunities = sam_api.search_opportunities_by_state(
            company_data["state"], 
            limit=5
        )
        
        base_info["federal_opportunities"] = {
            "count": len(opportunities),
            "total_available_in_state": "100+",
            "top_opportunities": opportunities[:3],
            "recommendation": "Register in SAM.gov to access all opportunities" if not company_data.get("sam_registered") else "Review matching opportunities daily"
        }
    
    return base_info

# Keep all your other existing endpoints...

if __name__ == "__main__":
    # Make sure API key is set
    if not os.environ.get("SAM_GOV_API_KEY"):
        print("⚠️  Warning: SAM_GOV_API_KEY not set")
        print("  Run: export SAM_GOV_API_KEY='your_key_here'")
    
    uvicorn.run(app, host="0.0.0.0", port=8005)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
