"""
Federal Opportunities endpoint (mock for demo)
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/opportunities/{state}")
async def get_federal_opportunities(
    state: str,
    naics: Optional[str] = Query(None, description="Filter by NAICS code")
):
    """Get federal contract opportunities by state (mock data for demo)"""
    
    # Mock data for demonstration
    opportunities = []
    states_map = {
        "FL": "Florida",
        "TX": "Texas", 
        "VA": "Virginia",
        "CA": "California"
    }
    
    state_name = states_map.get(state.upper(), state)
    
    for i in range(5):
        opportunities.append({
            "id": f"FA{random.randint(1000,9999)}-{state}-{i}",
            "title": f"{state_name} IT Services Contract #{i+1}",
            "agency": random.choice(["DoD", "VA", "GSA", "HHS"]),
            "posted_date": (datetime.now() - timedelta(days=random.randint(1,30))).isoformat(),
            "response_deadline": (datetime.now() + timedelta(days=random.randint(10,60))).isoformat(),
            "estimated_value": random.randint(100000, 5000000),
            "set_aside": random.choice(["Small Business", "8(a)", "WOSB", "Open"]),
            "naics_code": naics or random.choice(["541512", "541611", "541519"]),
            "place_of_performance": f"{state_name}, USA"
        })
    
    return {
        "state": state_name,
        "count": len(opportunities),
        "opportunities": opportunities,
        "generated_at": datetime.now().isoformat()
    }

@router.get("/opportunities/stats/{state}")
async def get_opportunity_stats(state: str):
    """Get statistics about opportunities in a state"""
    return {
        "state": state,
        "total_opportunities": random.randint(50, 200),
        "total_value": random.randint(10000000, 100000000),
        "small_business_setasides": random.randint(30, 80),
        "average_contract_value": random.randint(250000, 1500000)
    }
