"""Application settings"""
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "KBI Labs API"
    debug: bool = True
    port: int = 8000
    secret_key: str = "development-secret-key-change-in-production"
    jwt_secret: str = "development-jwt-secret-change-in-production"
    
    # Database
    database_url: str = "sqlite:///./kbi_production.db"
    
    # Redis
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    # External APIs (optional)
    sam_gov_api_key: Optional[str] = None
    uspto_api_key: Optional[str] = None
    census_api_key: Optional[str] = None
    nsf_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    
    # Processing settings
    batch_size: int = 50
    max_concurrent_requests: int = 25
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields

def get_settings():
    return Settings()

# Create singleton
settings = get_settings()
