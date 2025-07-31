#!/usr/bin/env python3
"""
Simplified Government Contractor API Server
Runs independently without complex database dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import uvicorn
import json
import os

# Load real company data
def load_company_data():
    """Load company data from JSON file"""
    try:
        with open('companies.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  companies.json not found, using mock data")
        return []

# Global data store
COMPANIES_DATA = load_company_data()

# Create FastAPI app
app = FastAPI(
    title="KBI Labs Government Contractor API",
    description="Simplified API for Government Contractor Dashboard Demo",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "KBI Labs Government Contractor API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Government Contractor API"
    }

def calculate_dashboard_metrics():
    """Calculate real metrics from company data"""
    if not COMPANIES_DATA:
        return {
            "totalCompanies": 0,
            "avgInvestmentScore": 0,
            "totalContracts": 0,
            "naicsBreakdown": {}
        }
    
    total_companies = len(COMPANIES_DATA)
    total_investment_score = sum(c.get('pe_investment_score', 0) for c in COMPANIES_DATA)
    avg_investment_score = total_investment_score / total_companies if total_companies > 0 else 0
    
    # Count companies with federal contracts
    companies_with_contracts = [c for c in COMPANIES_DATA if c.get('federal_contracts_value', 0) > 0]
    total_contract_value = sum(c.get('federal_contracts_value', 0) for c in COMPANIES_DATA)
    
    # NAICS breakdown
    naics_count = {}
    for company in COMPANIES_DATA:
        naics = company.get('primary_naics', 'Unknown')
        naics_count[naics] = naics_count.get(naics, 0) + 1
    
    return {
        "totalCompanies": total_companies,
        "avgInvestmentScore": round(avg_investment_score, 1),
        "companiesWithContracts": len(companies_with_contracts),
        "totalContractValue": total_contract_value,
        "naicsBreakdown": naics_count
    }

@app.get("/api/v1/government-contractor/")
async def get_government_contractor_data():
    """Get comprehensive government contractor dashboard data"""
    metrics = calculate_dashboard_metrics()
    
    return {
        "complianceStatus": {
            "cmmc": {
                "level": "Level 2",
                "status": "In Progress",
                "score": 75,
                "nextAssessment": "2025-09-15"
            },
            "dfars": {
                "status": "Compliant",
                "score": 90,
                "lastAudit": "2024-12-01"
            },
            "fedramp": {
                "status": "Not Required",
                "cloudProvider": "AWS GovCloud",
                "authorized": True
            }
        },
        "contractPipeline": {
            "active": metrics["companiesWithContracts"],
            "pending": 8,
            "totalValue": metrics["totalContractValue"],
            "winRate": 68
        },
        "naicsAnalysis": {
            "primary": "541511",
            "secondary": ["541512", "541330", "541519"],
            "opportunities": 45,
            "competition": "Medium"
        },
        "performance": {
            "cpars": 4.2,
            "pastPerformance": "Excellent",
            "onTimeDelivery": 94,
            "qualityScore": 4.6
        },
        "realData": {
            "totalCompanies": metrics["totalCompanies"],
            "avgInvestmentScore": metrics["avgInvestmentScore"],
            "naicsBreakdown": metrics["naicsBreakdown"]
        }
    }

@app.get("/api/v1/companies")
async def get_companies(limit: int = 20, offset: int = 0, naics: Optional[str] = None):
    """Get company data with filtering"""
    companies = COMPANIES_DATA
    
    # Filter by NAICS if provided
    if naics:
        companies = [c for c in companies if c.get('primary_naics') == naics]
    
    # Pagination
    total = len(companies)
    companies = companies[offset:offset + limit]
    
    return {
        "companies": companies,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/government-contractor/compliance/cmmc")
async def get_cmmc_compliance():
    """Get detailed CMMC compliance status"""
    return {
        "level": "Level 2",
        "status": "In Progress",
        "score": 75,
        "requiredControls": 110,
        "implementedControls": 83,
        "nextAssessment": "2025-09-15",
        "assessor": "TBD",
        "documentation": {
            "ssp": "90% Complete",
            "poam": "In Review",
            "evidenceCollection": "75% Complete"
        },
        "gapAnalysis": [
            {
                "control": "AC.1.001",
                "status": "Partially Implemented",
                "priority": "High",
                "description": "Limit information system access to authorized users"
            },
            {
                "control": "AC.1.002", 
                "status": "Not Implemented",
                "priority": "Medium",
                "description": "Limit information system access to the types of transactions"
            }
        ]
    }

@app.get("/api/v1/government-contractor/compliance/dfars")
async def get_dfars_compliance():
    """Get detailed DFARS compliance status"""
    return {
        "status": "Compliant",
        "score": 90,
        "lastAudit": "2024-12-01",
        "nextAudit": "2025-12-01",
        "nistControls": {
            "total": 110,
            "implemented": 99,
            "partiallyImplemented": 8,
            "notImplemented": 3
        },
        "businessSystems": {
            "accounting": "Adequate",
            "purchasing": "Adequate", 
            "estimating": "Adequate",
            "compensation": "Adequate",
            "material": "Adequate",
            "subcontractor": "Needs Improvement"
        },
        "incidentReporting": {
            "lastIncident": None,
            "reportingCompliant": True,
            "proceduresUpdated": "2024-11-15"
        }
    }

@app.get("/api/v1/government-contractor/compliance/fedramp")
async def get_fedramp_status():
    """Get FedRAMP compliance status"""
    return {
        "required": False,
        "cloudProvider": "AWS GovCloud",
        "authorized": True,
        "level": "Moderate",
        "authorizationDate": "2024-06-15",
        "expirationDate": "2027-06-15",
        "services": [
            {
                "name": "KBI Labs Platform",
                "status": "Authorized",
                "level": "Moderate"
            }
        ],
        "assessment": {
            "lastAssessment": "2024-06-01",
            "nextAssessment": "2025-06-01",
            "assessor": "Third Party"
        }
    }

def calculate_opportunity_match_score(opportunity: Dict, user_naics: str = None) -> int:
    """Calculate how well an opportunity matches the user's profile"""
    score = 50  # Base score
    
    # NAICS code match
    if user_naics and opportunity.get("naics") == user_naics:
        score += 30
    elif user_naics and opportunity.get("naics", "").startswith(user_naics[:4]):
        score += 15
    
    # Set-aside advantages
    set_aside = opportunity.get("setAside", "").lower()
    if "8(a)" in set_aside or "small business" in set_aside:
        score += 10
    if "service-disabled" in set_aside or "veteran" in set_aside:
        score += 5
    if "women-owned" in set_aside:
        score += 5
    
    # Recent posting (more recent = higher score)
    posted_date = opportunity.get("postedDate", "")
    if "2025-01" in posted_date:
        score += 10
    elif "2025" in posted_date:
        score += 5
    
    return min(score, 100)  # Cap at 100

