import ast
import importlib
import pkgutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _collect_module_names(package_dir: Path):
    return [
        f"app.{path.stem}"
        for path in package_dir.rglob("*.py")
        if path.name != "__init__.py"
    ]


def test_no_circular_imports():
    package_dir = ROOT / "app"
    modules = []
    for path in package_dir.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(package_dir)
        module_name = ".".join(rel.with_suffix("").parts)
        modules.append(f"app.{module_name}")

    for module_name in modules:
        module = importlib.import_module(module_name)
        assert module is not None
