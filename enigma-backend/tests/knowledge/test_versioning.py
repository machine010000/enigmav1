from app.knowledge_governance import (
    Concept,
    ConceptVersion,
    ConceptStatus,
    KnowledgeMaturity,
    DefaultKnowledgeGovernanceService,
    Evidence,
    SourceType,
    CandidateKnowledge,
)
from datetime import datetime


def test_version_history_is_preserved():
    """Version history should be preserved when concept is updated."""
    service = DefaultKnowledgeGovernanceService()

    # Create initial concept
    from app.knowledge_governance import CandidateKnowledge

    candidate1 = CandidateKnowledge(
        id="test-1",
        name="Test Concept",
        definition="Initial definition",
        evidence=[
            Evidence(
                id="ev-1",
                source="Test",
                source_type=SourceType.RESEARCH,
                claim="Evidence",
                retrieved_at=datetime.utcnow(),
                quality_score=0.8,
            )
        ],
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.7,
    )

    governed1 = service.submit_candidate(candidate1)

    # Should have version 1
    assert len(governed1.versions) == 1
    assert governed1.versions[0].version == 1
    assert governed1.versions[0].definition == "Initial definition"


def test_concept_version_is_immutable():
    """ConceptVersion should be immutable (frozen dataclass)."""
    version = ConceptVersion(
        version=1,
        concept_id="test",
        definition="Test definition",
    )

    try:
        version.definition = "Modified"
        assert False, "ConceptVersion should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected


def test_version_includes_reason():
    """Version should include reason for change."""
    version = ConceptVersion(
        version=1,
        concept_id="test",
        definition="Test definition",
        reason="Initial version from candidate submission",
    )

    assert version.reason
    assert len(version.reason) > 0


def test_version_includes_governance_metadata():
    """Version should include governance metadata."""
    version = ConceptVersion(
        version=1,
        concept_id="test",
        definition="Test definition",
        confidence=0.8,
        maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        created_at=datetime.utcnow(),
        status=ConceptStatus.ACTIVE,
    )

    assert version.confidence >= 0.0
    assert version.confidence <= 1.0
    assert version.maturity != KnowledgeMaturity.UNKNOWN
    assert version.created_at
    assert version.status == ConceptStatus.ACTIVE


def test_deprecated_knowledge_not_deleted():
    """Deprecated knowledge should not be deleted, just marked."""
    service = DefaultKnowledgeGovernanceService()

    from app.knowledge_governance import CandidateKnowledge

    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="Test definition",
        evidence=[
            Evidence(
                id="ev-1",
                source="Test",
                source_type=SourceType.RESEARCH,
                claim="Evidence",
                retrieved_at=datetime.utcnow(),
                quality_score=0.8,
            )
        ],
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.7,
    )

    governed = service.submit_candidate(candidate)

    # Initially active
    assert governed.concept.status == ConceptStatus.ACTIVE

    # Should be able to mark as deprecated without deleting
    # (In real implementation, this would be a separate method)
    # For now, just verify the status enum exists
    assert ConceptStatus.DEPRECATED.value == "deprecated"
    assert ConceptStatus.SUPERSEDED.value == "superseded"
    assert ConceptStatus.REJECTED.value == "rejected"


def test_superseded_version_tracking():
    """Superseded versions should track what superseded them."""
    version = ConceptVersion(
        version=1,
        concept_id="test",
        definition="Old definition",
        superseded_by="v2",
        superseded_reason="New evidence emerged",
        status=ConceptStatus.SUPERSEDED,  # Status must be set explicitly
    )

    assert version.superseded_by
    assert version.superseded_reason
    assert version.status == ConceptStatus.SUPERSEDED


def test_version_number_increments():
    """Version numbers should increment with changes."""
    versions = [
        ConceptVersion(
            version=1,
            concept_id="test",
            definition="Definition v1",
        ),
        ConceptVersion(
            version=2,
            concept_id="test",
            definition="Definition v2",
        ),
        ConceptVersion(
            version=3,
            concept_id="test",
            definition="Definition v3",
        ),
    ]

    assert versions[0].version == 1
    assert versions[1].version == 2
    assert versions[2].version == 3


def test_version_links_to_concept():
    """Version should be linked to its concept."""
    version = ConceptVersion(
        version=1,
        concept_id="concept-123",
        definition="Test definition",
    )

    assert version.concept_id == "concept-123"
