import pytest

from app.intelligence.reasoning_session import ReasoningSession


def test_reasoning_session_is_immutable_and_returns_new_instances():
    session = ReasoningSession(goal="Launch a product", scenario="Own Brand")

    with pytest.raises((AttributeError, TypeError)):
        session.goal = "Changed"

    updated = session.with_decision({"decision": "launch"})
    planned = updated.with_plan({"steps": ["execute"]})

    assert session is not updated
    assert updated is not planned
    assert updated.decision == {"decision": "launch"}
    assert planned.execution_plan == {"steps": ["execute"]}
    assert session.goal == "Launch a product"
