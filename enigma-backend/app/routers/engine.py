"""
Engine API Router — TASK-001: Execution Engine

## Endpoints

GET  /engine/workers
    List all registered workers

POST /engine/execute
    Execute a worker and return the full WorkerResult

GET  /engine/executions/{id}
    Get execution record (status + result + time)

GET  /engine/executions/{id}/result
    Get result only

GET  /engine/executions/{id}/status
    Get status only

POST /engine/orchestrate
    Run a multi-worker pipeline

GET  /engine/executions
    List recent execution records
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engine.engine import engine
from app.engine.context_builder import build_context
from app.routers.auth import get_current_user


router = APIRouter(prefix="/engine", tags=["engine"])


class ExecuteRequest(BaseModel):
    worker: str = Field(
        ...,
        description="Name of the registered worker to execute",
    )

    product_id: Optional[str] = Field(
        None,
        description="Product UUID to load from DB",
    )

    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Extra context data merged into the WorkerContext",
    )


class OrchestrateRequest(BaseModel):
    plan: List[Dict[str, Any]] = Field(
        ...,
        description="Pipeline steps: {step, worker, input}",
    )

    product_id: Optional[str] = None
    user_id: Optional[str] = None
    extra_memory: Optional[Dict[str, Any]] = None


@router.get("/workers")
async def list_workers(
    current_user=Depends(get_current_user),
):
    """TASK-001: List registered workers."""

    workers = engine.list_workers()

    return {
        "workers": workers,
        "count": len(workers),
    }


@router.post("/execute")
async def execute_worker(
    data: ExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    TASK-001: Execute a worker and return status,
    result, evidence, timing, and metadata.
    """

    # ---------------------------------------------------------
    # Validate worker
    # ---------------------------------------------------------

    if data.worker not in engine.registered_names:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Worker '{data.worker}' is not registered. "
                f"Available: {engine.registered_names}"
            ),
        )

    # ---------------------------------------------------------
    # Build execution context
    # ---------------------------------------------------------

    ctx = await build_context(
        db=db,
        user_id=str(current_user.id),
        product_id=data.product_id,
        execution_id=str(uuid.uuid4()),
        extra_memory=data.context or {},
    )

    # ---------------------------------------------------------
    # IMPORTANT:
    # If product_id is not supplied, allow the caller to
    # provide product data directly inside:
    #
    # context.product
    #
    # Previously this was incorrectly gated behind
    # `data.product_id`, which meant product_id=null caused
    # the direct product payload to be ignored.
    # ---------------------------------------------------------

    if not ctx.product and data.context:
        direct_product = data.context.get("product")

        if isinstance(direct_product, dict):
            ctx.product = direct_product

    # ---------------------------------------------------------
    # Execute worker
    # ---------------------------------------------------------

    result = await engine.execute(
        data.worker,
        ctx,
        save=True,
        db=db,
    )

    return result.to_dict()


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """TASK-001: Return full execution record."""

    record = await engine.get_execution_record(
        db,
        execution_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution '{execution_id}' not found",
        )

    events = await engine.get_event_logs(
        db,
        execution_id=execution_id,
    )

    record["events"] = events

    return record


@router.get("/executions/{execution_id}/result")
async def get_execution_result(
    execution_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """TASK-001: Return only the result payload."""

    record = await engine.get_execution_record(
        db,
        execution_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution '{execution_id}' not found",
        )

    return {
        "result": record["result"],
        "evidence": record["evidence"],
    }


@router.get("/executions/{execution_id}/status")
async def get_execution_status(
    execution_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """TASK-001: Return only status and timing."""

    record = await engine.get_execution_record(
        db,
        execution_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Execution '{execution_id}' not found",
        )

    return {
        "status": record["status"],
        "execution_time": record["execution_time"],
        "confidence": record["confidence"],
        "llm_calls": record["llm_calls"],
        "memory_usage_mb": record["memory_usage_mb"],
        "started_at": record["started_at"],
        "completed_at": record["completed_at"],
    }


@router.post("/orchestrate")
async def orchestrate(
    data: OrchestrateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """TASK-004: Execute a multi-worker pipeline."""

    ctx = await build_context(
        db=db,
        user_id=data.user_id or str(current_user.id),
        product_id=data.product_id,
        execution_id=str(uuid.uuid4()),
        extra_memory=data.extra_memory or {},
    )

    result = await engine.orchestrate(
        data.plan,
        ctx,
        db=db,
    )

    return result


@router.get("/executions")
async def list_executions(
    limit: int = 50,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent execution records."""

    records = await engine.get_recent_executions(
        db,
        limit=limit,
        status_filter=status,
    )

    return {
        "executions": records,
        "count": len(records),
    }