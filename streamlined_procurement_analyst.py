"""
KBI Labs Streamlined Federal Procurement Analyst
==============================================

Unified, contextually aware government contracting intelligence system that 
consolidates all procurement APIs into a single comprehensive analyst platform.

This replaces the scattered API architecture with a focused, AI-powered
federal procurement analyst that provides:

1. Unified Government Data Access
2. Contextually Aware Opportunity Analysis
3. AI-Powered Win Probability Predictions
4. Strategic Teaming Recommendations
5. Automated Agency Intelligence

Author: KBI Labs + AI Pair Programming (GPT-5 x Claude Code)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import redis
import numpy as np
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisDepth(Enum):
    """Analysis depth options"""
    QUICK = "quick"          # Basic opportunity matching
    STANDARD = "standard"    # Full analysis with ML predictions
    DEEP = "deep"           # Comprehensive competitive intelligence

class OpportunityStatus(Enum):
    """Opportunity status tracking"""
    ACTIVE = "active"
    CLOSED = "closed"
    AWARDED = "awarded"
    CANCELLED = "cancelled"

@dataclass
class ProcurementOpportunity:
    """Unified procurement opportunity data model"""
    notice_id: str
    title: str
    agency: str
    office: str
    naics_codes: List[str]
    set_aside_type: Optional[str]
    description: str
    response_deadline: datetime
    estimated_value: Optional[float]
    contract_type: str
    place_of_performance: str
    point_of_contact: Dict[str, str]
    status: OpportunityStatus
    
    # Enriched intelligence fields
    win_probability: Optional[float] = None
    confidence_score: Optional[float] = None
    competitive_landscape: Optional[Dict] = None
    strategic_recommendations: Optional[List[str]] = None
    teaming_opportunities: Optional[List[Dict]] = None

@dataclass
class CompanyProfile:
    """Company intelligence profile"""
    uei: str
    duns: Optional[str]
    name: str
    primary_naics: List[str]
    capabilities: List[str]
    past_performance: Dict[str, Any]
    certifications: List[str]
    team_size: Optional[int]
    annual_revenue: Optional[float]
    geographic_presence: List[str]
    
    # AI-derived insights
    capability_score: Optional[float] = None
    agency_alignment: Optional[Dict[str, float]] = None
    competitive_positioning: Optional[str] = None

class StreamlinedProcurementAnalyst:
    """
    Unified Federal Procurement Analyst
    
    Consolidates all government APIs into a single contextually aware system
    that provides comprehensive procurement intelligence and strategic recommendations.
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.ml_models = self._load_ml_models()
        self.government_apis = self._initialize_api_clients()
        self.context_memory = {}
        
        logger.info("StreamlinedProcurementAnalyst initialized")
    
    def _load_ml_models(self) -> Dict[str, Any]:
        """Load pre-trained ML models for procurement intelligence"""
        try:
            import pickle
            models = {}
            
            # Load existing KBI Labs models
            model_paths = {
                'contract_success': 'models/contract_success_model.pkl',
                'fraud_detection': 'models/fraud_detection_model.pkl',
                'contract_scaler': 'models/contract_success_scaler.pkl'
            }
            
            for model_name, path in model_paths.items():
                try:
                    with open(path, 'rb') as f:
                        models[model_name] = pickle.load(f)
                except FileNotFoundError:
                    logger.warning(f"Model {model_name} not found at {path}")
                    
            logger.info(f"Loaded {len(models)} ML models")
            return models
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            return {}
    
    def _initialize_api_clients(self) -> Dict[str, Any]:
        """Initialize consolidated government API clients"""
        return {
            'sam_gov': self._create_sam_client(),
            'usaspending': self._create_usaspending_client(),
            'federal_register': self._create_federal_register_client(),
            'gsa_client': self._create_gsa_client(),
            'fpds': self._create_fpds_client()
        }
    
    def _create_sam_client(self):
        """Create SAM.gov API client"""
        # Use existing SAM integration
        from src.integrations.government.sam_gov import SAMGovAPI
        return SAMGovAPI()
    
    def _create_usaspending_client(self):
        """Create USASpending.gov client"""
        from src.integrations.government.usaspending import USASpendingAPI
        return USASpendingAPI()
    
    def _create_federal_register_client(self):
        """Create Federal Register client"""
        from src.integrations.federal_register import get_contractor_regulatory_intelligence
        return get_contractor_regulatory_intelligence
    
    def _create_gsa_client(self):
        """Create GSA API client"""
        from src.government_apis.gsa_client import GSAClient
        return GSAClient()
    
    def _create_fpds_client(self):
        """Create FPDS client"""
        from src.government_apis.fpds_client import FPDSClient
        return FPDSClient()

    async def analyze_procurement_landscape(
        self, 
        company_uei: str,
        analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD,
        focus_agencies: Optional[List[str]] = None,
        naics_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive procurement landscape analysis for a specific company
        
        This is the main entry point that consolidates all scattered functionality
        into a single contextually aware analysis.
        """
        start_time = datetime.now()
        logger.info(f"Starting procurement landscape analysis for {company_uei}")
        
        try:
            # Step 1: Build comprehensive company profile
            company_profile = await self._build_company_intelligence(company_uei)
            
            # Step 2: Identify relevant opportunities with AI scoring
            opportunities = await self._discover_relevant_opportunities(
                company_profile, focus_agencies, naics_filter
            )
            
            # Step 3: Generate competitive intelligence
            competitive_landscape = await self._analyze_competitive_landscape(
                company_profile, opportunities
            )
            
            # Step 4: AI-powered strategic recommendations
            strategic_insights = await self._generate_strategic_recommendations(
                company_profile, opportunities, competitive_landscape, analysis_depth
            )
            
            # Step 5: Identify teaming opportunities
            teaming_recommendations = await self._identify_teaming_opportunities(
                company_profile, opportunities
            )
            
            # Step 6: Generate contextual agency intelligence
            agency_intelligence = await self._generate_agency_intelligence(
                company_profile, opportunities
            )
            
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            # Consolidated analysis report
            comprehensive_analysis = {
                "analysis_metadata": {
                    "company_uei": company_uei,
                    "analysis_id": f"PA_{company_uei}_{int(datetime.now().timestamp())}",
                    "generated_at": datetime.now().isoformat(),
                    "analysis_depth": analysis_depth.value,
                    "duration_seconds": analysis_duration,
                    "data_sources": list(self.government_apis.keys())
                },
                
                "company_intelligence": {
                    "profile": company_profile.__dict__,
                    "capability_assessment": {
                        "primary_strengths": self._extract_key_capabilities(company_profile),
                        "market_positioning": company_profile.competitive_positioning,
                        "capability_score": company_profile.capability_score
                    }
                },
                
                "opportunity_intelligence": {
                    "total_relevant_opportunities": len(opportunities),
                    "high_probability_matches": [
                        opp for opp in opportunities if opp.win_probability and opp.win_probability > 0.7
                    ][:10],
                    "emerging_opportunities": [
                        opp for opp in opportunities if self._is_emerging_opportunity(opp)
                    ][:5],
                    "opportunity_pipeline": self._categorize_opportunities_by_timeline(opportunities)
                },
                
                "competitive_intelligence": competitive_landscape,
                
                "strategic_recommendations": {
                    "immediate_actions": strategic_insights.get("immediate", []),
                    "medium_term_strategy": strategic_insights.get("medium_term", []),
                    "long_term_positioning": strategic_insights.get("long_term", []),
                    "risk_mitigation": strategic_insights.get("risks", [])
                },
                
                "teaming_intelligence": {
                    "recommended_partners": teaming_recommendations[:10],
                    "teaming_strategies": self._generate_teaming_strategies(teaming_recommendations),
                    "partnership_opportunities": self._identify_strategic_partnerships(company_profile)
                },
                
                "agency_intelligence": agency_intelligence,
                
                "market_intelligence": {
                    "spend_forecasts": await self._get_spending_forecasts(focus_agencies, naics_filter),
                    "regulatory_changes": await self._get_regulatory_intelligence(),
                    "market_trends": await self._analyze_market_trends(naics_filter)
                }
            }
            
            # Cache results for future context awareness
            await self._cache_analysis_context(company_uei, comprehensive_analysis)
            
            logger.info(f"Completed comprehensive analysis for {company_uei} in {analysis_duration:.2f}s")
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error in procurement landscape analysis: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    async def _build_company_intelligence(self, company_uei: str) -> CompanyProfile:
        """Build comprehensive company intelligence profile from all available sources"""
        try:
            # Gather data from multiple sources
            sam_data = await self._get_sam_company_data(company_uei)
            contract_history = await self._get_contract_history(company_uei)
            capability_analysis = await self._analyze_capabilities(company_uei, contract_history)
            
            company_profile = CompanyProfile(
                uei=company_uei,
                duns=sam_data.get('duns'),
                name=sam_data.get('legalBusinessName', ''),
                primary_naics=sam_data.get('naicsCodes', []),
                capabilities=capability_analysis.get('capabilities', []),
                past_performance=contract_history,
                certifications=sam_data.get('certifications', []),
                team_size=sam_data.get('numberOfEmployees'),
                annual_revenue=sam_data.get('annualRevenue'),
                geographic_presence=sam_data.get('addresses', []),
                capability_score=capability_analysis.get('score', 0.0),
                competitive_positioning=capability_analysis.get('positioning', 'Unknown')
            )
            
            return company_profile
            
        except Exception as e:
            logger.error(f"Error building company intelligence: {e}")
            # Return minimal profile to allow analysis to continue
            return CompanyProfile(
                uei=company_uei,
                name="Unknown Company",
                primary_naics=[],
                capabilities=[],
                past_performance={},
                certifications=[],
                geographic_presence=[]
            )

    async def _discover_relevant_opportunities(
        self, 
        company_profile: CompanyProfile,
        focus_agencies: Optional[List[str]] = None,
        naics_filter: Optional[List[str]] = None
    ) -> List[ProcurementOpportunity]:
        """Discover and score relevant procurement opportunities using AI"""
        
        try:
            # Get opportunities from SAM.gov and other sources
            raw_opportunities = await self._fetch_all_opportunities(focus_agencies, naics_filter)
            
            # Score opportunities based on company profile
            scored_opportunities = []
            for opp_data in raw_opportunities:
                opportunity = self._create_opportunity_object(opp_data)
                
                # AI-powered relevance scoring
                opportunity.win_probability = await self._calculate_win_probability(
                    company_profile, opportunity
                )
                opportunity.confidence_score = await self._calculate_confidence_score(
                    company_profile, opportunity
                )
                
                # Only include relevant opportunities
                if opportunity.win_probability and opportunity.win_probability > 0.3:
                    scored_opportunities.append(opportunity)
            
            # Sort by win probability
            scored_opportunities.sort(key=lambda x: x.win_probability or 0, reverse=True)
            
            return scored_opportunities[:50]  # Top 50 most relevant
            
        except Exception as e:
            logger.error(f"Error discovering opportunities: {e}")
            return []

    # Additional helper methods would continue here...
    # This provides the foundation for the streamlined system

# FastAPI Application
app = FastAPI(
    title="Streamlined KBI Labs Procurement Analyst",
    description="Unified Federal Procurement Intelligence System",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyst
analyst = StreamlinedProcurementAnalyst()

# Streamlined API Endpoints
@app.post("/api/analyze/comprehensive")
async def comprehensive_procurement_analysis(
    company_uei: str,
    analysis_depth: str = "standard",
    focus_agencies: Optional[str] = None,
    naics_codes: Optional[str] = None
):
    """
    Single endpoint for comprehensive procurement intelligence analysis
    Replaces multiple scattered API endpoints with one unified interface
    """
    try:
        # Parse parameters
        depth = AnalysisDepth(analysis_depth)
        agencies = focus_agencies.split(",") if focus_agencies else None
        naics = naics_codes.split(",") if naics_codes else None
        
        # Run comprehensive analysis
        analysis = await analyst.analyze_procurement_landscape(
            company_uei=company_uei,
            analysis_depth=depth,
            focus_agencies=agencies,
            naics_filter=naics
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"API error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/opportunities/live")
async def get_live_opportunities(
    company_uei: str,
    limit: int = 25
):
    """Real-time opportunity feed tailored to company profile"""
    try:
        company_profile = await analyst._build_company_intelligence(company_uei)
        opportunities = await analyst._discover_relevant_opportunities(company_profile)
        
        return {
            "company_uei": company_uei,
            "opportunities": [opp.__dict__ for opp in opportunities[:limit]],
            "total_relevant": len(opportunities),
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/intelligence/contextual")
async def get_contextual_intelligence(company_uei: str):
    """Get contextually aware intelligence based on company profile and market conditions"""
    try:
        # This would leverage the context memory and provide adaptive intelligence
        context = await analyst._get_company_context(company_uei)
        
        return {
            "company_uei": company_uei,
            "contextual_insights": context,
            "adaptive_recommendations": await analyst._generate_adaptive_recommendations(company_uei),
            "market_positioning": await analyst._analyze_competitive_position(company_uei)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "service": "KBI Labs Streamlined Procurement Analyst",
        "version": "3.0.0",
        "description": "Unified Federal Procurement Intelligence System",
        "status": "operational",
        "endpoints": {
            "comprehensive_analysis": "/api/analyze/comprehensive",
            "live_opportunities": "/api/opportunities/live",
            "contextual_intelligence": "/api/intelligence/contextual"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)