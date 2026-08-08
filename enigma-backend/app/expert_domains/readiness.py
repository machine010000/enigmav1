from __future__ import annotations

from typing import List, Dict, Any

from app.expert_domains.models import DomainReadiness
from app.expert_domains.contracts import ReadinessScore


class ReadinessFramework:
    """Framework for calculating readiness scores for expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.readiness = DomainReadiness(domain_id)

    def calculate_readiness(
        self,
        concepts: list,
        required_concepts: List[str],
        past_executions: List[Dict[str, Any]],
        standards: list,
        recent_learning: List[Dict[str, Any]],
    ) -> ReadinessScore:
        """Calculate the readiness score for the domain."""
        knowledge_readiness = self.readiness.calculate_knowledge_readiness(
            concepts, required_concepts
        )
        execution_readiness = self.readiness.calculate_execution_readiness(
            past_executions, standards
        )
        evidence_readiness = self.readiness.calculate_evidence_readiness(concepts, [])
        learning_readiness = self.readiness.calculate_learning_readiness(recent_learning)
        overall_readiness = self.readiness.calculate_overall_readiness(
            knowledge_readiness,
            execution_readiness,
            evidence_readiness,
            learning_readiness,
        )

        return ReadinessScore(
            domain_id=self.domain_id,
            knowledge_readiness=knowledge_readiness,
            execution_readiness=execution_readiness,
            evidence_readiness=evidence_readiness,
            learning_readiness=learning_readiness,
            overall_readiness=overall_readiness,
        )

    def get_readiness_summary(self, score: ReadinessScore) -> Dict[str, Any]:
        """Get a summary of the readiness score."""
        return {
            "domain_id": score.domain_id,
            "knowledge_readiness": score.knowledge_readiness,
            "execution_readiness": score.execution_readiness,
            "evidence_readiness": score.evidence_readiness,
            "learning_readiness": score.learning_readiness,
            "overall_readiness": score.overall_readiness,
            "calculated_at": score.calculated_at.isoformat(),
        }

    def get_readiness_recommendation(self, score: ReadinessScore) -> str:
        """Get a recommendation based on readiness score."""
        if score.overall_readiness >= 0.8:
            return "READY"
        elif score.overall_readiness >= 0.5:
            return "SOMEWHAT_READY"
        elif score.overall_readiness >= 0.3:
            return "NOT_READY"
        else:
            return "UNREADY"
