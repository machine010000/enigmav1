"""
Production configuration for Enigma.

Environment-based configuration management with secure secrets handling.
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # NVIDIA NIM API
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: Optional[str] = os.getenv("NVIDIA_BASE_URL", None)
    AI_MODEL: str = os.getenv("AI_MODEL", "meta/llama-3.3-70b-instruct")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "nvidia")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Redis - No localhost default for production
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    
    # Upwork Marketplace Adapter - No localhost default for production (TASK-051)
    UPWORK_CLIENT_ID: str = os.getenv("UPWORK_CLIENT_ID", "")
    UPWORK_CLIENT_SECRET: str = os.getenv("UPWORK_CLIENT_SECRET", "")
    UPWORK_REDIRECT_URI: str = os.getenv("UPWORK_REDIRECT_URI", "")
    
    # Fiverr Marketplace Adapter - No localhost default for production (TASK-051)
    FIVERR_CLIENT_ID: str = os.getenv("FIVERR_CLIENT_ID", "")
    FIVERR_CLIENT_SECRET: str = os.getenv("FIVERR_CLIENT_SECRET", "")
    FIVERR_REDIRECT_URI: str = os.getenv("FIVERR_REDIRECT_URI", "")
    
    # Freelancer Marketplace Adapter - No localhost default for production (TASK-051)
    FREELANCER_CLIENT_ID: str = os.getenv("FREELANCER_CLIENT_ID", "")
    FREELANCER_CLIENT_SECRET: str = os.getenv("FREELANCER_CLIENT_SECRET", "")
    FREELANCER_REDIRECT_URI: str = os.getenv("FREELANCER_REDIRECT_URI", "")
    
    # Mostaql Marketplace Adapter - No localhost default for production (TASK-051)
    MOSTAQL_CLIENT_ID: str = os.getenv("MOSTAQL_CLIENT_ID", "")
    MOSTAQL_CLIENT_SECRET: str = os.getenv("MOSTAQL_CLIENT_SECRET", "")
    MOSTAQL_REDIRECT_URI: str = os.getenv("MOSTAQL_REDIRECT_URI", "")
    
    # Application Base URL for OAuth callbacks (TASK-051)
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "")
    
    # CORS - No localhost default for production
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # Security
    ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "false").lower() == "true"
    
    # Encryption for OAuth tokens (TASK-052D)
    ENIGMA_ENCRYPTION_KEY: str = os.getenv("ENIGMA_ENCRYPTION_KEY", "")
    
    # Timeouts
    API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "30"))
    DATABASE_TIMEOUT_SECONDS: int = int(os.getenv("DATABASE_TIMEOUT_SECONDS", "10"))
    REDIS_TIMEOUT_SECONDS: int = int(os.getenv("REDIS_TIMEOUT_SECONDS", "5"))
    
    # Retry Policy
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", "1"))
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        valid_environments = ["development", "test", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of {valid_environments}")
        return v.lower()
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        """Parse CORS origins from comma-separated string."""
        # Keep as string, parse in property
        return v if isinstance(v, str) else ""
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is set in production."""
        if os.getenv("ENVIRONMENT", "development").lower() == "production" and not v:
            raise ValueError("SECRET_KEY must be set in production")
        return v
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        return self.parse_cors_origins(self.CORS_ORIGINS)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


def get_settings() -> Settings:
    """Get application settings based on environment."""
    return Settings()


settings = get_settings()


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.ENVIRONMENT.lower() == "development"


def is_testing() -> bool:
    """Check if running in testing environment."""
    return settings.ENVIRONMENT.lower() == "test"
