"""Patents API Router - Example of external API integration"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from typing import Optional, Dict
from src.services.patent_service import PatentService
from src.api.dependencies import get_current_user, require_auth

router = APIRouter()
patent_service = PatentService()

@router.get("/search")
async def search_patents(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, le=100),
    offset: int = Query(0),
    current_user: Dict = Depends(get_current_user)
):
    """Search patents from USPTO and other sources"""
    return await patent_service.search_patents(
        query=q,
        limit=limit,
        offset=offset,
        user_context=current_user
    )

@router.post("/analyze/{patent_id}")
async def analyze_patent(
    patent_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_auth)
):
    """Queue patent for deep analysis"""
    job_id = await patent_service.queue_analysis(patent_id, current_user)
    background_tasks.add_task(patent_service.run_analysis, job_id)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Patent analysis queued for processing"
    }

@router.get("/company/{uei}")
async def get_company_patents(
    uei: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get all patents associated with a company"""
    return await patent_service.get_company_patents(uei, current_user)
