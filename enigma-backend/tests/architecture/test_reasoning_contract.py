from app.intelligence import ReasoningSession


def test_reasoning_session_contract_is_locked():
    context = ReasoningSession()
    required_fields = {
        "goal",
        "scenario",
        "memory",
        "knowledge",
        "academy",
        "research",
        "profession",
        "assumptions",
        "risks",
        "evidence",
        "confidence",
    }

    assert required_fields.issubset(set(context.to_dict().keys()))
