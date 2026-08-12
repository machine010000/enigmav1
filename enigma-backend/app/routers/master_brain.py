from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.ai.master_brain import master_brain
from app.ai.client import AITimeoutError, AIConfigurationError, AIAuthenticationError, AIConnectionError, AIProviderError
from app.models.knowledge import MasterKnowledge
from sqlalchemy import select

router = APIRouter(prefix="/brain", tags=["master_brain"])

class ChatMessage(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_master_brain(data: ChatMessage, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await master_brain.chat(db, str(current_user.id), data.message)
        return {"reply": result["reply"], "intent": result["intent"], "knowledge_used": result["knowledge_used"]}
    except AITimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI provider timed out. Please try again."
        )
    except (AIAuthenticationError, AIConnectionError, AIProviderError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider error. Please try again later."
        )
    except AIConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI configuration error. Please contact support."
        )

@router.get("/knowledge")
async def get_master_knowledge(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MasterKnowledge).order_by(MasterKnowledge.created_at.desc()).limit(50))
    knowledge = result.scalars().all()
    return {"knowledge": [{"id": str(k.id), "category": k.category, "domain": k.domain, "market": k.market, "key": k.key, "value": k.value, "confidence": k.confidence, "source": k.source} for k in knowledge]}
