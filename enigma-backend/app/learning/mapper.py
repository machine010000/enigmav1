"""
Result → Evidence Mapper

Maps WorkerResult to persistent evidence structures.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.learning.observation import ExecutionObservation, ObservationStatus
from app.models.execution import WorkerExecution
from app.models.product import Product
from app.models.knowledge import MasterKnowledge
from app.memory.memory_engine import MemoryEngine, Episode
from datetime import datetime, timezone


class EvidenceMapper:
    """
    Maps WorkerResult to persistent evidence.
    
    This is the learning loop's evidence layer.
    """
    
    def __init__(self, memory_engine: Optional[MemoryEngine] = None):
        self.memory_engine = memory_engine or MemoryEngine()
    
    async def persist_observation(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Persist an execution observation to all relevant stores.

        TASK-016 transaction safety:
        - Failure observations update the execution record (failure recorded)
          but do NOT update product state or extract positive knowledge.
        - Positive capability/profile evidence only follows a SUCCESS observation.
        - This prevents a prohibited or failed step from writing misleading
          positive learning evidence.

        Args:
            observation: ExecutionObservation to persist
            db: Database session

        Returns:
            Dict with persistence results
        """
        results = {
            "worker_execution": False,
            "memory_episode": False,
            "product_update": False,
            "knowledge_entries": 0,
        }

        # 1. Always update WorkerExecution with actual outcome (success or failure)
        results["worker_execution"] = await self._update_worker_execution(observation, db)

        # 2. Always store memory episode (success and failure are both learning signals)
        results["memory_episode"] = self._store_memory_episode(observation)

        # 3. TASK-016: only update product state and extract knowledge on SUCCESS
        #    A failed execution must not leave positive evidence in product or knowledge tables.
        if observation.status == ObservationStatus.SUCCESS:
            if observation.target_id:
                results["product_update"] = await self._update_product_state(observation, db)
            knowledge_count = await self._extract_knowledge(observation, db)
            results["knowledge_entries"] = knowledge_count

        return results
    
    async def _update_worker_execution(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """Update WorkerExecution record with observation data."""
        try:
            result = await db.execute(
                select(WorkerExecution).where(WorkerExecution.id == observation.execution_id)
            )
            execution = result.scalar_one_or_none()
            
            if execution:
                # Update with observation data
                execution.evidence = observation.evidence
                execution.confidence = observation.confidence
                execution.status = observation.status.value
                await db.commit()
                return True
            return False
        except Exception:
            return False
    
    def _store_memory_episode(self, observation: ExecutionObservation) -> bool:
        """Store observation as a MemoryEngine Episode."""
        try:
            episode = Episode(
                id=f"ep_{observation.execution_id}",
                execution_id=observation.execution_id,
                decision_id=None,  # Can be added later
                product_id=observation.target_id,
                worker=observation.worker,
                goal=f"Execute {observation.capability}",
                inputs={"capability": observation.capability},
                outputs=observation.result_summary,
                evidence=observation.evidence,
                confidence=observation.confidence,
                execution_time=observation.execution_time,
                llm_calls=observation.llm_calls,
                success=(observation.status == ObservationStatus.SUCCESS),
            )
            self.memory_engine.store_episode(episode)
            return True
        except Exception:
            return False
    
    async def _update_product_state(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """
        Update product state with verification results.
        
        For product_verification capability, update ai_understanding with verified data.
        """
        if observation.capability != "product_verification":
            return False
        
        if not observation.target_id:
            return False
        
        try:
            result = await db.execute(
                select(Product).where(Product.id == observation.target_id)
            )
            product = result.scalar_one_or_none()
            
            if product and observation.status == ObservationStatus.SUCCESS:
                # Update ai_understanding with verified data
                if not product.ai_understanding:
                    product.ai_understanding = {}
                
                product.ai_understanding.update({
                    "verified_at": datetime.utcnow().isoformat(),
                    "verified_name": observation.result_summary.get("verified_name"),
                    "verified_category": observation.result_summary.get("category"),
                    "verification_confidence": observation.confidence,
                    "verification_issues": observation.issues,
                    "verification_execution_id": observation.execution_id,
                })
                
                await db.commit()
                return True
            return False
        except Exception:
            return False
    
    async def _extract_knowledge(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> int:
        """
        Extract knowledge entries from observation.
        
        For product_verification, extract verified attributes as knowledge.
        """
        if observation.capability != "product_verification":
            return 0
        
        if observation.status != ObservationStatus.SUCCESS:
            return 0
        
        try:
            knowledge_count = 0
            
            # Extract verified product name as knowledge
            verified_name = observation.result_summary.get("verified_name")
            if verified_name:
                knowledge = MasterKnowledge(
                    category="product",
                    domain=observation.result_summary.get("category", "unknown"),
                    market="general",
                    key=f"product_{observation.target_id}_verified_name",
                    value=verified_name,
                    confidence=observation.confidence,
                    source="execution",
                )
                db.add(knowledge)
                knowledge_count += 1
            
            # Extract verified category as knowledge
            verified_category = observation.result_summary.get("category")
            if verified_category:
                knowledge = MasterKnowledge(
                    category="product",
                    domain=verified_category,
                    market="general",
                    key=f"product_{observation.target_id}_category",
                    value=verified_category,
                    confidence=observation.confidence,
                    source="execution",
                )
                db.add(knowledge)
                knowledge_count += 1
            
            if knowledge_count > 0:
                await db.commit()
            
            return knowledge_count
        except Exception:
            return 0
