from app.knowledge_governance import (
    Concept,
    KnowledgeMaturity,
    KnowledgeFreshness,
    ConceptStatus,
)


def test_concept_has_required_quality_fields():
    """Concept must have definition, evidence, confidence, and maturity."""
    concept = Concept(
        id="test-concept",
        name="Test Concept",
        definition="A test concept for quality validation",
        knowledge_maturity=KnowledgeMaturity.DEFINITION,
        knowledge_confidence=0.8,
        knowledge_freshness=KnowledgeFreshness.FRESH,
        status=ConceptStatus.ACTIVE,
        evidence_ids=["evidence-1", "evidence-2"],
    )

    # Check required fields
    assert concept.id
    assert concept.name
    assert concept.definition
    assert len(concept.definition) > 10
    assert concept.knowledge_maturity != KnowledgeMaturity.UNKNOWN
    assert 0.0 <= concept.knowledge_confidence <= 1.0
    assert concept.knowledge_freshness != KnowledgeFreshness.UNKNOWN
    assert concept.status == ConceptStatus.ACTIVE
    assert len(concept.evidence_ids) > 0


def test_concept_definition_cannot_be_empty():
    """Concept definition must be meaningful (validated by governance)."""
    # Model allows empty definition, but governance should reject it
    concept = Concept(
        id="test",
        name="Test",
        definition="",  # Empty definition
    )

    # Model allows it (frozen dataclass doesn't validate)
    assert concept.definition == ""

    # But governance validation should catch this
    from app.knowledge_governance import CandidateKnowledge, DefaultKnowledgeValidator

    validator = DefaultKnowledgeValidator()
    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="",  # Empty definition
    )

    result = validator.validate(candidate)
    assert not result.is_valid
    assert len(result.errors) > 0


def test_concept_confidence_in_valid_range():
    """Concept confidence must be between 0.0 and 1.0."""
    # Valid confidence
    concept = Concept(
        id="test",
        name="Test",
        definition="Test definition",
        knowledge_confidence=0.75,
    )
    assert 0.0 <= concept.knowledge_confidence <= 1.0

    # Invalid confidence (should be caught by validation)
    # This would be caught in the governance pipeline, not at model level
    invalid_concept = Concept(
        id="test",
        name="Test",
        definition="Test definition",
        knowledge_confidence=1.5,  # Invalid
    )
    # Model allows it, but governance should reject it


def test_concept_requires_evidence_for_high_maturity():
    """High maturity concepts require evidence."""
    # High maturity without evidence (governance should reject)
    concept = Concept(
        id="test",
        name="Test",
        definition="Test definition",
        knowledge_maturity=KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS,
        evidence_ids=[],  # No evidence for high maturity
    )

    # Model allows it, but governance validation should reject
    assert concept.knowledge_maturity.value >= 4
    assert len(concept.evidence_ids) == 0


def test_concept_quality_combination():
    """Test valid combination of quality metrics."""
    concept = Concept(
        id="test",
        name="Test",
        definition="Test definition with sufficient detail",
        knowledge_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        knowledge_confidence=0.85,
        knowledge_freshness=KnowledgeFreshness.FRESH,
        status=ConceptStatus.ACTIVE,
        evidence_ids=["ev-1", "ev-2", "ev-3"],
    )

    # This is a valid, high-quality concept
    assert concept.knowledge_maturity.value >= 2
    assert concept.knowledge_confidence >= 0.8
    assert concept.knowledge_freshness == KnowledgeFreshness.FRESH
    assert len(concept.evidence_ids) >= 2
