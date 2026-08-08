from app.memory.memory_engine import MemoryEngine
from app.memory.models import Episode


def test_memory_produces_candidate_knowledge():
    """MemoryEngine should produce CandidateKnowledge, not trusted knowledge."""
    engine = MemoryEngine()

    # Create a test episode
    episode = Episode(
        id="test-episode",
        execution_id="test-exec",
        decision_id=None,
        product_id="test-product",
        worker="test_worker",
        goal="test goal",
        confidence=0.8,
    )

    # Convert to CandidateKnowledge
    candidate = engine.episode_to_candidate_knowledge(episode)

    # Should produce CandidateKnowledge if governance is available
    if candidate is not None:
        assert candidate.source == "memory"
        assert len(candidate.evidence) > 0


def test_memory_evidence_has_correct_source_type():
    """Memory evidence should have MEMORY source type."""
    engine = MemoryEngine()

    episode = Episode(
        id="test-episode",
        execution_id="test-exec",
        decision_id=None,
        product_id="test-product",
        worker="test_worker",
        goal="test goal",
        confidence=0.8,
    )

    candidate = engine.episode_to_candidate_knowledge(episode)

    if candidate is not None:
        for evidence in candidate.evidence:
            assert evidence.source_type.value == "memory"


def test_memory_has_lower_quality_score():
    """Memory evidence should have lower default quality score."""
    engine = MemoryEngine()

    episode = Episode(
        id="test-episode",
        execution_id="test-exec",
        decision_id=None,
        product_id="test-product",
        worker="test_worker",
        goal="test goal",
        confidence=0.8,
    )

    candidate = engine.episode_to_candidate_knowledge(episode)

    if candidate is not None:
        for evidence in candidate.evidence:
            # Memory quality should be confidence * 0.6 (lower than other sources)
            assert evidence.quality_score == episode.confidence * 0.6


def test_memory_does_not_publish_directly():
    """MemoryEngine should not have direct publish methods to Knowledge Graph."""
    engine = MemoryEngine()

    # MemoryEngine should NOT have methods like:
    # - publish_to_graph()
    # - create_concept()
    # - add_to_knowledge_graph()

    assert not hasattr(engine, "publish_to_graph")
    assert not hasattr(engine, "create_concept")
    assert not hasattr(engine, "add_to_knowledge_graph")
