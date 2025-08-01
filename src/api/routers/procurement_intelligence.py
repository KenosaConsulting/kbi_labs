"""
Procurement Intelligence API Routes

FastAPI routes for the AI-powered senior analyst platform.
Integrates with existing KBI Labs API patterns and authentication.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
import redis
import os

from ...integrations.procurement import GovernmentDataManager
from ...ai_analysis import ProcurementIntelligenceProcessor, IntelligenceReport

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v3/procurement-intelligence", tags=["Procurement Intelligence"])

# Pydantic models for request/response
class OpportunityAnalysisRequest(BaseModel):
    company_uei: str = Field(..., description="Company UEI for analysis")
    opportunity_id: Optional[str] = Field(None, description="Specific opportunity to analyze")
    analysis_depth: str = Field("standard", description="Analysis depth: quick, standard, or deep")

class IntelligenceReportResponse(BaseModel):
    report_id: str
    generated_at: str
    company_uei: str
    opportunity_id: Optional[str] = None
    win_probability: float
    confidence_score: float
    opportunity_assessment: Optional[Dict[str, Any]] = None
    competitive_landscape: Optional[Dict[str, Any]] = None
    recommended_actions: List[str] = []
    teaming_recommendations: List[Dict] = []
    proposal_strategy: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    analysis_duration_seconds: float

class OpportunitySearchRequest(BaseModel):
    company_uei: str
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_results: int = Field(50, le=200)

class MarketIntelligenceRequest(BaseModel):
    naics_codes: Optional[List[str]] = Field(None, description="NAICS codes to analyze")
    agencies: Optional[List[str]] = Field(None, description="Specific agencies to focus on")
    time_range_days: int = Field(365, description="Historical data range in days")

# Dependency for getting services
async def get_government_data_manager() -> GovernmentDataManager:
    """Get initialized government data manager"""
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    manager = GovernmentDataManager(redis_client)
    await manager.initialize()
    return manager

async def get_intelligence_processor() -> ProcurementIntelligenceProcessor:
    """Get initialized intelligence processor"""
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    return ProcurementIntelligenceProcessor(openai_api_key, redis_client)

@router.post("/analyze", response_model=IntelligenceReportResponse)
async def analyze_procurement_opportunity(
    request: OpportunityAnalysisRequest,
    background_tasks: BackgroundTasks,
    data_manager: GovernmentDataManager = Depends(get_government_data_manager),
    intelligence_processor: ProcurementIntelligenceProcessor = Depends(get_intelligence_processor)
):
    """
    Generate comprehensive procurement intelligence analysis for a company
    and optionally a specific opportunity.
    """
    try:
        logger.info(f"Analyzing procurement opportunity for UEI: {request.company_uei}")
        
        # Get opportunity data if specific opportunity requested
        opportunity_data = None
        if request.opportunity_id:
            # Search for the specific opportunity
            opportunities = await data_manager.get_opportunity_data({
                'notice_id': request.opportunity_id
            })
            
            if opportunities:
                opportunity_data = opportunities[0]
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Opportunity {request.opportunity_id} not found"
                )
        
        # Generate comprehensive intelligence report
        report = await intelligence_processor.generate_comprehensive_intelligence(
            company_uei=request.company_uei,
            opportunity_data=opportunity_data,
            analysis_depth=request.analysis_depth
        )
        
        # Convert to response model
        response = IntelligenceReportResponse(
            report_id=report.report_id,
            generated_at=report.generated_at,
            company_uei=report.company_uei,
            opportunity_id=report.opportunity_id,
            win_probability=report.win_probability,
            confidence_score=report.confidence_score,
            opportunity_assessment=report.opportunity_assessment,
            competitive_landscape=report.competitive_landscape,
            recommended_actions=report.recommended_actions or [],
            teaming_recommendations=report.teaming_recommendations or [],
            proposal_strategy=report.proposal_strategy,
            risk_assessment=report.risk_assessment,
            analysis_duration_seconds=report.analysis_duration_seconds
        )
        
        logger.info(f"Analysis completed for {request.company_uei}: {report.report_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in procurement analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/opportunities/search")
async def search_procurement_opportunities(
    company_uei: str = Query(..., description="Company UEI"),
    agency: Optional[str] = Query(None, description="Filter by agency"),
    naics: Optional[str] = Query(None, description="Filter by NAICS code"),
    set_aside: Optional[str] = Query(None, description="Filter by set-aside type"),
    min_value: Optional[float] = Query(None, description="Minimum contract value"),
    max_results: int = Query(50, le=200, description="Maximum results to return"),
    data_manager: GovernmentDataManager = Depends(get_government_data_manager)
):
    """
    Search for relevant procurement opportunities based on company profile
    and optional filters.
    """
    try:
        logger.info(f"Searching opportunities for UEI: {company_uei}")
        
        # Build filters
        filters = {}
        if agency:
            filters['agency'] = agency
        if naics:
            filters['naics'] = naics
        if set_aside:
            filters['set_aside'] = set_aside
        if min_value:
            filters['min_value'] = min_value
        
        # Get opportunities
        opportunities = await data_manager.get_opportunity_data(filters)
        
        # Limit results
        limited_opportunities = opportunities[:max_results]
        
        logger.info(f"Found {len(limited_opportunities)} opportunities for {company_uei}")
        
        return {
            "company_uei": company_uei,
            "total_found": len(opportunities),
            "returned": len(limited_opportunities),
            "opportunities": limited_opportunities,
            "filters_applied": filters
        }
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/companies/{uei}/contracts")
async def get_company_contract_history(
    uei: str,
    data_manager: GovernmentDataManager = Depends(get_government_data_manager)
):
    """
    Get comprehensive contract history for a specific company.
    """
    try:
        logger.info(f"Fetching contract history for UEI: {uei}")
        
        contract_data = await data_manager.get_contract_data(uei)
        
        logger.info(f"Retrieved {len(contract_data.get('contracts', []))} contracts for {uei}")
        
        return contract_data
        
    except Exception as e:
        logger.error(f"Error fetching contract history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-intelligence")
async def get_market_intelligence(
    naics_codes: Optional[str] = Query(None, description="Comma-separated NAICS codes"),
    agencies: Optional[str] = Query(None, description="Comma-separated agency names"),
    time_range_days: int = Query(365, description="Historical data range in days"),
    data_manager: GovernmentDataManager = Depends(get_government_data_manager)
):
    """
    Get market intelligence including spending trends, forecasts, and opportunities.
    """
    try:
        logger.info("Generating market intelligence report")
        
        # Parse comma-separated parameters
        naics_list = naics_codes.split(',') if naics_codes else None
        agency_list = agencies.split(',') if agencies else None
        
        # Get budget forecasts
        forecasts = await data_manager.get_budget_forecasts()
        
        # Filter by agencies if specified
        if agency_list:
            forecasts = [
                f for f in forecasts 
                if any(agency.lower() in f.get('agency', '').lower() for agency in agency_list)
            ]
        
        # Get opportunities for market analysis
        opportunity_filters = {}
        if naics_list:
            # For now, use first NAICS code
            opportunity_filters['naics'] = naics_list[0]
        
        opportunities = await data_manager.get_opportunity_data(opportunity_filters)
        
        # Compile market intelligence
        market_intel = {
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": {
                "naics_codes": naics_list,
                "agencies": agency_list,
                "time_range_days": time_range_days
            },
            "budget_forecasts": forecasts,
            "active_opportunities": len(opportunities),
            "opportunity_sample": opportunities[:10],  # Sample of opportunities
            "market_summary": {
                "total_forecasted_opportunities": len(forecasts),
                "active_solicitations": len(opportunities),
                "covered_agencies": len(set(f.get('agency', '') for f in forecasts))
            }
        }
        
        logger.info("Market intelligence report generated successfully")
        return market_intel
        
    except Exception as e:
        logger.error(f"Error generating market intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}")
async def get_intelligence_report(
    report_id: str,
    intelligence_processor: ProcurementIntelligenceProcessor = Depends(get_intelligence_processor)
):
    """
    Retrieve a previously generated intelligence report.
    """
    try:
        logger.info(f"Retrieving intelligence report: {report_id}")
        
        report = await intelligence_processor.get_cached_report(report_id)
        
        if not report:
            raise HTTPException(
                status_code=404, 
                detail=f"Intelligence report {report_id} not found"
            )
        
        # Convert to response model
        response = IntelligenceReportResponse(
            report_id=report.report_id,
            generated_at=report.generated_at,
            company_uei=report.company_uei,
            opportunity_id=report.opportunity_id,
            win_probability=report.win_probability,
            confidence_score=report.confidence_score,
            opportunity_assessment=report.opportunity_assessment,
            competitive_landscape=report.competitive_landscape,
            recommended_actions=report.recommended_actions or [],
            teaming_recommendations=report.teaming_recommendations or [],
            proposal_strategy=report.proposal_strategy,
            risk_assessment=report.risk_assessment,
            analysis_duration_seconds=report.analysis_duration_seconds
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving intelligence report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-analyze")
async def batch_analyze_opportunities(
    request: OpportunitySearchRequest,
    background_tasks: BackgroundTasks,
    data_manager: GovernmentDataManager = Depends(get_government_data_manager),
    intelligence_processor: ProcurementIntelligenceProcessor = Depends(get_intelligence_processor)
):
    """
    Analyze multiple opportunities for a company in batch.
    Returns immediately with job ID, processes in background.
    """
    try:
        logger.info(f"Starting batch analysis for UEI: {request.company_uei}")
        
        # Get opportunities based on filters
        opportunities = await data_manager.get_opportunity_data(request.filters)
        
        # Limit results
        limited_opportunities = opportunities[:request.max_results]
        
        if not limited_opportunities:
            raise HTTPException(
                status_code=404, 
                detail="No opportunities found matching criteria"
            )
        
        # Generate job ID
        job_id = f"batch_{request.company_uei}_{int(datetime.utcnow().timestamp())}"
        
        # Start background analysis
        background_tasks.add_task(
            _process_batch_analysis,
            job_id,
            request.company_uei,
            limited_opportunities,
            intelligence_processor
        )
        
        return {
            "job_id": job_id,
            "company_uei": request.company_uei,
            "opportunities_to_analyze": len(limited_opportunities),
            "status": "processing",
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_batch_analysis(
    job_id: str,
    company_uei: str,
    opportunities: List[Dict],
    intelligence_processor: ProcurementIntelligenceProcessor
):
    """Process batch analysis in background"""
    try:
        logger.info(f"Processing batch analysis job {job_id}")
        
        reports = await intelligence_processor.analyze_multiple_opportunities(
            company_uei, 
            opportunities
        )
        
        # Cache batch results
        if intelligence_processor.redis_client:
            import json
            
            batch_result = {
                "job_id": job_id,
                "company_uei": company_uei,
                "completed_at": datetime.utcnow().isoformat(),
                "total_opportunities": len(opportunities),
                "successful_analyses": len(reports),
                "report_ids": [r.report_id for r in reports]
            }
            
            cache_key = f"batch_analysis:{job_id}"
            intelligence_processor.redis_client.setex(
                cache_key, 
                86400,  # 24 hours
                json.dumps(batch_result, default=str)
            )
        
        logger.info(f"Batch analysis job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in batch analysis job {job_id}: {e}")

@router.get("/batch-status/{job_id}")
async def get_batch_analysis_status(
    job_id: str,
    intelligence_processor: ProcurementIntelligenceProcessor = Depends(get_intelligence_processor)
):
    """
    Get status of batch analysis job.
    """
    try:
        if not intelligence_processor.redis_client:
            raise HTTPException(status_code=500, detail="Cache not available")
        
        cache_key = f"batch_analysis:{job_id}"
        cached_result = intelligence_processor.redis_client.get(cache_key)
        
        if cached_result:
            import json
            result = json.loads(cached_result)
            result["status"] = "completed"
            return result
        else:
            # Job might still be processing or doesn't exist
            return {
                "job_id": job_id,
                "status": "processing_or_not_found",
                "message": "Job is still processing or does not exist"
            }
            
    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data-sources/status")
async def get_data_sources_status(
    data_manager: GovernmentDataManager = Depends(get_government_data_manager)
):
    """
    Get status of all data sources in the procurement intelligence system.
    """
    try:
        status = await data_manager.get_processing_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting data sources status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data-sources/refresh")
async def refresh_data_sources(
    background_tasks: BackgroundTasks,
    data_manager: GovernmentDataManager = Depends(get_government_data_manager)
):
    """
    Trigger refresh of all data sources.
    """
    try:
        # Start background refresh
        background_tasks.add_task(_refresh_all_sources, data_manager)
        
        return {
            "status": "refresh_started",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Data source refresh has been initiated in the background"
        }
        
    except Exception as e:
        logger.error(f"Error starting data refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _refresh_all_sources(data_manager: GovernmentDataManager):
    """Refresh all data sources in background"""
    try:
        logger.info("Starting background data source refresh")
        
        results = await data_manager.refresh_all_sources()
        
        logger.info(f"Data source refresh completed: {results['sources_successful']}/{results['sources_processed']} successful")
        
    except Exception as e:
        logger.error(f"Error in background data refresh: {e}")