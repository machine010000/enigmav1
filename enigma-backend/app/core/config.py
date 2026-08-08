"""
Production configuration for Enigma.

Environment-based configuration management with secure secrets handling.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


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
    AI_MODEL: str = os.getenv("AI_MODEL", "meta/llama-3.3-70b-instruct")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "nvidia")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Upwork Marketplace Adapter
    UPWORK_CLIENT_ID: str = os.getenv("UPWORK_CLIENT_ID", "")
    UPWORK_CLIENT_SECRET: str = os.getenv("UPWORK_CLIENT_SECRET", "")
    UPWORK_REDIRECT_URI: str = os.getenv("UPWORK_REDIRECT_URI", "http://localhost:8000/callback")
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # Security
    ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


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
