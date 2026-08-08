def test_pipeline_order_is_frozen():
    expected = [
        "Goal",
        "Intelligence",
        "ReasoningSession",
        "Master Brain",
        "Decision",
        "Planner",
        "ExecutionPlan",
        "Workers",
        "Memory Update",
    ]

    assert expected == [
        "Goal",
        "Intelligence",
        "ReasoningSession",
        "Master Brain",
        "Decision",
        "Planner",
        "ExecutionPlan",
        "Workers",
        "Memory Update",
    ]
