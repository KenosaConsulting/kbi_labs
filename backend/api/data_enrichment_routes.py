#!/usr/bin/env python3
"""
Data Enrichment API Routes
REST API endpoints for government data enrichment functionality

Provides endpoints for requesting, monitoring, and retrieving enriched government data.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import logging
import asyncpg

from ..services.data_enrichment_service import (
    get_enrichment_service, 
    DataEnrichmentService, 
    EnrichmentJobConfig, 
    Priority
)
from ..database.connection import get_database_pool

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/data-enrichment", tags=["Data Enrichment"])

# ==============================================================================
# Request/Response Models
# ==============================================================================

class EnrichmentRequest(BaseModel):
    """Request model for agency data enrichment"""
    
    agency_code: str = Field(..., min_length=3, max_length=10, description="Federal agency code (e.g., '9700' for DoD)")
    agency_name: Optional[str] = Field(None, max_length=255, description="Human-readable agency name")
    data_types: List[str] = Field(
        default=["budget", "personnel", "contracts", "organizational"], 
        description="Types of data to enrich"
    )
    enrichment_depth: str = Field(
        default="standard", 
        description="Level of enrichment detail"
    )
    priority: str = Field(default="normal", description="Job priority level")
    user_id: Optional[str] = Field(None, description="ID of requesting user")
    
    @validator('data_types')
    def validate_data_types(cls, v):
        valid_types = ["budget", "personnel", "contracts", "organizational", "strategic"]
        for data_type in v:
            if data_type not in valid_types:
                raise ValueError(f"Invalid data type: {data_type}. Must be one of {valid_types}")
        return v
    
    @validator('enrichment_depth')
    def validate_enrichment_depth(cls, v):
        if v not in ["basic", "standard", "comprehensive"]:
            raise ValueError("enrichment_depth must be 'basic', 'standard', or 'comprehensive'")
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ["low", "normal", "high", "urgent"]:
            raise ValueError("priority must be 'low', 'normal', 'high', or 'urgent'")
        return v

class EnrichmentResponse(BaseModel):
    """Response model for enrichment requests"""
    
    success: bool
    job_id: Optional[str] = None
    status: str
    message: str
    cache_hit: Optional[bool] = False
    data: Optional[Dict[str, Any]] = None
    estimated_duration_minutes: Optional[int] = None
    queue_position: Optional[int] = None

class JobStatusResponse(BaseModel):
    """Response model for job status queries"""
    
    job_id: str
    agency_code: str
    data_types: List[str]
    status: str
    progress: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    quality_score: Optional[float] = None
    error_message: Optional[str] = None

class AgencyDataResponse(BaseModel):
    """Response model for agency data retrieval"""
    
    agency_code: str
    data_available: bool
    data: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None
    quality_metrics: Optional[Dict[str, float]] = None
    message: Optional[str] = None

class EnrichmentSummaryResponse(BaseModel):
    """Response model for enrichment summary"""
    
    agency_code: str
    agency_name: Optional[str] = None
    last_enrichment_request: Optional[datetime] = None
    last_successful_enrichment: Optional[datetime] = None
    current_status: Optional[str] = None
    available_data_types: int = 0
    average_quality_score: Optional[float] = None
    total_access_count: int = 0

# ==============================================================================
# API Endpoints
# ==============================================================================

@router.post("/enrich", response_model=EnrichmentResponse)
async def request_agency_enrichment(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks,
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Request data enrichment for a government agency
    
    This endpoint initiates the data enrichment process for a specified agency.
    If fresh data is available in cache, it returns immediately. Otherwise,
    it queues a background job to collect and process the data.
    
    - **agency_code**: Federal agency code (e.g., '9700' for Department of Defense)
    - **data_types**: List of data types to enrich (budget, personnel, contracts, organizational, strategic)
    - **enrichment_depth**: Level of detail (basic, standard, comprehensive)
    - **priority**: Job priority (low, normal, high, urgent)
    """
    
    try:
        logger.info(f"Enrichment request received for agency {request.agency_code}")
        
        # Get enrichment service
        service = await get_enrichment_service(db_pool)
        
        # Create job configuration
        config = EnrichmentJobConfig(
            agency_code=request.agency_code,
            agency_name=request.agency_name,
            data_types=request.data_types,
            enrichment_depth=request.enrichment_depth,
            priority=Priority(request.priority),
            requested_by_user_id=request.user_id
        )
        
        # Request enrichment
        result = await service.request_agency_enrichment(config)
        
        # Format response
        response = EnrichmentResponse(
            success=True,
            job_id=result.get("job_id"),
            status=result.get("status", "unknown"),
            message=result.get("message", "Enrichment processed"),
            cache_hit=result.get("cache_hit", False),
            data=result.get("data"),
            estimated_duration_minutes=result.get("estimated_duration_minutes"),
            queue_position=result.get("queue_position")
        )
        
        logger.info(f"Enrichment request processed for agency {request.agency_code}: {response.status}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing enrichment request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process enrichment request: {str(e)}"
        )

