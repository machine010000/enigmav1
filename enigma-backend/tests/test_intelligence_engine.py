from app.intelligence import IntelligenceEngine, ContextEngine, ScenarioEngine, GapEngine, ConfidenceEngine


def test_intelligence_engine_builds_reasoning_session():
    engine = IntelligenceEngine()
    context = engine.build_reasoning_session(
        goal="Launch an affiliate marketing business",
        user={"role": "founder"},
        business={"industry": "ecommerce"},
        product={"name": "Online Coaching"},
        academy={"topics": ["affiliate", "digital marketing"]},
        memory={"past_campaigns": ["spring launch"]},
        knowledge={"market": "small business"},
    )

    assert context.goal == "Launch an affiliate marketing business"
    assert context.scenario == "Affiliate Seller"
    assert len(context.gaps) == 2
    assert len(context.opportunities) == 1
    assert isinstance(context.generated_at, type(context.generated_at))


def test_scenario_engine_detects_affiliate_seller():
    engine = ScenarioEngine()
    context = type("Ctx", (), {"goal": "Build an affiliate partnership", "scenario": None})()

    result = engine.detect(context)
    assert result == "Affiliate Seller"
    assert engine.score(context) == 1.0


def test_gap_engine_prioritizes_blocking_gaps():
    engine = GapEngine()
    context = type("Ctx", (), {"goal": "Launch a store", "scenario": "Local Store", "topics": []})()
    gaps = engine.find_gaps(context)
    prioritized = engine.prioritize(gaps)

    assert prioritized[0].blocking is True
    assert set(engine.blocking_gaps(gaps)) == {prioritized[0]}
    assert len(engine.optional_gaps(gaps)) == 1


def test_confidence_engine_estimates_context_confidence():
    engine = ConfidenceEngine()
    context = type("Ctx", (), {
        "scenario": "Own Brand",
        "gaps": ["audience"],
        "topics": ["branding"],
    })()

    estimate = engine.estimate(context)
    assert 0.0 <= estimate.score <= 1.0
    assert "scenario alignment" in estimate.rationale
    assert engine.is_confident(context, threshold=0.1)


def test_context_engine_summarizes_reasoning_context():
    engine = ContextEngine()
    context = type("Ctx", (), {
        "goal": "Grow online sales",
        "scenario": "Digital Product",
        "topics": ["ecommerce", "funnels"],
    })()

    summary = engine.summarize(context)
    text = str(summary)
    assert "Grow online sales" in text
    assert "Digital Product" in text
    assert "ecommerce" in text
