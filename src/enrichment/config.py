import os
from dataclasses import dataclass
from typing import Dict

@dataclass
class APIConfig:
    name: str
    base_url: str
    rate_limit: int  # requests per minute
    timeout: int  # seconds
    api_key: str = None

class EnrichmentConfig:
    # Database configuration - USE SQLITE
    DATABASE_URL = os.getenv(
        "ENRICHMENT_DATABASE_URL",
        "sqlite:///./kbi_enriched.db"
    )
    
    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API configurations
    APIS = {
        "sam_gov": APIConfig(
            name="SAM.gov",
            base_url="https://api.sam.gov",
            rate_limit=10,
            timeout=30,
            api_key=os.getenv("SAM_API_KEY")
        ),
        "usaspending": APIConfig(
            name="USAspending",
            base_url="https://api.usaspending.gov/api/v2",
            rate_limit=100,
            timeout=20
        ),
        "census": APIConfig(
            name="Census",
            base_url="https://api.census.gov/data",
            rate_limit=500,
            timeout=10,
            api_key=os.getenv("CENSUS_API_KEY")
        ),
        "patents": APIConfig(
            name="Patents",
            base_url="http://localhost:8000/api/patents",
            rate_limit=1000,
            timeout=5
        )
    }
    
    # Enrichment settings
    BATCH_SIZE = 100
    MAX_CONCURRENT_REQUESTS = 10
    CACHE_TTL_DAYS = 7
    
    # Data quality thresholds
    MIN_CONFIDENCE_SCORE = 0.7
    MAX_RETRY_ATTEMPTS = 3
