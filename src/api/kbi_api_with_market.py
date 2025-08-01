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

# Mock data for company details
MOCK_COMPANIES = {
    "HEALTH345678901": {
        "id": "HEALTH345678901",
        "name": "HealthTech Pro",
        "dba_name": "HealthTech Professional Services",
        "industry": "Healthcare",
        "naics_code": "621111",
        "address": {
            "line1": "123 Medical Plaza",
            "line2": "Suite 500",
            "city": "Boston",
            "state": "MA",
            "zipcode": "02110"
        },
        "contact": {
            "website": "https://healthtechpro.com",
            "phone": "(617) 555-0100"
        },
        "financials": {
            "revenue": "$7.1M",
            "revenue_raw": 7100000,
            "contracts_count": 22,
            "grants_received": 3,
            "annual_revenue": "$7.1M"
        },
        "certifications": {
            "cage_code": "1ABC2",
            "sam_status": "Active",
            "sam_date": "2023-01-15",
            "clearance_level": "Public Trust",
            "socioeconomic": ["Woman-Owned", "Small Business"]
        },
        "metrics": {
            "kbi_score": 88,
            "risk_score": 12,
            "patent_count": 5,
            "employee_count": 67,
            "business_age": "8 years"
        },
        "enrichment": {
            "status": {"status": "completed", "apis": ["sam", "clearbit", "patents"]},
            "last_updated": "2024-03-15"
        }
    },
    "CYBER678901234": {
        "id": "CYBER678901234",
        "name": "CyberShield Security",
        "dba_name": None,
        "industry": "Technology",
        "naics_code": "541512",
        "address": {
            "line1": "2000 Pentagon Row",
            "line2": None,
            "city": "Arlington",
            "state": "VA",
            "zipcode": "22202"
        },
        "contact": {
            "website": "https://cybershieldsec.com",
            "phone": "(703) 555-0200"
        },
        "financials": {
            "revenue": "$6.8M",
            "revenue_raw": 6800000,
            "contracts_count": 25,
            "grants_received": 0,
            "annual_revenue": "$6.8M"
        },
        "certifications": {
            "cage_code": "2DEF3",
            "sam_status": "Active",
            "sam_date": "2022-06-20",
            "clearance_level": "Secret",
            "socioeconomic": ["Veteran-Owned", "Small Business"]
        },
        "metrics": {
            "kbi_score": 85,
            "risk_score": 15,
            "patent_count": 12,
            "employee_count": 67,
            "business_age": "6 years"
        },
        "enrichment": {
            "status": {"status": "completed", "apis": ["sam", "clearbit"]},
            "last_updated": "2024-03-10"
        }
    },
    "TECH123456789": {
        "id": "TECH123456789",
        "name": "TechCorp Solutions",
        "dba_name": "TechCorp",
        "industry": "Technology",
        "naics_code": "541511",
        "address": {
            "line1": "100 Innovation Way",
            "line2": None,
            "city": "San Francisco",
            "state": "CA",
            "zipcode": "94105"
        },
        "contact": {
            "website": "https://techcorpsolutions.com",
            "phone": "(415) 555-0300"
        },
        "financials": {
            "revenue": "$5.2M",
            "revenue_raw": 5200000,
            "contracts_count": 15,
            "grants_received": 2,
            "annual_revenue": "$5.2M"
        },
        "certifications": {
            "cage_code": "3GHI4",
            "sam_status": "Active",
            "sam_date": "2023-03-10",
            "clearance_level": None,
            "socioeconomic": ["Small Business"]
        },
        "metrics": {
            "kbi_score": 78,
            "risk_score": 22,
            "patent_count": 8,
            "employee_count": 45,
            "business_age": "5 years"
        },
        "enrichment": {
            "status": {"status": "completed", "apis": ["sam"]},
            "last_updated": "2024-03-01"
        }
    }
}

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
    # Return mock data for now
    if company_id in MOCK_COMPANIES:
        return MOCK_COMPANIES[company_id]
    
    # For other companies, return a generic response
    return {
        "id": company_id,
        "name": "Company Details",
        "dba_name": None,
        "industry": "Other",
        "naics_code": "000000",
        "address": {
            "line1": "123 Main Street",
            "line2": None,
            "city": "City",
            "state": "ST",
            "zipcode": "00000"
        },
        "contact": {
            "website": "https://example.com",
            "phone": "(555) 555-5555"
        },
        "financials": {
            "revenue": "$0M",
            "revenue_raw": 0,
            "contracts_count": 0,
            "grants_received": 0,
            "annual_revenue": "$0M"
        },
        "certifications": {
            "cage_code": "00000",
            "sam_status": "Active",
            "sam_date": "2024-01-01",
            "clearance_level": None,
            "socioeconomic": []
        },
        "metrics": {
            "kbi_score": 50,
            "risk_score": 50,
            "patent_count": 0,
            "employee_count": 0,
            "business_age": "N/A"
        },
        "enrichment": {
            "status": {"status": "pending"},
            "last_updated": None
        }
    }

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
