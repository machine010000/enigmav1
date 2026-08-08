from app.memory.models import Episode


def test_episode_model_builds_expected_payload():
    episode = Episode(
        id="ep-1",
        execution_id="exec-1",
        decision_id="decision-1",
        product_id="product-1",
        worker="product_verification",
        goal="Verify the product",
        inputs={"name": "Nike"},
        outputs={"category": "Sports"},
        evidence=[{"field": "category", "value": "Sports"}],
        confidence=0.9,
        execution_time=0.3,
        llm_calls=0,
        success=True,
    )

    payload = episode.to_dict()
    assert payload["worker"] == "product_verification"
    assert payload["success"] is True
    assert payload["outputs"]["category"] == "Sports"
