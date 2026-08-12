"""
Master Brain Router

TASK-016 API Consolidation
--------------------------
BEFORE:
  POST /brain/autonomous          → MasterBrain.execute_with_learning (single-step)
  POST /brain/autonomous/multi-step → AutonomousOrchestrator (multi-step, different shape)

AFTER:
  POST /brain/autonomous          → CANONICAL endpoint.
                                    Delegates to AutonomousOrchestrator for ALL runs.
                                    Supports single-step (max_steps=1) transparently.
                                    Always returns the stable AutonomousRunResponse shape.

  POST /brain/autonomous/multi-step → COMPATIBILITY ALIAS (deprecated).
                                    Routes to the same underlying service.
                                    Returns identical shape.
                                    Retained so existing clients are not broken.

Public Request Contract (TASK-016 Phase 8)
------------------------------------------
Allowed:   goal, product_id, module, max_steps (bounded 1–5 server-side)
Rejected:  worker_name, capability override, raw system prompt, shell command,
           execution_code, arbitrary allowlist.
           Any attempt to supply worker_name is silently ignored — the Brain
           chooses capability, the Registry resolves the worker.

Stable Response Contract (TASK-016 Phase 9)
-------------------------------------------
{
  "run_id":     "...",
  "status":     "finished|failed|step_limit_reached|blocked",
  "module":     "seller",
  "goal":       "...",
  "steps": [
    {
      "step":         1,
      "capability":   "...",
      "execution_id": "...",
      "status":       "completed|failed|skipped"
    }
  ],
  "reply":       "...",
  "next_action": { ... },     // optional
  "stop_reason": "..."        // optional
}

Never exposed:
  - chain-of-thought / raw LLM reasoning
  - worker_name (internal)
  - secrets, tokens, full prompts, stack traces
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.ai.master_brain import master_brain
from app.ai.master_brain.models import BrainAction
from app.ai.client import (
    AITimeoutError,
    AIConfigurationError,
    AIAuthenticationError,
    AIConnectionError,
    AIProviderError,
)
from app.models.knowledge import MasterKnowledge
from app.autonomy.orchestrator import AutonomousOrchestrator
from app.core.config import settings

router = APIRouter(prefix="/brain", tags=["master_brain"])

# ------------------------------------------------------------------ constants
_DEFAULT_MAX_STEPS: int = settings.MAX_AUTONOMOUS_STEPS
_MIN_MAX_STEPS: int = settings.MIN_AUTONOMOUS_STEPS
_MAX_MAX_STEPS: int = settings.MAX_AUTONOMOUS_STEPS_LIMIT


# ------------------------------------------------------------------ request models

class ChatMessage(BaseModel):
    message: str


class AutonomousRequest(BaseModel):
    """
    Canonical autonomous request contract.

    The client provides business intent only.  Worker names, capability
    overrides, raw prompts, and execution code are NOT accepted.
    """
    goal: str = Field(
        ...,
        description="Business goal or intent — what the user wants to achieve",
        min_length=1,
        max_length=2000,
    )
    product_id: Optional[str] = Field(
        None,
        description="Product ID to act on (must be owned by the authenticated user)",
    )
    module: Optional[str] = Field(
        "seller",
        description="Module scope: seller | content_creator | service_provider",
    )
    max_steps: Optional[int] = Field(
        None,
        description="Maximum autonomous steps (server-enforced 1–5; default from config)",
    )

    # TASK-016: backward-compat alias — 'message' maps to 'goal'
    message: Optional[str] = Field(
        None,
        description="Alias for goal (deprecated, use goal)",
        exclude=True,
    )

    @field_validator("max_steps", mode="before")
    @classmethod
    def clamp_max_steps(cls, v: Any) -> Optional[int]:
        """Server-side clamp — client cannot exceed the hard ceiling."""
        if v is None:
            return None
        try:
            v = int(v)
        except (TypeError, ValueError):
            return None
        return max(_MIN_MAX_STEPS, min(v, _MAX_MAX_STEPS))

    def effective_goal(self) -> str:
        """Return goal, falling back to legacy 'message' field."""
        return self.goal or self.message or ""


class MultiStepAutonomousRequest(BaseModel):
    """
    Deprecated multi-step request — kept for backward compatibility.
    Routes to the same underlying service as AutonomousRequest.
    """
    message: str
    product_id: Optional[str] = Field(None)
    max_steps: Optional[int] = Field(None)
    module: Optional[str] = Field("seller")

    @field_validator("max_steps", mode="before")
    @classmethod
    def clamp_max_steps(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            v = int(v)
        except (TypeError, ValueError):
            return None
        return max(_MIN_MAX_STEPS, min(v, _MAX_MAX_STEPS))


# ------------------------------------------------------------------ response models

class AutonomousStepResponse(BaseModel):
    step: int
    capability: Optional[str]
    execution_id: Optional[str]
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class AutonomousRunResponse(BaseModel):
    """
    Stable response shape for all autonomous endpoints.

    Deliberately omits: worker_name, raw LLM reasoning, chain-of-thought,
    full prompts, secrets, stack traces.
    """
    run_id: str
    status: str
    module: str
    goal: str
    steps: List[AutonomousStepResponse]
    reply: Optional[str] = None
    next_action: Optional[Dict[str, Any]] = None
    stop_reason: Optional[str] = None


# ------------------------------------------------------------------ helpers

def _build_run_response(run: Any, goal: str) -> AutonomousRunResponse:
    """
    Convert AutonomousRun to the stable public response contract.

    - Omits worker_name from step responses
    - Omits raw decision chain-of-thought
    - Omits error details from steps (returns generic status only)
    """
    # Map RunStatus to public status string
    status_map = {
        "completed": "finished",
        "stopped": _map_stop_reason(run.stop_reason),
        "running": "running",
        "failed": "failed",
        "pending": "pending",
    }
    public_status = status_map.get(run.status.value, run.status.value)

    # Build step responses — strip internal worker details
    step_responses = [
        AutonomousStepResponse(
            step=s.step_number,
            capability=s.capability,
            execution_id=s.execution_id,
            status=s.status.value,
            started_at=s.started_at.isoformat() if s.started_at else None,
            completed_at=s.completed_at.isoformat() if s.completed_at else None,
            # Only surface error presence, not raw message (may contain internals)
            error="execution_failed" if s.error else None,
        )
        for s in run.steps
    ]

    # Build next_action only when Brain recommends a next step
    next_action = None
    if run.final_decision and run.final_decision.action == BrainAction.RECOMMEND_NEXT_ACTION:
        next_action = {
            "suggested_goal": run.final_decision.next_action,
            "reasoning": run.final_decision.next_action_reasoning,
        }

    return AutonomousRunResponse(
        run_id=run.run_id,
        status=public_status,
        module=run.module,
        goal=goal,
        steps=step_responses,
        reply=run.final_response,
        next_action=next_action,
        stop_reason=run.stop_reason.value if run.stop_reason else None,
    )


def _map_stop_reason(stop_reason: Any) -> str:
    """Map internal StopReason to a public-facing status string."""
    if stop_reason is None:
        return "stopped"
    mapping = {
        "finished": "finished",
        "step_limit_reached": "step_limit_reached",
        "duplicate_action": "blocked",
        "failure": "failed",
        "timeout": "failed",
        "authentication_failure": "failed",
        "ownership_failure": "failed",
        "capability_not_available": "blocked",
        "configuration_error": "failed",
        "user_cancelled": "blocked",
    }
    return mapping.get(stop_reason.value, "stopped")


def _map_ai_error_to_http(e: Exception) -> int:
    return {
        AITimeoutError: 504,
        AIAuthenticationError: 502,
        AIConnectionError: 502,
        AIProviderError: 502,
        AIConfigurationError: 500,
    }.get(type(e), 500)


# ------------------------------------------------------------------ endpoints

@router.post("/chat")
async def chat_with_master_brain(
    data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Conversational endpoint — no capability execution."""
    try:
        result = await master_brain.chat(db, str(current_user.id), data.message)
        return {
            "reply": result["reply"],
            "intent": result["intent"],
            "knowledge_used": result["knowledge_used"],
        }
    except (AITimeoutError, AIAuthenticationError, AIConnectionError,
            AIProviderError, AIConfigurationError) as e:
        raise HTTPException(status_code=_map_ai_error_to_http(e),
                            detail="AI provider error. Please try again later.")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/autonomous", response_model=AutonomousRunResponse)
