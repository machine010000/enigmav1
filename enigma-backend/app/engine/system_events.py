"""
System Event Enum — emitted ONLY by the Engine.

These represent infrastructure / lifecycle events:
    worker registered, worker started, worker finished, worker failed,
    pipeline started, pipeline finished.

Workers must NOT emit SystemEvent values — they emit DomainEvent instead
(see app/domain/events.py).

This separation keeps the EventBus clean when dozens of Workers are
registered: system events live in one namespace, business events in another.
"""
from __future__ import annotations

from enum import Enum


class SystemEvent(Enum):
    WORKER_REGISTERED = "worker_registered"
    WORKER_STARTED = "worker_started"
    WORKER_FINISHED = "worker_finished"
    WORKER_FAILED = "worker_failed"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_FINISHED = "pipeline_finished"
