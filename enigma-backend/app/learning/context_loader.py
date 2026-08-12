"""
Learning Context Loader

Loads learning-relevant context for MasterBrain re-evaluation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.execution import WorkerExecution
from app.models.enigma_profile import EnigmaProfile, KnowledgeProgress
from app.memory.memory_engine import MemoryEngine


class LearningContextLoader:
    """
    Loads learning context for MasterBrain re-evaluation.
    
    This extends the existing context_builder with learning-specific data.
    """
    
    def __init__(self, memory_engine: Optional[MemoryEngine] = None):
        self.memory_engine = memory_engine or MemoryEngine()
    
    async def load_learning_context(
        self,
        db: AsyncSession,
        user_id: str,
        product_id: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Load learning-relevant context for Brain re-evaluation.
        
        Args:
            db: Database session
            user_id: User ID
            product_id: Optional product ID
            capability: Optional capability ID
            
        Returns:
            Dict with learning context
        """
        context = {
            "recent_executions": [],
            "capability_history": {},
            "enigma_profile": {},
            "memory_episodes": [],
        }
        
        # Load recent executions for this user/product
        context["recent_executions"] = await self._load_recent_executions(
            db, user_id, product_id, capability, limit=5
        )
        
        # Load capability history from EnigmaProfile
        context["capability_history"] = await self._load_capability_history(db, capability)
        
        # Load EnigmaProfile summary
        context["enigma_profile"] = await self._load_enigma_profile(db)
        
        # Load relevant memory episodes
        context["memory_episodes"] = self._load_memory_episodes(product_id, capability, limit=3)
        
        return context
    
    async def _load_recent_executions(
        self,
        db: AsyncSession,
        user_id: str,
        product_id: Optional[str] = None,
        capability: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Load recent executions scoped to this user.

        TASK-016: query is filtered by WorkerExecution.user_id so User A
        can never see User B's execution history.  Rows with user_id=NULL
        are legacy pre-016 records; they are excluded by the strict filter
        to prevent any accidental cross-user data exposure.
        """
        try:
            from app.models.execution import WorkerExecution
            stmt = (
                select(WorkerExecution)
                .where(WorkerExecution.user_id == user_id)
                .order_by(WorkerExecution.created_at.desc())
                .limit(limit)
            )
            result = await db.execute(stmt)
            executions = result.scalars().all()

            return [
                {
                    "execution_id": str(exec.id),
                    "worker_name": exec.worker_name,
                    "status": exec.status,
                    "confidence": exec.confidence,
                    "created_at": exec.created_at.isoformat() if exec.created_at else None,
                }
                for exec in executions
            ]
        except Exception:
            return []
    
    async def _load_capability_history(
        self,
        db: AsyncSession,
        capability: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Load capability history from EnigmaProfile."""
        try:
            result = await db.execute(
                select(KnowledgeProgress).where(
                    KnowledgeProgress.profile_id == "enigma_profile"
                )
            )
            progress_items = result.scalars().all()
            
            history = {}
            for item in progress_items:
                if capability is None or item.domain == capability:
                    history[item.domain] = {
                        "confidence": item.confidence,
                        "execution_score": item.execution_score,
                        "evidence_score": item.evidence_score,
                        "readiness": item.readiness,
                        "freshness": item.freshness,
                        "last_verified": item.last_verified.isoformat() if item.last_verified else None,
                    }
            
            return history
        except Exception:
            return {}
    
    async def _load_enigma_profile(self, db: AsyncSession) -> Dict[str, Any]:
        """Load EnigmaProfile summary."""
        try:
            result = await db.execute(
                select(EnigmaProfile).where(EnigmaProfile.profile_id == "enigma_profile")
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                return {}
            
            return {
                "active_goals": profile.active_goals,
                "target_professions": profile.target_professions,
                "target_platforms": profile.target_platforms,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            }
        except Exception:
            return {}
    
    def _load_memory_episodes(
        self,
        product_id: Optional[str] = None,
        capability: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Load relevant memory episodes."""
        try:
            episodes = self.memory_engine.recall(
                goal=capability,
                product_id=product_id,
            )
            
            return [
                {
                    "id": ep.id,
                    "worker": ep.worker,
                    "goal": ep.goal,
                    "confidence": ep.confidence,
                    "success": ep.success,
                    "created_at": ep.created_at.isoformat(),
                }
                for ep in episodes[:limit]
            ]
        except Exception:
            return []
