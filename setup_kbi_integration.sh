#!/bin/bash
# KBI Labs API Integration Setup Script
# This script sets up the complete multi-API integration structure

echo "🚀 KBI Labs API Integration Setup"
echo "================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command executed successfully
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1 failed${NC}"
        exit 1
    fi
}

# Check current directory
if [ ! -d "src" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Please run from KBILabs root directory${NC}"
    echo "Current directory: $(pwd)"
    echo "Expected to find: src/ directory and requirements.txt"
    exit 1
fi

echo -e "${GREEN}✓ Running from correct directory${NC}"

# Step 1: Create directory structure
echo -e "\n${YELLOW}📁 Creating directory structure...${NC}"

mkdir -p src/integrations/{government,financial,technology,academic,news}
check_status "Created integrations directories"

mkdir -p src/api/routers
check_status "Created API routers directory"

mkdir -p src/services
check_status "Created services directory"

mkdir -p src/utils
check_status "Created utils directory"

mkdir -p tests/integrations
check_status "Created test directories"

mkdir -p migrations
check_status "Created migrations directory"

mkdir -p logs
check_status "Created logs directory"

# Step 2: Create the base integration class
echo -e "\n${YELLOW}📝 Creating base integration class...${NC}"

cat > src/integrations/base_enhanced.py << 'EOF'
"""Enhanced base class for external API integrations"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class APIStatus(Enum):
    """API integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


@dataclass
class RateLimiter:
    """Simple rate limiter"""
    max_requests: int
    window_seconds: int
    requests: List[datetime] = None
    
    def __post_init__(self):
        self.requests = []
    
    async def acquire(self):
        """Wait if necessary to respect rate limit"""
        now = datetime.now()
        # Remove old requests outside window
        self.requests = [
            req for req in self.requests 
            if (now - req).total_seconds() < self.window_seconds
        ]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest = min(self.requests)
            wait_time = self.window_seconds - (now - oldest).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                await self.acquire()  # Recursive call after wait
        
        self.requests.append(now)


class CircuitBreaker:
    """Simple circuit breaker implementation"""
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def __aenter__(self):
        if self.state == "open":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() > self.recovery_timeout:
                self.state = "half-open"
            else:
                raise Exception(f"Circuit breaker is open")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success
            self.failure_count = 0
            self.state = "closed"
        elif issubclass(exc_type, self.expected_exception):
            # Expected failure
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        return False  # Don't suppress exceptions


class EnhancedAPIIntegration(ABC):
    """Enhanced base class for external API integrations"""
    
    def __init__(
        self, 
        name: str, 
        base_url: str, 
        api_key: Optional[str] = None,
        rate_limit: int = 60,  # requests per minute
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=httpx.HTTPError
        )
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit,
            window_seconds=60
        )
        
        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            headers=self._get_default_headers()
        )
        
        # Status tracking
        self.last_error: Optional[str] = None
        self.last_success: Optional[datetime] = None
        self.status = APIStatus.INACTIVE
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        headers = {
            "User-Agent": "KBI-Labs/3.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """Make HTTP request with circuit breaker, rate limiting"""
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Make request with circuit breaker
        try:
            async with self.circuit_breaker:
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    **kwargs
                )
                response.raise_for_status()
                
                # Update status
                self.status = APIStatus.ACTIVE
                self.last_success = datetime.now()
                
                # Return appropriate response type
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return response.json()
                elif "application/xml" in content_type or "text/xml" in content_type:
                    return response.text
                else:
                    return response.content
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.status = APIStatus.RATE_LIMITED
            else:
                self.status = APIStatus.ERROR
            self.last_error = str(e)
            raise
        except Exception as e:
            self.status = APIStatus.ERROR
            self.last_error = str(e)
            raise
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate API connection"""
        pass
    
    @abstractmethod
    async def get_enrichment_data(self, **kwargs) -> Dict[str, Any]:
        """Get enrichment data - must be implemented by subclasses"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "name": self.name,
            "status": self.status.value,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_error": self.last_error,
            "circuit_breaker_state": self.circuit_breaker.state
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
EOF

check_status "Created base integration class"

# Step 3: Create SAM.gov integration
echo -e "\n${YELLOW}🏛️ Creating government API integrations...${NC}"

cat > src/integrations/government/sam_gov.py << 'EOF'
"""SAM.gov API Integration"""
from typing import Dict, Any, Optional
from src.integrations.base_enhanced import EnhancedAPIIntegration
import os
import logging

logger = logging.getLogger(__name__)


class SAMGovIntegration(EnhancedAPIIntegration):
    """SAM.gov Entity Management API Integration"""
    
    def __init__(self):
        super().__init__(
            name="SAM.gov",
            base_url="https://api.sam.gov/entity-information/v3",
            api_key=os.getenv("SAM_GOV_API_KEY"),
            rate_limit=10,  # 10 requests per minute
            timeout=30
        )
    
    async def validate_connection(self) -> bool:
        """Validate SAM.gov API connection"""
        try:
            # Try a simple entity lookup
            await self._make_request(
                "GET",
                "/entities",
                params={"api_key": self.api_key, "limit": 1}
            )
            return True
        except Exception as e:
            logger.error(f"SAM.gov validation failed: {e}")
            return False
    
    async def get_enrichment_data(self, uei: str) -> Dict[str, Any]:
        """Get entity information from SAM.gov"""
        try:
            response = await self._make_request(
                "GET",
                f"/entities/{uei}",
                params={"api_key": self.api_key}
            )
            
            return self._parse_entity_response(response)
        except Exception as e:
            logger.error(f"Error fetching SAM.gov data for {uei}: {e}")
            return {"error": str(e)}
    
    def _parse_entity_response(self, data: Dict) -> Dict[str, Any]:
        """Parse SAM.gov entity response"""
        entity = data.get("entityData", [{}])[0]
        registration = entity.get("entityRegistration", {})
        assertions = entity.get("assertions", {})
        
        return {
            "sam_registration_status": registration.get("registrationStatus"),
            "sam_registration_date": registration.get("registrationDate"),
            "sam_expiration_date": registration.get("expirationDate"),
            "cage_code": registration.get("cageCode"),
            "business_types": assertions.get("businessTypes", []),
            "sam_points_of_contact": entity.get("pointsOfContact", []),
            "sam_certifications": assertions.get("certifications", {}),
            "sam_disaster_response": assertions.get("disasterResponse", {}),
            "physical_address": registration.get("physicalAddress", {}),
            "mailing_address": registration.get("mailingAddress", {}),
            "congressional_district": registration.get("congressionalDistrict"),
            "sam_url": registration.get("samUrl")
        }
EOF

check_status "Created SAM.gov integration"

# Step 4: Create USASpending integration
cat > src/integrations/government/usaspending.py << 'EOF'
"""USASpending.gov API Integration"""
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
            timeout=45  # Longer timeout for complex queries
        )
    
    async def validate_connection(self) -> bool:
        """Validate USASpending API connection"""
        try:
            await self._make_request("GET", "/agency/list/")
            return True
        except Exception as e:
            logger.error(f"USASpending validation failed: {e}")
            return False
    
    async def get_enrichment_data(self, uei: str) -> Dict[str, Any]:
        """Get federal spending data for a company"""
        try:
            # Get awards for the past 5 years
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5*365)
            
            payload = {
                "filters": {
                    "recipient_uei": [uei],
                    "time_period": [{
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    }]
                },
                "fields": [
                    "Award ID", "Award Amount", "Total Outlays",
                    "Start Date", "End Date", "Award Type",
                    "Awarding Agency", "Awarding Sub Agency",
                    "Contract Award Type", "Description"
                ],
                "page": 1,
                "limit": 100,
                "sort": "End Date",
                "order": "desc"
            }
            
            response = await self._make_request(
                "POST",
                "/search/spending_by_award",
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
                "federal_awards_total_outlays": 0,
                "federal_awards_by_agency": {},
                "federal_awards_by_type": {},
                "federal_awards_recent": []
            }
        
        # Aggregate data
        total_value = sum(float(r.get("Award Amount", 0)) for r in results)
        total_outlays = sum(float(r.get("Total Outlays", 0)) for r in results)
        
        # Group by agency
        agencies = {}
        award_types = {}
        
        for result in results:
            # By agency
            agency = result.get("Awarding Agency", "Unknown")
            if agency not in agencies:
                agencies[agency] = {"count": 0, "value": 0}
            agencies[agency]["count"] += 1
            agencies[agency]["value"] += float(result.get("Award Amount", 0))
            
            # By type
            award_type = result.get("Award Type", "Unknown")
            if award_type not in award_types:
                award_types[award_type] = {"count": 0, "value": 0}
            award_types[award_type]["count"] += 1
            award_types[award_type]["value"] += float(result.get("Award Amount", 0))
        
        return {
            "federal_awards_count": len(results),
            "federal_awards_total_value": total_value,
            "federal_awards_total_outlays": total_outlays,
            "federal_awards_by_agency": agencies,
            "federal_awards_by_type": award_types,
            "federal_awards_recent": results[:10],  # Top 10 most recent
            "federal_spending_trend": self._calculate_spending_trend(results)
        }
    
    def _calculate_spending_trend(self, awards: List[Dict]) -> Dict[str, float]:
        """Calculate spending trend over years"""
        yearly_spending = {}
        
        for award in awards:
            start_date = award.get("Start Date", "")
            if start_date:
                year = start_date[:4]
                amount = float(award.get("Award Amount", 0))
                yearly_spending[year] = yearly_spending.get(year, 0) + amount
        
        return yearly_spending
EOF

check_status "Created USASpending integration"

# Step 5: Create simple cache service if it doesn't exist
echo -e "\n${YELLOW}💾 Creating cache service...${NC}"

if [ ! -f "src/utils/cache.py" ]; then
    cat > src/utils/cache.py << 'EOF'
"""Simple in-memory cache service"""
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
EOF
    check_status "Created cache service"
else
    echo -e "${GREEN}✓ Cache service already exists${NC}"
fi

# Step 6: Create database connection helper if needed
echo -e "\n${YELLOW}🗄️ Creating database helpers...${NC}"

if [ ! -f "src/db.py" ]; then
    cat > src/db.py << 'EOF'
"""Database connection helpers"""
import sqlite3
import aiosqlite
from contextlib import asynccontextmanager
import os

DATABASE_PATH = os.getenv("DATABASE_URL", "sqlite:///./kbi_production.db").replace("sqlite:///", "")

@asynccontextmanager
async def get_db_connection():
    """Get async database connection"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
EOF
    check_status "Created database helpers"
else
    echo -e "${GREEN}✓ Database helpers already exist${NC}"
fi

# Step 7: Create enrichment service
echo -e "\n${YELLOW}🔧 Creating enrichment service...${NC}"

cat > src/services/enrichment_service.py << 'EOF'
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
        if apis:
            selected_apis = apis
        else:
            selected_apis = list(self.enrichment_weights.keys())
        
        # Create tasks for parallel API calls
        tasks = {}
        for api_name in selected_apis:
            try:
                integration = self.registry.get(api_name)
                if api_name in ["sam_gov", "usaspending"]:
                    # Government APIs use UEI
                    tasks[api_name] = integration.get_enrichment_data(uei=uei)
                else:
                    # Other APIs use company name
                    tasks[api_name] = integration.get_enrichment_data(company_name=company_name)
            except ValueError:
                logger.warning(f"Integration {api_name} not available")
                continue
        
        # Execute all API calls in parallel
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True
        )
        
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
        await self._save_enrichment_data(enriched_data)
        
        # Cache the result
        cache_key = f"enrichment:{uei}"
        await cache_service.set(cache_key, enriched_data, ttl=3600)
        
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
EOF

