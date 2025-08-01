"""Company Enrichment Service"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from src.integrations.registry import integration_registry
from src.db import get_db_connection
from src.utils.cache import cache_service

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Service for enriching company data from multiple sources"""
    
    def __init__(self):
        self.registry = integration_registry
        self.enrichment_weights = {
            "sam_gov": 0.25,
            "usaspending": 0.20,
            "sbir": 0.15,
            "uspto": 0.15,
            "crunchbase": 0.15,
            "news": 0.10
        }
    
    async def initialize(self):
        """Initialize all integrations"""
        await self.registry.initialize_all()
        logger.info("Enrichment service initialized")
    
    async def enrich_company(
        self, 
        uei: str, 
        company_name: str,
        apis: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Enrich a company with data from multiple APIs"""
        logger.info(f"Starting enrichment for {company_name} (UEI: {uei})")
        
        # Determine which APIs to use
        available_apis = self.registry.get_all()
        if apis:
            selected_apis = [api for api in apis if api in available_apis]
        else:
            selected_apis = list(available_apis.keys())
        
        logger.info(f"Using APIs: {selected_apis}")
        
        # Create tasks for parallel API calls
        tasks = {}
        for api_name in selected_apis:
            try:
                integration = available_apis[api_name]
                if api_name in ["sam_gov", "usaspending"]:
                    # Government APIs use UEI
                    tasks[api_name] = integration.get_enrichment_data(uei=uei)
                else:
                    # Other APIs use company name
                    tasks[api_name] = integration.get_enrichment_data(company_name=company_name)
            except Exception as e:
                logger.error(f"Error creating task for {api_name}: {e}")
                continue
        
        # Execute all API calls in parallel
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        else:
            results = []
        
        # Combine results
        enriched_data = {
            "uei": uei,
            "company_name": company_name,
            "enrichment_timestamp": datetime.now().isoformat(),
            "api_results": {}
        }
        
        for api_name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error in {api_name}: {result}")
                enriched_data["api_results"][api_name] = {"error": str(result)}
            elif result:
                enriched_data["api_results"][api_name] = result
            else:
                enriched_data["api_results"][api_name] = {"status": "no_data"}
        
        # Calculate enrichment score
        enriched_data["enrichment_score"] = self._calculate_enrichment_score(enriched_data)
        
        # Save to database
        try:
            await self._save_enrichment_data(enriched_data)
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
        
        # Cache the result
        try:
            cache_key = f"enrichment:{uei}"
            await cache_service.set(cache_key, enriched_data, ttl=3600)
        except Exception as e:
            logger.error(f"Error caching result: {e}")
        
        return enriched_data
    
    def _calculate_enrichment_score(self, data: Dict) -> float:
        """Calculate enrichment score based on data completeness"""
        api_results = data.get("api_results", {})
        score = 0.0
        total_weight = 0.0
        
        for api_name, weight in self.enrichment_weights.items():
            if api_name in api_results:
                total_weight += weight
                result = api_results.get(api_name, {})
                if result and "error" not in result and "status" not in result:
                    score += weight
        
        if total_weight > 0:
            return round((score / total_weight) * 100, 2)
        return 0.0
    
    async def _save_enrichment_data(self, data: Dict):
        """Save enrichment data to database"""
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO company_enrichment 
                (uei, enrichment_data, enrichment_score, last_updated)
                VALUES (?, ?, ?, ?)
            """, (
                data["uei"],
                json.dumps(data),
                data["enrichment_score"],
                data["enrichment_timestamp"]
            ))
            await conn.commit()
    
    async def get_enrichment_status(self, uei: str) -> Dict[str, Any]:
        """Get enrichment status for a company"""
        # Try cache first
        cache_key = f"enrichment:{uei}"
        cached = await cache_service.get(cache_key)
        if cached:
            return {
                "status": "enriched",
                "data": cached,
                "from_cache": True
            }
        
        # Check database
        async with get_db_connection() as conn:
            async with conn.execute("""
                SELECT enrichment_data, enrichment_score, last_updated
                FROM company_enrichment
                WHERE uei = ?
            """, (uei,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return {
                        "status": "enriched",
                        "data": json.loads(row[0]),
                        "from_cache": False
                    }
                else:
                    return {
                        "status": "not_enriched",
                        "data": None,
                        "from_cache": False
                    }
    
    async def get_api_health(self) -> List[Dict[str, Any]]:
        """Get health status of all APIs"""
        health_checks = []
        
        for name, integration in self.registry.get_all().items():
            health = await integration.health_check()
            health_checks.append(health)
        
        return health_checks
