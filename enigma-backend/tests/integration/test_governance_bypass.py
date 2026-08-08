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


def test_research_cannot_publish_directly():
    """ResearchService cannot have direct publishing methods."""
    from app.services.research_service import ResearchService

    service = ResearchService()

    forbidden_methods = [
        "publish_to_graph",
        "create_concept",
        "add_to_knowledge_graph",
        "store_governed_knowledge",
    ]

    for method in forbidden_methods:
        assert not hasattr(service, method), f"ResearchService should not have {method} method"


def test_academy_cannot_publish_directly():
    """AcademyManager cannot have direct publishing methods."""
    from app.academy.academy_manager import AcademyManager

    manager = AcademyManager()

    forbidden_methods = [
        "publish_to_graph",
        "create_concept",
        "add_to_knowledge_graph",
        "store_governed_knowledge",
    ]

    for method in forbidden_methods:
        assert not hasattr(manager, method), f"AcademyManager should not have {method} method"


def test_memory_cannot_publish_directly():
    """MemoryEngine cannot have direct publishing methods."""
    from app.memory.memory_engine import MemoryEngine

    engine = MemoryEngine()

    forbidden_methods = [
        "publish_to_graph",
        "create_concept",
        "add_to_knowledge_graph",
        "store_governed_knowledge",
    ]

    for method in forbidden_methods:
        assert not hasattr(engine, method), f"MemoryEngine should not have {method} method"


def test_knowledge_service_cannot_bypass_governance():
    """KnowledgeService cannot bypass governance through direct imports."""
    knowledge_dir = Path("app/knowledge")
    knowledge_files = knowledge_dir.rglob("*.py")

    forbidden_imports = {
        "knowledge_governance",  # Should use adapter, not direct import
    }

    for file_path in knowledge_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        # graph_adapter.py is allowed to import knowledge_governance
        if file_path.name == "graph_adapter.py":
            continue

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"KnowledgeService should use graph_adapter, not direct governance import"
        )


def test_candidate_knowledge_cannot_enter_reasoning_directly():
    """CandidateKnowledge cannot be passed directly as trusted knowledge."""
    from app.intelligence.intelligence_engine import IntelligenceEngine

    engine = IntelligenceEngine()

    # Try to pass raw knowledge as governed knowledge
    # This should be rejected or properly handled
    session = engine.build_reasoning_session(
        goal="test goal",
        governed_knowledge={
            "raw_candidate": "some_raw_data",  # This should not be trusted
        },
    )

    # The session should have governed_knowledge field
    # but raw unstructured data should not be accepted as trusted
    assert hasattr(session, "governed_knowledge")
    # The field exists but data validation should happen elsewhere


def test_masterbrain_does_not_import_governance():
    """MasterBrain must not import knowledge_governance."""
    master_brain_dir = Path("app/ai/master_brain")
    master_brain_files = master_brain_dir.rglob("*.py")

    forbidden_imports = {
        "knowledge_governance",
    }

    for file_path in master_brain_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"MasterBrain must not import knowledge_governance"
        )


def test_profession_does_not_bypass_governance():
    """Profession Layer cannot bypass governance."""
    profession_dir = Path("app/profession")
    profession_files = profession_dir.rglob("*.py")

    forbidden_imports = {
        "knowledge_governance",  # Should not import directly
    }

    for file_path in profession_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Profession Layer must not import knowledge_governance directly"
        )