check_status "Created enrichment service"

# Step 8: Create initial integration registry
echo -e "\n${YELLOW}📋 Creating integration registry...${NC}"

cat > src/integrations/registry.py << 'EOF'
"""Registry for all external API integrations"""
from typing import Dict, Type
import logging
from src.integrations.base_enhanced import EnhancedAPIIntegration
from src.integrations.government.sam_gov import SAMGovIntegration
from src.integrations.government.usaspending import USASpendingIntegration

logger = logging.getLogger(__name__)


class IntegrationRegistry:
    """Registry for all external API integrations"""
    
    def __init__(self):
        self._integrations: Dict[str, EnhancedAPIIntegration] = {}
        self._integration_classes: Dict[str, Type[EnhancedAPIIntegration]] = {
            "sam_gov": SAMGovIntegration,
            "usaspending": USASpendingIntegration,
            # Add more as implemented
        }
    
    async def initialize_all(self):
        """Initialize all registered integrations"""
        logger.info("Initializing API integrations...")
        
        for name, integration_class in self._integration_classes.items():
            try:
                integration = integration_class()
                if await integration.validate_connection():
                    self._integrations[name] = integration
                    logger.info(f"✅ Initialized {name} integration")
                else:
                    logger.warning(f"❌ Failed to validate {name} integration")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name}: {e}")
        
        logger.info(f"Initialized {len(self._integrations)}/{len(self._integration_classes)} integrations")
    
    def get(self, name: str) -> EnhancedAPIIntegration:
        """Get integration by name"""
        if name not in self._integrations:
            raise ValueError(f"Integration {name} not found or not initialized")
        return self._integrations[name]
    
    def get_all(self) -> Dict[str, EnhancedAPIIntegration]:
        """Get all initialized integrations"""
        return self._integrations
    
    async def close_all(self):
        """Close all integrations"""
        for name, integration in self._integrations.items():
            try:
                await integration.close()
                logger.info(f"Closed {name} integration")
            except Exception as e:
                logger.error(f"Error closing {name}: {e}")


