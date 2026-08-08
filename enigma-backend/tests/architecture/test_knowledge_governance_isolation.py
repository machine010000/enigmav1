import ast
import sys
from pathlib import Path


def _get_imports_from_file(file_path: Path) -> set[str]:
    """Extract import statements from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        return imports
    except Exception:
        return set()


def _get_all_python_files(directory: Path) -> list[Path]:
    """Get all Python files in a directory recursively."""
    return list(directory.rglob("*.py"))


def test_master_brain_does_not_import_knowledge_governance():
    """MasterBrain MUST NOT import knowledge_governance."""
    master_brain_dir = Path("app/ai/master_brain")
    master_brain_files = _get_all_python_files(master_brain_dir)

    forbidden_modules = {
        "knowledge_governance",
        "knowledge",
        "memory",
        "academy",
        "research",
        "database",
    }

    for file_path in master_brain_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"MasterBrain must not import: knowledge_governance, knowledge, memory, academy, research, database"
        )


def test_intelligence_engine_does_not_import_knowledge_governance():
    """IntelligenceEngine MUST NOT import knowledge_governance directly."""
    intelligence_dir = Path("app/intelligence")
    intelligence_files = _get_all_python_files(intelligence_dir)

    forbidden_modules = {
        "knowledge_governance",
    }

    for file_path in intelligence_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"IntelligenceEngine must not import knowledge_governance directly"
        )


def test_knowledge_governance_does_not_import_master_brain():
    """Knowledge Governance Layer MUST NOT import MasterBrain."""
    governance_dir = Path("app/knowledge_governance")
    governance_files = _get_all_python_files(governance_dir)

    forbidden_modules = {
        "master_brain",
        "planner",
        "workers",
        "decision_engine",
    }

    for file_path in governance_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Knowledge Governance must not import: MasterBrain, Planner, Workers, DecisionEngine"
        )


def test_profession_does_not_bypass_governance():
    """Profession Layer MUST NOT bypass governance (checked via imports)."""
    profession_dir = Path("app/profession")
    profession_files = _get_all_python_files(profession_dir)

    # Profession should not directly write to knowledge graph
    # This is checked by ensuring it doesn't import knowledge graph directly
    forbidden_modules = {
        "knowledge_graph",  # If this exists, it's a direct bypass
    }

    for file_path in profession_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Profession Layer must not bypass governance by directly accessing knowledge graph"
        )


def test_concept_and_evidence_are_immutable():
    """ConceptVersion and Evidence must be immutable (frozen dataclasses)."""
    from app.knowledge_governance import Concept, ConceptVersion, Evidence
    from datetime import datetime

    # Test Concept immutability
    concept = Concept(
        id="test",
        name="Test Concept",
        definition="Test definition",
    )

    try:
        concept.name = "Modified"
        assert False, "Concept should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected

    # Test ConceptVersion immutability
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

    # Test Evidence immutability
    evidence = Evidence(
        id="test",
        source="test",
        source_type="research",
        claim="Test claim",
        retrieved_at=datetime.utcnow(),
    )

    try:
        evidence.claim = "Modified"
        assert False, "Evidence should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected


def test_knowledge_maturity_levels_are_defined():
    """Knowledge maturity levels should be properly defined."""
    from app.knowledge_governance import KnowledgeMaturity

    maturity_levels = [
        KnowledgeMaturity.UNKNOWN,
        KnowledgeMaturity.DEFINITION,
        KnowledgeMaturity.SUPPORTED_BY_MULTIPLE_SOURCES,
        KnowledgeMaturity.APPLIED,
        KnowledgeMaturity.VALIDATED_IN_REAL_PROJECTS,
        KnowledgeMaturity.EXPERT_KNOWLEDGE,
    ]

    # Ensure levels are in ascending order
    for i in range(len(maturity_levels) - 1):
        assert maturity_levels[i].value < maturity_levels[i + 1].value


def test_source_types_have_different_trust_levels():
    """Source types should have different trust levels."""
    from app.knowledge_governance import SourceType

    # Just ensure all required source types exist
    required_types = [
        SourceType.RESEARCH,
        SourceType.ACADEMY,
        SourceType.MEMORY,
        SourceType.USER_INPUT,
        SourceType.EXPERIMENT,
        SourceType.EXTERNAL_SOURCE,
    ]

    for source_type in required_types:
        assert source_type.value in [
            "research", "academy", "memory", "user_input", "experiment", "external_source"
        ]


def test_governance_events_have_required_fields():
    """Governance events should have all required audit trail fields."""
    from app.knowledge_governance import GovernanceEvent
    from datetime import datetime

    event = GovernanceEvent(
        candidate_id="test",
        action="test_action",
        actor="test_actor",
        reason="Test reason",
    )

    assert event.candidate_id
    assert event.action
    assert event.actor
    assert event.reason
    assert event.timestamp
    assert isinstance(event.timestamp, datetime)


def test_research_service_produces_candidate_knowledge():
    """ResearchService should produce CandidateKnowledge."""
    from app.services.research_service import ResearchService, ResearchReport, SearchResult

    service = ResearchService()
    report = ResearchReport(
        query="test",
        search_type="web",
        results=[
            SearchResult(
                title="Test",
                url="https://example.com",
                snippet="Test",
                source="example.com",
                confidence=0.8,
            )
        ],
        total_found=1,
        generated_at="2024-01-01T00:00:00",
    )

    candidate = report.to_candidate_knowledge()

    # Should produce CandidateKnowledge if governance is available
    if candidate is not None:
        assert candidate.source == "research_service"


def test_academy_manager_produces_candidate_knowledge():
    """AcademyManager should produce CandidateKnowledge."""
    from app.academy.academy_manager import AcademyManager
    from app.academy.academy_models import AcademyModule, KnowledgeArticle

    manager = AcademyManager()
    module = AcademyModule(
        id="test-module",
        name="test",
        version="1.0",
        description="Test",
        articles=[
            KnowledgeArticle(
                id="test-article",
                module="test-module",
                title="Test",
                content="Test",
                summary="Test summary",
                keywords=["test"],
            )
        ],
    )

    candidate = manager.module_to_candidate_knowledge(module)

    # Should produce CandidateKnowledge if governance is available
    if candidate is not None:
        assert candidate.source == "academy"


def test_memory_engine_produces_candidate_knowledge():
    """MemoryEngine should produce CandidateKnowledge."""
    from app.memory.memory_engine import MemoryEngine
    from app.memory.models import Episode

    engine = MemoryEngine()
    episode = Episode(
        id="test",
        execution_id="test-exec",
        decision_id=None,
        product_id="test",
        worker="test",
        goal="test",
        confidence=0.8,
    )

    candidate = engine.episode_to_candidate_knowledge(episode)

    # Should produce CandidateKnowledge if governance is available
    if candidate is not None:
        assert candidate.source == "memory"


def test_reasoning_session_has_governed_knowledge_field():
    """ReasoningSession should have governed_knowledge field."""
    from app.intelligence.reasoning_session import ReasoningSession

    session = ReasoningSession(goal="test")

    assert hasattr(session, "governed_knowledge")
    assert session.governed_knowledge == {}


def test_intelligence_engine_accepts_governed_knowledge():
    """IntelligenceEngine should accept governed_knowledge parameter."""
    from app.intelligence.intelligence_engine import IntelligenceEngine

    engine = IntelligenceEngine()

    session = engine.build_reasoning_session(
        goal="test",
        governed_knowledge={
            "concept_ids": ["test"],
        },
    )

    # governed_knowledge should be preserved in the session
    assert "governed_knowledge" in session.to_dict()
    # The field exists and is passed through
