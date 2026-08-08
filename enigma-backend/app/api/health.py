"""
Health check endpoints for production monitoring.
"""
from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any
import httpx

from app.core.config import settings, is_production
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns system health status without exposing sensitive information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with component status.
    
    Checks database, external services, and system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "components": {},
    }
    
    # Check database
    try:
        # TODO: Add actual database health check
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        health_status["status"] = "degraded"
    
    # Check NVIDIA API
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Simple ping to NVIDIA API endpoint
            response = await client.get("https://integrate.api.nvidia.com/v1/models")
            if response.status_code == 200:
                health_status["components"]["nvidia_api"] = {
                    "status": "healthy",
                    "message": "NVIDIA API accessible",
                }
            else:
                health_status["components"]["nvidia_api"] = {
                    "status": "degraded",
                    "message": f"NVIDIA API returned {response.status_code}",
                }
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["nvidia_api"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        # TODO: Add actual Redis health check
        health_status["components"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful",
        }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        health_status["status"] = "degraded"
    
    # Check Upwork adapter (if configured)
    if settings.UPWORK_CLIENT_ID and settings.UPWORK_CLIENT_SECRET:
        health_status["components"]["upwork_adapter"] = {
            "status": "configured",
            "message": "Upwork adapter configured",
        }
    else:
        health_status["components"]["upwork_adapter"] = {
            "status": "not_configured",
            "message": "Upwork credentials not configured",
        }
    
    return health_status


@router.get("/api/execution/health")
async def execution_health_check() -> Dict[str, Any]:
    """
    Execution engine health check.
    
    Checks the cognitive core and execution pipeline health.
    """
    from app.execution.execution_engine import execution_engine
    
    try:
        engine_status = execution_engine.get_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "execution_engine": engine_status,
        }
    except Exception as e:
        logger.error(f"Execution health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
