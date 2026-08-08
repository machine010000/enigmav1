from app.profession import (
    Profession,
    ProfessionPack,
    ProfessionKnowledge,
    Skill,
    ProfessionTask,
    DecisionPattern,
)
from app.profession.reference_professions import create_marketing_social_selling_pack


def test_profession_pack_has_required_contract():
    """Profession Pack must contain all required fields."""
    pack = create_marketing_social_selling_pack()

    # Check profession
    assert pack.profession.id
    assert pack.profession.name
    assert pack.profession.description
    assert pack.profession.category
    assert pack.profession.version
    assert pack.profession.status

    # Check knowledge
    assert pack.knowledge.profession_id
    assert isinstance(pack.knowledge.concepts, list)
    assert isinstance(pack.knowledge.evidence_sources, list)
    assert pack.knowledge.maturity
    assert isinstance(pack.knowledge.confidence, float)

    # Check skills
    assert isinstance(pack.skills, list)
    for skill in pack.skills:
        assert skill.id
        assert skill.name
        assert skill.description

    # Check tasks
    assert isinstance(pack.tasks, list)
    for task in pack.tasks:
        assert task.id
        assert task.name
        assert task.description
        assert isinstance(task.required_skills, list)
        assert isinstance(task.required_knowledge, list)
        assert isinstance(task.expected_deliverables, list)
        assert isinstance(task.success_criteria, list)

    # Check decision patterns
    assert isinstance(pack.decision_patterns, list)
    for pattern in pack.decision_patterns:
        assert pattern.id
        assert pattern.name
        assert pattern.description
        assert pattern.condition
        assert pattern.action
        assert pattern.rationale

    # Check metadata
    assert isinstance(pack.kpis, list)
    assert isinstance(pack.deliverables, list)
    assert isinstance(pack.common_mistakes, list)
    assert isinstance(pack.best_practices, list)
    assert isinstance(pack.tools, list)


def test_profession_models_are_immutable():
    """Profession models should be immutable (frozen dataclasses)."""
    profession = Profession(
        id="test",
        name="Test Profession",
        description="Test",
        category="Test",
    )

    # Should raise error when trying to modify
    try:
        profession.name = "Modified"
        assert False, "Profession should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected


def test_profession_knowledge_has_governance_ready_fields():
    """ProfessionKnowledge should have fields ready for Knowledge Governance."""
    knowledge = ProfessionKnowledge(
        profession_id="test",
        concepts=["concept1", "concept2"],
        evidence_sources=["source1"],
        maturity="initial",
        confidence=0.8,
    )

    assert knowledge.profession_id
    assert knowledge.concepts
    assert knowledge.evidence_sources
    assert knowledge.maturity
    assert isinstance(knowledge.confidence, float)
    # Future fields: freshness, metadata are already in the contract


def test_decision_pattern_represents_thinking_not_just_knowledge():
    """DecisionPattern should represent professional thinking patterns."""
    pattern = DecisionPattern(
        id="test_pattern",
        name="Test Pattern",
        description="Test decision pattern",
        condition="IF high competition AND low authority",
        action="THEN prefer lower-competition opportunities",
        rationale="Low authority sites cannot compete for high-competition keywords",
    )

    assert pattern.condition  # The IF part
    assert pattern.action  # The THEN part
    assert pattern.rationale  # The WHY part
    assert "IF" in pattern.condition or "WHEN" in pattern.condition
    assert "THEN" in pattern.action or "SHOULD" in pattern.action


def test_tools_are_not_capabilities():
    """Tools in ProfessionPack should be software/tools, not capabilities."""
    pack = create_marketing_social_selling_pack()

    # Tools should be concrete software names
    assert "Ahrefs" in pack.tools or "Semrush" in pack.tools or "Google Search Console" in pack.tools

    # Tools are different from capabilities (which would be like "keyword_research")
    # This is a conceptual test - the architecture separates tools from capabilities
    for tool in pack.tools:
        assert isinstance(tool, str)
        assert len(tool) > 0
