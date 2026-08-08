import pytest

from app.expert_domains.evaluation import EvaluationFramework
from app.expert_domains.contracts import EvaluationResult, ExecutionStandard
from app.expert_domains.models import DomainConcept, DomainEvidence
from datetime import datetime


class TestEvaluationFramework:
    """Tests for EvaluationFramework."""

    def test_evaluation_framework_initialization(self):
        """Test evaluation framework initialization."""
        framework = EvaluationFramework("test_domain")
        assert framework.domain_id == "test_domain"

    def test_evaluate_domain(self):
        """Test evaluating a domain."""
        framework = EvaluationFramework("test_domain")
        concepts = [
            DomainConcept(
                concept_id="concept1",
                name="Test Concept",
                definition="A test concept",
                importance="medium",
            )
        ]
        evidence = []
        execution_results = [{"success": True}]
        standards = [ExecutionStandard(standard_id="s1", name="Standard")]

        result = framework.evaluate_domain(concepts, evidence, execution_results, standards)
        assert isinstance(result, EvaluationResult)
        assert result.domain_id == "test_domain"
        assert 0.0 <= result.execution_quality <= 1.0
        assert 0.0 <= result.knowledge_quality <= 1.0
        assert 0.0 <= result.evidence_coverage <= 1.0

    def test_evaluate_domain_empty_concepts(self):
        """Test evaluating a domain with no concepts."""
        framework = EvaluationFramework("test_domain")
        concepts = []
        evidence = []
        execution_results = []
        standards = []

        result = framework.evaluate_domain(concepts, evidence, execution_results, standards)
        assert result.knowledge_quality == 0.0
        assert result.evidence_coverage == 0.0

    def test_evaluate_domain_with_evidence(self):
        """Test evaluating a domain with evidence."""
        framework = EvaluationFramework("test_domain")
        concepts = [
            DomainConcept(
                concept_id="concept1",
                name="Test Concept",
                definition="A test concept",
                importance="medium",
                evidence_ids=["evidence1"],
            )
        ]
        evidence = [
            DomainEvidence(
                evidence_id="evidence1",
                source="test",
                reliability=0.9,
                timestamp=datetime.utcnow(),
                domain="test_domain",
                concept_id="concept1",
                confidence=0.85,
                validation_status="validated",
            )
        ]
        execution_results = []
        standards = []

        result = framework.evaluate_domain(concepts, evidence, execution_results, standards)
        assert result.evidence_coverage > 0.0

    def test_get_evaluation_summary(self):
        """Test getting evaluation summary."""
        framework = EvaluationFramework("test_domain")
        result = EvaluationResult(
            domain_id="test",
            execution_quality=0.8,
            knowledge_quality=0.7,
            evidence_coverage=0.9,
            risk=0.3,
            confidence=0.75,
            completeness=0.8,
        )
        summary = framework.get_evaluation_summary(result)
        assert summary["domain_id"] == "test"
        assert summary["execution_quality"] == 0.8
        assert summary["knowledge_quality"] == 0.7
        assert "overall_score" in summary