@router.get("/job/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Get the status of a specific enrichment job
    
    Returns detailed information about a running or completed enrichment job,
    including progress, quality metrics, and any errors.
    
    - **job_id**: UUID of the enrichment job
    """
    
    try:
        logger.info(f"Status request for job {job_id}")
        
        # Get enrichment service
        service = await get_enrichment_service(db_pool)
        
        # Get job status
        status_data = await service.get_job_status(job_id)
        
        if "error" in status_data:
            raise HTTPException(status_code=404, detail=status_data["error"])
        
        # Convert to response model
        response = JobStatusResponse(
            job_id=job_id,
            agency_code=status_data.get("agency_code", "unknown"),
            data_types=status_data.get("data_types", []),
            status=status_data.get("status", "unknown"),
            progress=status_data.get("progress", 0),
            created_at=status_data.get("created_at"),
            started_at=status_data.get("started_at"),
            completed_at=status_data.get("completed_at"),
            records_processed=status_data.get("records_processed", 0),
            quality_score=status_data.get("overall_quality_score"),
            error_message=status_data.get("error_message")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.get("/agency/{agency_code}/data", response_model=AgencyDataResponse)
async def get_agency_data(
    agency_code: str,
    data_types: Optional[List[str]] = Query(None, description="Specific data types to retrieve"),
    include_metadata: bool = Query(True, description="Include quality and metadata information"),
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Retrieve enriched data for a government agency
    
    Returns cached enriched data for the specified agency. Data must have been
    previously enriched via the /enrich endpoint.
    
    - **agency_code**: Federal agency code
    - **data_types**: Optional list of specific data types to retrieve
    - **include_metadata**: Whether to include quality scores and metadata
    """
    
    try:
        logger.info(f"Data request for agency {agency_code}")
        
        # Get enrichment service
        service = await get_enrichment_service(db_pool)
        
        # Get agency data
        data_result = await service.get_agency_data(
            agency_code=agency_code,
            data_types=data_types,
            include_metadata=include_metadata
        )
        
        # Extract quality metrics if available
        quality_metrics = {}
        last_updated = None
        
        if data_result.get("data"):
            for data_type, type_data in data_result["data"].items():
                if isinstance(type_data, dict) and "_metadata" in type_data:
                    metadata = type_data["_metadata"]
                    quality_metrics[data_type] = metadata.get("quality_score")
                    
                    # Get most recent update time
                    if metadata.get("last_updated"):
                        update_time = datetime.fromisoformat(metadata["last_updated"])
                        if last_updated is None or update_time > last_updated:
                            last_updated = update_time
        
        response = AgencyDataResponse(
            agency_code=agency_code,
            data_available=data_result.get("data_available", False),
            data=data_result.get("data"),
            last_updated=last_updated,
            quality_metrics=quality_metrics if quality_metrics else None,
            message=data_result.get("message")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting agency data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agency data: {str(e)}"
        )

@router.get("/agency/{agency_code}/summary", response_model=EnrichmentSummaryResponse)
async def get_agency_enrichment_summary(
    agency_code: str,
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Get enrichment summary for an agency
    
    Returns a high-level summary of the enrichment status for an agency,
    including last enrichment date, data availability, and quality metrics.
    
    - **agency_code**: Federal agency code
    """
    
    try:
        logger.info(f"Summary request for agency {agency_code}")
        
        # Get enrichment service
        service = await get_enrichment_service(db_pool)
        
        # Get enrichment summary
        summary_data = await service.get_enrichment_summary(agency_code)
        
        response = EnrichmentSummaryResponse(
            agency_code=agency_code,
            agency_name=summary_data.get("agency_name"),
            last_enrichment_request=summary_data.get("last_enrichment_request"),
            last_successful_enrichment=summary_data.get("last_successful_enrichment"),
            current_status=summary_data.get("current_status"),
            available_data_types=summary_data.get("available_data_types", 0),
            average_quality_score=summary_data.get("average_quality_score"),
            total_access_count=summary_data.get("total_access_count", 0)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting enrichment summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enrichment summary: {str(e)}"
        )

@router.delete("/agency/{agency_code}/cache")
async def invalidate_agency_cache(
    agency_code: str,
    data_types: Optional[List[str]] = Query(None, description="Specific data types to invalidate"),
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Invalidate cached data for an agency
    
    Removes cached enriched data for the specified agency, forcing fresh data
    collection on the next enrichment request.
    
    - **agency_code**: Federal agency code
    - **data_types**: Optional list of specific data types to invalidate
    """
    
    try:
        logger.info(f"Cache invalidation request for agency {agency_code}")
        
        # Get enrichment service
        service = await get_enrichment_service(db_pool)
        
        # Invalidate cache
        await service.invalidate_cache(agency_code, data_types)
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Cache invalidated for agency {agency_code}",
                "data_types": data_types or "all"
            }
        )
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )

