"""
Production configuration for Enigma.

Environment-based configuration management with secure secrets handling.
"""
import os
from typing import Optional, List
from urllib.parse import urlsplit
from pydantic_settings import BaseSettings
from pydantic import field_validator

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Accept", "Authorization", "Content-Type"]


def parse_cors_origins(value: str) -> List[str]:
    """Parse and validate a comma-separated list of exact HTTP origins."""
    if not isinstance(value, str):
        raise ValueError("CORS_ORIGINS must be a comma-separated string")

    origins: List[str] = []
    for entry in value.split(","):
        origin = entry.strip()
        if not origin:
            continue
        if origin == "*":
            raise ValueError(
                "CORS_ORIGINS cannot contain '*' while credentialed CORS is enabled"
            )
        if any(character.isspace() for character in origin) or "\\" in origin:
            raise ValueError(f"Invalid CORS origin: {origin!r}")

        parsed = urlsplit(origin)
        try:
            parsed_port = parsed.port
        except ValueError as exc:
            raise ValueError(f"Invalid CORS origin: {origin!r}") from exc

        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                f"Invalid CORS origin {origin!r}; expected scheme://host[:port]"
            )

        host = parsed.hostname.lower()
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        normalized = f"{parsed.scheme.lower()}://{host}"
        if parsed_port is not None:
            normalized += f":{parsed_port}"
        if normalized not in origins:
            origins.append(normalized)

    return origins


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
    KEYWORD_RESEARCH_MODEL: str = os.getenv(
        "KEYWORD_RESEARCH_MODEL", "meta/llama-3.1-8b-instruct"
    )
    PRODUCT_VERIFICATION_MODEL: str = os.getenv(
        "PRODUCT_VERIFICATION_MODEL", "meta/llama-3.1-8b-instruct"
    )
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
    FREELANCER_API_TOKEN: str = os.getenv("FREELANCER_API_TOKEN", "")
    FREELANCER_SANDBOX: bool = os.getenv("FREELANCER_SANDBOX", "false").lower() == "true"

    # Canonical administrative identity used by admin-only API dependencies.
    ADMIN_USER_EMAIL: str = os.getenv("ADMIN_USER_EMAIL", "admin@enigma.local")
    
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

    # Autonomous execution step budget (TASK-016)
    # Range enforced: 1 – 5.  Client cannot exceed this.
    MAX_AUTONOMOUS_STEPS: int = int(os.getenv("MAX_AUTONOMOUS_STEPS", "3"))
    MIN_AUTONOMOUS_STEPS: int = 1
    MAX_AUTONOMOUS_STEPS_LIMIT: int = 5  # hard ceiling, never raised by client
    
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
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS configuration while retaining its environment form."""
        parse_cors_origins(v)
        return v

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
        return parse_cors_origins(self.CORS_ORIGINS)
    
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
