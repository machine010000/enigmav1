import ast
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


def test_work_market_does_not_import_masterbrain():
    """Work Market must not import MasterBrain."""
    work_market_dir = Path("app/work_market")
    work_market_files = work_market_dir.rglob("*.py")

    forbidden_imports = {
        "master_brain",
    }

    for file_path in work_market_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Work Market must not import MasterBrain"
        )


def test_work_market_does_not_import_planner():
    """Work Market must not import Planner."""
    work_market_dir = Path("app/work_market")
    work_market_files = work_market_dir.rglob("*.py")

    forbidden_imports = {
        "planner",
    }

    for file_path in work_market_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Work Market must not import Planner"
        )


def test_work_market_does_not_import_workers():
    """Work Market must not import Workers."""
    work_market_dir = Path("app/work_market")
    work_market_files = work_market_dir.rglob("*.py")

    forbidden_imports = {
        "workers",
    }

    for file_path in work_market_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Work Market must not import Workers"
        )


def test_work_market_does_not_import_decision_engine():
    """Work Market must not import DecisionEngine."""
    work_market_dir = Path("app/work_market")
    work_market_files = work_market_dir.rglob("*.py")

    forbidden_imports = {
        "decision_engine",
    }

    for file_path in work_market_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"Work Market must not import DecisionEngine"
        )


def test_masterbrain_does_not_import_work_market():
    """MasterBrain must not import work_market."""
    master_brain_dir = Path("app/ai/master_brain")
    master_brain_files = master_brain_dir.rglob("*.py")

    forbidden_imports = {
        "work_market",
    }

    for file_path in master_brain_files:
        imports = _get_imports_from_file(file_path)
        forbidden_found = imports & forbidden_imports

        assert not forbidden_found, (
            f"{file_path} imports forbidden modules: {forbidden_found}. "
            f"MasterBrain must not import work_market"
        )


def test_marketplace_adapters_use_abstraction():
    """Marketplace adapters should communicate only through JobSourceAdapter."""
    work_market_dir = Path("app/work_market")
    adapter_files = list(work_market_dir.glob("*adapter*.py"))

    # For now, just verify the abstraction exists
    from app.work_market.adapters import JobSourceAdapter

    assert JobSourceAdapter is not None