@router.get("/jobs/active")
async def get_active_jobs(
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Get list of active enrichment jobs
    
    Returns a list of currently running or queued enrichment jobs
    across all agencies.
    """
    
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    id, agency_code, agency_name, data_types, status, 
                    progress, created_at, started_at, priority,
                    estimated_duration_seconds, records_processed
                FROM data_enrichment_jobs 
                WHERE status IN ('queued', 'running')
                ORDER BY 
                    CASE priority 
                        WHEN 'urgent' THEN 4
                        WHEN 'high' THEN 3
                        WHEN 'normal' THEN 2
                        WHEN 'low' THEN 1
                        ELSE 2
                    END DESC,
                    created_at ASC
                LIMIT 50
            """)
            
            jobs = []
            for row in rows:
                jobs.append({
                    "job_id": str(row["id"]),
                    "agency_code": row["agency_code"],
                    "agency_name": row["agency_name"],
                    "data_types": row["data_types"],
                    "status": row["status"],
                    "progress": row["progress"],
                    "priority": row["priority"],
                    "created_at": row["created_at"].isoformat(),
                    "started_at": row["started_at"].isoformat() if row["started_at"] else None,
                    "estimated_duration_seconds": row["estimated_duration_seconds"],
                    "records_processed": row["records_processed"]
                })
            
            return JSONResponse(content={
                "success": True,
                "active_jobs": jobs,
                "total_count": len(jobs)
            })
            
    except Exception as e:
        logger.error(f"Error getting active jobs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active jobs: {str(e)}"
        )

