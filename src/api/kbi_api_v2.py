#!/usr/bin/env python3
"""
KBI Labs API v2.0
Connect the enriched database to your FastAPI backend
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
from contextlib import contextmanager

app = FastAPI(title="KBI Labs API", version="2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DATABASE_PATH = "kbi_production.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Models
class Company(BaseModel):
    uei: str
    organization_name: str
    city: Optional[str]
    state: Optional[str]
    pe_investment_score: float
    business_health_grade: str
    innovation_score: Optional[float]
    growth_potential_score: Optional[float]
    federal_contracts_value: Optional[float]
    patent_count: Optional[int]

class CompanyDetail(Company):
    primary_naics: Optional[str]
    industry_sector: Optional[str]
    website: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    sam_registration_status: Optional[str]
    cage_code: Optional[str]
    market_position_score: Optional[float]
    nsf_total_funding: Optional[float]
    state_gdp_billions: Optional[float]
    state_gdp_growth_rate: Optional[float]

class Analytics(BaseModel):
    total_companies: int
    avg_pe_score: float
    grade_distribution: dict
    top_states: List[dict]
    top_industries: List[dict]

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "KBI Labs API v2.0",
        "endpoints": [
            "/companies",
            "/companies/{uei}",
            "/companies/search",
            "/analytics",
            "/analytics/state/{state}",
            "/analytics/industry/{naics}"
        ]
    }

@app.get("/companies", response_model=List[Company])
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    state: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    grade: Optional[str] = None
):
    """Get companies with filtering options"""
    with get_db() as conn:
        query = "SELECT * FROM companies WHERE 1=1"
        params = []
        
        if state:
            query += " AND state = ?"
            params.append(state)
        if min_score:
            query += " AND pe_investment_score >= ?"
            params.append(min_score)
        if grade:
            query += " AND business_health_grade = ?"
            params.append(grade)
            
        query += " ORDER BY pe_investment_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        
        cursor = conn.execute(query, params)
        companies = [dict(row) for row in cursor]
        
    return companies

@app.get("/companies/search")
async def search_companies(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100)
):
    """Search companies by name"""
    with get_db() as conn:
        cursor = conn.execute(
            """SELECT * FROM companies 
            WHERE organization_name LIKE ? 
            ORDER BY pe_investment_score DESC 
            LIMIT ?""",
            (f"%{q}%", limit)
        )
        companies = [dict(row) for row in cursor]
    
    return companies

@app.get("/companies/{uei}", response_model=CompanyDetail)
async def get_company(uei: str):
    """Get detailed company information"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM companies WHERE uei = ?", (uei,))
        company = cursor.fetchone()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
            
    return dict(company)

@app.get("/analytics", response_model=Analytics)
async def get_analytics():
    """Get platform-wide analytics"""
    with get_db() as conn:
        # Total and average
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(pe_investment_score) as avg_score
            FROM companies
        """).fetchone()
        
        # Grade distribution
        grades = conn.execute("""
            SELECT business_health_grade, COUNT(*) as count
            FROM companies
            GROUP BY business_health_grade
            ORDER BY business_health_grade
        """).fetchall()
        
        # Top states
        states = conn.execute("""
            SELECT * FROM state_analytics
            ORDER BY avg_pe_score DESC
            LIMIT 10
        """).fetchall()
        
        # Top industries
        industries = conn.execute("""
            SELECT * FROM industry_analytics
            WHERE company_count > 10
            ORDER BY avg_pe_score DESC
            LIMIT 10
        """).fetchall()
        
    return {
        "total_companies": stats["total"],
        "avg_pe_score": round(stats["avg_score"], 1),
        "grade_distribution": {row["business_health_grade"]: row["count"] for row in grades},
        "top_states": [dict(row) for row in states],
        "top_industries": [dict(row) for row in industries]
    }

@app.get("/analytics/state/{state}")
async def get_state_analytics(state: str):
    """Get analytics for a specific state"""
    with get_db() as conn:
        # State summary
        summary = conn.execute(
            "SELECT * FROM state_analytics WHERE state = ?", 
            (state.upper(),)
        ).fetchone()
        
        if not summary:
            raise HTTPException(status_code=404, detail="State not found")
            
        # Top companies in state
        top_companies = conn.execute("""
            SELECT uei, organization_name, city, pe_investment_score, business_health_grade
            FROM companies
            WHERE state = ?
            ORDER BY pe_investment_score DESC
            LIMIT 10
        """, (state.upper(),)).fetchall()
        
        # Industry breakdown
        industries = conn.execute("""
            SELECT 
                industry_sector,
                COUNT(*) as count,
                AVG(pe_investment_score) as avg_score
            FROM companies
            WHERE state = ?
            GROUP BY industry_sector
            ORDER BY count DESC
        """, (state.upper(),)).fetchall()
        
    return {
        "summary": dict(summary),
        "top_companies": [dict(row) for row in top_companies],
        "industry_breakdown": [dict(row) for row in industries]
    }

@app.get("/analytics/industry/{naics}")
async def get_industry_analytics(naics: str):
    """Get analytics for a specific NAICS code"""
    with get_db() as conn:
        companies = conn.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(pe_investment_score) as avg_score,
                AVG(innovation_score) as avg_innovation,
                SUM(federal_contracts_value) as total_contracts
            FROM companies
            WHERE primary_naics LIKE ?
        """, (f"{naics}%",)).fetchone()
        
        if companies["total"] == 0:
            raise HTTPException(status_code=404, detail="No companies found for this NAICS")
            
        # Geographic distribution
        states = conn.execute("""
            SELECT 
                state,
                COUNT(*) as count,
                AVG(pe_investment_score) as avg_score
            FROM companies
            WHERE primary_naics LIKE ?
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """, (f"{naics}%",)).fetchall()
        
    return {
        "naics": naics,
        "total_companies": companies["total"],
        "avg_pe_score": round(companies["avg_score"], 1) if companies["avg_score"] else 0,
        "avg_innovation_score": round(companies["avg_innovation"], 1) if companies["avg_innovation"] else 0,
        "total_federal_contracts": companies["total_contracts"] or 0,
        "geographic_distribution": [dict(row) for row in states]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
