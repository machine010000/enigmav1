from app.memory.memory_engine import MemoryEngine
from app.memory.models import Episode, Pattern, Strategy


def test_memory_engine_stores_and_recalls_experience():
    engine = MemoryEngine()

    episode = Episode(
        id="ep-1",
        execution_id="exec-1",
        decision_id="decision-1",
        product_id="product-1",
        worker="product_verification",
        goal="Verify a product",
        inputs={"title": "Nike Air Max 270"},
        outputs={"category": "Sports"},
        evidence=[{"field": "category", "value": "Sports"}],
        confidence=0.91,
        execution_time=0.44,
        llm_calls=1,
        success=True,
    )
    engine.store_episode(episode)

    strategy = Strategy(
        id="strategy-1",
        name="Verify Sports Products",
        description="Use category classification for sports products",
        steps=["classify", "verify"],
        success_rate=0.9,
        usage_count=2,
    )
    engine.store_strategy(strategy)

    pattern = Pattern(
        id="pattern-1",
        category="product_verification",
        description="Sports products have high category confidence",
        trigger="sports",
        outcome="success",
        confidence=0.88,
        occurrences=2,
    )
    engine.store_pattern(pattern)

    recalled = engine.recall(goal="Verify", worker="product_verification")
    similar = engine.find_similar_episodes("Verify sports products")
    best = engine.find_best_strategy("sports")
    ranked = engine.search_patterns(category="product_verification")

    assert len(recalled) == 1
    assert similar[0].id == episode.id
    assert best is not None and best.id == strategy.id
    assert ranked[0].id == pattern.id

    metrics = engine.metrics()
    assert metrics["episode_count"] == 1
    assert metrics["pattern_count"] == 1
    assert metrics["strategy_reuse_percent"] == 100.0
