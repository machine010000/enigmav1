"""
Knowledge Progress

Tracking and analysis of knowledge domain progress.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime

from app.enigma_profile.contracts import (
    KnowledgeProgress,
    SkillLevel,
)
from app.enigma_profile.repositories import KnowledgeProgressRepository


class KnowledgeProgressTracker:
    """
    Tracker for knowledge domain progress.
    
    Tracks knowledge, execution, evidence, confidence, and readiness
    for various knowledge domains.
    """
    
    def __init__(self, knowledge_repo: Optional[KnowledgeProgressRepository] = None):
        """Initialize knowledge progress tracker.
        
        Args:
            knowledge_repo: Knowledge progress repository
        """
        self._progress: Dict[str, KnowledgeProgress] = {}
        self._knowledge_repo = knowledge_repo
    
    async def register_domain(self, progress: KnowledgeProgress) -> None:
        """
        Register knowledge progress for a domain.
        
        Args:
            progress: Knowledge progress data
        """
        self._progress[progress.domain] = progress
        if self._knowledge_repo:
            await self._knowledge_repo.save_progress("enigma_profile", progress)
    
    def get_progress(self, domain: str) -> Optional[KnowledgeProgress]:
        """
        Get knowledge progress for a domain.
        
        Args:
            domain: Knowledge domain
            
        Returns:
            KnowledgeProgress or None
        """
        return self._progress.get(domain)
    
    async def update_progress(
        self,
        domain: str,
        knowledge_score: Optional[float] = None,
        execution_score: Optional[float] = None,
        evidence_score: Optional[float] = None,
        confidence: Optional[float] = None,
        readiness: Optional[float] = None,
        freshness: Optional[str] = None,
    ) -> None:
        """
        Update knowledge progress for a domain.
        
        Args:
            domain: Knowledge domain
            knowledge_score: Knowledge score (0.0 to 1.0)
            execution_score: Execution score (0.0 to 1.0)
            evidence_score: Evidence score (0.0 to 1.0)
            confidence: Confidence (0.0 to 1.0)
            readiness: Readiness (0.0 to 1.0)
            freshness: Freshness status
        """
        if domain not in self._progress:
            return
        
        progress = self._progress[domain]
        
        if knowledge_score is not None:
            progress.knowledge_score = knowledge_score
        if execution_score is not None:
            progress.execution_score = execution_score
        if evidence_score is not None:
            progress.evidence_score = evidence_score
        if confidence is not None:
            progress.confidence = confidence
        if readiness is not None:
            progress.readiness = readiness
        if freshness is not None:
            progress.freshness = freshness
        
        progress.last_verified = datetime.utcnow().isoformat()
        
        if self._knowledge_repo:
            await self._knowledge_repo.save_progress("enigma_profile", progress)
    
    def calculate_readiness(self, domain: str) -> float:
        """
        Calculate overall readiness for a domain.
        
        Args:
            domain: Knowledge domain
            
        Returns:
            Readiness score (0.0 to 1.0)
        """
        progress = self.get_progress(domain)
        if not progress:
            return 0.0
        
        # Weighted average
        weights = {
            "knowledge": 0.3,
            "execution": 0.3,
            "evidence": 0.25,
            "confidence": 0.15,
        }
        
        readiness = (
            progress.knowledge_score * weights["knowledge"] +
            progress.execution_score * weights["execution"] +
            progress.evidence_score * weights["evidence"] +
            progress.confidence * weights["confidence"]
        )
        
        return min(1.0, max(0.0, readiness))
    
    def get_skill_level(self, domain: str) -> SkillLevel:
        """
        Determine skill level based on readiness.
        
        Args:
            domain: Knowledge domain
            
        Returns:
            SkillLevel
        """
        readiness = self.calculate_readiness(domain)
        
        if readiness >= 0.8:
            return SkillLevel.EXPERT
        elif readiness >= 0.6:
            return SkillLevel.OPERATIONAL
        elif readiness >= 0.4:
            return SkillLevel.GROWING
        elif readiness >= 0.2:
            return SkillLevel.LEARNING
        else:
            return SkillLevel.UNKNOWN
    
    def identify_gaps(self, domain: str) -> List[str]:
        """
        Identify knowledge gaps for a domain.
        
        Args:
            domain: Knowledge domain
            
        Returns:
            List of gap descriptions
        """
        progress = self.get_progress(domain)
        if not progress:
            return ["Domain not tracked"]
        
        gaps = []
        
        if progress.knowledge_score < 0.5:
            gaps.append(f"Low knowledge score ({progress.knowledge_score:.0%})")
        if progress.execution_score < 0.5:
            gaps.append(f"Low execution score ({progress.execution_score:.0%})")
        if progress.evidence_score < 0.5:
            gaps.append(f"Low evidence score ({progress.evidence_score:.0%})")
        if progress.confidence < 0.5:
            gaps.append(f"Low confidence ({progress.confidence:.0%})")
        if progress.freshness == "stale":
            gaps.append("Knowledge is stale")
        if progress.freshness == "expired":
            gaps.append("Knowledge is expired")
        
        return gaps
    
    async def get_all_progress(self) -> Dict[str, KnowledgeProgress]:
        """Get all knowledge progress."""
        if self._knowledge_repo:
            return await self._knowledge_repo.get_all_progress("enigma_profile")
        return self._progress
    
    def get_all_domains(self) -> List[str]:
        """Get all tracked domains."""
        return list(self._progress.keys())
    
    def get_stale_domains(self, max_age_hours: int = 24) -> List[str]:
        """
        Get domains with stale knowledge.
        
        Args:
            max_age_hours: Maximum age in hours to consider fresh
            
        Returns:
            List of domain names
        """
        stale = []
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        for domain, progress in self._progress.items():
            if progress.last_verified:
                try:
                    verified_time = datetime.fromisoformat(progress.last_verified).timestamp()
                    if verified_time < cutoff:
                        stale.append(domain)
                except ValueError:
                    stale.append(domain)
            elif progress.freshness in ["stale", "expired"]:
                stale.append(domain)
        
        return stale
