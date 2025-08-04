#!/usr/bin/env python3
"""
Data Enrichment Service
Core service integrating the government data pipeline into the KBI Labs platform

This service manages data enrichment jobs, caching, and integration with the frontend.
"""

import asyncio
import asyncpg
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import time

# Import our pipeline components
from ..data_enrichment.government_data_pipeline import GovernmentDataPipeline, EnrichmentResult
from ..data_enrichment.personnel_data_collector import PersonnelDataCollector
from ..data_enrichment.budget_extraction_pipeline import BudgetExtractionPipeline
from ..data_enrichment.organizational_chart_scraper import OrganizationalChartScraper
from ..data_enrichment.data_validation_system import DataValidationSystem, DataSourceType

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class EnrichmentJobConfig:
    """Configuration for an enrichment job"""
    agency_code: str
    agency_name: Optional[str] = None
    data_types: List[str] = None
    enrichment_depth: str = "standard"  # basic, standard, comprehensive
    priority: Priority = Priority.NORMAL
    requested_by_user_id: Optional[str] = None
    max_retries: int = 3
    
    def __post_init__(self):
        if self.data_types is None:
            self.data_types = ["budget", "personnel", "contracts", "organizational"]

@dataclass  
class EnrichmentJob:
    """Represents an enrichment job in the system"""
    id: str
    config: EnrichmentJobConfig
    status: JobStatus
    progress: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    records_processed: int = 0
    overall_quality_score: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class CachedData:
    """Represents cached enriched data"""
    id: str
    agency_code: str
    data_type: str
    data: Dict[str, Any]
    quality_score: float
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed: Optional[datetime] = None
    access_count: int = 0

