from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(
        database='kbi_enriched',
        user='postgres',
        host='/var/run/postgresql',
        port='5433',
        cursor_factory=RealDictCursor
    )

@app.get("/api/v1/companies")
def get_companies(skip: int = 0, limit: int = 20, search: str = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all companies
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
                website,
                federal_contracts_value as revenue,
                federal_contracts_count as contracts
            FROM enriched_companies
            ORDER BY federal_contracts_value DESC
        """
        
        cursor.execute(query)
        all_companies = cursor.fetchall()
        
        # Format companies
        formatted_companies = []
        for company in all_companies:
            if company['revenue'] > 6000000:
                employees = 67
            elif company['revenue'] > 4000000:
                employees = 47
            elif company['revenue'] > 2000000:
                employees = 33
            elif company['revenue'] > 1000000:
                employees = 23
            elif company['revenue'] > 100000:
                employees = 11
            else:
                employees = 7
            
            # Calculate KBI score
            revenue_score = min(40, (company['revenue'] / 10000000) * 40)
            contracts_score = min(30, (company['contracts'] / 100) * 30)
            base_score = 30
            kbi_score = int(revenue_score + contracts_score + base_score)
            
            formatted_companies.append({
                "id": company['id'],
                "name": company['name'],
                "industry": company['industry'],
                "location": company['location'],
                "website": company['website'] or '',
                "employees": employees,
                "revenue": f"${company['revenue']/1000000:.1f}M",
                "revenue_raw": company['revenue'],
                "kbi_score": min(100, kbi_score),
                "contracts_count": company['contracts']
            })
        
        # Apply pagination
        start = skip
        end = skip + limit
        paginated_companies = formatted_companies[start:end]
        
        cursor.close()
        conn.close()
        
        return {
            "companies": paginated_companies,
            "total": len(formatted_companies),
            "totalCount": len(formatted_companies),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"companies": [], "totalCount": 0}

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
    uvicorn.run(app, host="0.0.0.0", port=9999)