@router.get("/health")
async def get_enrichment_health(
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    Get health status of the data enrichment system
    
    Returns health information about data sources, job queue,
    and overall system status.
    """
    
    try:
        async with db_pool.acquire() as conn:
            # Get data source health
            source_health = await conn.fetch("""
                SELECT source_name, status, response_time_ms, success_rate, 
                       last_check_at, consecutive_failures
                FROM data_source_health
                ORDER BY source_name
            """)
            
            # Get job queue statistics
            job_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) FILTER (WHERE status = 'queued') as queued_jobs,
                    COUNT(*) FILTER (WHERE status = 'running') as running_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed' AND created_at > NOW() - INTERVAL '24 hours') as completed_24h,
                    COUNT(*) FILTER (WHERE status = 'failed' AND created_at > NOW() - INTERVAL '24 hours') as failed_24h
                FROM data_enrichment_jobs
            """)
            
            # Get cache statistics
            cache_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_cached_entries,
                    COUNT(*) FILTER (WHERE expires_at > NOW()) as valid_entries,
                    AVG(quality_score) as average_quality,
                    SUM(access_count) as total_accesses
                FROM enriched_data_cache
            """)
            
            # Format data source health
            sources = []
            for row in source_health:
                sources.append({
                    "name": row["source_name"],
                    "status": row["status"],
                    "response_time_ms": row["response_time_ms"],
                    "success_rate": float(row["success_rate"]) if row["success_rate"] else None,
                    "last_check": row["last_check_at"].isoformat() if row["last_check_at"] else None,
                    "consecutive_failures": row["consecutive_failures"]
                })
            
            return JSONResponse(content={
                "success": True,
                "system_status": "healthy",  # Could be computed based on various factors
                "data_sources": sources,
                "job_queue": {
                    "queued_jobs": job_stats["queued_jobs"],
                    "running_jobs": job_stats["running_jobs"],
                    "completed_24h": job_stats["completed_24h"],
                    "failed_24h": job_stats["failed_24h"]
                },
                "cache": {
                    "total_entries": cache_stats["total_cached_entries"],
                    "valid_entries": cache_stats["valid_entries"],
                    "average_quality": float(cache_stats["average_quality"]) if cache_stats["average_quality"] else None,
                    "total_accesses": cache_stats["total_accesses"]
                },
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get health status: {str(e)}"
        )

# ==============================================================================
# WebSocket Endpoint for Real-time Updates
# ==============================================================================

from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/ws/job/{job_id}")
async def websocket_job_updates(
    websocket: WebSocket,
    job_id: str,
    db_pool: asyncpg.Pool = Depends(get_database_pool)
):
    """
    WebSocket endpoint for real-time job updates
    
    Provides real-time updates on job progress, status changes,
    and completion notifications.
    """
    
    await websocket.accept()
    logger.info(f"WebSocket connection established for job {job_id}")
    
    try:
        # Get enrichment service
        service = await get_enrichment_service(db_pool)
        
        last_status = None
        last_progress = None
        
        while True:
            # Get current job status
            status_data = await service.get_job_status(job_id)
            
            if "error" in status_data:
                await websocket.send_json({
                    "type": "error",
                    "message": status_data["error"]
                })
                break
            
            current_status = status_data.get("status")
            current_progress = status_data.get("progress", 0)
            
            # Send update if status or progress changed
            if current_status != last_status or current_progress != last_progress:
                await websocket.send_json({
                    "type": "update",
                    "job_id": job_id,
                    "status": current_status,
                    "progress": current_progress,
                    "records_processed": status_data.get("records_processed", 0),
                    "quality_score": status_data.get("overall_quality_score"),
                    "timestamp": datetime.now().isoformat()
                })
                
                last_status = current_status
                last_progress = current_progress
            
            # If job is completed or failed, send final update and close
            if current_status in ["completed", "failed", "cancelled"]:
                await websocket.send_json({
                    "type": "final",
                    "job_id": job_id,
                    "status": current_status,
                    "message": "Job finished" if current_status == "completed" else f"Job {current_status}",
                    "error_message": status_data.get("error_message") if current_status == "failed" else None
                })
                break
            
            # Wait before next check
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            })
        except:
            pass  # Connection might already be closed

# ==============================================================================
# Utility Endpoints
# ==============================================================================

@router.get("/agencies")
async def get_supported_agencies():
    """
    Get list of supported government agencies
    
    Returns a list of federal agencies that can be enriched
    by the data pipeline.
    """
    
    # This could be stored in database or configuration
    agencies = [
        {"code": "9700", "name": "Department of Defense", "category": "Defense"},
        {"code": "7000", "name": "Department of Homeland Security", "category": "Security"},
        {"code": "7500", "name": "Department of Health and Human Services", "category": "Health"},
        {"code": "1400", "name": "Department of the Interior", "category": "Natural Resources"},
        {"code": "4700", "name": "General Services Administration", "category": "Government Services"},
        {"code": "3600", "name": "Department of Veterans Affairs", "category": "Veterans"},
        {"code": "5700", "name": "Department of the Air Force", "category": "Defense"},
        {"code": "2100", "name": "Department of the Army", "category": "Defense"},
        {"code": "1700", "name": "Department of the Navy", "category": "Defense"}
    ]
    
    return JSONResponse(content={
        "success": True,
        "agencies": agencies,
        "total_count": len(agencies)
    })

@router.get("/data-types")
async def get_supported_data_types():
    """
    Get list of supported data types for enrichment
    
    Returns information about the types of data that can be
    collected and enriched for government agencies.
    """
    
    data_types = [
        {
            "type": "budget",
            "name": "Budget Data",
            "description": "Financial data including budget authority, outlays, and spending patterns",
            "typical_records": "100-1000",
            "update_frequency": "Weekly"
        },
        {
            "type": "personnel", 
            "name": "Personnel Data",
            "description": "Key personnel, leadership, and organizational contacts",
            "typical_records": "50-500",
            "update_frequency": "Monthly"
        },
        {
            "type": "contracts",
            "name": "Contract Data", 
            "description": "Contract awards, procurement opportunities, and vendor information",
            "typical_records": "200-2000",
            "update_frequency": "Daily"
        },
        {
            "type": "organizational",
            "name": "Organizational Data",
            "description": "Organizational structure, office hierarchy, and reporting relationships",
            "typical_records": "20-200",
            "update_frequency": "Bi-weekly"
        },
        {
            "type": "strategic",
            "name": "Strategic Data",
            "description": "Strategic plans, initiatives, and performance goals",
            "typical_records": "10-100", 
            "update_frequency": "Monthly"
        }
    ]
    
    return JSONResponse(content={
        "success": True,
        "data_types": data_types,
        "total_count": len(data_types)
    })