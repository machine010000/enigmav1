from app.knowledge_governance import (
    Concept,
    KnowledgeConflict,
    SourceType,
    Evidence,
    DefaultConflictResolver,
)
from datetime import datetime


def test_conflicting_claims_not_converted_to_truth():
    """Conflicting claims should not be automatically converted to truth."""
    resolver = DefaultConflictResolver()

    # Create two concepts with same name but different definitions
    concept1 = Concept(
        id="concept-1",
        name="CTR",
        definition="Click-through rate is the ratio of users who click",
        knowledge_confidence=0.8,
        evidence_ids=["ev-1"],
    )

    concept2 = Concept(
        id="concept-2",
        name="CTR",
        definition="Click-through rate is conversion rate",  # Wrong definition
        knowledge_confidence=0.7,
        evidence_ids=["ev-2"],
    )

    conflicts = resolver.detect_conflicts(concept1, [concept2])

    # Should detect conflict
    assert len(conflicts) > 0

    # Try to resolve
    evidence = [
        Evidence(
            id="ev-1",
            source="Research",
            source_type=SourceType.RESEARCH,
            claim="CTR is click-through rate",
            retrieved_at=datetime.utcnow(),
            quality_score=0.8,
        ),
        Evidence(
            id="ev-2",
            source="Blog",
            source_type=SourceType.EXTERNAL_SOURCE,
            claim="CTR is conversion rate",
            retrieved_at=datetime.utcnow(),
            quality_score=0.3,
        ),
    ]

    for conflict in conflicts:
        resolution = resolver.resolve_conflict(conflict, evidence)

        # If unresolvable, should return None
        if resolution is None:
            assert conflict.status == "unresolved"
        else:
            # If resolved, should have a reason
            assert conflict.resolution_reason


def test_unresolved_conflicts_are_preserved():
    """Unresolved conflicts should be preserved in the system."""
    resolver = DefaultConflictResolver()

    concept1 = Concept(
        id="concept-1",
        name="Test",
        definition="Definition A",
        knowledge_confidence=0.5,
        evidence_ids=["ev-1"],
    )

    concept2 = Concept(
        id="concept-2",
        name="Test",
        definition="Definition B",
        knowledge_confidence=0.5,
        evidence_ids=["ev-2"],
    )

    conflicts = resolver.detect_conflicts(concept1, [concept2])

    # At least one conflict should be detected
    assert len(conflicts) > 0

    # Check that conflict has required fields
    for conflict in conflicts:
        assert conflict.id
        assert conflict.concept_id
        assert len(conflict.competing_claims) >= 2
        assert conflict.status in ["unresolved", "resolved", "rejected"]
        assert conflict.created_at


def test_conflict_resolution_uses_evidence_quality():
    """Conflict resolution should prioritize evidence quality."""
    resolver = DefaultConflictResolver()

    conflict = KnowledgeConflict(
        id="conflict-1",
        concept_id="test",
        competing_claims=["Claim A", "Claim B"],
        evidence_comparison={
            "concept_evidence_count": 3,
            "existing_evidence_count": 1,
            "concept_confidence": 0.8,
            "existing_confidence": 0.6,
        },
        status="unresolved",
    )

    evidence = []  # Evidence not needed for this test

    resolution = resolver.resolve_conflict(conflict, evidence)

    # Should resolve in favor of concept (more evidence)
    assert resolution == "concept"


def test_conflict_resolution_uses_confidence():
    """Conflict resolution should use confidence when evidence counts are equal."""
    resolver = DefaultConflictResolver()

    conflict = KnowledgeConflict(
        id="conflict-1",
        concept_id="test",
        competing_claims=["Claim A", "Claim B"],
        evidence_comparison={
            "concept_evidence_count": 2,
            "existing_evidence_count": 2,
            "concept_confidence": 0.9,
            "existing_confidence": 0.6,
        },
        status="unresolved",
    )

    evidence = []

    resolution = resolver.resolve_conflict(conflict, evidence)

    # Should resolve in favor of concept (higher confidence)
    assert resolution == "concept"


def test_conflict_with_equal_metrics_remains_unresolved():
    """Conflicts with equal metrics should remain unresolved."""
    resolver = DefaultConflictResolver()

    conflict = KnowledgeConflict(
        id="conflict-1",
        concept_id="test",
        competing_claims=["Claim A", "Claim B"],
        evidence_comparison={
            "concept_evidence_count": 2,
            "existing_evidence_count": 2,
            "concept_confidence": 0.7,
            "existing_confidence": 0.7,
        },
        status="unresolved",
    )

    evidence = []

    resolution = resolver.resolve_conflict(conflict, evidence)

    # Should remain unresolved
    assert resolution is None


def test_conflict_detection_ignores_different_names():
    """Conflict detection should not flag concepts with different names."""
    resolver = DefaultConflictResolver()

    concept1 = Concept(
        id="concept-1",
        name="CTR",
        definition="Click-through rate",
        knowledge_confidence=0.8,
    )

    concept2 = Concept(
        id="concept-2",
        name="Conversion Rate",
        definition="Conversion rate is different",
        knowledge_confidence=0.8,
    )

    conflicts = resolver.detect_conflicts(concept1, [concept2])

    # Should not detect conflict (different names)
    assert len(conflicts) == 0
