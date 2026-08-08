from app.knowledge_governance import (
    Concept,
    KnowledgeMaturity,
    DefaultKnowledgeGovernanceService,
    Evidence,
    SourceType,
    KnowledgeFreshness,
    CandidateKnowledge,
)
from datetime import datetime


def test_maturity_does_not_jump_without_evidence():
    """Maturity should not increase without sufficient evidence."""
    service = DefaultKnowledgeGovernanceService()

    # Create candidate with high proposed maturity but low evidence
    from app.knowledge_governance import CandidateKnowledge

    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="Test definition",
        evidence=[],  # No evidence
        proposed_maturity=KnowledgeMaturity.EXPERT_KNOWLEDGE,  # Unrealistic
        proposed_confidence=0.9,
    )

    governed = service.submit_candidate(candidate)

    # Actual maturity should be lower than proposed due to lack of evidence
    assert governed.concept.knowledge_maturity != KnowledgeMaturity.EXPERT_KNOWLEDGE
    assert governed.concept.knowledge_maturity == KnowledgeMaturity.UNKNOWN


def test_maturity_increases_with_multiple_evidence():
    """Maturity should increase with multiple quality evidence sources."""
    service = DefaultKnowledgeGovernanceService()

    # Create candidate with multiple evidence sources
    evidence = [
        Evidence(
            id="ev-1",
            source="Research Paper",
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
    ]

    from app.knowledge_governance import CandidateKnowledge

    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="Test definition",
        evidence=evidence,
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.8,
    )

    governed = service.submit_candidate(candidate)

    # Should achieve at least level 2 with multiple sources
    assert governed.concept.knowledge_maturity.value >= KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES.value


def test_maturity_levels_are_sequential():
    """Maturity levels should progress sequentially with evidence."""
    service = DefaultKnowledgeGovernanceService()

    # Level 0: No evidence
    candidate0 = CandidateKnowledge(
        id="test-0",
        name="Test",
        definition="Test definition",
        evidence=[],
        proposed_maturity=KnowledgeMaturity.UNKNOWN,
        proposed_confidence=0.5,
    )
    governed0 = service.submit_candidate(candidate0)
    assert governed0.concept.knowledge_maturity == KnowledgeMaturity.UNKNOWN

    # Level 1: Single evidence
    evidence1 = [
        Evidence(
            id="ev-1",
            source="Test",
            source_type=SourceType.RESEARCH,
            claim="Evidence",
            retrieved_at=datetime.utcnow(),
            quality_score=0.7,
        )
    ]
    candidate1 = CandidateKnowledge(
        id="test-1",
        name="Test",
        definition="Test definition",
        evidence=evidence1,
        proposed_maturity=KnowledgeMaturity.DEFINITION,
        proposed_confidence=0.7,
    )
    governed1 = service.submit_candidate(candidate1)
    assert governed1.concept.knowledge_maturity == KnowledgeMaturity.DEFINITION

    # Level 2: Multiple evidence
    evidence2 = evidence1 + [
        Evidence(
            id="ev-2",
            source="Test2",
            source_type=SourceType.ACADEMY,
            claim="Evidence 2",
            retrieved_at=datetime.utcnow(),
            quality_score=0.7,
        )
    ]
    candidate2 = CandidateKnowledge(
        id="test-2",
        name="Test",
        definition="Test definition",
        evidence=evidence2,
        proposed_maturity=KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        proposed_confidence=0.75,
    )
    governed2 = service.submit_candidate(candidate2)
    assert governed2.concept.knowledge_maturity.value >= KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES.value


def test_maturity_requires_high_quality_evidence():
    """High maturity requires high-quality evidence."""
    service = DefaultKnowledgeGovernanceService()

    # Low quality evidence should not achieve high maturity
    low_quality_evidence = [
        Evidence(
            id="ev-1",
            source="Blog",
            source_type=SourceType.EXTERNAL_SOURCE,
            claim="Low quality claim",
            retrieved_at=datetime.utcnow(),
            quality_score=0.3,  # Low quality
        ),
        Evidence(
            id="ev-2",
            source="Forum",
            source_type=SourceType.USER_INPUT,
            claim="Another low quality claim",
            retrieved_at=datetime.utcnow(),
            quality_score=0.2,  # Low quality
        ),
    ]

    from app.knowledge_governance import CandidateKnowledge

    candidate = CandidateKnowledge(
        id="test",
        name="Test",
        definition="Test definition",
        evidence=low_quality_evidence,
        proposed_maturity=KnowledgeMaturity.EXPERT_KNOWLEDGE,  # Too ambitious
        proposed_confidence=0.9,
    )

    governed = service.submit_candidate(candidate)

    # Governance should calculate achievable maturity based on evidence
    # With low quality evidence, should not achieve expert knowledge
    # (Achievable will be lower than proposed)
    assert governed.concept.knowledge_maturity != KnowledgeMaturity.EXPERT_KNOWLEDGE
