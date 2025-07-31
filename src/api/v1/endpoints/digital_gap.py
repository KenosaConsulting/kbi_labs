from fastapi import APIRouter, HTTPException, Security, Depends, Query
from fastapi.security import APIKeyHeader
from sqlalchemy import text
from src.database.connection import engine
from datetime import datetime
import json

router = APIRouter()

# API Key configuration
API_KEYS = {
    'demo-trial-key': {'tier': 'trial', 'limit': 100, 'calls': 0},
    'demo-basic-key': {'tier': 'basic', 'limit': 1000, 'calls': 0},
    'demo-pro-key': {'tier': 'professional', 'limit': 10000, 'calls': 0}
}

api_key_header = APIKeyHeader(name='X-Api-Key', auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail='API key required')
    
    if api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail='Invalid API key')
    
    # Simple rate limiting
    key_data = API_KEYS[api_key]
    if key_data['calls'] >= key_data['limit']:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Limit: {key_data['limit']} calls/day"
        )
    
    key_data['calls'] += 1
    return key_data

@router.get("/stats", dependencies=[Depends(verify_api_key)])
async def get_opportunity_stats():
    """Get overall opportunity statistics"""
    try:
        with engine.connect() as conn:
            total_companies = conn.execute(text("SELECT COUNT(*) FROM digital_gap_companies")).scalar()
            companies_without_websites = conn.execute(text("SELECT COUNT(*) FROM digital_gap_companies WHERE website_opportunity = true")).scalar()
            high_opportunities = conn.execute(text("SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'HIGH'")).scalar()
            medium_opportunities = conn.execute(text("SELECT COUNT(*) FROM digital_gap_companies WHERE opportunity_level = 'MEDIUM'")).scalar()
            
            percentage_without_websites = (companies_without_websites / total_companies * 100) if total_companies > 0 else 0
            total_market_value = companies_without_websites * 25000
            
            return {
                "total_companies": total_companies,
                "companies_without_websites": companies_without_websites,
                "percentage_without_websites": round(percentage_without_websites, 1),
                "high_opportunities": high_opportunities,
                "medium_opportunities": medium_opportunities,
                "total_market_value": total_market_value
            }
    except Exception as e:
        return {"error": str(e)}

@router.get("/companies", dependencies=[Depends(verify_api_key)])
async def get_companies(
    state: str = Query(None),
    city: str = Query(None),
    opportunity_level: str = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get companies with filtering"""
    try:
        query = "SELECT * FROM digital_gap_companies WHERE 1=1"
        params = {}
        
        if state:
            query += " AND LOWER(state) = LOWER(:state)"
            params['state'] = state
        if city:
            query += " AND LOWER(city) = LOWER(:city)"
            params['city'] = city
        if opportunity_level:
            query += " AND opportunity_level = :opportunity_level"
            params['opportunity_level'] = opportunity_level.upper()
            
        query += " ORDER BY opportunity_score DESC LIMIT :limit"
        params['limit'] = limit
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            companies = []
            for row in result.fetchall():
                companies.append({
                    "id": row[0],
                    "organization_name": row[1],
                    "city": row[2],
                    "state": row[3],
                    "phone_number": row[6],
                    "opportunity_score": row[14],
                    "opportunity_level": row[15],
                    "website_opportunity": row[13]
                })
            return companies
    except Exception as e:
        return {"error": str(e)}

@router.get("/states", dependencies=[Depends(verify_api_key)])
async def get_state_opportunities():
    """Get opportunity breakdown by state"""
    try:
        query = """
            SELECT 
                state,
                COUNT(*) as companies_without_websites,
                AVG(opportunity_score) as avg_opportunity_score
            FROM digital_gap_companies
            WHERE website_opportunity = true AND state IS NOT NULL AND state != ''
            GROUP BY state
            ORDER BY companies_without_websites DESC
            LIMIT 20
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            states = []
            for row in result.fetchall():
                states.append({
                    "state": row[0],
                    "companies_without_websites": row[1],
                    "avg_opportunity_score": round(row[2], 1),
                    "market_value": row[1] * 25000
                })
            return states
    except Exception as e:
        return {"error": str(e)}

@router.get("/api-keys")
async def get_demo_api_keys():
    """Get demo API keys for testing"""
    return {
        "demo_keys": [
            {"key": "demo-trial-key", "tier": "trial", "limit": 100},
            {"key": "demo-basic-key", "tier": "basic", "limit": 1000},
            {"key": "demo-pro-key", "tier": "professional", "limit": 10000}
        ],
        "usage_example": "curl -H 'X-Api-Key: demo-basic-key' http://localhost:8000/api/v1/digital-gap/stats"
    }
