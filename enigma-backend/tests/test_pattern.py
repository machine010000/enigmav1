from app.memory.models import Pattern


def test_pattern_model_preserves_occurrence_metadata():
    pattern = Pattern(
        id="pattern-1",
        category="product_verification",
        description="Sports products usually verify quickly",
        trigger="sports",
        outcome="success",
        confidence=0.77,
        occurrences=3,
    )

    payload = pattern.to_dict()
    assert payload["category"] == "product_verification"
    assert payload["occurrences"] == 3
