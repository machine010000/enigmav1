"""
Health Check and Startup Validation

Production health checks and configuration validation.
"""

from typing import Dict, Any, List
from datetime import datetime
import asyncio

from app.core.config import settings, is_production


class HealthCheck:
    """Health check for production readiness."""
    
    def __init__(self):
        """Initialize health check."""
        self.checks: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def check_configuration(self) -> bool:
        """Check configuration validity."""
        self.checks.append("Configuration validation")
        
        try:
            # Validate environment
            if settings.ENVIRONMENT not in ["development", "test", "production"]:
                self.errors.append(f"Invalid ENVIRONMENT: {settings.ENVIRONMENT}")
                return False
            
            # Production-specific checks
            if is_production():
                if not settings.SECRET_KEY:
                    self.errors.append("SECRET_KEY not set in production")
                    return False
                
                if not settings.DATABASE_URL:
                    self.errors.append("DATABASE_URL not set in production")
                    return False
                
                if not settings.REDIS_URL:
                    self.warnings.append("REDIS_URL not set (caching disabled)")
                
                if "localhost" in settings.REDIS_URL:
                    self.errors.append("REDIS_URL contains localhost in production")
                    return False
                
                if "localhost" in settings.UPWORK_REDIRECT_URI:
                    self.errors.append("UPWORK_REDIRECT_URI contains localhost in production")
                    return False
                
                if any("localhost" in origin for origin in settings.cors_origins_list):
                    self.errors.append("CORS_ORIGINS contains localhost in production")
                    return False
            
            return True
        
        except Exception as e:
            self.errors.append(f"Configuration check failed: {str(e)}")
            return False
    
    def check_essential_secrets(self) -> bool:
        """Check essential secrets are set."""
        self.checks.append("Essential secrets validation")
        
        missing = []
        
        if not settings.SECRET_KEY:
            missing.append("SECRET_KEY")
        
        if not settings.DATABASE_URL:
            missing.append("DATABASE_URL")
        
        if not settings.NVIDIA_API_KEY:
            missing.append("NVIDIA_API_KEY")
        
        if missing:
            if is_production():
                self.errors.append(f"Missing essential secrets: {', '.join(missing)}")
                return False
            else:
                self.warnings.append(f"Missing optional secrets: {', '.join(missing)}")
        
        return True
    
    def check_no_localhost_leakage(self) -> bool:
        """Check no localhost leakage in production."""
        self.checks.append("Localhost leakage check")
        
        if not is_production():
            return True  # Skip in development
        
        localhost_found = []
        
        if "localhost" in settings.REDIS_URL:
            localhost_found.append("REDIS_URL")
        
        if "localhost" in settings.UPWORK_REDIRECT_URI:
            localhost_found.append("UPWORK_REDIRECT_URI")
        
        if "localhost" in settings.CORS_ORIGINS:
            localhost_found.append("CORS_ORIGINS")
        
        if "localhost" in settings.API_HOST:
            localhost_found.append("API_HOST")
        
        if localhost_found:
            self.errors.append(f"Localhost found in production: {', '.join(localhost_found)}")
            return False
        
        return True
    
    def check_timeout_configuration(self) -> bool:
        """Check timeout configuration is reasonable."""
        self.checks.append("Timeout configuration check")
        
        issues = []
        
        if settings.API_TIMEOUT_SECONDS <= 0:
            issues.append("API_TIMEOUT_SECONDS must be positive")
        
        if settings.DATABASE_TIMEOUT_SECONDS <= 0:
            issues.append("DATABASE_TIMEOUT_SECONDS must be positive")
        
        if settings.REDIS_TIMEOUT_SECONDS <= 0:
            issues.append("REDIS_TIMEOUT_SECONDS must be positive")
        
        if settings.API_TIMEOUT_SECONDS > 300:
            self.warnings.append("API_TIMEOUT_SECONDS > 300 seconds (5 minutes)")
        
        if issues:
            self.errors.append(f"Timeout configuration issues: {', '.join(issues)}")
            return False
        
        return True
    
    def check_retry_configuration(self) -> bool:
        """Check retry configuration is reasonable."""
        self.checks.append("Retry configuration check")
        
        issues = []
        
        if settings.MAX_RETRIES < 0:
            issues.append("MAX_RETRIES cannot be negative")
        
        if settings.MAX_RETRIES > 10:
            self.warnings.append("MAX_RETRIES > 10 (may cause long delays)")
        
        if settings.RETRY_DELAY_SECONDS < 0:
            issues.append("RETRY_DELAY_SECONDS cannot be negative")
        
        if issues:
            self.errors.append(f"Retry configuration issues: {', '.join(issues)}")
            return False
        
        return True
    
    async def check_database_connection(self) -> bool:
        """Check database connection."""
        self.checks.append("Database connection check")
        
        if not settings.DATABASE_URL:
            self.warnings.append("DATABASE_URL not set (skipping database check)")
            return True
        
        try:
            from app.database import engine
            
            # Simple connection test
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            return True
        
        except Exception as e:
            self.errors.append(f"Database connection failed: {str(e)}")
            return False
    
    async def check_redis_connection(self) -> bool:
        """Check Redis connection."""
        self.checks.append("Redis connection check")
        
        if not settings.REDIS_URL:
            self.warnings.append("REDIS_URL not set (skipping Redis check)")
            return True
        
        try:
            import redis.asyncio as redis
            
            client = redis.from_url(settings.REDIS_URL)
            await client.ping()
            await client.close()
            
            return True
        
        except Exception as e:
            self.warnings.append(f"Redis connection failed: {str(e)}")
            return False  # Not critical, but warn
    
    async def check_ai_provider_connection(self) -> bool:
        """Check AI provider connection."""
        self.checks.append("AI provider connection check")
        
        if not settings.NVIDIA_API_KEY:
            self.warnings.append("NVIDIA_API_KEY not set (skipping AI provider check)")
            return True
        
        try:
            from app.ai.gateway import gateway
            
            # Simple test call
            result = await gateway.classify(
                system="You are a classifier.",
                user="Test connection.",
                temperature=0.1,
                max_tokens=10,
            )
            
            if not result:
                self.errors.append("AI provider returned empty response")
                return False
            
            return True
        
        except Exception as e:
            self.errors.append(f"AI provider connection failed: {str(e)}")
            return False
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Health check result
        """
        self.checks = []
        self.errors = []
        self.warnings = []
        
        # Synchronous checks
        self.check_configuration()
        self.check_essential_secrets()
        self.check_no_localhost_leakage()
        self.check_timeout_configuration()
        self.check_retry_configuration()
        
        # Asynchronous checks
        await self.check_database_connection()
        await self.check_redis_connection()
        await self.check_ai_provider_connection()
        
        # Determine overall status
        is_healthy = len(self.errors) == 0
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "checks_performed": len(self.checks),
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "is_production": is_production(),
        }


async def perform_startup_health_check() -> Dict[str, Any]:
    """
    Perform startup health check.
    
    Returns:
        Health check result
    """
    health_check = HealthCheck()
    return await health_check.run_all_checks()


def get_health_status() -> Dict[str, Any]:
    """
    Get basic health status (synchronous).
    
    Returns:
        Basic health status
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "is_production": is_production(),
    }
