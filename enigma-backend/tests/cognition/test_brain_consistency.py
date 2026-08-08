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


def test_same_knowledge_context_and_goal_produce_same_decision_shape():
    engine = DecisionEngine(planner=FakePlanner(), execution_engine=FakeExecutionEngine())

    first = __import__("asyncio").run(
        engine.create_decision(
            db=FakeDB(),
            goal="Launch",
            context={"goal": "Launch", "knowledge": {"concepts": ["market"]}, "context": {"goal": "Launch"}},
        )
    )
    second = __import__("asyncio").run(
        engine.create_decision(
            db=FakeDB(),
            goal="Launch",
            context={"goal": "Launch", "knowledge": {"concepts": ["market"]}, "context": {"goal": "Launch"}},
        )
    )

    assert first["decision"]["selected_capability"] == second["decision"]["selected_capability"]
    assert first["decision"]["assumptions"] == second["decision"]["assumptions"]
