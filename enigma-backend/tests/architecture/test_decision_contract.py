from app.models.decision import Decision


def test_decision_contract_contains_required_fields():
    decision = Decision(goal="demo")
    required_fields = {
        "evidence",
        "confidence",
        "assumptions",
        "risks",
        "execution_strategy",
    }

    for field in required_fields:
        assert hasattr(decision, field), f"Decision is missing required field: {field}"
