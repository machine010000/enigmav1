from app.academy.academy_manager import AcademyManager
from app.academy.academy_models import AcademyModule, KnowledgeArticle


def test_academy_produces_candidate_knowledge():
    """AcademyManager should produce CandidateKnowledge, not trusted knowledge."""
    manager = AcademyManager()

    # Create a test module
    module = AcademyModule(
        id="test-module",
        name="test_module",
        version="1.0",
        description="Test module description",
        articles=[
            KnowledgeArticle(
                id="test-article",
                module="test-module",
                title="Test Article",
                content="Test content",
                summary="Test summary",
                keywords=["test"],
            )
        ],
    )

    # Convert to CandidateKnowledge
    candidate = manager.module_to_candidate_knowledge(module)

    # Should produce CandidateKnowledge if governance is available
    if candidate is not None:
        assert candidate.name == module.name
        assert candidate.source == "academy"
        assert len(candidate.evidence) > 0


def test_academy_evidence_has_correct_source_type():
    """Academy evidence should have ACADEMY source type."""
    manager = AcademyManager()

    module = AcademyModule(
        id="test-module",
        name="test_module",
        version="1.0",
        description="Test",
        articles=[
            KnowledgeArticle(
                id="test-article",
                module="test-module",
                title="Test",
                content="Test content",
                summary="Test summary",
                keywords=["test"],
            )
        ],
    )

    candidate = manager.module_to_candidate_knowledge(module)

    if candidate is not None:
        for evidence in candidate.evidence:
            assert evidence.source_type.value == "academy"


def test_academy_does_not_publish_directly():
    """AcademyManager should not have direct publish methods to Knowledge Graph."""
    manager = AcademyManager()

    # AcademyManager should NOT have methods like:
    # - publish_to_graph()
    # - create_concept()
    # - add_to_knowledge_graph()

    assert not hasattr(manager, "publish_to_graph")
    assert not hasattr(manager, "create_concept")
    assert not hasattr(manager, "add_to_knowledge_graph")
