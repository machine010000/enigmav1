import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _iter_python_files(root: Path, relative_dir: str):
    return sorted((root / relative_dir).rglob("*.py"))


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


@pytest.mark.parametrize(
    ("module_path", "forbidden_import"),
    [
        ("app/workers", "app.ai.master_brain"),
        ("app/workers", "app.intelligence"),
        ("app/engine", "app.memory"),
        ("app/engine", "app.academy"),
        ("app/engine", "app.knowledge"),
        ("app/ai/master_brain", "app.memory"),
        ("app/ai/master_brain", "app.academy"),
        ("app/ai/master_brain", "app.knowledge"),
        ("app/ai/master_brain", "app.services.research"),
        ("app/knowledge", "app.engine"),
        ("app/knowledge", "app.workers"),
        ("app/academy", "app.engine"),
        ("app/academy", "app.workers"),
    ],
)
def test_forbidden_dependencies_are_absent(module_path, forbidden_import):
    for path in _iter_python_files(ROOT, module_path):
        if path.name == "__init__.py":
            continue
        assert not _has_import_prefix(_collect_imports(path), forbidden_import)
