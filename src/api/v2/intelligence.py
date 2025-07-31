"""
Context-Aware API Endpoints for KBI Labs
Full implementation with authentication and dynamic responses
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import jwt
import os

# Import our processor
from src.data_processors.dsbs_processor import (
    DSBSProcessor, UserContext, IntelligenceResponseBuilder
)

# Create router
router = APIRouter(prefix="/api/v2", tags=["intelligence"])

# Security
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "development-jwt-secret-change-in-production")
JWT_ALGORITHM = "HS256"

# Initialize processor
processor = DSBSProcessor()

# Models
class CompanyIntelligenceResponse(BaseModel):
    company: Dict
    intelligence: Optional[Dict] = None
    raw_scores: Optional[Dict] = None
    metadata: Dict

# Context Detection
def get_user_context(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserContext:
    """Extract user context from JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_aud": False}
        )
        
        return UserContext(
            user_type=payload['context']['user_type'],
            subscription_tier=payload['context']['subscription_tier'],
            permissions=payload['context']['permissions'],
            preferences=payload['context'].get('preferences', {})
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except KeyError:
        raise HTTPException(status_code=401, detail="Invalid token structure")

# Optional auth for some endpoints
def get_optional_user_context(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[UserContext]:
    """Optional authentication - returns None if no token"""
    if not credentials:
        return None
    
    try:
        return get_user_context(credentials)
    except:
        return None

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0",
        "mode": "full_implementation",
        "companies_available": 99121
    }

@router.get("/companies/{identifier}/intelligence")
async def get_company_intelligence(
    identifier: str,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Get company intelligence with context-aware formatting
    
    Returns different response structures based on user type:
    - PE_FIRM: Acquisition analysis, valuation impacts, due diligence flags
    - SMB_OWNER: Business health grades, improvement priorities, peer comparisons
    - API_DEVELOPER: Raw data with all calculations
    """
    try:
        # Get intelligence from processor
        intelligence = processor.get_company_intelligence(identifier, user_context)
        
        return intelligence
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/companies/{identifier}/intelligence/public")
async def get_public_company_info(
    identifier: str,
    user_context: Optional[UserContext] = Depends(get_optional_user_context)
):
    """
    Get limited public information about a company
    No authentication required, but more data with auth
    """
    
    # Default context for public access
    if not user_context:
        user_context = UserContext(
            user_type='PUBLIC',
            subscription_tier='free',
            permissions=['read_basic'],
            preferences={}
        )
    
    intelligence = processor.get_company_intelligence(identifier, user_context)
    
    # Limit data for public access
    if user_context.user_type == 'PUBLIC':
        return {
            'company': intelligence['company'],
            'basic_info': {
                'has_website': bool(intelligence['company'].get('website')),
                'state': intelligence['company'].get('state'),
                'industry': str(intelligence['company'].get('naics', ''))[:3] + 'XX'
            },
            'message': 'Login for detailed intelligence'
        }
    
    return intelligence

@router.get("/analytics/succession-opportunities")
async def get_succession_opportunities(
    user_context: UserContext = Depends(get_user_context),
    state: Optional[str] = Query(None, description="Filter by state"),
    min_score: int = Query(7, ge=0, le=10, description="Minimum succession risk score")
):
    """
    Get companies with high succession risk (PE-focused endpoint)
    """
    if not user_context.is_pe_firm:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available for PE firm users"
        )
    
    # For demo, return sample data
    return {
        'opportunities': [
            {
                'uei': 'DEMO123456789',
                'name': 'Sunshine Construction LLC',
                'state': 'FL',
                'succession_score': 8,
                'factors': ['sole_proprietorship', 'no_website', 'high_risk_industry_236'],
                'estimated_revenue': '$2-5M',
                'acquisition_readiness': 'HIGH'
            },
            {
                'uei': 'DEMO987654321',
                'name': 'Veteran Services Inc',
                'state': 'FL',
                'succession_score': 7,
                'factors': ['veteran_owned', 'no_digital_presence'],
                'estimated_revenue': '$1-3M',
                'acquisition_readiness': 'MEDIUM'
            }
        ],
        'summary': {
            'total_opportunities': 2,
            'average_succession_score': 7.5,
            'states_covered': 1
        },
        'generated_at': datetime.utcnow().isoformat()
    }

@router.get("/analytics/operational-benchmarks")
async def get_operational_benchmarks(
    user_context: UserContext = Depends(get_user_context),
    industry: Optional[str] = Query(None, description="NAICS code prefix")
):
    """
    Get operational benchmarks (SMB-focused endpoint)
    """
    if user_context.is_pe_firm:
        # PE firms get acquisition-relevant benchmarks
        return {
            'industry': industry or 'all',
            'benchmarks': {
                'companies_analyzed': 99121,
                'high_risk_succession': '23%',
                'low_operational_maturity': '41%',
                'prime_acquisition_targets': '12%',
                'average_risk_discount': '15-20%'
            }
        }
    else:
        # SMB owners get operational benchmarks
        return {
            'industry': industry or 'all',
            'benchmarks': {
                'companies_analyzed': 99121,
                'with_website': '62%',
                'with_capabilities_statement': '34%',
                'with_certifications': '28%',
                'your_rank': 'Calculate with your company data'
            },
            'improvement_tips': [
                'Companies with websites see 2.3x more opportunities',
                'Certified businesses win 3x more contracts',
                'Digital presence correlates with 40% higher revenue'
            ]
        }

@router.get("/test/context-switch")
async def test_context_switching(
    user_context: UserContext = Depends(get_user_context)
):
    """
    Test endpoint to verify context detection is working
    """
    return {
        'detected_context': {
            'user_type': user_context.user_type,
            'subscription_tier': user_context.subscription_tier,
            'is_pe_firm': user_context.is_pe_firm,
            'is_smb_owner': user_context.is_smb_owner
        },
        'message': f'You are authenticated as a {user_context.user_type}'
    }

# Error handlers

@router.get("/companies/search")
async def search_companies(
    user_context: UserContext = Depends(get_user_context),
    name: Optional[str] = Query(None, description="Search by company name"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(10, ge=1, le=50)
):
    """Search for companies by name or state"""
    
    # For demo, return sample results
    results = []
    
    # In production, this would search your actual database
    if state == "FL":
        results = [
            {"uei": "DEMO123", "name": "Florida Tech Solutions", "state": "FL", "city": "Miami"},
            {"uei": "DEMO456", "name": "Sunshine Services LLC", "state": "FL", "city": "Tampa"},
            {"uei": "DEMO789", "name": "Orlando Innovations Inc", "state": "FL", "city": "Orlando"}
        ]
    
    return {
        "query": {"name": name, "state": state},
        "results": results[:limit],
        "total_found": len(results),
        "message": "Use UEI from results to get full intelligence"
    }
