from app.intelligence import IntelligenceEngine, ReasoningSession


def test_profession_enriches_reasoning_session():
    """Profession information should be loaded into ReasoningSession."""
    engine = IntelligenceEngine()

    # Marketing goal should trigger profession detection
    session = engine.build_reasoning_session(
        goal="I want to grow my social media audience and increase engagement",
    )

    # Session should contain profession data
    assert session.profession is not None
    assert "profession" in session.profession
    assert "knowledge" in session.profession
    assert "skills" in session.profession
    assert "tasks" in session.profession
    assert "decision_patterns" in session.profession


def test_profession_data_has_correct_structure():
    """Profession data in session should have correct structure."""
    engine = IntelligenceEngine()

    session = engine.build_reasoning_session(
        goal="I want to improve my marketing campaign",
    )

    profession_data = session.profession

    # Check profession info
    assert profession_data["profession"]["id"]
    assert profession_data["profession"]["name"]
    assert profession_data["profession"]["category"]

    # Check knowledge
    assert profession_data["knowledge"]["profession_id"]
    assert isinstance(profession_data["knowledge"]["concepts"], list)

    # Check skills
    assert isinstance(profession_data["skills"], list)
    if profession_data["skills"]:
        assert profession_data["skills"][0]["id"]
        assert profession_data["skills"][0]["name"]

    # Check tasks
    assert isinstance(profession_data["tasks"], list)
    if profession_data["tasks"]:
        assert profession_data["tasks"][0]["id"]
        assert profession_data["tasks"][0]["name"]

    # Check detection confidence
    assert "detection_confidence" in profession_data
    assert isinstance(profession_data["detection_confidence"], float)


def test_non_marketing_goal_has_no_profession():
    """Non-marketing goals should not trigger profession detection."""
    engine = IntelligenceEngine()

    session = engine.build_reasoning_session(
        goal="I want to build a software application",
    )

    # Should not have profession data for non-matching goal
    # (unless we add other profession detectors later)
    assert session.profession == {} or session.profession is None


def test_profession_with_decision_pattern_in_session():
    """Decision patterns should be included in session."""
    engine = IntelligenceEngine()

    session = engine.build_reasoning_session(
        goal="I want to do marketing and social selling",
    )

    profession_data = session.profession

    if profession_data and profession_data.get("decision_patterns"):
        # Check decision pattern structure
        pattern = profession_data["decision_patterns"][0]
        assert pattern["id"]
        assert pattern["name"]
        assert pattern["condition"]
        assert pattern["action"]
        assert pattern["rationale"]


def test_session_remains_immutable_with_profession():
    """Adding profession data should not break session immutability."""
    engine = IntelligenceEngine()

    session1 = engine.build_reasoning_session(goal="Test marketing goal")

    # with_profession should return new instance
    session2 = session1.with_profession({"test": "data"})
    assert session1 is not session2
    assert session1.profession != session2.profession
