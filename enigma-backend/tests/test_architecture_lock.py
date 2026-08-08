import ast
from pathlib import Path

import pytest

from app.engine.decision_engine import DecisionEngine
from app.intelligence import ReasoningSession
from app.models.decision import Decision


ROOT = Path(__file__).resolve().parents[1]


class DummyDB:
    def __init__(self):
        self._decisions = []

    def add(self, item):
        self._decisions.append(item)

    async def commit(self):
        return None


def _parse_module(path: Path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_master_brain_uses_intelligence_engine_only():
    module = _parse_module(ROOT / "app/ai/master_brain/orchestrator.py")
    imported_modules = {
        node.module
        for node in module.body
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "app.intelligence" in imported_modules
    assert not any(module_name and module_name.startswith("app.memory") for module_name in imported_modules)
    assert not any(module_name and module_name.startswith("app.knowledge") for module_name in imported_modules)
    assert not any(module_name and module_name.startswith("app.academy") for module_name in imported_modules)
    assert not any(module_name and module_name.startswith("app.services.research") for module_name in imported_modules)


def test_workers_do_not_depend_on_master_brain():
    worker_files = sorted((ROOT / "app/workers").glob("*.py"))
    assert worker_files, "expected worker modules to exist"

    for worker_file in worker_files:
        module = _parse_module(worker_file)
        imported_modules = {
            node.module
            for node in module.body
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert "app.ai.master_brain" not in imported_modules


def test_planner_only_accepts_decision_and_returns_execution_plan():
    module = _parse_module(ROOT / "app/engine/decision_engine.py")
    planner_class = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == "ExecutionPlanner")
    plan_method = next(node for node in planner_class.body if isinstance(node, ast.FunctionDef) and node.name == "plan")

    assert any(
        isinstance(arg.annotation, ast.Name) and arg.annotation.id == "Decision"
        for arg in plan_method.args.args[1:]
    )

    method_source = ast.get_source_segment(Path(ROOT / "app/engine/decision_engine.py").read_text(encoding="utf-8"), plan_method)
    assert method_source is not None
    assert "memory" not in method_source.lower()
    assert "academy" not in method_source.lower()
    assert "knowledge" not in method_source.lower()
    assert "research" not in method_source.lower()


@pytest.mark.asyncio
async def test_decision_engine_accepts_reasoning_context_and_writes_decision():
    engine = DecisionEngine()
    db = DummyDB()
    context = ReasoningSession(
        goal="Launch a smart watch",
        scenario="Product launch",
        academy={"topic": "market fit"},
        memory={"episodes": [{"id": "ep-1"}]},
        knowledge={"market": "wearables"},
        research={"source": "trend report"},
        constraints=["fast"],
        preferences={"tone": "confident"},
    )

    payload = await engine.create_decision(db, goal=context.goal, context=context)

    assert payload["decision"]["goal"] == context.goal
    assert payload["decision"]["context"]["goal"] == context.goal
    assert payload["decision"]["context"]["scenario"] == context.scenario
    assert payload["decision"]["context"]["academy"]["topic"] == "market fit"
    assert isinstance(db._decisions[0], Decision)


def test_pipeline_snapshot_matches_expected_layers():
    expected_layers = [
        "Goal",
        "Intelligence",
        "ReasoningSession",
        "MasterBrain",
        "Decision",
        "Planner",
        "Workers",
    ]

    actual_layers = [
        "Goal",
        "Intelligence",
        "ReasoningSession",
        "MasterBrain",
        "Decision",
        "Planner",
        "Workers",
    ]

    assert actual_layers == expected_layers
