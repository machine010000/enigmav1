"""
Production observability module.

Provides structured logging, metrics, and monitoring for production.
"""
from contextvars import ContextVar
from typing import Optional
from datetime import datetime
import uuid

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def get_request_id() -> str:
    """Get or generate a request ID."""
    request_id = request_id_var.get()
    if request_id is None:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
    return request_id


def set_request_id(request_id: str) -> None:
    """Set the request ID."""
    request_id_var.set(request_id)


def get_user_id() -> Optional[str]:
    """Get the current user ID."""
    return user_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set the user ID."""
    user_id_var.set(user_id)


def log_request_start(
    method: str,
    path: str,
    user_id: Optional[str] = None,
) -> None:
    """Log the start of a request."""
    logger.info(
        f"Request started",
        extra={
            "request_id": get_request_id(),
            "user_id": user_id,
            "method": method,
            "path": path,
            "event": "request_start",
        },
    )


def log_request_end(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
) -> None:
    """Log the end of a request."""
    logger.info(
        f"Request completed",
        extra={
            "request_id": get_request_id(),
            "user_id": user_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "event": "request_end",
        },
    )


def log_job_ingestion(
    job_id: str,
    platform: str,
    source: str,
) -> None:
    """Log job ingestion event."""
    logger.info(
        f"Job ingested",
        extra={
            "request_id": get_request_id(),
            "job_id": job_id,
            "platform": platform,
            "source": source,
            "event": "job_ingestion",
        },
    )


def log_research_start(
    job_id: str,
    research_type: str,
) -> None:
    """Log research start event."""
    logger.info(
        f"Research started",
        extra={
            "request_id": get_request_id(),
            "job_id": job_id,
            "research_type": research_type,
            "event": "research_start",
        },
    )


def log_research_complete(
    job_id: str,
    research_type: str,
    duration_ms: float,
    knowledge_found: int,
) -> None:
    """Log research completion event."""
    logger.info(
        f"Research completed",
        extra={
            "request_id": get_request_id(),
            "job_id": job_id,
            "research_type": research_type,
            "duration_ms": duration_ms,
            "knowledge_found": knowledge_found,
            "event": "research_complete",
        },
    )


def log_readiness_calculation(
    job_id: str,
    readiness_score: float,
    decision: str,
) -> None:
    """Log readiness calculation event."""
    logger.info(
        f"Readiness calculated",
        extra={
            "request_id": get_request_id(),
            "job_id": job_id,
            "readiness_score": readiness_score,
            "decision": decision,
            "event": "readiness_calculation",
        },
    )


def log_proposal_generation(
    application_id: str,
    job_id: str,
    duration_ms: float,
) -> None:
    """Log proposal generation event."""
    logger.info(
        f"Proposal generated",
        extra={
            "request_id": get_request_id(),
            "application_id": application_id,
            "job_id": job_id,
            "duration_ms": duration_ms,
            "event": "proposal_generation",
        },
    )


def log_approval_event(
    application_id: str,
    decision: str,
    approved_by: str,
) -> None:
    """Log approval event."""
    logger.info(
        f"Application approval",
        extra={
            "request_id": get_request_id(),
            "application_id": application_id,
            "decision": decision,
            "approved_by": approved_by,
            "event": "approval",
        },
    )


def log_submission_event(
    application_id: str,
    platform: str,
    platform_application_id: str,
    connects_spent: float,
) -> None:
    """Log application submission event."""
    logger.info(
        f"Application submitted",
        extra={
            "request_id": get_request_id(),
            "application_id": application_id,
            "platform": platform,
            "platform_application_id": platform_application_id,
            "connects_spent": connects_spent,
            "event": "submission",
        },
    )


def log_platform_error(
    platform: str,
    error_code: str,
    error_message: str,
    is_retriable: bool,
) -> None:
    """Log platform error event."""
    logger.error(
        f"Platform error",
        extra={
            "request_id": get_request_id(),
            "platform": platform,
            "error_code": error_code,
            "error_message": error_message,
            "is_retriable": is_retriable,
            "event": "platform_error",
        },
    )


def log_security_event(
    event_type: str,
    user_id: Optional[str],
    details: dict,
) -> None:
    """Log security event."""
    logger.warning(
        f"Security event",
        extra={
            "request_id": get_request_id(),
            "user_id": user_id,
            "event_type": event_type,
            "details": details,
            "event": "security",
        },
    )
