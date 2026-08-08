"""
Tests for the EventBus and event flow (TASK-006 — Live Console).

Covers:
  - EventBus stores events in its history ring buffer
  - broadcast() pushes to connected WebSocket mock clients
  - emit_sync stores without broadcasting
  - clear() resets history and connections
  - WorkerEvent.to_dict serialises correctly
  - EventBus connected_clients count
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from app.engine.contracts import WorkerEvent
from app.engine.events import EventBus


# --------------------------------------------------------------------------- #
# WorkerEvent serialisation
# --------------------------------------------------------------------------- #

def test_worker_event_to_dict_has_required_fields():
    event = WorkerEvent(
        worker_name="test_worker",
        type="progress",
        message="working...",
        data={"step": 1},
        execution_id="exec-001",
    )
    d = event.to_dict()
    assert d["worker_name"] == "test_worker"
    assert d["type"] == "progress"
    assert d["message"] == "working..."
    assert d["data"] == {"step": 1}
    assert d["execution_id"] == "exec-001"
    assert "timestamp" in d


def test_worker_event_timestamp_is_isoformat():
    event = WorkerEvent(worker_name="w", type="progress", message="m")
    d = event.to_dict()
    parsed = datetime.fromisoformat(d["timestamp"])
    assert parsed is not None


def test_worker_event_default_fields():
    event = WorkerEvent(worker_name="w", type="started", message="hello")
    assert event.data == {}
    assert event.execution_id == ""


# --------------------------------------------------------------------------- #
# EventBus history storage
# --------------------------------------------------------------------------- #

@pytest.fixture
def fresh_bus():
    bus = EventBus(history_size=10)
    yield bus
    bus.clear()


def test_emit_sync_stores_event(fresh_bus):
    event = WorkerEvent(worker_name="w", type="progress", message="m")
    fresh_bus.emit_sync(event)
    history = fresh_bus.get_history()
    assert len(history) == 1
    assert history[0]["worker_name"] == "w"


async def test_broadcast_stores_and_sends(fresh_bus):
    received = []

    class FakeWS:
        async def send_json(self, data):
            received.append(data)

    fresh_bus.connections.connect(FakeWS())
    event = WorkerEvent(worker_name="w", type="finished", message="done")

    await fresh_bus.broadcast(event)

    assert len(fresh_bus._history) == 1
    assert len(received) == 1
    assert received[0]["type"] == "finished"


async def test_broadcast_to_disconnects_dead_client(fresh_bus):
    class DeadWS:
        async def send_json(self, data):
            raise Exception("connection broken")

    dead = DeadWS()
    fresh_bus.connections.connect(dead)
    event = WorkerEvent(worker_name="w", type="progress", message="m")

    await fresh_bus.broadcast(event)

    assert fresh_bus.connected_clients == 0


def test_history_replays_recent_first(fresh_bus):
    for i in range(3):
        fresh_bus.emit_sync(WorkerEvent(worker_name="w", type="progress", message=f"msg{i}"))
    history = fresh_bus.get_history(limit=10)
    assert len(history) == 3
    assert history[0]["message"] == "msg2"
    assert history[2]["message"] == "msg0"


def test_history_respects_maxlen(fresh_bus):
    for i in range(20):
        fresh_bus.emit_sync(WorkerEvent(worker_name="w", type="progress", message=f"msg{i}"))
    history = fresh_bus.get_history(limit=100)
    assert len(history) <= 10


def test_connected_clients_count(fresh_bus):
    assert fresh_bus.connected_clients == 0

    class FakeWS:
        async def send_json(self, data):
            pass

    ws1 = FakeWS()
    ws2 = FakeWS()
    fresh_bus.connections.connect(ws1)
    assert fresh_bus.connected_clients == 1

    fresh_bus.connections.connect(ws2)
    assert fresh_bus.connected_clients == 2

    fresh_bus.connections.disconnect(ws1)
    assert fresh_bus.connected_clients == 1


def test_clear_resets_history_and_connections(fresh_bus):
    class FakeWS:
        async def send_json(self, data):
            pass

    fresh_bus.emit_sync(WorkerEvent(worker_name="w", type="progress", message="m"))
    fresh_bus.connections.connect(FakeWS())
    assert len(fresh_bus.get_history()) == 1
    assert fresh_bus.connected_clients == 1

    fresh_bus.clear()
    assert len(fresh_bus.get_history()) == 0
    assert fresh_bus.connected_clients == 0


# --------------------------------------------------------------------------- #
# Async event handlers
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_add_handler_receives_events(fresh_bus):
    received = []

    async def handler(event_dict):
        received.append(event_dict)

    fresh_bus.add_handler(handler)
    event = WorkerEvent(worker_name="w", type="finished", message="done")
    fresh_bus.emit_sync(event)

    await fresh_bus._run_handlers(event.to_dict())
    assert len(received) == 1
    assert received[0]["type"] == "finished"


@pytest.mark.asyncio
async def test_sync_handler_receives_events(fresh_bus):
    received = []

    def handler(event_dict):
        received.append(event_dict)

    fresh_bus.add_handler(handler)
    event = WorkerEvent(worker_name="w", type="started", message="begin")
    fresh_bus.emit_sync(event)

    await fresh_bus._run_handlers(event.to_dict())
    assert len(received) == 1


@pytest.mark.asyncio
async def test_handler_exception_does_not_crash_bus(fresh_bus):
    def bad_handler(event_dict):
        raise RuntimeError("handler failed")

    fresh_bus.add_handler(bad_handler)
    event = WorkerEvent(worker_name="w", type="progress", message="m")
    fresh_bus.emit_sync(event)

    await fresh_bus._run_handlers(event.to_dict())
    assert fresh_bus.connected_clients == 0