def extract_requirements(description: str) -> List[str]:
    """Extract key requirements from opportunity description"""
    requirements = []
    description_lower = description.lower()
    
    if "cmmc" in description_lower:
        if "level 2" in description_lower:
            requirements.append("CMMC Level 2 Required")
        else:
            requirements.append("CMMC Compliance Required")
    
    if "fedramp" in description_lower:
        requirements.append("FedRAMP Experience Preferred")
    
    if "security clearance" in description_lower:
        requirements.append("Security Clearance Required")
    
    if "past performance" in description_lower:
        requirements.append("Past Performance Required")
    
    if "nist" in description_lower:
        requirements.append("NIST Framework Experience")
    
    return requirements

def estimate_contract_value(description: str) -> str:
    """Estimate contract value from description"""
    description_lower = description.lower()
    
    if "enterprise" in description_lower or "large scale" in description_lower:
        return "$5,000,000 - $25,000,000"
    elif "comprehensive" in description_lower or "full service" in description_lower:
        return "$1,000,000 - $5,000,000"
    elif "consulting" in description_lower or "advisory" in description_lower:
        return "$500,000 - $2,000,000"
    else:
        return "$100,000 - $1,000,000"

def assess_competition_level(set_aside: str) -> str:
    """Assess competition level based on set-aside type"""
    if not set_aside:
        return "High"
    
    set_aside_lower = set_aside.lower()
    if "8(a)" in set_aside_lower:
        return "Low"
    elif "small business" in set_aside_lower:
        return "Medium"
    elif "unrestricted" in set_aside_lower:
        return "High"
    else:
        return "Medium"

