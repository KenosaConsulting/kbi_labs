from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Configuration
    API_SECRET_KEY: str = Field("default-secret-key", env="API_SECRET_KEY")
    API_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="API_ACCESS_TOKEN_EXPIRE_MINUTES")
    API_ALGORITHM: str = Field("HS256", env="API_ALGORITHM")
    
    # Environment
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(True, env="DEBUG")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    
    # Database URLs
    DATABASE_URL: str = Field("postgresql://kbi_user:defaultpassword@localhost:5432/kbi_labs", env="DATABASE_URL")
    MONGO_URL: str = Field("mongodb://kbi_user:defaultpassword@localhost:27017/kbi_labs", env="MONGO_URL")
    NEO4J_URL: str = Field("bolt://localhost:7687", env="NEO4J_URL")
    REDIS_URL: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # Kafka
    KAFKA_BROKER: str = Field("localhost:9092", env="KAFKA_BROKER")
    
    # External APIs
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
