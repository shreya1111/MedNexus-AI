"""
Configuration management for MedNexus-AI backend.

Loads configuration from environment variables.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "MedNexus-AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_DB: int = 1
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v: str) -> List[str]:
        """Parse CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,txt,md"
    UPLOAD_DIR: str = "storage/uploads"
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_extensions(cls, v: str) -> List[str]:
        """Parse allowed extensions."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    # Gemini API
    GEMINI_API_KEY: str
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "storage/chroma"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/backend.log"
    
    # Features
    ENABLE_REGISTRATION: bool = True
    ENABLE_FILE_UPLOAD: bool = True
    ENABLE_ADMIN_PANEL: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
