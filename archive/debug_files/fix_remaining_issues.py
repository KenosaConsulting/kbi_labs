#!/usr/bin/env python3
"""Fix remaining integration issues"""

import os

print("🔧 Fixing Remaining Integration Issues")
print("=" * 40)

# Fix 1: Update cache service to use correct parameter name
print("\n1. Fixing cache service...")
cache_fix = '''"""Simple in-memory cache service"""
from typing import Any, Optional
from datetime import datetime, timedelta
import asyncio

class CacheService:
    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > datetime.now():
                    return value
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set a value with TTL in seconds"""
        async with self._lock:
            expiry = datetime.now() + timedelta(seconds=ttl)
            self._cache[key] = (value, expiry)
    
    async def delete(self, key: str):
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self):
        async with self._lock:
            self._cache.clear()

# Global cache instance
cache_service = CacheService()
'''

with open('src/utils/cache.py', 'w') as f:
    f.write(cache_fix)

print("✅ Fixed cache service")

# Fix 2: Update enrichment service to handle errors better
print("\n2. Updating enrichment service...")
enrichment_fix = '''"""Company Enrichment Service"""
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
'''

with open('src/services/enrichment_service.py', 'w') as f:
    f.write(enrichment_fix)

print("✅ Updated enrichment service")

# Fix 3: Fix USASpending request format
print("\n3. Fixing USASpending integration...")
usaspending_fix = '''"""USASpending.gov API Integration"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.integrations.base_enhanced import EnhancedAPIIntegration
import logging

logger = logging.getLogger(__name__)


class USASpendingIntegration(EnhancedAPIIntegration):
    """USASpending.gov API Integration"""
    
    def __init__(self):
        super().__init__(
            name="USASpending",
            base_url="https://api.usaspending.gov/api/v2",
            api_key=None,  # Public API
            rate_limit=30,
            timeout=45
        )
    
    async def validate_connection(self) -> bool:
        """Validate USASpending API connection"""
        try:
            # Use the autocomplete endpoint
            response = await self._make_request(
                "POST",
                "/autocomplete/funding_agency/",
                json={"search_text": "defense", "limit": 1}
            )
            return True
        except Exception as e:
            logger.error(f"USASpending validation failed: {e}")
            return False
    
    async def get_enrichment_data(self, uei: str) -> Dict[str, Any]:
        """Get federal spending data for a company"""
        try:
            # Use proper date format
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
            
            # Use the correct payload format
            payload = {
                "filters": {
                    "recipient_uei": uei,
                    "time_period": [
                        {
                            "start_date": start_date,
                            "end_date": end_date
                        }
                    ]
                },
                "fields": [
                    "Award ID",
                    "Award Amount",
                    "Start Date",
                    "End Date",
                    "Awarding Agency",
                    "Awarding Sub Agency",
                    "Award Type",
                    "Description"
                ],
                "page": 1,
                "limit": 100,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            response = await self._make_request(
                "POST",
                "/search/spending_by_award/",
                json=payload
            )
            
            return self._parse_spending_response(response)
            
        except Exception as e:
            logger.error(f"Error fetching USASpending data for {uei}: {e}")
            return {"error": str(e)}
    
    def _parse_spending_response(self, data: Dict) -> Dict[str, Any]:
        """Parse USASpending response"""
        results = data.get("results", [])
        
        if not results:
            return {
                "federal_awards_count": 0,
                "federal_awards_total_value": 0,
                "federal_awards_by_agency": {},
                "federal_awards_by_type": {},
                "federal_awards_recent": []
            }
        
        # Aggregate data
        total_value = 0
        agencies = {}
        award_types = {}
        
        for result in results:
            # Safe get of award amount
            try:
                amount = float(result.get("Award Amount", 0) or 0)
                total_value += amount
            except (ValueError, TypeError):
                amount = 0
            
            # By agency
            agency = result.get("Awarding Agency", "Unknown")
            if agency not in agencies:
                agencies[agency] = {"count": 0, "value": 0}
            agencies[agency]["count"] += 1
            agencies[agency]["value"] += amount
            
            # By type
            award_type = result.get("Award Type", "Unknown")
            if award_type not in award_types:
                award_types[award_type] = {"count": 0, "value": 0}
            award_types[award_type]["count"] += 1
            award_types[award_type]["value"] += amount
        
        return {
            "federal_awards_count": len(results),
            "federal_awards_total_value": total_value,
            "federal_awards_by_agency": agencies,
            "federal_awards_by_type": award_types,
            "federal_awards_recent": results[:10]
        }
'''

with open('src/integrations/government/usaspending.py', 'w') as f:
    f.write(usaspending_fix)

print("✅ Fixed USASpending integration")

# Create a test to verify everything works
print("\n4. Creating integration test...")
test_script = '''#!/usr/bin/env python3
"""Test the fixed integrations"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def test_integrations():
    print("🧪 Testing Fixed Integrations")
    print("=" * 40)
    
    # Test individual integrations
    print("\\n1. Testing SAM.gov...")
    try:
        from src.integrations.government.sam_gov import SAMGovIntegration
        sam = SAMGovIntegration()
        result = await sam.validate_connection()
        print(f"   SAM.gov: {'✅ Connected' if result else '❌ Failed'}")
        await sam.close()
    except Exception as e:
        print(f"   SAM.gov: ❌ Error - {e}")
    
    print("\\n2. Testing USASpending...")
    try:
        from src.integrations.government.usaspending import USASpendingIntegration
        usa = USASpendingIntegration()
        result = await usa.validate_connection()
        print(f"   USASpending: {'✅ Connected' if result else '❌ Failed'}")
        
        # Test actual data fetch
        if result:
            data = await usa.get_enrichment_data("SHKSNU48JHZ7")
            if "error" not in data:
                print(f"   ✅ Retrieved {data.get('federal_awards_count', 0)} awards")
        await usa.close()
    except Exception as e:
        print(f"   USASpending: ❌ Error - {e}")
    
    # Test full enrichment
    print("\\n3. Testing full enrichment...")
    try:
        from src.services.enrichment_service import EnrichmentService
        service = EnrichmentService()
        await service.initialize()
        
        result = await service.enrich_company(
            "SHKSNU48JHZ7",
            "1 SYNC TECHNOLOGIES LLC"
        )
        
        print(f"   ✅ Enrichment Score: {result.get('enrichment_score', 0)}")
        print(f"   APIs used: {list(result.get('api_results', {}).keys())}")
        
        # Show successful APIs
        for api, data in result.get('api_results', {}).items():
            if data and "error" not in data and data.get("status") != "no_data":
                print(f"   ✅ {api}: Success")
            else:
                print(f"   ❌ {api}: Failed")
                
    except Exception as e:
        print(f"   ❌ Enrichment Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_integrations())
'''

with open('test_integrations_fixed.py', 'w') as f:
    f.write(test_script)
os.chmod('test_integrations_fixed.py', 0o755)

print("✅ Created test_integrations_fixed.py")
print("\nRun: python3 test_integrations_fixed.py")
