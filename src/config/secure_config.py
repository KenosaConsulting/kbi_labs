"""
Secure Configuration Management for KBI Labs
Centralized, secure configuration with validation and environment detection
"""

import os
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, validator, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pathlib import Path
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityConfig(PydanticBaseSettings):
    """Security-related configuration"""
    
    # JWT Configuration
    jwt_secret: str = Field(..., min_length=32, description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_hours: int = Field(default=24, ge=1, le=168, description="JWT expiration hours")
    
    # Application Secret
    secret_key: str = Field(..., min_length=32, description="Application secret key")
    
    # Password policies
    min_password_length: int = Field(default=12, ge=8)
    require_password_complexity: bool = Field(default=True)
    
    @validator('jwt_secret', 'secret_key')
    def validate_secrets(cls, v):
        """Validate that secrets are not using default/weak values"""
        weak_secrets = [
            'your-secret-key',
            'development-secret',
            'change-me',
            'your-jwt-secret',
            'kbi-labs-secret-key-2024',
            'development-jwt-secret-change-in-production'
        ]
        
        if any(weak in v.lower() for weak in weak_secrets):
            raise ValueError(f"Secret contains weak/default values. Use a cryptographically secure secret.")
        
        return v

    class Config:
        env_prefix = ""
        case_sensitive = False

class DatabaseConfig(PydanticBaseSettings):
    """Database configuration"""
    
    # PostgreSQL
    postgres_user: str = Field(default="kbi_user")
    postgres_password: str = Field(..., min_length=8)
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = Field(default="kbi_labs")
    
    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379, ge=1, le=65535)
    redis_password: Optional[str] = None
    redis_db: int = Field(default=0, ge=0, le=15)
    
    # Connection settings
    max_connections: int = Field(default=20, ge=1, le=100)
    connection_timeout: int = Field(default=30, ge=5, le=300)
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class ExternalAPIConfig(PydanticBaseSettings):
    """External API configuration"""
    
    # Government APIs
    sam_gov_api_key: Optional[str] = None
    usaspending_api_key: Optional[str] = None
    census_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    uspto_api_key: Optional[str] = None
    nsf_api_key: Optional[str] = None
    
    # Commercial APIs
    google_places_api_key: Optional[str] = None
    hunter_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # API rate limiting
    default_rate_limit: int = Field(default=100, ge=1)
    burst_limit: int = Field(default=200, ge=1)
    
    def get_available_apis(self) -> List[str]:
        """Return list of configured APIs"""
        available = []
        for field_name, field_value in self.__dict__.items():
            if field_name.endswith('_api_key') and field_value:
                api_name = field_name.replace('_api_key', '').upper()
                available.append(api_name)
        return available
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class ApplicationConfig(PydanticBaseSettings):
    """Application configuration"""
    
    # Basic settings
    app_name: str = Field(default="KBI Labs API")
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = Field(default=False)
    
    # Server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    workers: int = Field(default=1, ge=1, le=32)
    
    # Logging
    log_level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    cors_enabled: bool = Field(default=True)
    
    # Processing
    batch_size: int = Field(default=50, ge=1, le=1000)
    max_concurrent_requests: int = Field(default=25, ge=1, le=100)
    
    @validator('environment')
    def validate_environment(cls, v):
        """Ensure production environment has appropriate settings"""
        return v.lower()
    
    @validator('debug')
    def validate_debug_in_production(cls, v, values):
        """Ensure debug is False in production"""
        if values.get('environment') == 'production' and v:
            warnings.warn("Debug mode should be disabled in production")
        return v
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class KBILabsConfig:
    """Main configuration class that combines all config sections"""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration with optional env file"""
        
        # Set environment file
        if env_file:
            os.environ.setdefault('ENV_FILE', env_file)
        
        # Load configuration sections
        try:
            self.security = SecurityConfig()
            self.database = DatabaseConfig()
            self.external_apis = ExternalAPIConfig()
            self.application = ApplicationConfig()
            
            self._validate_configuration()
            
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            raise
    
    def _validate_configuration(self):
        """Perform cross-section validation"""
        
        # Production environment checks
        if self.application.environment == 'production':
            
            # Check for secure secrets
            if 'development' in self.security.jwt_secret.lower():
                raise ValueError("Production environment cannot use development JWT secret")
            
            if 'development' in self.security.secret_key.lower():
                raise ValueError("Production environment cannot use development secret key")
            
            # Check debug is disabled
            if self.application.debug:
                raise ValueError("Debug mode must be disabled in production")
            
            # Check CORS is restricted
            if '*' in self.application.cors_origins:
                raise ValueError("CORS origins must be restricted in production")
        
        # Database connectivity validation would go here
        logger.info(f"Configuration validated for {self.application.environment} environment")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without secrets)"""
        
        available_apis = self.external_apis.get_available_apis()
        
        return {
            'environment': self.application.environment,
            'debug': self.application.debug,
            'database_configured': bool(self.database.postgres_password),
            'redis_configured': True,
            'available_apis': available_apis,
            'api_count': len(available_apis),
            'cors_enabled': self.application.cors_enabled,
            'jwt_algorithm': self.security.jwt_algorithm,
            'jwt_expire_hours': self.security.jwt_expire_hours
        }

# Global configuration instance
_config: Optional[KBILabsConfig] = None

def get_config(env_file: Optional[str] = None) -> KBILabsConfig:
    """Get or create global configuration instance"""
    global _config
    
    if _config is None:
        _config = KBILabsConfig(env_file)
    
    return _config

def reload_config(env_file: Optional[str] = None) -> KBILabsConfig:
    """Force reload of configuration"""
    global _config
    _config = None
    return get_config(env_file)

# Convenience function for FastAPI dependency injection
def get_settings() -> KBILabsConfig:
    """FastAPI dependency for configuration"""
    return get_config()

if __name__ == "__main__":
    # Test configuration loading
    try:
        config = get_config()
        summary = config.get_summary()
        
        print("KBI Labs Configuration Summary:")
        print("=" * 40)
        for key, value in summary.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Configuration error: {e}")