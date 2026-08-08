from app.knowledge_governance import (
    CandidateKnowledge,
    Concept,
    ConceptStatus,
    Evidence,
    KnowledgeMaturity,
    SourceType,
    DefaultKnowledgeGovernanceService,
    DefaultKnowledgeValidator,
    DefaultEvidenceScorer,
    DefaultConflictResolver,
)
from datetime import datetime


def test_governance_pipeline_full_flow():
    """Test full governance pipeline: Candidate -> Validation -> Scoring -> Conflict -> Version -> Governed."""
    service = DefaultKnowledgeGovernanceService()

    # Step 1: Create candidate
    candidate = CandidateKnowledge(
        id="candidate-1",
        name="Test Concept",
        definition="A test concept for governance pipeline validation",
        evidence=[
            Evidence(
                id="ev-1",
                source="Research Paper",
                source_type=SourceType.RESEARCH,
                claim="Supporting evidence from research",
                retrieved_at=datetime.utcnow(),
                published_at=datetime.utcnow(),
                quality_score=0.8,
            ),
            Evidence(
                id="ev-2",
                source="Academy",
                source_type=SourceType.ACADEMY,
                claim="Supporting evidence from academy",
                retrieved_at=datetime.utcnow(),
                published_at=datetime.utcnow(),
                quality_score=0.85,
            ),
        ],
        proposed_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        proposed_confidence=0.8,
        source="test_pipeline",
    )

    # Step 2: Submit through governance pipeline
    governed = service.submit_candidate(candidate, actor="test_user")

    # Step 3: Verify results
    # Should be governed (not rejected)
    assert governed.concept.status == ConceptStatus.ACTIVE

    # Should have version history
    assert len(governed.versions) == 1
    assert governed.versions[0].version == 1

    # Should have validation result
    assert governed.validation_result is not None
    assert governed.validation_result["is_valid"] is True

    # Should have governance events
    assert len(governed.governance_events) == 1
    assert governed.governance_events[0].action == "published"

    # Should have concept with proper fields
    assert governed.concept.id
    assert governed.concept.name == candidate.name
    assert governed.concept.definition == candidate.definition


def test_validation_rejects_invalid_candidates():
    """Validation should reject candidates that don't meet requirements."""
    service = DefaultKnowledgeGovernanceService()

    # Invalid candidate: empty definition
    invalid_candidate = CandidateKnowledge(
        id="invalid-1",
        name="Invalid",
        definition="",  # Empty definition
        evidence=[],
        proposed_maturity=KnowledgeMaturity.UNKNOWN,
        proposed_confidence=0.5,
    )

    governed = service.submit_candidate(invalid_candidate)

    # Should be rejected
    assert governed.concept.status == ConceptStatus.REJECTED
    assert governed.validation_result is not None
    assert governed.validation_result["is_valid"] is False
    assert len(governed.validation_result["errors"]) > 0


def test_evidence_scoring_in_pipeline():
    """Evidence scoring should be part of the governance pipeline."""
    service = DefaultKnowledgeGovernanceService()

    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="Test definition",
        evidence=[
            Evidence(
                id="ev-1",
                source="High Quality Source",
                source_type=SourceType.RESEARCH,
                claim="Test claim",
                retrieved_at=datetime.utcnow(),
                quality_score=0.9,  # High quality
            ),
        ],
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.8,
    )

    governed = service.submit_candidate(candidate)

    # Concept should reflect the evidence quality
    assert governed.concept.knowledge_confidence > 0.0


def test_conflict_detection_in_pipeline():
    """Conflict detection should be part of the governance pipeline."""
    service = DefaultKnowledgeGovernanceService()

    # Submit first concept
    candidate1 = CandidateKnowledge(
        id="test-1",
        name="CTR",
        definition="Click-through rate is click ratio",
        evidence=[
            Evidence(
                id="ev-1",
                source="Test",
                source_type=SourceType.RESEARCH,
                claim="CTR definition",
                retrieved_at=datetime.utcnow(),
                quality_score=0.8,
            )
        ],
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.8,
    )

    governed1 = service.submit_candidate(candidate1)

    # Submit conflicting concept
    candidate2 = CandidateKnowledge(
        id="test-2",
        name="CTR",
        definition="Click-through rate is conversion ratio",  # Conflicting
        evidence=[
            Evidence(
                id="ev-2",
                source="Test",
                source_type=SourceType.EXTERNAL_SOURCE,
                claim="Wrong CTR definition",
                retrieved_at=datetime.utcnow(),
                quality_score=0.5,
            )
        ],
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.6,
    )

    governed2 = service.submit_candidate(candidate2)

    # Second concept should have conflicts detected
    assert len(governed2.conflicts) > 0 or governed2.concept.status == ConceptStatus.REJECTED


def test_version_creation_in_pipeline():
    """Version creation should be part of the governance pipeline."""
    service = DefaultKnowledgeGovernanceService()

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

    # Should have created a version
    assert len(governed.versions) == 1
    version = governed.versions[0]

    # Version should have required fields
    assert version.version == 1
    assert version.concept_id == governed.concept.id
    assert version.definition == candidate.definition
    assert version.reason
    assert version.created_at


def test_maturity_update_in_pipeline():
    """Maturity update should be part of the governance pipeline."""
    service = DefaultKnowledgeGovernanceService()

    # Candidate with multiple evidence sources
    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="Test definition",
        evidence=[
            Evidence(
                id="ev-1",
                source="Research",
                source_type=SourceType.RESEARCH,
                claim="Evidence 1",
                retrieved_at=datetime.utcnow(),
                quality_score=0.8,
            ),
            Evidence(
                id="ev-2",
                source="Academy",
                source_type=SourceType.ACADEMY,
                claim="Evidence 2",
                retrieved_at=datetime.utcnow(),
                quality_score=0.85,
            ),
        ],
        proposed_maturity=KnowledgeMaturity.DEFINITION,  # Start with level 1
        proposed_confidence=0.8,
    )

    governed = service.submit_candidate(candidate)

    # Maturity should be updated based on evidence
    assert governed.concept.knowledge_maturity.value >= KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES.value


def test_governance_audit_trail():
    """Governance decisions should be traceable via audit trail."""
    service = DefaultKnowledgeGovernanceService()

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

    governed = service.submit_candidate(candidate, actor="test_user")

    # Get governance history
    history = service.get_governance_history(governed.concept.id)

    # Should have audit trail
    assert len(history) > 0

    event = history[0]
    assert event.candidate_id == candidate.id
    assert event.action == "published"
    assert event.actor == "test_user"
    assert event.reason
    assert event.timestamp


def test_governance_service_is_entry_point():
    """GovernanceService should be the only entry point to governed knowledge."""
    service = DefaultKnowledgeGovernanceService()

    # All access should go through service methods
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

    # Submit through service
    governed = service.submit_candidate(candidate)

    # Retrieve through service
    retrieved = service.get_governed_knowledge(governed.concept.id)

    assert retrieved is not None
    assert retrieved.concept.id == governed.concept.id

    # List through service
    all_governed = service.list_governed_knowledge()
    assert len(all_governed) > 0