# Global registry instance
integration_registry = IntegrationRegistry()
EOF

check_status "Created integration registry"

# Step 9: Create __init__.py files
echo -e "\n${YELLOW}📄 Creating __init__.py files...${NC}"

touch src/integrations/__init__.py
touch src/integrations/government/__init__.py
touch src/integrations/financial/__init__.py
touch src/integrations/technology/__init__.py
touch src/integrations/academic/__init__.py
touch src/integrations/news/__init__.py
touch src/services/__init__.py
touch src/utils/__init__.py

check_status "Created __init__.py files"

# Step 10: Create database migration
echo -e "\n${YELLOW}🗄️ Creating database migration...${NC}"

cat > migrations/add_enrichment_table.sql << 'EOF'
-- Add company enrichment table
CREATE TABLE IF NOT EXISTS company_enrichment (
    uei TEXT PRIMARY KEY,
    enrichment_data JSON NOT NULL,
    enrichment_score REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uei) REFERENCES companies(uei)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enrichment_score 
ON company_enrichment(enrichment_score DESC);

CREATE INDEX IF NOT EXISTS idx_enrichment_updated 
ON company_enrichment(last_updated DESC);

-- Add enrichment tracking to companies table (if columns don't exist)
-- Note: SQLite doesn't support IF NOT EXISTS for columns, so these might fail if already exist
-- That's okay, the error will be ignored
ALTER TABLE companies ADD COLUMN enrichment_status TEXT DEFAULT 'pending';
ALTER TABLE companies ADD COLUMN last_enriched TIMESTAMP;
EOF

check_status "Created database migration"

# Step 11: Create simple test script
echo -e "\n${YELLOW}🧪 Creating test script...${NC}"

cat > test_integration_setup.py << 'EOF'
#!/usr/bin/env python3
"""Test script to verify integration setup"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_setup():
    print("🧪 Testing KBI Labs Integration Setup")
    print("=" * 50)
    
    # Test imports
    try:
        from integrations.base_enhanced import EnhancedAPIIntegration
        print("✅ Base integration class imported")
    except ImportError as e:
        print(f"❌ Failed to import base class: {e}")
        return
    
    try:
        from integrations.registry import integration_registry
        print("✅ Integration registry imported")
    except ImportError as e:
        print(f"❌ Failed to import registry: {e}")
        return
    
    try:
        from services.enrichment_service import EnrichmentService
        print("✅ Enrichment service imported")
    except ImportError as e:
        print(f"❌ Failed to import service: {e}")
        return
    
    # Test initialization
    print("\n📊 Testing integration initialization...")
    await integration_registry.initialize_all()
    
    integrations = integration_registry.get_all()
    print(f"\n✅ Successfully initialized {len(integrations)} integrations:")
    for name in integrations:
        print(f"   - {name}")
    
    # Cleanup
    await integration_registry.close_all()
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_setup())
EOF

chmod +x test_integration_setup.py
check_status "Created test script"

# Step 12: Update requirements.txt
echo -e "\n${YELLOW}📦 Updating requirements.txt...${NC}"

# Check if already has required packages
if ! grep -q "aiohttp" requirements.txt; then
    cat >> requirements.txt << 'EOF'

# API Integration Dependencies
aiohttp==3.9.1
aiosqlite==0.19.0
tenacity==8.2.3
python-dotenv==1.0.0
httpx==0.25.2
EOF
    check_status "Updated requirements.txt"
else
    echo -e "${GREEN}✓ requirements.txt already has integration dependencies${NC}"
fi

# Step 13: Create .env.template if doesn't exist
echo -e "\n${YELLOW}🔑 Creating .env template...${NC}"

if [ ! -f ".env.template" ]; then
    cat > .env.template << 'EOF'
# KBI Labs API Configuration
# Copy this to .env and fill in your values

# Application
DEBUG=False
PORT=8000
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=sqlite:///./kbi_production.db

# Government APIs
SAM_GOV_API_KEY=your-sam-gov-api-key
USPTO_API_KEY=your-uspto-api-key

# Financial APIs
CRUNCHBASE_API_KEY=your-crunchbase-api-key
DNB_API_KEY=your-dnb-api-key

# News APIs
NEWS_API_KEY=your-news-api-key

# Optional
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
EOF
    check_status "Created .env template"
else
    echo -e "${GREEN}✓ .env template already exists${NC}"
fi

# Step 14: Create integration summary
echo -e "\n${YELLOW}📋 Creating integration summary...${NC}"

cat > INTEGRATION_SETUP.md << 'EOF'
# KBI Labs Integration Setup Complete

## ✅ Created Structure

```
src/
├── integrations/
│   ├── base_enhanced.py         ✓ Enhanced base class with circuit breaker
│   ├── registry.py              ✓ Integration registry
│   ├── government/
│   │   ├── sam_gov.py          ✓ SAM.gov integration
│   │   └── usaspending.py      ✓ USASpending integration
│   ├── financial/              ✓ Ready for additions
│   ├── technology/             ✓ Ready for additions
│   ├── academic/               ✓ Ready for additions
│   └── news/                   ✓ Ready for additions
├── services/
│   └── enrichment_service.py   ✓ Main enrichment logic
├── utils/
│   └── cache.py                ✓ Simple cache service
└── db.py                       ✓ Database helpers
```

## 🚀 Next Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Run database migration**:
   ```bash
   sqlite3 kbi_production.db < migrations/add_enrichment_table.sql
   ```

4. **Test the setup**:
   ```bash
   python test_integration_setup.py
   ```

5. **Add more integrations** (optional):
   - Copy integration pattern from sam_gov.py
   - Add to registry.py
   - Test with test script

## 📊 Available Integrations

- ✅ SAM.gov (Government registration data)
- ✅ USASpending (Federal contracts and grants)
- 🔄 SBIR/STTR (Ready to add)
- 🔄 USPTO (Ready to add)
- 🔄 Crunchbase (Ready to add)
- 🔄 NewsAPI (Ready to add)

## 🧪 Testing

Run the test script to verify everything is working:
```bash
python test_integration_setup.py
```

Expected output:
- ✅ All imports successful
- ✅ 2 integrations initialized (or more if API keys are set)
- ✅ No errors

## 🔧 Troubleshooting

If you encounter import errors:
```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

If database errors occur:
```bash
# Check database exists
ls -la kbi_production.db

# Check tables
sqlite3 kbi_production.db ".tables"
```
EOF

check_status "Created integration summary"

# Final summary
echo -e "\n${GREEN}✅ Integration setup complete!${NC}"
echo -e "\n📊 Summary:"
echo "  - Created directory structure"
echo "  - Added base integration class with circuit breaker"
echo "  - Created SAM.gov and USASpending integrations"
echo "  - Set up enrichment service"
echo "  - Created database migration"
echo "  - Added test scripts"

echo -e "\n🚀 Next steps:"
echo "  1. Install dependencies: pip install -r requirements.txt"
echo "  2. Copy .env.template to .env and add your API keys"
echo "  3. Run migration: sqlite3 kbi_production.db < migrations/add_enrichment_table.sql"
echo "  4. Test setup: python test_integration_setup.py"
echo "  5. Add more integrations as needed"

echo -e "\n📚 See INTEGRATION_SETUP.md for detailed instructions"
