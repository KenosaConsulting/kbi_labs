#!/usr/bin/env python3
"""
Simple API test without database dependencies
"""
from fastapi import FastAPI
import uvicorn
import json
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

app = FastAPI(title="KBI Labs Test API", version="1.0.0")

@app.get("/")
async def root():
    return {
        "message": "KBI Labs Test API",
        "status": "operational",
        "test_endpoints": {
            "health": "/health",
            "test_data": "/api/test/companies"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "kbi-labs-test"}

@app.get("/api/test/companies")
async def get_test_companies():
    """Return mock company data for testing"""
    mock_companies = [
        {
            "uei": "TEST123456789",
            "organization_name": "Alpha Tech Solutions",
            "city": "Austin",
            "state": "TX",
            "pe_investment_score": 87.5,
            "business_health_grade": "A"
        },
        {
            "uei": "TEST987654321", 
            "organization_name": "Beta Manufacturing",
            "city": "Denver",
            "state": "CO",
            "pe_investment_score": 72.3,
            "business_health_grade": "B+"
        }
    ]
    return {"companies": mock_companies, "count": len(mock_companies)}

if __name__ == "__main__":
    print("🚀 Starting KBI Labs Test API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)