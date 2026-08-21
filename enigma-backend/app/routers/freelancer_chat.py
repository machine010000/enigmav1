"""Admin-only HTTP boundary for the project-aware Freelancer Chat MVP."""
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.freelancing.manual_intake import DuplicateOpportunityError
from app.freelancing.project_chat import FreelancerChatService
from app.models.user import User
from app.routers.auth import require_admin_user

router = APIRouter(prefix="/api/freelancing/chat", tags=["Freelancer Chat"])
service = FreelancerChatService()


class OpportunityInput(BaseModel):
    platform: Optional[str] = Field(default=None, max_length=40)
    source_url: Optional[str] = Field(default=None, max_length=2000)
    external_project_id: Optional[str] = Field(default=None, max_length=200)
    title: Optional[str] = Field(default=None, max_length=500)
    original_description: Optional[str] = Field(default=None, max_length=30_000)
    budget_type: Optional[Literal["fixed", "hourly", "negotiable"]] = None
    budget_min: Optional[float] = Field(default=None, ge=0)
    budget_max: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    client_info: dict[str, Any] = Field(default_factory=dict)
    source_language: Literal["ar", "en", "es", "fr"] = "en"
    customer_preferred_language: Literal["ar", "en", "es", "fr"] = "en"
    proposal_language: Literal["ar", "en", "es", "fr"] = "en"

    @model_validator(mode="after")
    def valid_budget(self) -> "OpportunityInput":
        if self.budget_min is not None and self.budget_max is not None and self.budget_min > self.budget_max:
            raise ValueError("budget_min cannot exceed budget_max")
        return self


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=30_000)
    conversation_id: Optional[str] = Field(default=None, max_length=64)
    project_id: Optional[str] = Field(default=None, max_length=64)
    opportunity: Optional[OpportunityInput] = None


class SampleRequest(BaseModel):
    content: str = Field(min_length=1, max_length=30_000)
    sample_type: str = Field(default="example", min_length=1, max_length=50)
    project_id: Optional[str] = Field(default=None, max_length=64)
    reusable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


def _user_id(user: User) -> str:
    return str(user.id)


@router.post("")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        result = await service.handle(
            db, user_id=_user_id(current_user), message=request.message,
            conversation_id=request.conversation_id, project_id=request.project_id,
            opportunity=request.opportunity.model_dump() if request.opportunity else None,
        )
        await db.commit()
        return result
    except DuplicateOpportunityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.to_dict())
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflicting chat state")
    except Exception:
        await db.rollback()
        raise


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await service.conversation(db, user_id=_user_id(current_user), conversation_id=conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/projects")
async def list_projects(
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await service.projects(db, user_id=_user_id(current_user))


@router.post("/samples", status_code=status.HTTP_201_CREATED)
async def add_sample(
    request: SampleRequest,
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        artifact = await service.add_sample(
            db, user_id=_user_id(current_user), content=request.content,
            sample_type=request.sample_type, project_id=request.project_id,
            reusable=request.reusable, metadata=request.metadata,
        )
        await db.commit()
        return service._artifact_dict(artifact)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception:
        await db.rollback()
        raise


@router.get("/samples")
async def list_samples(
    project_id: Optional[str] = Query(default=None, max_length=64),
    current_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await service.samples(db, user_id=_user_id(current_user), project_id=project_id)
