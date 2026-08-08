from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.expert_domains.domains.seo_execution_orchestrator import (
    SEOExecutionOrchestrator,
    ExecutionReport,
    seo_execution_orchestrator,
)
from app.expert_domains.execution import ExecutionTemplate


router = APIRouter(prefix="/api/execution", tags=["execution"])


class ExecutionRequest(BaseModel):
    """Request model for execution endpoint."""
    
    work_specification_id: str = Field(..., description="ID of the work specification to execute")
    work_specification: Dict[str, Any] = Field(..., description="Work specification data")
    domain_id: str = Field(default="seo", description="Domain ID for execution")
    template_id: Optional[str] = Field(None, description="Optional template ID to use")


class ExecutionResponse(BaseModel):
    """Response model for execution endpoint."""
    
    session_id: str
    work_specification_id: str
    domain_id: str
    execution_status: str
    success: bool
    steps_completed: int
    steps_total: int
    outputs_generated: int
    validation_passed: bool
    reflection: Optional[Dict[str, Any]] = None
    knowledge_update: Optional[Dict[str, Any]] = None
    evidence_update: Optional[Dict[str, Any]] = None
    readiness_update: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    warnings: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


@router.post("/run", response_model=ExecutionResponse, status_code=status.HTTP_200_OK)
async def run_execution(request: ExecutionRequest) -> ExecutionResponse:
    """
    Execute a work specification through the complete execution pipeline.
    
    This endpoint orchestrates the end-to-end execution:
    1. Work Specification → Execution Plan (using Domain templates)
    2. Execution Plan → Runtime Session
    3. Runtime → Worker Execution (domain-specific workers)
    4. Worker Results → Outputs (domain-specific builders)
    5. Outputs → Validation
    6. Validation → Reflection (domain-specific)
    7. Reflection → Knowledge Update
    8. Knowledge Update → Evidence Update
    9. Evidence Update → Readiness Update
    
    Args:
        request: Execution request with work specification
        
    Returns:
        ExecutionResponse with complete execution results
        
    Raises:
        HTTPException: If execution fails
    """
    try:
        # Execute work specification
        report = seo_execution_orchestrator.execute_work_specification(
            work_specification_id=request.work_specification_id,
            work_specification=request.work_specification,
            domain_id=request.domain_id,
            template_id=request.template_id,
        )
        
        # Convert report to response
        response = ExecutionResponse(
            session_id=report.session_id,
            work_specification_id=report.work_specification_id,
            domain_id=report.domain_id,
            execution_status=report.execution_status,
            success=report.success,
            steps_completed=report.steps_completed,
            steps_total=report.steps_total,
            outputs_generated=report.outputs_generated,
            validation_passed=report.validation_passed,
            reflection=_convert_reflection_to_dict(report.reflection) if report.reflection else None,
            knowledge_update=report.knowledge_update,
            evidence_update=report.evidence_update,
            readiness_update=report.readiness_update,
            errors=report.errors,
            warnings=report.warnings,
            started_at=report.started_at,
            completed_at=report.completed_at,
            metadata=report.metadata,
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}",
        )


def _convert_reflection_to_dict(reflection: Any) -> Dict[str, Any]:
    """Convert reflection object to dictionary."""
    if hasattr(reflection, "__dict__"):
        return reflection.__dict__
    return reflection


@router.post("/register-template", status_code=status.HTTP_201_CREATED)
async def register_execution_template(template: ExecutionTemplate) -> Dict[str, str]:
    """
    Register an execution template for a domain.
    
    Args:
        template: Execution template to register
        
    Returns:
        Confirmation message
    """
    try:
        seo_execution_orchestrator.register_execution_template(template)
        return {"message": f"Template {template.template_id} registered successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register template: {str(e)}",
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for execution service.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "execution"}
