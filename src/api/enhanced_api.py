from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn

app = FastAPI(title="Enhanced SMB Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Enhanced SMB Intelligence API",
        "endpoints": {
            "/enhanced/search": "Search with Google data",
            "/enhanced/top-opportunities": "Best succession targets"
        }
    }

@app.get("/enhanced/top-opportunities")
def get_top_opportunities(
    min_risk: float = Query(7.0, description="Minimum succession risk"),
    has_google: bool = Query(False, description="Must have Google presence"),
    limit: int = Query(20)
):
    conn = sqlite3.connect("smb_intelligence_enhanced.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
    SELECT 
        organization_name,
        city,
        state,
        google_rating,
        google_reviews_count,
        digital_presence_score,
        succession_risk_score,
        estimated_revenue,
        company_logo_url
    FROM enriched_smbs_v2
    WHERE succession_risk_score >= ?
    """
    
    params = [min_risk]
    
    if has_google:
        query += " AND google_rating IS NOT NULL"
    
    query += " ORDER BY succession_risk_score DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "count": len(results),
        "opportunities": results
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
