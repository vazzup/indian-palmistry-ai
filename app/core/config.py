"""
Application configuration management using Pydantic settings.

This module provides centralized configuration loading from environment variables
with validation and type safety. Supports both development (SQLite + local Redis)
and production (Supabase + managed Redis) environments.

Key features:
- Environment-based configuration
- Database URL detection and validation
- Redis connection settings
- Security settings for sessions and JWT
- File storage configuration
"""

from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Database connection URL"
    )
    
    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for sessions and caching"
    )
    
    # Celery Configuration
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL for background jobs"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL"
    )
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for palmistry analysis"
    )
    openai_assistant_id: Optional[str] = Field(
        default=None,
        description="OpenAI Assistant ID for palmistry analysis"
    )
    
    # Security Configuration
    secret_key: str = Field(
        default="change-this-to-a-secure-secret-key-in-production",
        description="Secret key for session encryption"
    )
    jwt_secret: str = Field(
        default="change-this-to-a-secure-jwt-secret-in-production",
        description="JWT secret key"
    )
    
    # CORS Configuration
    allowed_origins_str: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
        alias="ALLOWED_ORIGINS"
    )
    
    # File Storage Configuration
    file_storage_root: str = Field(
        default="./data/images",
        description="Root directory for file storage"
    )
    
    # Application Configuration
    debug: bool = Field(
        default=True,
        description="Debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    environment: str = Field(
        default="development",
        description="Environment (development/production)"
    )
    
    # Session Configuration
    session_expire_seconds: int = Field(
        default=604800,  # 1 week
        description="Session expiration time in seconds"
    )
    session_cookie_name: str = Field(
        default="palmistry_session",
        description="Session cookie name"
    )
    session_cookie_secure: bool = Field(
        default=False,
        description="Secure session cookies (HTTPS only)"
    )
    session_cookie_samesite: str = Field(
        default="Lax",
        description="SameSite cookie setting"
    )
    
    @property
    def allowed_origins(self) -> List[str]:
        """Parse comma-separated origins string into list."""
        if self.allowed_origins_str:
            return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]
        return ["http://localhost:3000"]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return "sqlite" in self.database_url.lower()
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.database_url.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings