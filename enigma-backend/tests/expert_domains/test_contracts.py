import pytest
from datetime import datetime

from app.expert_domains.contracts import (
    ExpertDomainContract,
    DomainIdentity,
    KnowledgeArea,
    DomainConcept,
    DomainEvidence,
    ReasoningPattern,
    DecisionRule,
    DomainKPI,
    ExecutionStandard,
    EvaluationResult,
    ReadinessScore,
    DomainLifecycleStage,
    ReasoningPatternType,
)


class MockExpertDomain(ExpertDomainContract):
    """Mock implementation of ExpertDomainContract for testing."""

    def __init__(self, domain_id: str = "test_domain"):
        self.domain_id = domain_id
        self.identity = DomainIdentity(
            domain_id=domain_id,
            name="Test Domain",
            description="A test domain for unit testing",
            version="1.0.0",
        )

    def get_identity(self) -> DomainIdentity:
        return self.identity

    def get_knowledge_areas(self) -> list:
        return [
            KnowledgeArea(
                area_id="area1",
                name="Test Area",
                description="A test knowledge area",
            )
        ]

    def get_concepts(self) -> list:
        return [
            DomainConcept(
                concept_id="concept1",
                name="Test Concept",
                definition="A test concept",
                importance="medium",
            )
        ]

    def get_evidence_types(self) -> list:
        return ["evidence_type_1", "evidence_type_2"]

    def get_reasoning_patterns(self) -> list:
        return [
            ReasoningPattern(
                pattern_id="pattern1",
                pattern_type=ReasoningPatternType.DIAGNOSIS,
                name="Test Pattern",
                description="A test reasoning pattern",
            )
        ]

    def get_decision_rules(self) -> list:
        return [
            DecisionRule(
                rule_id="rule1",
                name="Test Rule",
                description="A test decision rule",
            )
        ]

    def get_kpis(self) -> list:
        return [
            DomainKPI(
                kpi_id="kpi1",
                metric="test_metric",
                target=1.0,
                threshold=0.5,
            )
        ]

    def get_execution_standards(self) -> list:
        return [
            ExecutionStandard(
                standard_id="standard1",
                name="Test Standard",
            )
        ]

    def evaluate(self) -> EvaluationResult:
        return EvaluationResult(
            domain_id=self.domain_id,
            execution_quality=0.8,
            knowledge_quality=0.7,
            evidence_coverage=0.9,
            risk=0.3,
            confidence=0.75,
            completeness=0.8,
        )

    def get_readiness(self) -> ReadinessScore:
        return ReadinessScore(
            domain_id=self.domain_id,
            knowledge_readiness=0.85,
            execution_readiness=0.8,
            evidence_readiness=0.9,
            learning_readiness=0.75,
            overall_readiness=0.82,
        )

    def get_lifecycle_stage(self) -> DomainLifecycleStage:
        return DomainLifecycleStage.OPERATIONAL

    def can_advance_to_stage(self, stage: DomainLifecycleStage) -> bool:
        return stage == DomainLifecycleStage.EXPERT


class TestExpertDomainContract:
    """Tests for ExpertDomainContract."""

    def test_domain_identity_creation(self):
        """Test creating a DomainIdentity."""
        identity = DomainIdentity(
            domain_id="test",
            name="Test",
            description="Test description",
            version="1.0.0",
        )
        assert identity.domain_id == "test"
        assert identity.name == "Test"
        assert identity.description == "Test description"
        assert identity.version == "1.0.0"

    def test_knowledge_area_creation(self):
        """Test creating a KnowledgeArea."""
        area = KnowledgeArea(
            area_id="area1",
            name="Test Area",
            description="A test area",
        )
        assert area.area_id == "area1"
        assert area.name == "Test Area"
        assert area.importance == "medium"

    def test_domain_concept_creation(self):
        """Test creating a DomainConcept."""
        concept = DomainConcept(
            concept_id="concept1",
            name="Test Concept",
            definition="A test concept",
            importance="high",
        )
        assert concept.concept_id == "concept1"
        assert concept.name == "Test Concept"
        assert concept.importance == "high"
        assert concept.confidence == 0.0

    def test_domain_evidence_creation(self):
        """Test creating a DomainEvidence."""
        evidence = DomainEvidence(
            evidence_id="evidence1",
            source="test_source",
            reliability=0.9,
            timestamp=datetime.utcnow(),
            domain="test_domain",
            concept_id="concept1",
            confidence=0.85,
            validation_status="validated",
        )
        assert evidence.evidence_id == "evidence1"
        assert evidence.reliability == 0.9
        assert evidence.validation_status == "validated"

    def test_reasoning_pattern_creation(self):
        """Test creating a ReasoningPattern."""
        pattern = ReasoningPattern(
            pattern_id="pattern1",
            pattern_type=ReasoningPatternType.DIAGNOSIS,
            name="Test Pattern",
            description="A test pattern",
        )
        assert pattern.pattern_id == "pattern1"
        assert pattern.pattern_type == ReasoningPatternType.DIAGNOSIS

    def test_decision_rule_creation(self):
        """Test creating a DecisionRule."""
        rule = DecisionRule(
            rule_id="rule1",
            name="Test Rule",
            description="A test rule",
        )
        assert rule.rule_id == "rule1"
        assert rule.name == "Test Rule"

    def test_domain_kpi_creation(self):
        """Test creating a DomainKPI."""
        kpi = DomainKPI(
            kpi_id="kpi1",
            metric="test_metric",
            target=1.0,
            threshold=0.5,
        )
        assert kpi.kpi_id == "kpi1"
        assert kpi.target == 1.0
        assert kpi.threshold == 0.5

    def test_execution_standard_creation(self):
        """Test creating an ExecutionStandard."""
        standard = ExecutionStandard(
            standard_id="standard1",
            name="Test Standard",
        )
        assert standard.standard_id == "standard1"
        assert standard.name == "Test Standard"

    def test_evaluation_result_creation(self):
        """Test creating an EvaluationResult."""
        result = EvaluationResult(
            domain_id="test",
            execution_quality=0.8,
            knowledge_quality=0.7,
            evidence_coverage=0.9,
            risk=0.3,
            confidence=0.75,
            completeness=0.8,
        )
        assert result.domain_id == "test"
        assert result.execution_quality == 0.8
        assert result.knowledge_quality == 0.7

    def test_readiness_score_creation(self):
        """Test creating a ReadinessScore."""
        score = ReadinessScore(
            domain_id="test",
            knowledge_readiness=0.85,
            execution_readiness=0.8,
            evidence_readiness=0.9,
            learning_readiness=0.75,
            overall_readiness=0.82,
        )
        assert score.domain_id == "test"
        assert score.knowledge_readiness == 0.85
        assert score.overall_readiness == 0.82

    def test_mock_domain_implements_contract(self):
        """Test that mock domain implements all required methods."""
        domain = MockExpertDomain()
        assert hasattr(domain, "get_identity")
        assert hasattr(domain, "get_knowledge_areas")
        assert hasattr(domain, "get_concepts")
        assert hasattr(domain, "get_evidence_types")
        assert hasattr(domain, "get_reasoning_patterns")
        assert hasattr(domain, "get_decision_rules")
        assert hasattr(domain, "get_kpis")
        assert hasattr(domain, "get_execution_standards")
        assert hasattr(domain, "evaluate")
        assert hasattr(domain, "get_readiness")
        assert hasattr(domain, "get_lifecycle_stage")
        assert hasattr(domain, "can_advance_to_stage")

    def test_mock_domain_contract_methods_return_correct_types(self):
        """Test that mock domain methods return correct types."""
        domain = MockExpertDomain()
        assert isinstance(domain.get_identity(), DomainIdentity)
        assert isinstance(domain.get_knowledge_areas(), list)
        assert isinstance(domain.get_concepts(), list)
        assert isinstance(domain.get_evidence_types(), list)
        assert isinstance(domain.get_reasoning_patterns(), list)
        assert isinstance(domain.get_decision_rules(), list)
        assert isinstance(domain.get_kpis(), list)
        assert isinstance(domain.get_execution_standards(), list)
        assert isinstance(domain.evaluate(), EvaluationResult)
        assert isinstance(domain.get_readiness(), ReadinessScore)
        assert isinstance(domain.get_lifecycle_stage(), DomainLifecycleStage)
        assert isinstance(domain.can_advance_to_stage(DomainLifecycleStage.EXPERT), bool)
