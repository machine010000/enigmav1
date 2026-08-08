import pytest

from app.ai.master_brain import (
    BrainEventType,
    MasterBrain,
    MasterBrainStateMachine,
    Planner,
    State,
)
from app.intelligence import ReasoningSession


class FakePlanner(Planner):
    def build_execution_plan(self, context):
        return {
            "goal": context.goal,
            "steps": ["gather evidence", "summarize findings"],
            "planner_requested": True,
        }


class FakeIntelligenceEngine:
    def build_reasoning_session(self, goal: str, **kwargs):
        return ReasoningSession(
            goal=goal,
            academy={"topic": "market trends", "guidance": "use evidence"},
            memory={"episodes": [{"id": "ep-1", "summary": "prior run"}], "similar_episodes": []},
            knowledge={"entities": [{"entity": "smart watch", "fact": "wearables market is growing"}]},
        )


def test_state_machine_transitions():
    machine = MasterBrainStateMachine()

    assert machine.current_state == State.RECEIVE_GOAL

    machine.advance()
    assert machine.current_state == State.UNDERSTAND_USER

    machine.advance()
    assert machine.current_state == State.IDENTIFY_SCENARIO

    machine.advance()
    assert machine.current_state == State.GENERATE_JOURNEY

    machine.advance()
    assert machine.current_state == State.RECALL_MEMORY

    machine.advance()
    assert machine.current_state == State.READ_ACADEMY

    machine.advance()
    assert machine.current_state == State.READ_KNOWLEDGE

    machine.advance()
    assert machine.current_state == State.GENERATE_HYPOTHESES

    machine.advance()
    assert machine.current_state == State.GAP_ANALYSIS

    machine.advance()
    assert machine.current_state == State.PLAN_EXECUTION

    machine.advance()
    assert machine.current_state == State.WAIT_FOR_RESULTS

    machine.advance()
    assert machine.current_state == State.UPDATE_DECISION

    machine.advance()
    assert machine.current_state == State.FINISHED


def test_reasoning_session_is_created_with_expected_fields():
    context = ReasoningSession(goal="Launch a smart watch", product={"name": "Smart Watch"}, user={"role": "founder"})

    assert context.goal == "Launch a smart watch"
    assert context.product["name"] == "Smart Watch"
    assert context.user["role"] == "founder"


def test_master_brain_builds_planner_request_from_interfaces():
    brain = MasterBrain(
        planner=FakePlanner(),
        intelligence_engine=FakeIntelligenceEngine(),
    )

    context = brain.intelligence_engine.build_reasoning_session(goal="Launch a smart watch")
    plan = brain.build_execution_plan(context)

    assert plan["planner_requested"] is True
    assert plan["goal"] == context.goal
    assert plan["steps"][0] == "gather evidence"
    assert brain.state_machine.current_state == State.PLAN_EXECUTION
    assert brain.event_bus.last_event().event_type == BrainEventType.PLAN_CREATED


def test_master_brain_event_bus_records_transitions():
    brain = MasterBrain(planner=FakePlanner(), intelligence_engine=FakeIntelligenceEngine())

    context = brain.intelligence_engine.build_reasoning_session(goal="Launch a smart watch")
    brain.recall_memory(context)
    brain.read_academy("market trends")
    brain.read_knowledge(context)

    assert brain.state_machine.current_state == State.READ_KNOWLEDGE
    event_types = [event.event_type for event in brain.event_bus.all_events()]
    assert event_types == [
        BrainEventType.MEMORY_RECALLED,
        BrainEventType.ACADEMY_READ,
        BrainEventType.KNOWLEDGE_READ,
    ]
