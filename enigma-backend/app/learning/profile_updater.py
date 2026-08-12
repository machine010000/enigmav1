"""
Profile / Business State Updater

Updates ENIGMA's capability profile based on execution observations.
"""
from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.learning.observation import ExecutionObservation, ObservationStatus
from app.models.enigma_profile import EnigmaProfile, KnowledgeProgress


class ProfileUpdater:
    """
    Updates ENIGMA's profile based on execution observations.
    
    This tracks ENIGMA's capability confidence and history.
    """
    
    async def update_capability_profile(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """
        Update ENIGMA's capability profile based on observation.
        
        Args:
            observation: ExecutionObservation
            db: Database session
            
        Returns:
            bool indicating success
        """
        if observation.status == ObservationStatus.FAILURE:
            # Failures don't increase capability confidence
            return await self._record_failure(observation, db)
        
        # Success: update capability confidence
        return await self._record_success(observation, db)
    
    async def _record_success(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """Record a successful capability execution."""
        try:
            # Get or create EnigmaProfile
            result = await db.execute(
                select(EnigmaProfile).where(EnigmaProfile.profile_id == "enigma_profile")
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                profile = EnigmaProfile(profile_id="enigma_profile")
                db.add(profile)
                await db.flush()
            
            # Get or create KnowledgeProgress for this capability
            result = await db.execute(
                select(KnowledgeProgress).where(
                    KnowledgeProgress.profile_id == profile.profile_id,
                    KnowledgeProgress.domain == observation.capability,
                )
            )
            knowledge_progress = result.scalar_one_or_none()
            
            if not knowledge_progress:
                knowledge_progress = KnowledgeProgress(
                    profile_id=profile.profile_id,
                    domain=observation.capability,
                )
                db.add(knowledge_progress)
                await db.flush()
            
            # Update scores based on success
            # Simple incremental update: increase confidence by 10% of remaining gap
            current_confidence = knowledge_progress.confidence or 0.0
            confidence_boost = (1.0 - current_confidence) * 0.1
            knowledge_progress.confidence = min(1.0, current_confidence + confidence_boost)
            
            # Update execution score
            current_execution_score = knowledge_progress.execution_score or 0.0
            execution_boost = (1.0 - current_execution_score) * 0.1
            knowledge_progress.execution_score = min(1.0, current_execution_score + execution_boost)
            
            # Update evidence score based on observation confidence
            current_evidence_score = knowledge_progress.evidence_score or 0.0
            evidence_boost = (observation.confidence - current_evidence_score) * 0.1
            knowledge_progress.evidence_score = max(0.0, min(1.0, current_evidence_score + evidence_boost))
            
            # Update readiness (average of scores)
            knowledge_progress.readiness = (
                knowledge_progress.knowledge_score +
                knowledge_progress.execution_score +
                knowledge_progress.evidence_score
            ) / 3.0
            
            # Update freshness
            knowledge_progress.freshness = "fresh"
            knowledge_progress.last_verified = observation.created_at
            
            await db.commit()
            return True
        except Exception:
            return False
    
    async def _record_failure(
        self,
        observation: ExecutionObservation,
        db: AsyncSession,
    ) -> bool:
        """Record a failed capability execution."""
        try:
            # Get or create EnigmaProfile
            result = await db.execute(
                select(EnigmaProfile).where(EnigmaProfile.profile_id == "enigma_profile")
            )
            profile = result.scalar_one_or_none()
            
            if not profile:
                profile = EnigmaProfile(profile_id="enigma_profile")
                db.add(profile)
                await db.flush()
            
            # Get or create KnowledgeProgress for this capability
            result = await db.execute(
                select(KnowledgeProgress).where(
                    KnowledgeProgress.profile_id == profile.profile_id,
                    KnowledgeProgress.domain == observation.capability,
                )
            )
            knowledge_progress = result.scalar_one_or_none()
            
            if not knowledge_progress:
                knowledge_progress = KnowledgeProgress(
                    profile_id=profile.profile_id,
                    domain=observation.capability,
                )
                db.add(knowledge_progress)
                await db.flush()
            
            # Failures decrease execution score slightly
            current_execution_score = knowledge_progress.execution_score or 0.0
            knowledge_progress.execution_score = max(0.0, current_execution_score - 0.05)
            
            # Update readiness
            knowledge_progress.readiness = (
                knowledge_progress.knowledge_score +
                knowledge_progress.execution_score +
                knowledge_progress.evidence_score
            ) / 3.0
            
            # Mark as aging if multiple failures
            knowledge_progress.freshness = "aging"
            
            await db.commit()
            return True
        except Exception:
            return False