async def autonomous_execution(
    request: AutonomousRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CANONICAL autonomous execution endpoint.

    Accepts business intent (goal + optional product_id + module).
    The Brain selects the capability; the Registry resolves the worker.
    The client never names a worker or capability directly.

    max_steps is clamped server-side to [1, 5] regardless of what the
    client sends.
    """
    goal = request.effective_goal()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    effective_steps = request.max_steps if request.max_steps is not None else _DEFAULT_MAX_STEPS

    try:
        orchestrator = AutonomousOrchestrator(max_steps=effective_steps)

        run = await orchestrator.run_autonomous(
            user_id=str(current_user.id),
            goal=goal,
            target_id=request.product_id,
            module=request.module or "seller",
            db=db,
        )

        return _build_run_response(run, goal)

    except (AITimeoutError, AIAuthenticationError, AIConnectionError,
            AIProviderError, AIConfigurationError) as e:
        raise HTTPException(status_code=_map_ai_error_to_http(e),
                            detail="AI provider error. Please try again later.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.post("/autonomous/multi-step", response_model=AutonomousRunResponse)
async def multi_step_autonomous_execution(
    request: MultiStepAutonomousRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    COMPATIBILITY ALIAS — deprecated.

    Routes to the SAME AutonomousOrchestrator service as POST /brain/autonomous.
    Retained so existing clients are not broken.
    Use POST /brain/autonomous for all new integrations.
    """
    effective_steps = request.max_steps if request.max_steps is not None else _DEFAULT_MAX_STEPS

    try:
        orchestrator = AutonomousOrchestrator(max_steps=effective_steps)

        run = await orchestrator.run_autonomous(
            user_id=str(current_user.id),
            goal=request.message,
            target_id=request.product_id,
            module=request.module or "seller",
            db=db,
        )

        return _build_run_response(run, request.message)

    except (AITimeoutError, AIAuthenticationError, AIConnectionError,
            AIProviderError, AIConfigurationError) as e:
        raise HTTPException(status_code=_map_ai_error_to_http(e),
                            detail="AI provider error. Please try again later.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get("/knowledge")
async def get_master_knowledge(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MasterKnowledge)
        .order_by(MasterKnowledge.created_at.desc())
        .limit(50)
    )
    knowledge = result.scalars().all()
    return {
        "knowledge": [
            {
                "id": str(k.id),
                "category": k.category,
                "domain": k.domain,
                "market": k.market,
                "key": k.key,
                "value": k.value,
                "confidence": k.confidence,
                "source": k.source,
            }
            for k in knowledge
        ]
    }
