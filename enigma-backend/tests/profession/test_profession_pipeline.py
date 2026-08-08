from app.intelligence import IntelligenceEngine
from app.ai.master_brain import MasterBrain, Planner


class FakePlanner(Planner):
    def build_execution_plan(self, context):
        return {
            "goal": context.goal,
            "steps": ["execute"],
        }


def test_profession_pipeline_goal_to_session():
    """Test pipeline: Goal -> Profession -> ReasoningSession."""
    engine = IntelligenceEngine()

    # Goal
    goal = "I want to grow my social media audience"

    # Profession detection happens inside IntelligenceEngine
    session = engine.build_reasoning_session(goal=goal)

    # Verify profession was loaded
    assert session.goal == goal
    assert session.profession is not None
    assert "profession" in session.profession


def test_profession_pipeline_session_to_masterbrain():
    """Test pipeline: ReasoningSession -> MasterBrain."""
    engine = IntelligenceEngine()
    brain = MasterBrain(planner=FakePlanner(), intelligence_engine=engine)

    session = engine.build_reasoning_session(
        goal="I want to improve my marketing campaign"
    )

    # MasterBrain should accept the session with profession data
    plan = brain.build_execution_plan(session)

    assert plan is not None
    assert plan["goal"] == session.goal


def test_profession_pipeline_masterbrain_uses_session_only():
    """MasterBrain should use ReasoningSession without knowing profession source."""
    engine = IntelligenceEngine()
    brain = MasterBrain(planner=FakePlanner(), intelligence_engine=engine)

    # Build session with profession
    session = engine.build_reasoning_session(
        goal="I want to do marketing and social selling"
    )

    # MasterBrain should work with the session
    # It doesn't need to know that profession data came from Profession Layer
    plan = brain.build_execution_plan(session)

    assert plan is not None
    # The plan should be based on the session, which contains profession knowledge
    assert session.profession is not None


def test_profession_pipeline_full_flow():
    """Test full pipeline: Goal -> Profession -> Session -> MasterBrain -> Decision -> Planner."""
    engine = IntelligenceEngine()
    brain = MasterBrain(planner=FakePlanner(), intelligence_engine=engine)

    # Goal
    goal = "I want to increase my social media engagement"

    # Profession Layer (integrated in IntelligenceEngine)
    session = engine.build_reasoning_session(goal=goal)

    # Verify profession was loaded
    assert session.profession is not None
    assert session.profession["profession"]["name"] == "Marketing & Social Selling"

    # MasterBrain
    plan = brain.build_execution_plan(session)

    # Planner (via MasterBrain)
    assert plan is not None
    assert plan["goal"] == goal


def test_profession_does_not_break_existing_flow():
    """Profession Layer should not break existing cognitive flow."""
    engine = IntelligenceEngine()

    # Test with marketing goal (should have profession)
    marketing_session = engine.build_reasoning_session(
        goal="I want to do marketing"
    )
    assert marketing_session.goal == "I want to do marketing"
    assert marketing_session.scenario  # Should still have scenario
    assert marketing_session.confidence is not None  # Should still have confidence

    # Test with non-marketing goal (should not have profession)
    other_session = engine.build_reasoning_session(
        goal="I want to launch a product"
    )
    assert other_session.goal == "I want to launch a product"
    assert other_session.scenario  # Should still have scenario
    assert other_session.confidence is not None  # Should still have confidence
