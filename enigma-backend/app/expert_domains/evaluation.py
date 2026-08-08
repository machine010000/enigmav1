from __future__ import annotations

from typing import Any, Dict, List

from app.expert_domains.models import DomainEvaluation
from app.expert_domains.contracts import EvaluationResult, ExecutionStandard


class EvaluationFramework:
    """Framework for evaluating expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.evaluation = DomainEvaluation(domain_id)

    def evaluate_domain(
        self,
        concepts: list,
        evidence: list,
        execution_results: List[Dict[str, Any]],
        standards: List[ExecutionStandard],
    ) -> EvaluationResult:
        """Evaluate the domain state."""
        execution_quality = self.evaluation.evaluate_execution_quality(
            execution_results, standards
        )
        knowledge_quality = self.evaluation.evaluate_knowledge_quality(concepts, evidence)
        evidence_coverage = self.evaluation.evaluate_evidence_coverage(concepts, evidence)
        risk = 0.5  # Placeholder risk
        confidence = 0.7  # Placeholder confidence
        completeness = (execution_quality + knowledge_quality + evidence_coverage) / 3

        result = EvaluationResult(
            domain_id=self.domain_id,
            execution_quality=execution_quality,
            knowledge_quality=knowledge_quality,
            evidence_coverage=evidence_coverage,
            risk=risk,
            confidence=confidence,
            completeness=completeness,
        )

        # Calculate risk based on evaluation
        result = self._evaluate_risk(result)

        return result

    def _evaluate_risk(self, result: EvaluationResult) -> EvaluationResult:
        """Evaluate risk based on evaluation result."""
        # Higher risk if quality is low
        if result.execution_quality < 0.5:
            risk = 0.7
        elif result.knowledge_quality < 0.5:
            risk = 0.6
        elif result.evidence_coverage < 0.5:
            risk = 0.5
        else:
            risk = 0.3

        return EvaluationResult(
            domain_id=result.domain_id,
            execution_quality=result.execution_quality,
            knowledge_quality=result.knowledge_quality,
            evidence_coverage=result.evidence_coverage,
            risk=risk,
            confidence=result.confidence,
            completeness=result.completeness,
        )

    def get_evaluation_summary(self, result: EvaluationResult) -> Dict[str, Any]:
        """Get a summary of the evaluation."""
        return {
            "domain_id": result.domain_id,
            "execution_quality": result.execution_quality,
            "knowledge_quality": result.knowledge_quality,
            "evidence_coverage": result.evidence_coverage,
            "risk": result.risk,
            "confidence": result.confidence,
            "completeness": result.completeness,
            "evaluated_at": result.evaluated_at.isoformat(),
            "overall_score": (
                result.execution_quality + result.knowledge_quality + result.evidence_coverage
            )
            / 3,
        }
