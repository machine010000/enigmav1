from app.memory.models import Strategy


def test_strategy_model_supports_update_payloads():
    strategy = Strategy(
        id="strategy-1",
        name="Verify Sports Products",
        description="Use category classification",
        steps=["classify", "verify"],
        success_rate=0.8,
        usage_count=1,
    )

    payload = strategy.to_dict()
    assert payload["name"] == "Verify Sports Products"
    assert payload["steps"] == ["classify", "verify"]
