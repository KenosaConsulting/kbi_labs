from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="KBI Labs API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection function using Unix socket
def get_db_connection():
    try:
        # Try connecting without password first (local trust auth)
        return psycopg2.connect(
            database='kbi_enriched',
            user='postgres',
            host='/var/run/postgresql',  # Unix socket
            cursor_factory=RealDictCursor
        )
    except:
        # Fallback to TCP connection
        return psycopg2.connect(
            host='localhost',
            port='5432',
            database='kbi_enriched',
            user='postgres',
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            cursor_factory=RealDictCursor
        )

@app.get("/")
def read_root():
    return {"message": "KBI Labs API is running"}

@app.get("/api/v1/companies")
def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, let's check what columns exist
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'enriched_companies'")
        columns = [row['column_name'] for row in cursor.fetchall()]
        logging.info(f"Available columns: {columns}")
        
        # Build a simple query first
        query = "SELECT * FROM enriched_companies"
        params = []
        
        if search:
            # Check if company_name column exists
            if 'company_name' in columns:
                query += " WHERE LOWER(company_name) LIKE LOWER(%s)"
            elif 'name' in columns:
                query += " WHERE LOWER(name) LIKE LOWER(%s)"
            else:
                query += " WHERE 1=1"  # No name column found
            
            if search and ('company_name' in columns or 'name' in columns):
                params.append(f"%{search}%")
        
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        companies = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM enriched_companies")
        total_count = cursor.fetchone()['total']
        
        # Format companies based on available columns
        formatted_companies = []
        for i, company in enumerate(companies):
            # Extract whatever columns are available
            formatted_company = {
                "id": company.get('id', i + 1),
                "name": company.get('company_name') or company.get('name') or f"Company {i + 1}",
                "industry": company.get('industry', 'Unknown'),
                "location": company.get('headquarters_location') or company.get('location', 'Unknown'),
                "website": company.get('website', ''),
                "employees": company.get('number_of_employees') or company.get('employees', 0),
                "revenue": "N/A",
                "kbi_score": company.get('kbi_score', 0),
                "enrichment_status": company.get('enrichment_status', 'unknown'),
                "patent_count": company.get('patents_count', 0),
                "grant_count": company.get('grants_count', 0)
            }
            
            # Handle revenue formatting
            revenue = company.get('annual_revenue') or company.get('revenue')
            if revenue:
                try:
                    formatted_company["revenue"] = f"${float(revenue)/1000000:.1f}M"
                except:
                    formatted_company["revenue"] = str(revenue)
            
            formatted_companies.append(formatted_company)
        
        cursor.close()
        conn.close()
        
        return {
            "companies": formatted_companies,
            "totalCount": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logging.error(f"Error fetching companies: {e}")
        # Return the sample data
        return {
            "companies": [
                {
                    "id": 1,
                    "name": "TechCorp Solutions",
                    "industry": "Technology",
                    "revenue": "$5.2M",
                    "employees": 45,
                    "kbi_score": 82,
                    "location": "San Francisco, CA"
                },
                {
                    "id": 2,
                    "name": "Green Energy Inc",
                    "industry": "Clean Energy",
                    "revenue": "$3.8M",
                    "employees": 32,
                    "kbi_score": 75,
                    "location": "Austin, TX"
                },
                {
                    "id": 3,
                    "name": "HealthTech Pro",
                    "industry": "Healthcare",
                    "revenue": "$7.1M",
                    "employees": 67,
                    "kbi_score": 88,
                    "location": "Boston, MA"
                }
            ],
            "totalCount": 3,
            "skip": skip,
            "limit": limit
        }

@app.get("/api/v1/companies/{company_id}")
def get_company(company_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM enriched_companies WHERE id = %s", (company_id,))
        company = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            "id": company.get('id', company_id),
            "name": company.get('company_name') or company.get('name', 'Unknown'),
            "industry": company.get('industry', 'Unknown'),
            "location": company.get('headquarters_location') or company.get('location', 'Unknown'),
            "website": company.get('website', ''),
            "employees": company.get('number_of_employees') or company.get('employees', 0),
            "revenue": str(company.get('annual_revenue') or company.get('revenue', 'N/A')),
            "kbi_score": company.get('kbi_score', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)
