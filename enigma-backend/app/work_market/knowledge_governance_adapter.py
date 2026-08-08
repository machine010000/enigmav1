from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.knowledge_governance.models import GovernedKnowledge
from app.knowledge_governance import KnowledgeMaturity, KnowledgeFreshness
from app.work_market.contracts import KnowledgeProvider


class KnowledgeGovernanceAdapter(KnowledgeProvider):
    """
    Adapter that bridges Freelancing layer with Knowledge Governance.
    
    This adapter implements the KnowledgeProvider contract using
    the existing Knowledge Governance framework without modifying it.
    """

    def __init__(self, governance_service: Optional[Any] = None) -> None:
        self._governance_service = governance_service

    def get_knowledge_for_concept(self, concept_id: str) -> Optional[GovernedKnowledge]:
        """Get governed knowledge for a specific concept."""
        if not self._governance_service:
            return None
        
        try:
            return self._governance_service.get_governed_knowledge(concept_id)
        except Exception:
            return None

    def get_knowledge_maturity(self, concept_id: str) -> float:
        """Get knowledge maturity score (0.0 to 1.0)."""
        knowledge = self.get_knowledge_for_concept(concept_id)
        if not knowledge:
            return 0.0
        
        # Convert KnowledgeMaturity enum to score
        maturity_map = {
            KnowledgeMaturity.UNKNOWN: 0.0,
            KnowledgeMaturity.DEFINED: 0.2,
            KnowledgeMaturity.SUPPORTED: 0.4,
            KnowledgeMaturity.APPLIED: 0.6,
            KnowledgeMaturity.VALIDATED: 0.8,
            KnowledgeMaturity.TRUSTED: 1.0,
        }
        
        return maturity_map.get(knowledge.maturity, 0.0)

    def get_knowledge_freshness(self, concept_id: str) -> float:
        """Get knowledge freshness score (0.0 to 1.0)."""
        knowledge = self.get_knowledge_for_concept(concept_id)
        if not knowledge:
            return 0.0
        
        # Convert KnowledgeFreshness enum to score
        freshness_map = {
            KnowledgeFreshness.UNKNOWN: 0.0,
            KnowledgeFreshness.STALE: 0.2,
            KnowledgeFreshness.AGING: 0.4,
            KnowledgeFreshness.FRESH: 0.8,
            KnowledgeFreshness.CURRENT: 1.0,
        }
        
        return freshness_map.get(knowledge.freshness, 0.0)

    def get_knowledge_confidence(self, concept_id: str) -> float:
        """Get knowledge confidence score (0.0 to 1.0)."""
        knowledge = self.get_knowledge_for_concept(concept_id)
        if not knowledge:
            return 0.0
        
        return knowledge.confidence if hasattr(knowledge, 'confidence') else 0.5


class MockKnowledgeProvider(KnowledgeProvider):
    """
    Mock implementation of KnowledgeProvider for testing.
    
    This provides static knowledge scores for development when the real
    Knowledge Governance framework is not fully configured.
    """

    def get_knowledge_for_concept(self, concept_id: str) -> Optional[GovernedKnowledge]:
        """Return mock governed knowledge."""
        return None  # No actual knowledge in mock

    def get_knowledge_maturity(self, concept_id: str) -> float:
        """Get mock knowledge maturity score."""
        # Return different scores based on concept to simulate real data
        concept_scores = {
            "seo": 0.85,
            "technical_seo": 0.75,
            "keyword_research": 0.90,
            "content_strategy": 0.65,
            "social_media": 0.70,
            "digital_marketing": 0.72,
        }
        return concept_scores.get(concept_id.lower(), 0.5)

    def get_knowledge_freshness(self, concept_id: str) -> float:
        """Get mock knowledge freshness score."""
        concept_scores = {
            "seo": 0.80,
            "technical_seo": 0.75,
            "keyword_research": 0.85,
            "content_strategy": 0.60,
            "social_media": 0.70,
            "digital_marketing": 0.68,
        }
        return concept_scores.get(concept_id.lower(), 0.5)

    def get_knowledge_confidence(self, concept_id: str) -> float:
        """Get mock knowledge confidence score."""
        concept_scores = {
            "seo": 0.88,
            "technical_seo": 0.82,
            "keyword_research": 0.92,
            "content_strategy": 0.70,
            "social_media": 0.75,
            "digital_marketing": 0.78,
        }
        return concept_scores.get(concept_id.lower(), 0.5)
