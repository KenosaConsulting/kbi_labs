"""Company Service - Business logic for company operations"""
from typing import List, Optional, Dict, Any
from src.services.enrichment_pipeline import EnrichmentPipeline
from src.utils.cache import cache_service
import logging

logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self):
        self.enrichment_pipeline = EnrichmentPipeline()
    
    async def list_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        search: Optional[str] = None,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """List companies with filtering and user context"""
        # For now, return mock data
        return {
            "companies": [
                {
                    "uei": "123456789",
                    "name": "Sample Company Inc",
                    "state": "CA",
                    "city": "San Francisco",
                    "industry": "Technology"
                }
            ],
            "total": 1,
            "skip": skip,
            "limit": limit
        }
    
    async def get_company(self, uei: str, user_context: Optional[Dict] = None) -> Optional[Dict]:
        """Get detailed company information"""
        # Mock implementation
        return {
            "uei": uei,
            "name": "Sample Company Inc",
            "state": "CA",
            "city": "San Francisco",
            "industry": "Technology",
            "metrics": {},
            "intelligence": {}
        }
    
    async def enrich_company(self, uei: str, user_context: Dict) -> Dict[str, Any]:
        """Trigger enrichment pipeline for a company"""
        job_id = await self.enrichment_pipeline.queue_enrichment(uei)
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Enrichment job queued for company {uei}"
        }
    
    async def list_companies_legacy(self, skip: int, limit: int) -> Dict[str, Any]:
        """Legacy endpoint support"""
        return await self.list_companies(skip=skip, limit=limit)
    
    def _build_company_query(self, state: Optional[str], search: Optional[str]) -> str:
        """Build SQL query with filters"""
        query = "SELECT * FROM companies WHERE 1=1"
        if state:
            query += f" AND state = '{state}'"
        if search:
            query += f" AND (name ILIKE '%{search}%' OR uei ILIKE '%{search}%')"
        query += " ORDER BY name LIMIT $2 OFFSET $1"
        return query
    
    def _apply_user_context(self, companies: List[Dict], user_context: Dict) -> List[Dict]:
        """Apply user-specific filtering"""
        return companies
    
    def _apply_user_context_single(self, company: Dict, user_context: Optional[Dict]) -> Dict:
        """Apply user context to single company"""
        return company
    
    async def _get_total_count(self, conn, state: Optional[str], search: Optional[str]) -> int:
        """Get total count of companies"""
        return 54799  # Mock count
    
    async def _get_company_metrics(self, uei: str) -> Dict[str, Any]:
        """Get company metrics"""
        return {"revenue": 1000000, "employees": 50}
    
    async def _get_company_intelligence(self, uei: str) -> Dict[str, Any]:
        """Get company intelligence"""
        return {"score": 85, "growth_potential": "High"}