class DataEnrichmentService:
    """
    Core service for managing government data enrichment
    Integrates with the database and manages the enrichment pipeline
    """
    
    def __init__(self, database_pool: asyncpg.Pool):
        self.db_pool = database_pool
        
        # Initialize pipeline components
        self.data_pipeline = GovernmentDataPipeline()
        self.personnel_collector = PersonnelDataCollector()
        self.budget_extractor = BudgetExtractionPipeline()
        self.org_scraper = OrganizationalChartScraper()
        self.data_validator = DataValidationSystem()
        
        # Cache configuration
        self.cache_expiry_policies = {
            'personnel': timedelta(days=30),    # Personnel data changes slowly
            'budget': timedelta(days=7),        # Budget data changes weekly  
            'contracts': timedelta(days=1),     # Contract data changes daily
            'organizational': timedelta(days=14), # Org charts change biweekly
            'strategic': timedelta(days=30)     # Strategic plans change monthly
        }
        
        # Background job management
        self.active_jobs: Dict[str, EnrichmentJob] = {}
        self.job_queue: List[EnrichmentJob] = []
        self.max_concurrent_jobs = 3
        
        logger.info("Data enrichment service initialized")
    
    async def initialize(self):
        """Initialize the service and all pipeline components"""
        
        logger.info("Initializing data enrichment service components")
        
        try:
            # Initialize all pipeline components
            await self.data_pipeline.initialize()
            await self.personnel_collector.initialize()
            await self.budget_extractor.initialize()
            await self.org_scraper.initialize()
            
            # Start background job processor
            asyncio.create_task(self._process_job_queue())
            
            logger.info("Data enrichment service fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize data enrichment service: {str(e)}")
            raise
    
    async def request_agency_enrichment(
        self, 
        config: EnrichmentJobConfig
    ) -> Dict[str, Any]:
        """
        Request enrichment for an agency - main entry point
        
        Args:
            config: Enrichment job configuration
            
        Returns:
            Job information including job_id and status
        """
        
        logger.info(f"Enrichment requested for agency {config.agency_code}")
        
        try:
            # Check if we have recent cached data
            cached_data = await self._get_fresh_cached_data(config.agency_code, config.data_types)
            
            if cached_data and self._is_cache_sufficient(cached_data, config):
                logger.info(f"Returning cached data for agency {config.agency_code}")
                return {
                    "status": "completed",
                    "cache_hit": True,
                    "data": cached_data,
                    "message": "Fresh data available from cache"
                }
            
            # Check for existing job
            existing_job = await self._get_active_job(config.agency_code)
            if existing_job:
                logger.info(f"Existing job found for agency {config.agency_code}")
                return {
                    "job_id": existing_job.id,
                    "status": existing_job.status.value,
                    "progress": existing_job.progress,
                    "message": "Enrichment already in progress"
                }
            
            # Create new enrichment job
            job = await self._create_enrichment_job(config)
            
            # Add to queue
            self.job_queue.append(job)
            self.job_queue.sort(key=lambda x: self._get_priority_value(x.config.priority), reverse=True)
            
            logger.info(f"Enrichment job {job.id} queued for agency {config.agency_code}")
            
            return {
                "job_id": job.id,
                "status": job.status.value,
                "progress": job.progress,
                "estimated_duration_minutes": self._estimate_job_duration(config),
                "queue_position": self._get_queue_position(job.id),
                "message": "Enrichment job queued successfully"
            }
            
        except Exception as e:
            logger.error(f"Error requesting agency enrichment: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status of an enrichment job"""
        
        try:
            # Check active jobs first
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return self._job_to_dict(job)
            
            # Check database for completed/failed jobs
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM data_enrichment_jobs WHERE id = $1",
                    uuid.UUID(job_id)
                )
                
                if row:
                    return dict(row)
                else:
                    return {"error": "Job not found"}
                    
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return {"error": str(e)}
    
    async def get_agency_data(
        self, 
        agency_code: str, 
        data_types: List[str] = None,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Get enriched data for an agency from cache
        
        Args:
            agency_code: Agency to get data for
            data_types: Specific data types to retrieve
            include_metadata: Whether to include quality and metadata
            
        Returns:
            Enriched agency data
        """
        
        try:
            if data_types is None:
                data_types = ["budget", "personnel", "contracts", "organizational", "strategic"]
            
            cached_data = await self._get_cached_data(agency_code, data_types)
            
            if not cached_data:
                return {
                    "agency_code": agency_code,
                    "data_available": False,
                    "message": "No enriched data available. Please request enrichment first."
                }
            
            # Update access metrics
            await self._update_access_metrics(cached_data)
            
            result = {
                "agency_code": agency_code,
                "data_available": True,
                "data": {}
            }
            
            for data_type, cache_entry in cached_data.items():
                result["data"][data_type] = cache_entry.data
                
                if include_metadata:
                    result["data"][data_type]["_metadata"] = {
                        "quality_score": cache_entry.quality_score,
                        "last_updated": cache_entry.created_at.isoformat(),
                        "expires_at": cache_entry.expires_at.isoformat() if cache_entry.expires_at else None,
                        "access_count": cache_entry.access_count
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting agency data: {str(e)}")
            raise
    
    async def get_enrichment_summary(self, agency_code: str) -> Dict[str, Any]:
        """Get enrichment summary for an agency"""
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get summary from the view
                summary = await conn.fetchrow(
                    "SELECT * FROM agency_enrichment_summary WHERE agency_code = $1",
                    agency_code
                )
                
                if not summary:
                    return {
                        "agency_code": agency_code,
                        "enrichment_status": "not_enriched",
                        "message": "No enrichment data available"
                    }
                
                return dict(summary)
                
        except Exception as e:
            logger.error(f"Error getting enrichment summary: {str(e)}")
            raise
    
    async def invalidate_cache(self, agency_code: str, data_types: List[str] = None):
        """Invalidate cached data for an agency"""
        
        try:
            async with self.db_pool.acquire() as conn:
                if data_types:
                    await conn.execute(
                        "DELETE FROM enriched_data_cache WHERE agency_code = $1 AND data_type = ANY($2)",
                        agency_code, data_types
                    )
                else:
                    await conn.execute(
                        "DELETE FROM enriched_data_cache WHERE agency_code = $1",
                        agency_code
                    )
                    
            logger.info(f"Cache invalidated for agency {agency_code}, data_types: {data_types}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            raise
    
    async def _process_job_queue(self):
        """Background task to process the enrichment job queue"""
        
        logger.info("Starting job queue processor")
        
        while True:
            try:
                # Check if we can process more jobs
                if len(self.active_jobs) < self.max_concurrent_jobs and self.job_queue:
                    # Get highest priority job
                    job = self.job_queue.pop(0)
                    
                    # Start processing the job
                    self.active_jobs[job.id] = job
                    asyncio.create_task(self._execute_enrichment_job(job))
                
                # Wait before checking again
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in job queue processor: {str(e)}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _execute_enrichment_job(self, job: EnrichmentJob):
        """Execute a single enrichment job"""
        
        logger.info(f"Starting execution of job {job.id} for agency {job.config.agency_code}")
        
        try:
            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            job.progress = 0
            
            await self._update_job_in_database(job)
            
            # Execute the enrichment based on requested data types
            enrichment_results = {}
            total_steps = len(job.config.data_types)
            
            for i, data_type in enumerate(job.config.data_types):
                logger.info(f"Processing {data_type} data for agency {job.config.agency_code}")
                
                try:
                    if data_type == "budget":
                        result = await self._enrich_budget_data(job.config)
                    elif data_type == "personnel":
                        result = await self._enrich_personnel_data(job.config)
                    elif data_type == "contracts":
                        result = await self._enrich_contract_data(job.config)
                    elif data_type == "organizational":
                        result = await self._enrich_organizational_data(job.config)
                    elif data_type == "strategic":
                        result = await self._enrich_strategic_data(job.config)
                    else:
                        logger.warning(f"Unknown data type: {data_type}")
                        continue
                    
                    enrichment_results[data_type] = result
                    
                    # Store in cache
                    await self._store_enriched_data(
                        job.config.agency_code,
                        data_type,
                        result.data,
                        result.quality_score,
                        job.id
                    )
                    
                    job.records_processed += result.records_found
                    
                except Exception as e:
                    logger.error(f"Error enriching {data_type} data: {str(e)}")
                    enrichment_results[data_type] = {"error": str(e)}
                
                # Update progress
                job.progress = int(((i + 1) / total_steps) * 100)
                await self._update_job_in_database(job)
            
            # Calculate overall quality score
            quality_scores = [
                result.quality_score for result in enrichment_results.values() 
                if hasattr(result, 'quality_score') and result.quality_score is not None
            ]
            
            if quality_scores:
                job.overall_quality_score = sum(quality_scores) / len(quality_scores)
            
            # Complete the job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 100
            
            await self._update_job_in_database(job)
            
            logger.info(f"Job {job.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {str(e)}")
            
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            await self._update_job_in_database(job)
            
            # Consider retry logic here based on job.retry_count
            
        finally:
            # Remove from active jobs
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
    
    async def _enrich_budget_data(self, config: EnrichmentJobConfig) -> EnrichmentResult:
        """Enrich budget data for an agency"""
        
        logger.info(f"Enriching budget data for agency {config.agency_code}")
        
        # Use the budget extractor for comprehensive budget analysis
        budget_analysis = await self.budget_extractor.extract_agency_budget(
            agency_code=config.agency_code,
            fiscal_years=[2022, 2023, 2024],
            analysis_depth=config.enrichment_depth
        )
        
        # Convert to EnrichmentResult format
        return EnrichmentResult(
            source="budget_extractor",
            data_type="budget",
            records_found=len(budget_analysis.budget_line_items),
            quality_score=budget_analysis.data_completeness / 100.0,
            last_updated=datetime.now(),
            data={
                "budget_analysis": asdict(budget_analysis),
                "summary": {
                    "total_budget_authority": float(budget_analysis.total_budget_authority),
                    "total_outlays": float(budget_analysis.total_outlays),
                    "execution_rate": budget_analysis.overall_execution_rate,
                    "line_items_count": len(budget_analysis.budget_line_items)
                }
            },
            errors=[]
        )
    
    async def _enrich_personnel_data(self, config: EnrichmentJobConfig) -> EnrichmentResult:
        """Enrich personnel data for an agency"""
        
        logger.info(f"Enriching personnel data for agency {config.agency_code}")
        
        # Use the personnel collector
        personnel_records = await self.personnel_collector.collect_agency_personnel(
            agency_code=config.agency_code,
            collection_depth=config.enrichment_depth,
            focus_roles=['Director', 'Program Manager', 'Contracting Officer']
        )
        
        # Calculate average confidence score
        if personnel_records:
            avg_confidence = sum(record.confidence_score for record in personnel_records) / len(personnel_records)
        else:
            avg_confidence = 0.0
        
        return EnrichmentResult(
            source="personnel_collector",
            data_type="personnel",
            records_found=len(personnel_records),
            quality_score=avg_confidence,
            last_updated=datetime.now(),
            data={
                "personnel_records": [asdict(record) for record in personnel_records],
                "summary": {
                    "total_personnel": len(personnel_records),
                    "average_confidence": avg_confidence,
                    "data_sources": list(set(record.data_sources[0] if record.data_sources else "unknown" for record in personnel_records))
                }
            },
            errors=[]
        )
    
    async def _enrich_contract_data(self, config: EnrichmentJobConfig) -> EnrichmentResult:
        """Enrich contract data for an agency"""
        
        logger.info(f"Enriching contract data for agency {config.agency_code}")
        
        # Use the main data pipeline for contract data
        enrichment_results = await self.data_pipeline.enrich_agency_data(
            agency_code=config.agency_code,
            data_types=['contracts']
        )
        
        return enrichment_results.get('contracts', EnrichmentResult(
            source="data_pipeline",
            data_type="contracts",
            records_found=0,
            quality_score=0.0,
            last_updated=datetime.now(),
            data={},
            errors=["No contract data available"]
        ))
    
    async def _enrich_organizational_data(self, config: EnrichmentJobConfig) -> EnrichmentResult:
        """Enrich organizational data for an agency"""
        
        logger.info(f"Enriching organizational data for agency {config.agency_code}")
        
        # Use the organizational chart scraper
        org_chart = await self.org_scraper.scrape_agency_organizational_chart(
            agency_code=config.agency_code,
            scraping_depth=config.enrichment_depth
        )
        
        return EnrichmentResult(
            source="org_scraper",
            data_type="organizational",
            records_found=org_chart.total_units + org_chart.total_personnel,
            quality_score=org_chart.data_completeness,
            last_updated=datetime.now(),
            data={
                "organizational_chart": asdict(org_chart),
                "summary": {
                    "total_units": org_chart.total_units,
                    "total_personnel": org_chart.total_personnel,
                    "organizational_depth": org_chart.organizational_depth
                }
            },
            errors=[]
        )
    
    async def _enrich_strategic_data(self, config: EnrichmentJobConfig) -> EnrichmentResult:
        """Enrich strategic data for an agency"""
        
        logger.info(f"Enriching strategic data for agency {config.agency_code}")
        
        # Use the main data pipeline for strategic data
        enrichment_results = await self.data_pipeline.enrich_agency_data(
            agency_code=config.agency_code,
            data_types=['strategic']
        )
        
        return enrichment_results.get('strategic', EnrichmentResult(
            source="data_pipeline",
            data_type="strategic",
            records_found=0,
            quality_score=0.0,
            last_updated=datetime.now(),
            data={},
            errors=["No strategic data available"]
        ))
    
    async def _create_enrichment_job(self, config: EnrichmentJobConfig) -> EnrichmentJob:
        """Create a new enrichment job in the database"""
        
        job_id = str(uuid.uuid4())
        job = EnrichmentJob(
            id=job_id,
            config=config,
            status=JobStatus.QUEUED
        )
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_enrichment_jobs 
                (id, agency_code, agency_name, data_types, enrichment_depth, priority, 
                 status, progress, created_at, requested_by_user_id, max_retries)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, 
            uuid.UUID(job_id), config.agency_code, config.agency_name, config.data_types,
            config.enrichment_depth, config.priority.value, job.status.value, job.progress,
            job.created_at, uuid.UUID(config.requested_by_user_id) if config.requested_by_user_id else None,
            config.max_retries)
        
        return job
    
    async def _update_job_in_database(self, job: EnrichmentJob):
        """Update job status in the database"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE data_enrichment_jobs 
                SET status = $2, progress = $3, started_at = $4, completed_at = $5,
                    error_message = $6, records_processed = $7, overall_quality_score = $8,
                    actual_duration_seconds = CASE 
                        WHEN $5 IS NOT NULL AND started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM ($5 - started_at))
                        ELSE NULL 
                    END
                WHERE id = $1
            """,
            uuid.UUID(job.id), job.status.value, job.progress, job.started_at, 
            job.completed_at, job.error_message, job.records_processed, job.overall_quality_score)
    
    async def _store_enriched_data(
        self, 
        agency_code: str, 
        data_type: str, 
        data: Dict[str, Any], 
        quality_score: float,
        job_id: str
    ):
        """Store enriched data in the cache"""
        
        cache_id = str(uuid.uuid4())
        expires_at = datetime.now() + self.cache_expiry_policies.get(data_type, timedelta(days=7))
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO enriched_data_cache 
                (id, agency_code, data_type, data, quality_score, created_at, expires_at, enrichment_job_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (agency_code, data_type) 
                DO UPDATE SET 
                    data = EXCLUDED.data,
                    quality_score = EXCLUDED.quality_score,
                    created_at = EXCLUDED.created_at,
                    expires_at = EXCLUDED.expires_at,
                    enrichment_job_id = EXCLUDED.enrichment_job_id
            """,
            uuid.UUID(cache_id), agency_code, data_type, json.dumps(data), 
            quality_score, datetime.now(), expires_at, uuid.UUID(job_id))
    
    async def _get_cached_data(self, agency_code: str, data_types: List[str]) -> Dict[str, CachedData]:
        """Get cached data for an agency and data types"""
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM enriched_data_cache 
                WHERE agency_code = $1 AND data_type = ANY($2)
                AND (expires_at IS NULL OR expires_at > NOW())
            """, agency_code, data_types)
            
            return {
                row['data_type']: CachedData(
                    id=str(row['id']),
                    agency_code=row['agency_code'],
                    data_type=row['data_type'],
                    data=json.loads(row['data']) if isinstance(row['data'], str) else row['data'],
                    quality_score=float(row['quality_score']),
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    last_accessed=row['last_accessed'],
                    access_count=row['access_count']
                )
                for row in rows
            }
    
    async def _get_fresh_cached_data(self, agency_code: str, data_types: List[str]) -> Optional[Dict[str, Any]]:
        """Get fresh cached data if available"""
        
        cached_data = await self._get_cached_data(agency_code, data_types)
        
        if not cached_data:
            return None
        
        # Check if we have all requested data types and they're fresh
        if set(data_types).issubset(set(cached_data.keys())):
            return {dt: cd.data for dt, cd in cached_data.items()}
        
        return None
    
    def _is_cache_sufficient(self, cached_data: Dict[str, Any], config: EnrichmentJobConfig) -> bool:
        """Check if cached data is sufficient for the request"""
        
        # For now, simple check - has all requested data types
        return set(config.data_types).issubset(set(cached_data.keys()))
    
    async def _get_active_job(self, agency_code: str) -> Optional[EnrichmentJob]:
        """Check if there's an active job for an agency"""
        
        # Check in-memory active jobs
        for job in self.active_jobs.values():
            if job.config.agency_code == agency_code:
                return job
        
        # Check queued jobs
        for job in self.job_queue:
            if job.config.agency_code == agency_code:
                return job
        
        return None
    
    async def _update_access_metrics(self, cached_data: Dict[str, CachedData]):
        """Update access metrics for cached data"""
        
        for data_type, cache_entry in cached_data.items():
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE enriched_data_cache 
                    SET last_accessed = NOW(), access_count = access_count + 1
                    WHERE id = $1
                """, uuid.UUID(cache_entry.id))
    
    def _get_priority_value(self, priority: Priority) -> int:
        """Get numeric value for priority"""
        priority_values = {
            Priority.LOW: 1,
            Priority.NORMAL: 2, 
            Priority.HIGH: 3,
            Priority.URGENT: 4
        }
        return priority_values.get(priority, 2)
    
    def _get_queue_position(self, job_id: str) -> int:
        """Get position of job in queue"""
        for i, job in enumerate(self.job_queue):
            if job.id == job_id:
                return i + 1
        return -1
    
    def _estimate_job_duration(self, config: EnrichmentJobConfig) -> int:
        """Estimate job duration in minutes"""
        
        base_duration = {
            'basic': 2,
            'standard': 5, 
            'comprehensive': 15
        }
        
        duration = base_duration.get(config.enrichment_depth, 5)
        duration *= len(config.data_types)
        
        return duration
    
    def _job_to_dict(self, job: EnrichmentJob) -> Dict[str, Any]:
        """Convert job to dictionary for API response"""
        
        return {
            "job_id": job.id,
            "agency_code": job.config.agency_code,
            "data_types": job.config.data_types,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "records_processed": job.records_processed,
            "quality_score": job.overall_quality_score,
            "error_message": job.error_message
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        logger.info("Cleaning up data enrichment service")
        
        try:
            await self.data_pipeline.close()
            await self.personnel_collector.close()
            await self.budget_extractor.close()
            await self.org_scraper.close()
            
            logger.info("Data enrichment service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

# Global service instance
enrichment_service = None

async def get_enrichment_service(db_pool: asyncpg.Pool) -> DataEnrichmentService:
    """Get or create the global enrichment service instance"""
    
    global enrichment_service
    
    if enrichment_service is None:
        enrichment_service = DataEnrichmentService(db_pool)
        await enrichment_service.initialize()
    
    return enrichment_service