from app.engine.decision_engine import DecisionEngine


class FakeDB:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    async def commit(self):
        return None


class FakePlanner:
    def plan(self, decision):
        return {"capability_id": "product_verification", "worker_name": "product_verification"}


class FakeExecutionEngine:
    async def execute(self, plan, context=None, db=None):
        return {"status": "success", "result": {}, "evidence": [], "confidence": 0.9}


def test_decisions_capture_explicit_assumptions():
    engine = DecisionEngine(planner=FakePlanner(), execution_engine=FakeExecutionEngine())
    decision_payload = __import__("asyncio").run(
        engine.create_decision(db=FakeDB(), goal="Launch", context={"goal": "Launch"})
    )

    assert decision_payload["decision"]["assumptions"]
