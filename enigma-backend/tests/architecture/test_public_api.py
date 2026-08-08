import asyncio

from app.ai.master_brain.orchestrator import MasterBrain
from app.engine.decision_engine import DecisionEngine
from app.intelligence.intelligence_engine import IntelligenceEngine
from app.ai.master_brain.models import Planner
from app.intelligence import ReasoningSession


def test_public_api_contracts_exist_and_are_callable():
    intelligence = IntelligenceEngine()
    brain = MasterBrain(intelligence_engine=intelligence)
    planner = Planner.__new__(Planner)

    assert hasattr(intelligence, "build_reasoning_session")
    assert callable(intelligence.build_reasoning_session)
    assert not hasattr(intelligence, "build_reasoning_context")

    assert hasattr(brain, "reason")
    assert callable(brain.reason)

    assert hasattr(brain, "decide")
    assert callable(brain.decide)

    assert hasattr(planner, "build_execution_plan")
    assert callable(planner.build_execution_plan)

    assert hasattr(DecisionEngine, "create_decision")
    assert callable(DecisionEngine.create_decision)


def test_master_brain_passes_reasoning_context_to_decision_engine_without_flattening():
    class FakeDB:
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

        async def commit(self):
            return None

    class FakePlanner:
        def build_execution_plan(self, context):
            return {"goal": context.goal}

    class FakeDecisionEngine:
        def __init__(self):
            self.received_context = None

        async def create_decision(self, db, goal, context=None, constraints=None):
            self.received_context = context
            return {"decision": {"goal": goal, "context": context}}

    fake_decision_engine = FakeDecisionEngine()
    brain = MasterBrain(planner=FakePlanner(), intelligence_engine=IntelligenceEngine())
    brain.decision_engine = fake_decision_engine

    ctx = ReasoningSession(goal="launch", scenario="test")
    asyncio.run(brain.decide(FakeDB(), goal="launch", context=ctx))

    assert fake_decision_engine.received_context is not None
    assert fake_decision_engine.received_context.goal == "launch"
