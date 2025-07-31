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

@app.get("/api/v1/companies")
def get_companies(skip: int = 0, limit: int = 20):
    print(f"\n=== API CALLED: skip={skip}, limit={limit} ===")
    
    try:
        print("1. Attempting database connection...")
        conn = psycopg2.connect(
            database='kbi_enriched',
            user='postgres',
            host='/var/run/postgresql',
            port='5433',
            cursor_factory=RealDictCursor
        )
        print("2. Connected successfully!")
        
        cursor = conn.cursor()
        
        # Simple query first
        print("3. Executing count query...")
        cursor.execute("SELECT COUNT(*) as total FROM enriched_companies")
        total = cursor.fetchone()['total']
        print(f"4. Found {total} companies in database")
        
        # Get companies
        print("5. Fetching companies...")
        query = """
            SELECT 
                uei as id,
                organization_name as name,
                city || ', ' || state as location,
                federal_contracts_value as revenue
            FROM enriched_companies
            ORDER BY federal_contracts_value DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, skip))
        companies = cursor.fetchall()
        print(f"6. Retrieved {len(companies)} companies")
        
        # Format response
        result = []
        for company in companies:
            result.append({
                "id": company['id'],
                "name": company['name'],
                "industry": "Technology",  # Simplified for now
                "location": company['location'],
                "revenue": f"${float(company['revenue'])/1000000:.1f}M",
                "employees": 50,
                "kbi_score": 75
            })
        
        cursor.close()
        conn.close()
        
        print("7. Returning real data")
        return {
            "companies": result,
            "totalCount": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        print("8. Returning fallback data")
        return {
            "companies": [
                {"id": "1", "name": "Fallback Company", "industry": "Error", "revenue": "$0M", "employees": 0, "kbi_score": 0}
            ],
            "totalCount": 1,
            "skip": skip,
            "limit": limit,
            "error": str(e)
        }

if __name__ == "__main__":
    print("Starting KBI API Debug Server...")
    uvicorn.run(app, host="0.0.0.0", port=9999)
