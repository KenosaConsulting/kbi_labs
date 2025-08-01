from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
from decimal import Decimal
import json

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
        
        formatted_companies = []
        for company in all_companies:
            revenue = float(company['revenue']) if company['revenue'] else 0
            contracts = int(company['contracts']) if company['contracts'] else 0
            
            if revenue > 6000000:
                employees = 67
            elif revenue > 4000000:
                employees = 47  
            elif revenue > 2000000:
                employees = 33
            else:
                employees = 23
            
            revenue_score = min(40, (revenue / 10000000) * 40)
            contracts_score = min(30, (contracts / 100) * 30)
            kbi_score = int(revenue_score + contracts_score + 30)
            
            formatted_companies.append({
                "id": company['id'],
                "name": company['name'],
                "industry": company['industry'],
                "location": company['location'],
                "revenue": f"${revenue/1000000:.1f}M",
                "employees": employees,
                "kbi_score": min(100, kbi_score)
            })
        
        paginated = formatted_companies[skip:skip+limit]
        
        cursor.close()
        conn.close()
        
        return {
            "companies": paginated,
            "total": len(formatted_companies),
            "totalCount": len(formatted_companies)
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"companies": [], "totalCount": 0}

@app.get("/api/v1/companies/{company_id}")
def get_company_details(company_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                uei as id,
                organization_name as name,
                dba_name,
                CASE 
                    WHEN primary_naics LIKE '54%' THEN 'Technology'
                    WHEN primary_naics LIKE '22%' THEN 'Energy'
                    WHEN primary_naics LIKE '62%' THEN 'Healthcare'
                    WHEN primary_naics LIKE '23%' THEN 'Construction'
                    WHEN primary_naics LIKE '33%' THEN 'Manufacturing'
                    ELSE 'Other'
                END as industry,
                primary_naics,
                address_line_1,
                address_line_2,
                city,
                state,
                zipcode,
                website,
                phone_number,
                federal_contracts_value as revenue,
                federal_contracts_count as contracts,
                cage_code,
                sam_registration_status,
                sam_registration_date,
                entity_type,
                business_start_date,
                employee_count,
                annual_revenue,
                socioeconomic_categories,
                clearance_level,
                grants_received,
                patent_count,
                enrichment_status,
                last_enriched_at,
                created_at,
                updated_at
            FROM enriched_companies
            WHERE uei = %s
        """
        
        cursor.execute(query, (company_id,))
        company = cursor.fetchone()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Convert values
        revenue = float(company['revenue']) if company['revenue'] else 0
        contracts = int(company['contracts']) if company['contracts'] else 0
        
        # Calculate scores
        revenue_score = min(40, (revenue / 10000000) * 40)
        contracts_score = min(30, (contracts / 100) * 30)
        kbi_score = int(revenue_score + contracts_score + 30)
        
        # Calculate risk score (simplified)
        risk_score = 100 - kbi_score
        
        cursor.close()
        conn.close()
        
        return {
            "id": company['id'],
            "name": company['name'],
            "dba_name": company['dba_name'],
            "industry": company['industry'],
            "naics_code": company['primary_naics'],
            "address": {
                "line1": company['address_line_1'],
                "line2": company['address_line_2'],
                "city": company['city'],
                "state": company['state'],
                "zipcode": company['zipcode']
            },
            "contact": {
                "website": company['website'],
                "phone": company['phone_number']
            },
            "financials": {
                "revenue": f"${revenue/1000000:.1f}M",
                "revenue_raw": revenue,
                "contracts_count": contracts,
                "grants_received": company['grants_received'] or 0,
                "annual_revenue": company['annual_revenue']
            },
            "certifications": {
                "cage_code": company['cage_code'],
                "sam_status": company['sam_registration_status'],
                "sam_date": str(company['sam_registration_date']) if company['sam_registration_date'] else None,
                "clearance_level": company['clearance_level'],
                "socioeconomic": json.loads(company['socioeconomic_categories']) if company['socioeconomic_categories'] else []
            },
            "metrics": {
                "kbi_score": min(100, kbi_score),
                "risk_score": risk_score,
                "patent_count": company['patent_count'] or 0,
                "employee_count": company['employee_count'] or 0,
                "business_age": "5 years"  # Calculate from business_start_date
            },
            "enrichment": {
                "status": json.loads(company['enrichment_status']) if company['enrichment_status'] else {},
                "last_updated": str(company['last_enriched_at']) if company['last_enriched_at'] else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics")
def get_analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get overall stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_companies,
                COALESCE(SUM(federal_contracts_value), 0) as total_revenue,
                COALESCE(AVG(federal_contracts_value), 0) as avg_revenue,
                COUNT(DISTINCT state) as state_count
            FROM enriched_companies
        """)
        stats = cursor.fetchone()
        
        # Get industry breakdown
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN primary_naics LIKE '54%' THEN 'Technology'
                    WHEN primary_naics LIKE '22%' THEN 'Energy'
                    WHEN primary_naics LIKE '62%' THEN 'Healthcare'
                    WHEN primary_naics LIKE '23%' THEN 'Construction'
                    WHEN primary_naics LIKE '33%' THEN 'Manufacturing'
                    ELSE 'Other'
                END as industry,
                COUNT(*) as count,
                SUM(federal_contracts_value) as revenue
            FROM enriched_companies
            GROUP BY industry
            ORDER BY revenue DESC
        """)
        industries = cursor.fetchall()
        
        # Get top states
        cursor.execute("""
            SELECT 
                state,
                COUNT(*) as count,
                SUM(federal_contracts_value) as revenue
            FROM enriched_companies
            GROUP BY state
            ORDER BY revenue DESC
            LIMIT 5
        """)
        states = cursor.fetchall()
        
        # Get revenue trends (mock data for now)
        trends = [
            {"month": "Jan", "revenue": 2.5},
            {"month": "Feb", "revenue": 3.1},
            {"month": "Mar", "revenue": 2.8},
            {"month": "Apr", "revenue": 3.5},
            {"month": "May", "revenue": 4.2},
            {"month": "Jun", "revenue": 4.8}
        ]
        
        cursor.close()
        conn.close()
        
        return {
            "overview": {
                "totalCompanies": stats['total_companies'],
                "totalRevenue": f"${float(stats['total_revenue'])/1000000:.1f}M",
                "avgRevenue": f"${float(stats['avg_revenue'])/1000000:.1f}M",
                "stateCount": stats['state_count']
            },
            "industries": [
                {
                    "name": ind['industry'],
                    "count": ind['count'],
                    "revenue": float(ind['revenue'])
                } for ind in industries
            ],
            "topStates": [
                {
                    "state": st['state'],
                    "count": st['count'],
                    "revenue": float(st['revenue'])
                } for st in states
            ],
            "revenueTrends": trends
        }
        
    except Exception as e:
        print(f"Analytics error: {e}")
        return {
            "overview": {
                "totalCompanies": 0,
                "totalRevenue": "$0M",
                "avgRevenue": "$0M",
                "stateCount": 0
            },
            "industries": [],
            "topStates": [],
            "revenueTrends": []
        }

@app.get("/api/v1/kpis")
def get_kpis():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_companies,
                SUM(federal_contracts_value) as total_revenue
            FROM enriched_companies
        """)
        
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        total_revenue = float(result['total_revenue']) if result['total_revenue'] else 0
        
        return {
            "totalCompanies": result['total_companies'],
            "totalRevenue": total_revenue,
            "avgKBIScore": 75,
            "activeDeals": result['total_companies']
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
