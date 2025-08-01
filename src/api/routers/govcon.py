"""Government Contractor API Router"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from datetime import datetime, date
from src.api.dependencies import get_current_user
from src.models.database_manager import db_manager

router = APIRouter(prefix="/government-contractor", tags=["government-contractor"])

@router.get("/")
async def get_government_contractor_data(current_user = Depends(get_current_user)):
    """Get comprehensive government contractor dashboard data"""
    try:
        # This would normally query your database for real compliance data
        # For now, returning structured mock data that matches your dashboard
        
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
                "active": 12,
                "pending": 8,
                "totalValue": 2850000,
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
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching government contractor data: {str(e)}")

@router.get("/compliance/cmmc")
async def get_cmmc_compliance(current_user = Depends(get_current_user)):
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

@router.get("/compliance/dfars")
async def get_dfars_compliance(current_user = Depends(get_current_user)):
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

@router.get("/compliance/fedramp")
async def get_fedramp_status(current_user = Depends(get_current_user)):
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

@router.get("/opportunities")
async def get_contract_opportunities(
    naics: Optional[str] = None,
    keywords: Optional[str] = None,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get relevant contract opportunities from SAM.gov"""
    try:
        from src.integrations.government.sam_gov import SAMGovIntegration
        
        sam_integration = SAMGovIntegration()
        opportunities_data = await sam_integration.search_opportunities(
            naics_code=naics,
            keywords=keywords,
            limit=limit
        )
        
        # Enhance opportunities with match scoring
        enhanced_opportunities = []
        for opp in opportunities_data.get("opportunities", []):
            # Calculate match score based on NAICS alignment and requirements
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching opportunities: {str(e)}")

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
    # This would use ML/NLP to estimate value from description
    # For now, return ranges based on keywords
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

@router.get("/performance/cpars")
async def get_cpars_data(current_user = Depends(get_current_user)):
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

@router.get("/analytics/naics")
async def get_naics_analytics(current_user = Depends(get_current_user)):
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

@router.post("/simulation/pipeline")
async def run_pipeline_simulation(
    scenarios: Dict,
    current_user = Depends(get_current_user)
):
    """Run contract pipeline simulation"""
    # This would run Monte Carlo simulation
    return {
        "simulation_id": "sim_001",
        "scenarios": scenarios,
        "results": {
            "probable_revenue_6m": 1850000,
            "probable_revenue_12m": 4200000,
            "win_probability": 0.68,
            "risk_factors": [
                {"factor": "Competition Level", "impact": "Medium"},
                {"factor": "Past Performance", "impact": "Low"},
                {"factor": "Price Competitiveness", "impact": "High"}
            ]
        }
    }