from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from app.knowledge_governance import (
        CandidateKnowledge,
        Concept,
        GovernedKnowledge,
        KnowledgeGovernanceService,
        SourceType,
    )
    GOVERNANCE_AVAILABLE = True
except ImportError:
    GOVERNANCE_AVAILABLE = False


class KnowledgeGraphAdapter:
    """
    Adapter that enforces Knowledge Governance before allowing knowledge to be stored in the Knowledge Graph.

    This prevents direct bypass of governance by KnowledgeService or other components.
    """

    def __init__(self, governance_service: Optional[Any] = None) -> None:
        self._governance_service = governance_service
        self._governed_knowledge: Dict[str, GovernedKnowledge] = {}

    def set_governance_service(self, service: Any) -> None:
        """Set the governance service to use for validation."""
        self._governance_service = service

    def submit_candidate_for_governance(self, candidate: CandidateKnowledge, actor: str = "system") -> Optional[GovernedKnowledge]:
        """
        Submit candidate knowledge through governance before allowing it to be stored.

        This is the ONLY way knowledge can enter the Knowledge Graph.
        """
        if not GOVERNANCE_AVAILABLE or self._governance_service is None:
            # If governance not available, return None (knowledge will not be stored)
            return None

        governed = self._governance_service.submit_candidate(candidate, actor=actor)

        # Store governed knowledge
        if governed.concept.status.value == "active":
            self._governed_knowledge[governed.concept.id] = governed

        return governed

    def get_governed_knowledge(self, concept_id: str) -> Optional[GovernedKnowledge]:
        """Retrieve governed knowledge by concept ID."""
        return self._governed_knowledge.get(concept_id)

    def list_governed_knowledge(self) -> List[GovernedKnowledge]:
        """List all governed knowledge."""
        return list(self._governed_knowledge.values())

    def is_governed(self, concept_id: str) -> bool:
        """Check if a concept has been governed."""
        return concept_id in self._governed_knowledge


# Global adapter instance
knowledge_graph_adapter = KnowledgeGraphAdapter()
