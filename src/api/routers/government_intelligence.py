"""
Government Intelligence API Router

Exposes government intelligence data from various free APIs including
GSA Website Index, Federal Register, and other government sources.
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
import logging
from datetime import datetime

from src.integrations.gsa_website_index import get_federal_website_intelligence, get_agency_digital_profile, get_enhanced_gsa_intelligence
from src.integrations.federal_register import get_contractor_regulatory_intelligence, get_agency_regulatory_profile
from src.integrations.congress_gov import get_congressional_contractor_intelligence, get_contractor_bills
from src.integrations.sam_opportunities import get_real_procurement_opportunities, get_agency_opportunities
from src.integrations.govinfo import get_govinfo_congressional_intelligence, get_govinfo_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/government-intelligence", tags=["government-intelligence"])

@router.get("/federal-websites", response_model=Dict)
async def get_federal_websites():
    """Get comprehensive federal website intelligence from GSA"""
    try:
        logger.info("Fetching federal website intelligence")
        intelligence = await get_federal_website_intelligence()
        
        if not intelligence:
            raise HTTPException(status_code=503, detail="Unable to fetch federal website data")
        
        return {
            "status": "success",
            "data": intelligence,
            "source": "GSA Federal Website Index",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching federal websites: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agency-digital-profile/{agency_name}", response_model=Dict)
async def get_agency_digital_intelligence(agency_name: str):
    """Get digital intelligence profile for specific agency"""
    try:
        logger.info(f"Fetching digital profile for agency: {agency_name}")
        profile = await get_agency_digital_profile(agency_name)
        
        return {
            "status": "success",
            "agency": agency_name,
            "data": profile,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching agency digital profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulatory-intelligence", response_model=Dict)
async def get_regulatory_intelligence():
    """Get contractor-focused regulatory intelligence from Federal Register"""
    try:
        logger.info("Fetching regulatory intelligence for contractors")
        intelligence = await get_contractor_regulatory_intelligence()
        
        if not intelligence:
            raise HTTPException(status_code=503, detail="Unable to fetch regulatory data")
        
        return {
            "status": "success",
            "data": intelligence,
            "source": "Federal Register API",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching regulatory intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agency-regulatory-profile/{agency_name}", response_model=Dict)
async def get_agency_regulatory_intelligence(agency_name: str):
    """Get regulatory activity profile for specific agency"""
    try:
        logger.info(f"Fetching regulatory profile for agency: {agency_name}")
        profile = await get_agency_regulatory_profile(agency_name)
        
        return {
            "status": "success",
            "agency": agency_name,
            "data": profile,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching agency regulatory profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/government-digital-overview", response_model=Dict)
async def get_government_digital_overview():
    """Get comprehensive overview of government digital capabilities"""
    try:
        logger.info("Generating government digital overview")
        
        # Get federal website intelligence
        website_data = await get_federal_website_intelligence()
        
        # Get regulatory intelligence
        regulatory_data = await get_contractor_regulatory_intelligence()
        
        # Combine insights
        overview = {
            "digital_infrastructure": {
                "total_websites": website_data.get('metadata', {}).get('total_websites', 0),
                "unique_domains": website_data.get('metadata', {}).get('unique_domains', 0),
                "unique_agencies": website_data.get('metadata', {}).get('unique_agencies', 0),
                "https_adoption": website_data.get('digital_presence', {}).get('security', {}).get('https_adoption', 0),
                "digital_maturity_score": website_data.get('digital_presence', {}).get('digital_maturity_score', 0)
            },
            "regulatory_activity": {
                "recent_regulations": regulatory_data.get('summary', {}).get('total_regulations', 0),
                "high_relevance_count": regulatory_data.get('summary', {}).get('high_relevance_count', 0),
                "policy_changes": regulatory_data.get('summary', {}).get('policy_changes_count', 0),
                "high_impact_policies": regulatory_data.get('summary', {}).get('high_impact_policies', 0)
            },
            "top_agencies": website_data.get('agency_stats', {}).get('top_agencies', {}),
            "intelligence_sources": [
                "GSA Federal Website Index",
                "Federal Register API",
                "USASpending.gov",
                "SAM.gov"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "data": overview,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating government digital overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contractor-intelligence-dashboard", response_model=Dict)
async def get_contractor_intelligence_dashboard():
    """Get comprehensive contractor intelligence dashboard data"""
    try:
        logger.info("Generating contractor intelligence dashboard")
        
        # Fetch all intelligence data
        website_data = await get_federal_website_intelligence()
        regulatory_data = await get_contractor_regulatory_intelligence()
        
        # Extract key insights for contractors
        dashboard_data = {
            "overview": {
                "total_federal_websites": website_data.get('metadata', {}).get('total_websites', 0),
                "active_regulations": regulatory_data.get('summary', {}).get('total_regulations', 0),
                "high_priority_regulations": regulatory_data.get('summary', {}).get('high_relevance_count', 0),
                "government_digital_maturity": website_data.get('digital_presence', {}).get('digital_maturity_score', 0)
            },
            "opportunities": {
                "agencies_with_strong_digital_presence": [
                    agency for agency, count in website_data.get('agency_stats', {}).get('top_agencies', {}).items()
                    if count > 10
                ][:10],
                "recent_policy_changes": [
                    {
                        "title": reg.get('title', ''),
                        "relevance_score": reg.get('contractor_relevance_score', 0),
                        "publication_date": reg.get('publication_date', ''),
                        "agencies": reg.get('agency_names', [])
                    }
                    for reg in regulatory_data.get('recent_regulations', [])[:5]
                ]
            },
            "market_intelligence": {
                "most_active_agencies": list(website_data.get('agency_stats', {}).get('top_agencies', {}).keys())[:10],
                "regulatory_trends": {
                    "total_contractor_relevant": regulatory_data.get('summary', {}).get('total_regulations', 0),
                    "high_impact_policies": regulatory_data.get('summary', {}).get('high_impact_policies', 0),
                    "trend": "increasing" if regulatory_data.get('summary', {}).get('total_regulations', 0) > 20 else "stable"
                }
            },
            "data_sources": {
                "government_apis": [
                    "GSA Federal Website Index",
                    "Federal Register API",
                    "USASpending.gov", 
                    "SAM.gov",
                    "USPTO Patents",
                    "FRED Economic Data"
                ],
                "update_frequency": "Real-time to daily",
                "data_coverage": "Comprehensive federal government intelligence"
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating contractor intelligence dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh-cache")
async def refresh_intelligence_cache(background_tasks: BackgroundTasks):
    """Refresh cached government intelligence data"""
    try:
        def refresh_data():
            """Background task to refresh all cached data"""
            import asyncio
            
            async def refresh_all():
                await get_federal_website_intelligence()
                await get_contractor_regulatory_intelligence()
            
            asyncio.run(refresh_all())
        
        background_tasks.add_task(refresh_data)
        
        return {
            "status": "success",
            "message": "Cache refresh initiated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/congressional-intelligence", response_model=Dict)
async def get_congressional_intelligence():
    """Get congressional intelligence for contractors"""
    try:
        logger.info("Fetching congressional intelligence")
        intelligence = await get_congressional_contractor_intelligence()
        
        return {
            "status": "success",
            "data": intelligence,
            "source": "Congress.gov API",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching congressional intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/procurement-opportunities", response_model=Dict)
async def get_procurement_opportunities():
    """Get real procurement opportunities from SAM.gov"""
    try:
        logger.info("Fetching real procurement opportunities")
        opportunities = await get_real_procurement_opportunities()
        
        return {
            "status": "success",
            "data": opportunities,
            "source": "SAM.gov Opportunities API",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching procurement opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agency-opportunities/{agency_name}", response_model=Dict)
async def get_agency_procurement_opportunities(agency_name: str):
    """Get procurement opportunities for specific agency"""
    try:
        logger.info(f"Fetching opportunities for agency: {agency_name}")
        opportunities = await get_agency_opportunities(agency_name)
        
        return {
            "status": "success",
            "agency": agency_name,
            "data": opportunities,
            "count": len(opportunities),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching agency opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comprehensive-intelligence", response_model=Dict)
async def get_comprehensive_intelligence():
    """Get comprehensive government contractor intelligence from all sources"""
    try:
        logger.info("Generating comprehensive intelligence report")
        
        # Fetch data from all sources
        website_data = await get_federal_website_intelligence()
        regulatory_data = await get_contractor_regulatory_intelligence()
        congressional_data = await get_congressional_contractor_intelligence()
        opportunities_data = await get_real_procurement_opportunities()
        govinfo_data = await get_govinfo_congressional_intelligence()
        
        # Combine all intelligence
        comprehensive_report = {
            "executive_summary": {
                "total_federal_websites": website_data.get('metadata', {}).get('total_websites', 0),
                "active_opportunities": opportunities_data.get('summary', {}).get('total_active_opportunities', 0),
                "contractor_relevant_regulations": regulatory_data.get('summary', {}).get('total_regulations', 0),
                "congressional_bills_tracked": congressional_data.get('summary', {}).get('total_contractor_bills', 0),
                "govinfo_documents": govinfo_data.get('summary', {}).get('total_congressional_documents', 0),
                "estimated_opportunity_value": opportunities_data.get('summary', {}).get('estimated_total_value', 0)
            },
            "digital_intelligence": {
                "government_websites": website_data.get('metadata', {}),
                "digital_maturity_score": website_data.get('digital_presence', {}).get('digital_maturity_score', 0),
                "top_digital_agencies": list(website_data.get('agency_stats', {}).get('top_agencies', {}).keys())[:5]
            },
            "market_opportunities": {
                "active_opportunities": opportunities_data.get('active_opportunities', [])[:10],
                "small_business_opportunities": opportunities_data.get('small_business_opportunities', [])[:5],
                "most_active_agencies": opportunities_data.get('market_intelligence', {}).get('most_active_agencies', [])
            },
            "policy_intelligence": {
                "recent_regulations": regulatory_data.get('recent_regulations', [])[:5],
                "high_impact_policies": regulatory_data.get('policy_changes', [])[:3],
                "congressional_activity": congressional_data.get('top_contractor_bills', [])[:5],
                "govinfo_documents": govinfo_data.get('congressional_documents', [])[:5]
            },
            "competitive_intelligence": {
                "trending_naics": opportunities_data.get('naics_breakdown', {}),
                "agency_activity": opportunities_data.get('agency_breakdown', {}),
                "market_trends": congressional_data.get('activity_trend', 'stable')
            },
            "data_sources": [
                "GSA Federal Website Index",
                "Federal Register API", 
                "Congress.gov API",
                "SAM.gov Opportunities API",
                "GovInfo API",
                "USASpending.gov",
                "USPTO Patents",
                "FRED Economic Data"
            ],
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "data": comprehensive_report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating comprehensive intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enhanced-gsa-intelligence", response_model=Dict)
async def get_enhanced_gsa_scanning():
    """Get enhanced GSA intelligence with Site Scanning API data"""
    try:
        logger.info("Fetching enhanced GSA intelligence")
        intelligence = await get_enhanced_gsa_intelligence()
        
        return {
            "status": "success",
            "data": intelligence,
            "source": "GSA Federal Website Index + Site Scanning API",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching enhanced GSA intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/govinfo-intelligence", response_model=Dict)
async def get_govinfo_intelligence():
    """Get congressional documents and federal publications from GovInfo"""
    try:
        logger.info("Fetching GovInfo congressional intelligence")
        intelligence = await get_govinfo_congressional_intelligence()
        
        return {
            "status": "success",
            "data": intelligence,
            "source": "GovInfo API",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching GovInfo intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/govinfo-documents", response_model=Dict)
async def get_govinfo_document_feed(
    doc_type: str = Query("congressional", description="Document type: congressional or federal_register"),
    limit: int = Query(20, le=100, description="Maximum number of documents to return")
):
    """Get specific document types from GovInfo"""
    try:
        logger.info(f"Fetching GovInfo {doc_type} documents")
        documents = await get_govinfo_documents(doc_type)
        
        return {
            "status": "success",
            "data": documents[:limit],
            "document_type": doc_type,
            "count": len(documents[:limit]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching GovInfo documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check for government intelligence services"""
    try:
        from config.api_config import api_config
        
        # Test each integration
        available_apis = api_config.get_available_apis()
        health_status = {
            "api_keys_available": available_apis,
            "integrations": {
                "gsa_website_index": "operational",
                "gsa_site_scanning": "operational" if available_apis.get('gsa') else "public_data_only",
                "federal_register": "operational",
                "congress_gov": "operational" if available_apis.get('congress_gov') else "mock_data",
                "sam_opportunities": "operational" if available_apis.get('sam_gov') else "mock_data",
                "govinfo": "operational" if available_apis.get('govinfo') else "mock_data"
            },
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "overall_status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }