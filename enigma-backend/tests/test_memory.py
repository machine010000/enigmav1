"""
Tests for the ExecutionContext memory subsystem (TASK-012.3 — Context Audit).

The unified memory model lives on ExecutionContext:
  context.memory   — mutable dict scratch-space (recall/remember)
  context.history  — list of WorkerResult summaries
  context.knowledge — list of MasterKnowledge entries

All memory access goes through ExecutionContext.recall / ExecutionContext.remember.
There are no legacy short_term_memory / working_memory / long_term_memory fields.
"""
from __future__ import annotations

from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus


# --------------------------------------------------------------------------- #
# recall / remember
# --------------------------------------------------------------------------- #

def test_recall_returns_stored_value():
    ctx = ExecutionContext()
    ctx.remember("foo", "bar")
    assert ctx.recall("foo") == "bar"


def test_recall_returns_default_for_missing_key():
    ctx = ExecutionContext()
    assert ctx.recall("missing") is None
    assert ctx.recall("missing", "fallback") == "fallback"


def test_remember_overwrites_existing_value():
    ctx = ExecutionContext()
    ctx.remember("count", 1)
    ctx.remember("count", 2)
    assert ctx.recall("count") == 2


def test_memory_is_independent_per_context():
    ctx_a = ExecutionContext()
    ctx_b = ExecutionContext()
    ctx_a.remember("shared", "A")
    assert ctx_b.recall("shared") is None
    assert ctx_a.recall("shared") == "A"


def test_memory_accepts_complex_types():
    ctx = ExecutionContext()
    ctx.remember("payload", {"nested": [1, 2, 3], "flag": True})
    assert ctx.recall("payload")["nested"] == [1, 2, 3]
    assert ctx.recall("payload")["flag"] is True


# --------------------------------------------------------------------------- #
# history
# --------------------------------------------------------------------------- #

def test_add_history_appends_worker_result():
    ctx = ExecutionContext()
    result = WorkerResult(
        worker_name="test_worker",
        status=WorkerStatus.SUCCESS,
        confidence=0.9,
        result={"key": "value"},
    )
    ctx.add_history(result)
    assert len(ctx.history) == 1
    assert ctx.history[0]["worker_name"] == "test_worker"
    assert ctx.history[0]["status"] == "success"
    assert ctx.history[0]["confidence"] == 0.9


def test_add_history_appends_multiple():
    ctx = ExecutionContext()
    for i in range(3):
        r = WorkerResult(worker_name=f"w{i}", status=WorkerStatus.SUCCESS, confidence=0.5)
        ctx.add_history(r)
    assert len(ctx.history) == 3


def test_add_history_preserves_failed_status():
    ctx = ExecutionContext()
    result = WorkerResult(
        worker_name="failing",
        status=WorkerStatus.FAILED,
        error="boom",
        confidence=0.0,
    )
    ctx.add_history(result)
    assert ctx.history[0]["status"] == "failed"
    assert ctx.history[0]["confidence"] == 0.0


# --------------------------------------------------------------------------- #
# knowledge
# --------------------------------------------------------------------------- #

def test_get_knowledge_filters_by_category():
    ctx = ExecutionContext(
        knowledge=[
            {"category": "pricing", "key": "k1", "value": "v1"},
            {"category": "audience", "key": "k2", "value": "v2"},
            {"category": "pricing", "key": "k3", "value": "v3"},
        ]
    )
    pricing = ctx.get_knowledge("pricing")
    assert len(pricing) == 2
    assert pricing[0]["key"] == "k1"
    assert pricing[1]["key"] == "k3"


def test_get_knowledge_returns_empty_for_unknown_category():
    ctx = ExecutionContext(knowledge=[{"category": "pricing", "key": "k1", "value": "v1"}])
    assert ctx.get_knowledge("unknown") == []


def test_get_knowledge_returns_empty_when_no_knowledge():
    ctx = ExecutionContext()
    assert ctx.get_knowledge("anything") == []


# --------------------------------------------------------------------------- #
# Context defaults
# --------------------------------------------------------------------------- #

def test_context_defaults_are_independent():
    ctx = ExecutionContext()
    ctx.memory["key"] = "value"
    ctx.knowledge.append({"category": "test"})
    ctx.history.append({"worker_name": "w"})

    ctx2 = ExecutionContext()
    assert ctx2.memory == {}
    assert ctx2.knowledge == []
    assert ctx2.history == []


def test_context_user_and_product_dicts():
    ctx = ExecutionContext(
        user={"id": "u1", "name": "Alice"},
        product={"id": "p1", "name": "Widget", "category": "Tech"},
    )
    assert ctx.user["name"] == "Alice"
    assert ctx.product["category"] == "Tech"
    assert ctx.product["name"] == "Widget"
