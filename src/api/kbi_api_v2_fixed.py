#!/usr/bin/env python3
"""
KBI Labs API v2.0 - Fixed Version
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
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

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "KBI Labs API v2.0",
        "status": "operational",
        "endpoints": [
            "/companies",
            "/companies/{uei}",
            "/companies/search",
            "/analytics",
            "/analytics/state/{state}"
        ]
    }

@app.get("/companies")
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
            params.append(state.upper())
        if min_score:
            query += " AND pe_investment_score >= ?"
            params.append(min_score)
        if grade:
            query += " AND business_health_grade = ?"
            params.append(grade)
            
        query += " ORDER BY pe_investment_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        
        try:
            cursor = conn.execute(query, params)
            companies = [dict(row) for row in cursor]
            return {"data": companies, "count": len(companies)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/search")
async def search_companies(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100)
):
    """Search companies by name"""
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """SELECT * FROM companies 
                WHERE organization_name LIKE ? 
                ORDER BY pe_investment_score DESC 
                LIMIT ?""",
                (f"%{q}%", limit)
            )
            companies = [dict(row) for row in cursor]
            return {"data": companies, "count": len(companies)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/companies/{uei}")
async def get_company(uei: str):
    """Get detailed company information"""
    with get_db() as conn:
        try:
            cursor = conn.execute("SELECT * FROM companies WHERE uei = ?", (uei,))
            company = cursor.fetchone()
            
            if not company:
                raise HTTPException(status_code=404, detail="Company not found")
                
            return dict(company)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics():
    """Get platform-wide analytics"""
    with get_db() as conn:
        try:
            # Get basic stats
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
                WHERE business_health_grade IS NOT NULL
                GROUP BY business_health_grade
                ORDER BY business_health_grade
            """).fetchall()
            
            # Top states
            states = conn.execute("""
                SELECT 
                    state,
                    COUNT(*) as company_count,
                    AVG(pe_investment_score) as avg_score
                FROM companies
                WHERE state IS NOT NULL
                GROUP BY state
                ORDER BY company_count DESC
                LIMIT 10
            """).fetchall()
            
            return {
                "total_companies": stats["total"],
                "avg_pe_score": round(stats["avg_score"], 1) if stats["avg_score"] else 0,
                "grade_distribution": {row["business_health_grade"]: row["count"] for row in grades},
                "top_states": [
                    {
                        "state": row["state"],
                        "company_count": row["company_count"],
                        "avg_score": round(row["avg_score"], 1) if row["avg_score"] else 0
                    } for row in states
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/state/{state}")
async def get_state_analytics(state: str):
    """Get analytics for a specific state"""
    with get_db() as conn:
        try:
            # State summary
            summary = conn.execute("""
                SELECT 
                    state,
                    COUNT(*) as company_count,
                    AVG(pe_investment_score) as avg_score
                FROM companies
                WHERE state = ?
                GROUP BY state
            """, (state.upper(),)).fetchone()
            
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
            
            return {
                "state": state.upper(),
                "summary": {
                    "company_count": summary["company_count"],
                    "avg_score": round(summary["avg_score"], 1) if summary["avg_score"] else 0
                },
                "top_companies": [dict(row) for row in top_companies]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting KBI Labs API v2.0 on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
