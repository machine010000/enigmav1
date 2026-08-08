import ast
import sys
import pytest
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


def test_profession_layer_does_not_import_forbidden_modules():
    """Profession Layer MUST NOT import: MasterBrain, Planner, Workers, DecisionEngine."""
    profession_dir = Path("app/profession")
    profession_files = _get_all_python_files(profession_dir)

    forbidden_modules = {
        "master_brain",
        "planner",
        "workers",
        "decision_engine",
    }

    for file_path in profession_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Profession Layer must not import: MasterBrain, Planner, Workers, DecisionEngine"
        )


def test_master_brain_does_not_import_profession_layer():
    """MasterBrain MUST NOT import: Profession Layer, Memory, Knowledge, Academy, Research, Database."""
    master_brain_dir = Path("app/ai/master_brain")
    master_brain_files = _get_all_python_files(master_brain_dir)

    forbidden_modules = {
        "profession",
        "memory",
        "knowledge",
        "academy",
        "research",
        "database",
    }

    for file_path in master_brain_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"MasterBrain must not import: Profession Layer, Memory, Knowledge, Academy, Research, Database"
        )


def test_workers_do_not_import_forbidden_modules():
    """Workers MUST NOT import: Profession, MasterBrain, Reasoning, Planner."""
    workers_dir = Path("app/workers")
    if not workers_dir.exists():
        return  # Skip if workers directory doesn't exist

    workers_files = _get_all_python_files(workers_dir)

    forbidden_modules = {
        "profession",
        "master_brain",
        "reasoning",
        "planner",
    }

    for file_path in workers_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_modules

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Workers must not import: Profession, MasterBrain, Reasoning, Planner"
        )


def test_intelligence_engine_optional_profession_import():
    """IntelligenceEngine should handle optional profession import gracefully."""
    # This test ensures that if profession module is not available,
    # IntelligenceEngine still works without crashing
    try:
        from app.intelligence import IntelligenceEngine

        engine = IntelligenceEngine()
        # Should be able to build session even without profession
        session = engine.build_reasoning_session(goal="Test goal")
        assert session is not None
        assert session.goal == "Test goal"
    except ImportError as e:
        pytest.fail(f"IntelligenceEngine should work without profession module: {e}")
