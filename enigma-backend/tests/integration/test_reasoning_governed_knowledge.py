from app.intelligence.intelligence_engine import IntelligenceEngine
from app.intelligence.reasoning_session import ReasoningSession


def test_reasoning_session_accepts_governed_knowledge():
    """ReasoningSession should accept governed knowledge as a parameter."""
    engine = IntelligenceEngine()

    # Create a session with governed knowledge
    session = engine.build_reasoning_session(
        goal="test goal",
        governed_knowledge={
            "concept_ids": ["concept-1"],
            "evidence_ids": ["evidence-1", "evidence-2"],
            "concept_version": 1,
            "knowledge_maturity": 2,
            "knowledge_confidence": 0.8,
            "knowledge_freshness": "fresh",
        },
    )

    # Session should have governed_knowledge field
    assert hasattr(session, "governed_knowledge")
    assert session.governed_knowledge is not None
    # governed_knowledge is passed through directly
    assert session.governed_knowledge == {
        "concept_ids": ["concept-1"],
        "evidence_ids": ["evidence-1", "evidence-2"],
        "concept_version": 1,
        "knowledge_maturity": 2,
        "knowledge_confidence": 0.8,
        "knowledge_freshness": "fresh",
    }


def test_reasoning_session_preserves_provenance():
    """ReasoningSession should preserve knowledge provenance."""
    engine = IntelligenceEngine()

    governed_data = {
        "concept_ids": ["concept-1", "concept-2"],
        "evidence_ids": ["ev-1", "ev-2", "ev-3"],
        "concept_version": 2,
        "knowledge_maturity": 3,
        "knowledge_confidence": 0.85,
        "knowledge_freshness": "fresh",
    }

    session = engine.build_reasoning_session(
        goal="test goal",
        governed_knowledge=governed_data,
    )

    # All provenance fields should be preserved
    assert session.governed_knowledge["concept_ids"] == governed_data["concept_ids"]
    assert session.governed_knowledge["evidence_ids"] == governed_data["evidence_ids"]
    assert session.governed_knowledge["concept_version"] == governed_data["concept_version"]
    assert session.governed_knowledge["knowledge_maturity"] == governed_data["knowledge_maturity"]
    assert session.governed_knowledge["knowledge_confidence"] == governed_data["knowledge_confidence"]
    assert session.governed_knowledge["knowledge_freshness"] == governed_data["knowledge_freshness"]


def test_reasoning_session_without_governed_knowledge():
    """ReasoningSession should work without governed knowledge (backward compatibility)."""
    engine = IntelligenceEngine()

    session = engine.build_reasoning_session(goal="test goal")

    # Should have empty governed_knowledge
    assert hasattr(session, "governed_knowledge")
    assert session.governed_knowledge == {}


def test_reasoning_session_serializes_governed_knowledge():
    """ReasoningSession should serialize governed knowledge in to_dict()."""
    engine = IntelligenceEngine()

    session = engine.build_reasoning_session(
        goal="test goal",
        governed_knowledge={
            "concept_ids": ["concept-1"],
            "evidence_ids": ["evidence-1"],
        },
    )

    session_dict = session.to_dict()

    # governed_knowledge should be in the serialized dict
    assert "governed_knowledge" in session_dict
    assert session_dict["governed_knowledge"]["concept_ids"] == ["concept-1"]
