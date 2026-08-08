import asyncio

from app.ai.master_brain import master_brain
from app.engine.capabilities import Capability, capability_registry
from app.engine.decision_engine import DecisionEngine
from app.models.decision import Decision


class FakeDB:
    def __init__(self):
        self.added = []
        self._decisions = []

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, Decision):
            self._decisions.append(obj)

    async def execute(self, *args, **kwargs):
        class DummyResult:
            def __init__(self):
                self._rows = []

            def scalars(self):
                return self

            def all(self):
                return []

            def first(self):
                return None

            def scalar_one_or_none(self):
                return None

        return DummyResult()

    async def commit(self):
        return None

    async def rollback(self):
        return None


class FakeResult:
    def __init__(self):
        self.evidence = [{"field": "status", "value": "ok"}]
        self.confidence = 0.87
        self.result = {"status": "verified"}
        self.error = None
        self.status = type("Status", (), {"value": "success"})()


class FakePlanner:
    def plan(self, decision):
        return {
            "capability_id": "product_verification",
            "worker_name": "product_verification",
            "steps": [{"worker": "product_verification"}],
        }


class FakeExecutionEngine:
    async def execute(self, plan, context, db=None):
        return FakeResult()


def test_master_brain_decides_and_decision_engine_creates_versioned_history(monkeypatch):
    db = FakeDB()
    capability_registry._capabilities.clear()
    capability_registry._worker_capabilities.clear()
    capability_registry.register(Capability(id="product_verification", description="Verify product"), "product_verification")

    decision_engine = DecisionEngine(planner=FakePlanner(), execution_engine=FakeExecutionEngine())
    monkeypatch.setattr(master_brain, "decision_engine", decision_engine)

    result = asyncio.run(
        master_brain.decide(
            db,
            goal="Verify the product before launch",
            context={"source": "tests"},
            constraints=["fast response"],
        )
    )

    assert result["decision"]["selected_capability"] == "product_verification"
    assert result["decision"]["selected_worker"] == "product_verification"
    assert result["decision"]["version"] == 1
    assert any(isinstance(item, Decision) for item in db.added)

    execution_result = asyncio.run(
        decision_engine.execute_decision(
            db,
            decision_id=result["decision"]["decision_id"],
            context={"source": "tests"},
        )
    )

    versions = [item for item in db._decisions if getattr(item, "decision_id", None) == execution_result["decision"]["decision_id"]]
    assert len(versions) >= 2
    assert any(item.version == 2 for item in versions)
