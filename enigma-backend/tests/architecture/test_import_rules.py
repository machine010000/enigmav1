import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _collect_imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
    return imports


def _has_import_prefix(imports, prefix: str) -> bool:
    return any(name == prefix or name.startswith(prefix + ".") for name in imports)


def test_master_brain_uses_intelligence_engine_only():
    orchestrator = ROOT / "app/ai/master_brain/orchestrator.py"
    imports = _collect_imports(orchestrator)

    assert any(name.startswith("app.intelligence") for name in imports)
    assert not _has_import_prefix(imports, "app.memory")
    assert not _has_import_prefix(imports, "app.knowledge")
    assert not _has_import_prefix(imports, "app.academy")
    assert not _has_import_prefix(imports, "app.services.research")
