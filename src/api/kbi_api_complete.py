from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from decimal import Decimal

app = FastAPI()

# Configure CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_db_connection():
    return psycopg2.connect(
        database='kbi_enriched',
        user='postgres',
        host='/var/run/postgresql',
        port='5433',
        cursor_factory=RealDictCursor
    )

@app.get("/")
def root():
    return {"message": "KBI Labs API", "version": "1.0"}

@app.get("/api/v1/companies")
def get_companies(skip: int = 0, limit: int = 20, search: str = None):
    print(f"API Called - skip: {skip}, limit: {limit}, search: {search}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First get total count
        cursor.execute("SELECT COUNT(*) as total FROM enriched_companies")
        total_count = cursor.fetchone()['total']
        
        # Get companies with proper pagination
        query = """
            SELECT 
                uei as id,
                organization_name as name,
                CASE 
                    WHEN primary_naics LIKE '54%' THEN 'Technology'
                    WHEN primary_naics LIKE '22%' THEN 'Energy'
                    WHEN primary_naics LIKE '62%' THEN 'Healthcare'
                    WHEN primary_naics LIKE '23%' THEN 'Construction'
                    WHEN primary_naics LIKE '33%' THEN 'Manufacturing'
                    ELSE 'Other'
                END as industry,
                city || ', ' || state as location,
                COALESCE(website, '') as website,
                COALESCE(federal_contracts_value, 0) as revenue,
                COALESCE(federal_contracts_count, 0) as contracts
            FROM enriched_companies
            WHERE organization_name IS NOT NULL
            ORDER BY federal_contracts_value DESC NULLS LAST
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (limit, skip))
        companies_raw = cursor.fetchall()
        
        # Format companies with proper error handling
        companies = []
        for company in companies_raw:
            try:
                revenue = float(company['revenue']) if company['revenue'] else 0
                
                # Calculate employees based on revenue
                if revenue > 6000000:
                    employees = 67
                elif revenue > 4000000:
                    employees = 47
                elif revenue > 2000000:
                    employees = 33
                elif revenue > 1000000:
                    employees = 23
                elif revenue > 100000:
                    employees = 11
                else:
                    employees = 7
                
                # Calculate KBI score
                revenue_score = min(40, (revenue / 10000000) * 40) if revenue else 0
                contracts_score = min(30, (company['contracts'] / 100) * 30) if company['contracts'] else 0
                base_score = 30
                kbi_score = int(revenue_score + contracts_score + base_score)
                
                companies.append({
                    "id": company['id'],
                    "name": company['name'][:50] if company['name'] else "Unknown Company",
                    "industry": company['industry'],
                    "location": company['location'] if company['location'] else "Unknown Location",
                    "revenue": f"${revenue/1000000:.1f}M" if revenue > 0 else "$0M",
                    "revenue_raw": revenue,
                    "employees": employees,
                    "kbi_score": min(100, kbi_score),
                    "contracts_count": company['contracts']
                })
            except Exception as e:
                print(f"Error processing company: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        response = {
            "companies": companies,
            "total": total_count,
            "totalCount": total_count,  # For backwards compatibility
            "page": (skip // limit) + 1,
            "totalPages": (total_count + limit - 1) // limit,
            "status": "success"
        }
        
        print(f"Returning {len(companies)} companies")
        return response
        
    except Exception as e:
        print(f"Database error: {e}")
        return {
            "companies": [],
            "total": 0,
            "totalCount": 0,
            "page": 1,
            "totalPages": 0,
            "status": "error",
            "message": str(e)
        }

@app.get("/api/v1/kpis")
def get_kpis():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_companies,
                COALESCE(SUM(federal_contracts_value), 0) as total_revenue,
                COUNT(CASE WHEN federal_contracts_count > 5 THEN 1 END) as active_deals
            FROM enriched_companies
        """)
        
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            "totalCompanies": result['total_companies'],
            "totalRevenue": float(result['total_revenue']) if result['total_revenue'] else 0,
            "avgKBIScore": 75,
            "activeDeals": result['active_deals'] if result['active_deals'] else 0
        }
    except Exception as e:
        print(f"KPI Error: {e}")
        return {
            "totalCompanies": 0,
            "totalRevenue": 0,
            "avgKBIScore": 0,
            "activeDeals": 0
        }

if __name__ == "__main__":
    print("Starting KBI Labs API on port 9999...")
    uvicorn.run(app, host="0.0.0.0", port=9999)