@app.get("/api/v1/government-contractor/opportunities")
async def get_contract_opportunities(
    naics: Optional[str] = None,
    keywords: Optional[str] = None,
    limit: int = 20
):
    """Get relevant contract opportunities"""
    # Mock opportunities data
    mock_opportunities = [
        {
            "id": "SP060025Q0801",
            "title": "IT Support Services - Cybersecurity Implementation",
            "agency": "Department of Defense",
            "office": "Defense Information Systems Agency",
            "naics": "541511",
            "setAside": "8(a) Small Business",
            "postedDate": "2025-01-15",
            "responseDeadline": "2025-03-15",
            "type": "Solicitation",
            "baseType": "Combined Synopsis/Solicitation",
            "description": "The Department of Defense requires comprehensive IT support services including cybersecurity implementation, CMMC compliance assistance, and system modernization. Contractors must demonstrate CMMC Level 2 certification and experience with DoD security requirements."
        },
        {
            "id": "IN12568",
            "title": "Cybersecurity Consulting and Risk Assessment",
            "agency": "Department of Homeland Security",
            "office": "Cybersecurity and Infrastructure Security Agency",
            "naics": "541512",
            "setAside": "Service-Disabled Veteran-Owned Small Business",
            "postedDate": "2025-01-20",
            "responseDeadline": "2025-04-01",
            "type": "Solicitation",
            "baseType": "Request for Proposals",
            "description": "DHS CISA seeks cybersecurity consulting services to conduct risk assessments, develop security frameworks, and provide ongoing security monitoring. Experience with FedRAMP, NIST frameworks, and federal compliance required."
        },
        {
            "id": "GS060025R0123",
            "title": "Cloud Migration and Modernization Services",
            "agency": "General Services Administration",
            "office": "Technology Transformation Services",
            "naics": "541519",
            "setAside": "Women-Owned Small Business",
            "postedDate": "2025-01-25",
            "responseDeadline": "2025-04-15",
            "type": "Sources Sought",
            "baseType": "Market Research",
            "description": "GSA is conducting market research for cloud migration services to move legacy systems to FedRAMP authorized cloud platforms. Seeking contractors with experience in AWS GovCloud, Azure Government, and Google Cloud for Government."
        }
    ]
    
    # Filter by NAICS if provided
    if naics:
        mock_opportunities = [opp for opp in mock_opportunities if opp["naics"] == naics]
    
    # Filter by keywords if provided
    if keywords:
        keywords_lower = keywords.lower()
        mock_opportunities = [
            opp for opp in mock_opportunities 
            if keywords_lower in opp["title"].lower() or keywords_lower in opp["description"].lower()
        ]
    
    # Enhance opportunities with match scoring
    enhanced_opportunities = []
    for opp in mock_opportunities:
        match_score = calculate_opportunity_match_score(opp, naics)
        
        enhanced_opp = {
            **opp,
            "matchScore": match_score,
            "requirements": extract_requirements(opp.get("description", "")),
            "estimatedValue": estimate_contract_value(opp.get("description", "")),
            "competitionLevel": assess_competition_level(opp.get("setAside"))
        }
        enhanced_opportunities.append(enhanced_opp)
    
    # Sort by match score
    enhanced_opportunities.sort(key=lambda x: x.get("matchScore", 0), reverse=True)
    
    return {
        "total": len(enhanced_opportunities),
        "opportunities": enhanced_opportunities,
        "filters": {
            "naics": naics,
            "keywords": keywords,
            "limit": limit
        }
    }

@app.get("/api/v1/government-contractor/performance/cpars")
async def get_cpars_data():
    """Get CPARS performance data"""
    return {
        "overallRating": 4.2,
        "ratingHistory": [
            {"period": "2024", "rating": 4.2, "contracts": 5},
            {"period": "2023", "rating": 4.0, "contracts": 3},
            {"period": "2022", "rating": 4.1, "contracts": 4}
        ],
        "categories": {
            "qualityOfProduct": 4.4,
            "timeliness": 4.0,
            "costControl": 4.3,
            "businessRelations": 4.1,
            "management": 4.2,
            "keyPersonnel": 4.5
        },
        "recentEvaluations": [
            {
                "contractNumber": "HQ0034-21-D-0001",
                "period": "2024-01 to 2024-12",
                "rating": 4.2,
                "narrative": "Contractor performed satisfactorily with minor areas for improvement"
            }
        ]
    }

@app.get("/api/v1/government-contractor/analytics/naics")
async def get_naics_analytics():
    """Get NAICS code market analysis"""
    return {
        "primary": {
            "code": "541511",
            "description": "Custom Computer Programming Services",
            "marketSize": 15600000000,  # $15.6B
            "growthRate": 8.2,
            "competitorCount": 12500,
            "avgContractValue": 875000
        },
        "secondary": [
            {
                "code": "541512", 
                "description": "Computer Systems Design Services",
                "opportunities": 28,
                "avgValue": 1200000
            },
            {
                "code": "541330",
                "description": "Engineering Services", 
                "opportunities": 12,
                "avgValue": 650000
            }
        ],
        "trendAnalysis": {
            "emerging": ["Artificial Intelligence", "Cybersecurity", "Cloud Migration"],
            "declining": ["Legacy System Maintenance"],
            "stable": ["Software Development", "System Integration"]
        }
    }

if __name__ == "__main__":
    print("🏛️  Starting KBI Labs Government Contractor API...")
    print("📍 API will be available at: http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("❤️  Health Check: http://localhost:8001/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )