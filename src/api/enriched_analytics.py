#!/usr/bin/env python3
"""
Analytics API for fully enriched SMB data
"""

import sqlite3
import json
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="SMB Intelligence Analytics API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    conn = sqlite3.connect('smb_full_enrichment.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return {
        "message": "SMB Intelligence Analytics API",
        "endpoints": {
            "/prime-targets": "Highest value succession opportunities",
            "/no-digital-presence": "Businesses with no online presence",
            "/established-at-risk": "Old businesses with high risk",
            "/analytics/summary": "Overall market analytics"
        }
    }

@app.get("/prime-targets")
def get_prime_targets(limit: int = 20):
    """Get the highest value succession opportunities"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            organization_name,
            city,
            state,
            email,
            domain,
            website_status,
            google_rating,
            google_reviews_count,
            domain_age_years,
            succession_risk_score,
            estimated_revenue,
            technology_signals,
            risk_factors
        FROM fully_enriched_smbs
        WHERE succession_risk_score >= 8
        AND (website_status != 'active' OR google_rating IS NULL)
        ORDER BY succession_risk_score DESC, estimated_revenue DESC
        LIMIT ?
    """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    for r in results:
        if r['technology_signals']:
            r['technology_signals'] = json.loads(r['technology_signals'])
        if r['risk_factors']:
            r['risk_factors'] = json.loads(r['risk_factors'])
    
    conn.close()
    return {"count": len(results), "prime_targets": results}

@app.get("/no-digital-presence")
def get_no_digital_presence():
    """Find businesses with no online presence - highest risk"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            organization_name,
            city,
            state,
            email,
            succession_risk_score,
            estimated_revenue
        FROM fully_enriched_smbs
        WHERE website_status != 'active'
        AND google_rating IS NULL
        AND succession_risk_score >= 7
        ORDER BY estimated_revenue DESC
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "count": len(results),
        "total_value": sum(r['estimated_revenue'] for r in results if r['estimated_revenue']),
        "businesses": results
    }

@app.get("/established-at-risk")
def get_established_at_risk():
    """Find established businesses (10+ years) with high succession risk"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            organization_name,
            domain,
            domain_age_years,
            google_rating,
            succession_risk_score,
            estimated_revenue,
            city,
            state
        FROM fully_enriched_smbs
        WHERE domain_age_years >= 10
        AND succession_risk_score >= 7
        ORDER BY domain_age_years DESC
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "count": len(results),
        "avg_age": sum(r['domain_age_years'] for r in results) / len(results) if results else 0,
        "businesses": results
    }

@app.get("/analytics/summary")
def get_analytics_summary():
    """Get overall market analytics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_businesses,
            AVG(succession_risk_score) as avg_risk,
            COUNT(CASE WHEN succession_risk_score >= 8 THEN 1 END) as high_risk_count,
            COUNT(CASE WHEN website_status = 'active' THEN 1 END) as with_websites,
            COUNT(CASE WHEN google_rating IS NOT NULL THEN 1 END) as with_google,
            AVG(domain_age_years) as avg_domain_age,
            SUM(estimated_revenue) as total_market_value
        FROM fully_enriched_smbs
    """)
    
    stats = dict(cursor.fetchone())
    
    # Technology breakdown
    cursor.execute("""
        SELECT technology_signals, COUNT(*) as count
        FROM fully_enriched_smbs
        WHERE technology_signals != '[]' AND technology_signals IS NOT NULL
        GROUP BY technology_signals
    """)
    
    tech_counts = {}
    for row in cursor.fetchall():
        techs = json.loads(row['technology_signals'])
        for tech in techs:
            tech_counts[tech] = tech_counts.get(tech, 0) + row['count']
    
    conn.close()
    
    return {
        "overview": stats,
        "technology_usage": tech_counts,
        "insights": {
            "digital_presence_rate": f"{stats['with_websites']/stats['total_businesses']*100:.1f}%",
            "google_visibility_rate": f"{stats['with_google']/stats['total_businesses']*100:.1f}%",
            "immediate_opportunities": stats['high_risk_count'],
            "market_value_at_risk": stats['total_market_value'] * (stats['high_risk_count'] / stats['total_businesses'])
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
