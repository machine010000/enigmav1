import pytest

from app.expert_domains.readiness import ReadinessFramework
from app.expert_domains.contracts import ReadinessScore


class TestReadinessFramework:
    """Tests for ReadinessFramework."""

    def test_readiness_framework_initialization(self):
        """Test readiness framework initialization."""
        framework = ReadinessFramework("test_domain")
        assert framework.domain_id == "test_domain"

    def test_calculate_readiness(self):
        """Test calculating readiness."""
        framework = ReadinessFramework("test_domain")
        concepts = []  # No concepts required
        required_concepts = []
        past_executions = []
        standards = []
        recent_learning = []

        score = framework.calculate_readiness(
            concepts, required_concepts, past_executions, standards, recent_learning
        )
        assert isinstance(score, ReadinessScore)
        assert score.domain_id == "test_domain"
        assert 0.0 <= score.knowledge_readiness <= 1.0
        assert 0.0 <= score.execution_readiness <= 1.0
        assert 0.0 <= score.evidence_readiness <= 1.0
        assert 0.0 <= score.learning_readiness <= 1.0
        assert 0.0 <= score.overall_readiness <= 1.0

    def test_calculate_readiness_with_executions(self):
        """Test calculating readiness with past executions."""
        framework = ReadinessFramework("test_domain")
        concepts = []
        required_concepts = []
        past_executions = [{"success": True}, {"success": True}, {"success": False}]
        standards = []
        recent_learning = []

        score = framework.calculate_readiness(
            concepts, required_concepts, past_executions, standards, recent_learning
        )
        assert score.execution_readiness > 0.0

    def test_calculate_readiness_with_learning(self):
        """Test calculating readiness with recent learning."""
        framework = ReadinessFramework("test_domain")
        concepts = []
        required_concepts = []
        past_executions = []
        standards = []
        recent_learning = [
            {"type": "new_knowledge"},
            {"type": "evidence_update"},
            {"type": "reflection"},
        ]

        score = framework.calculate_readiness(
            concepts, required_concepts, past_executions, standards, recent_learning
        )
        assert score.learning_readiness > 0.0

    def test_get_readiness_summary(self):
        """Test getting readiness summary."""
        framework = ReadinessFramework("test_domain")
        score = ReadinessScore(
            domain_id="test",
            knowledge_readiness=0.85,
            execution_readiness=0.8,
            evidence_readiness=0.9,
            learning_readiness=0.75,
            overall_readiness=0.82,
        )
        summary = framework.get_readiness_summary(score)
        assert summary["domain_id"] == "test"
        assert summary["knowledge_readiness"] == 0.85
        assert summary["execution_readiness"] == 0.8
        assert summary["evidence_readiness"] == 0.9
        assert summary["learning_readiness"] == 0.75
        assert summary["overall_readiness"] == 0.82
        assert "calculated_at" in summary

    def test_get_readiness_recommendation_ready(self):
        """Test readiness recommendation for ready state."""
        framework = ReadinessFramework("test_domain")
        score = ReadinessScore(
            domain_id="test",
            knowledge_readiness=0.9,
            execution_readiness=0.9,
            evidence_readiness=0.9,
            learning_readiness=0.9,
            overall_readiness=0.9,
        )
        recommendation = framework.get_readiness_recommendation(score)
        assert recommendation == "READY"

    def test_get_readiness_recommendation_somewhat_ready(self):
        """Test readiness recommendation for somewhat ready state."""
        framework = ReadinessFramework("test_domain")
        score = ReadinessScore(
            domain_id="test",
            knowledge_readiness=0.6,
            execution_readiness=0.6,
            evidence_readiness=0.6,
            learning_readiness=0.6,
            overall_readiness=0.6,
        )
        recommendation = framework.get_readiness_recommendation(score)
        assert recommendation == "SOMEWHAT_READY"

    def test_get_readiness_recommendation_not_ready(self):
        """Test readiness recommendation for not ready state."""
        framework = ReadinessFramework("test_domain")
        score = ReadinessScore(
            domain_id="test",
            knowledge_readiness=0.4,
            execution_readiness=0.4,
            evidence_readiness=0.4,
            learning_readiness=0.4,
            overall_readiness=0.4,
        )
        recommendation = framework.get_readiness_recommendation(score)
        assert recommendation == "NOT_READY"

    def test_get_readiness_recommendation_unready(self):
        """Test readiness recommendation for unready state."""
        framework = ReadinessFramework("test_domain")
        score = ReadinessScore(
            domain_id="test",
            knowledge_readiness=0.2,
            execution_readiness=0.2,
            evidence_readiness=0.2,
            learning_readiness=0.2,
            overall_readiness=0.2,
        )
        recommendation = framework.get_readiness_recommendation(score)
        assert recommendation == "UNREADY"
