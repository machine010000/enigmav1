import asyncio

from app.engine.decision_engine import DecisionEngine
from app.ai.master_brain import MasterBrain
from app.intelligence import IntelligenceEngine, ReasoningSession


class FakePlanner:
    def build_execution_plan(self, context):
        return {
            "goal": context.goal,
            "scenario": context.scenario,
            "steps": ["plan", "execute"],
        }


class FakeExecutionEngine:
    async def execute(self, plan, context=None, db=None):
        return {
            "status": "success",
            "result": {"planned": True},
            "evidence": [{"field": "goal", "value": plan["goal"]}],
            "confidence": 0.9,
        }


class DummyDB:
    def __init__(self):
        self._decisions = []

    def add(self, item):
        self._decisions.append(item)

    async def commit(self):
        return None

    async def execute(self, *args, **kwargs):
        return None


def test_full_reasoning_pipeline_uses_reasoning_context_only():
    intelligence_engine = IntelligenceEngine()
    reasoning_context = intelligence_engine.build_reasoning_session(
        goal="Launch a smart watch",
        user={"role": "founder"},
        business={"mode": "launch"},
        product={"name": "Smart Watch"},
    )

    assert isinstance(reasoning_context, ReasoningSession)
    assert reasoning_context.goal == "Launch a smart watch"

    brain = MasterBrain(planner=FakePlanner(), intelligence_engine=intelligence_engine)
    decision_engine = DecisionEngine(planner=FakePlanner(), execution_engine=FakeExecutionEngine())

    decision_payload = asyncio.run(
        decision_engine.create_decision(
            db=DummyDB(),
            goal=reasoning_context.goal,
            context=reasoning_context.to_dict(),
        )
    )

    assert decision_payload["decision"]["goal"] == reasoning_context.goal
    assert decision_payload["decision"]["context"]["goal"] == reasoning_context.goal

    plan = FakePlanner().build_execution_plan(reasoning_context)
    assert plan["goal"] == reasoning_context.goal
    assert plan["scenario"] == reasoning_context.scenario
