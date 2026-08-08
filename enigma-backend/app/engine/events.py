"""
ENIGMA Engine — Event Bus

The EventBus is the backbone of the Live Console (TASK-006).  It maintains:

1. A set of connected WebSocket clients (via ConnectionManager)
2. An in-memory ring buffer of recent events (for clients that reconnect)

The ExecutionEngine calls ``event_bus.emit()`` (or ``await event_bus.broadcast()``)
whenever a worker starts, progresses, or finishes, and the events are fanned out
to every connected frontend client in real time.
"""
from __future__ import annotations

import asyncio
from collections import deque
from typing import Any, Deque, Dict, List, Set

from app.engine.contracts import WorkerEvent


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self) -> None:
        self._active: Set[Any] = set()

    def connect(self, websocket: Any) -> None:
        self._active.add(websocket)

    def disconnect(self, websocket: Any) -> None:
        self._active.discard(websocket)

    @property
    def count(self) -> int:
        return len(self._active)

    async def send_json(self, websocket: Any, data: Dict[str, Any]) -> bool:
        try:
            await websocket.send_json(data)
            return True
        except Exception:
            self.disconnect(websocket)
            return False

    async def broadcast(self, data: Dict[str, Any]) -> None:
        dead: List[Any] = []
        for ws in list(self._active):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._active.discard(ws)


class EventBus:
    """
    Global singleton event bus.

    Workers and the Engine emit WorkerEvent instances; the bus persists them to
    the ring buffer and broadcasts them to all connected WebSocket clients.
    """

    def __init__(self, history_size: int = 500) -> None:
        self.connections = ConnectionManager()
        self._history: Deque[Dict[str, Any]] = deque(maxlen=history_size)
        self._handlers: List[Any] = []

    # ---- WebSocket lifecycle -------------------------------------------------

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        self.connections.connect(websocket)
        # replay recent history to the newly connected client
        for event_dict in self._history:
            await self.connections.send_json(websocket, event_dict)

    def disconnect(self, websocket: Any) -> None:
        self.connections.disconnect(websocket)

    # ---- emission ------------------------------------------------------------

    def _store(self, event: WorkerEvent) -> None:
        self._history.append(event.to_dict())

    async def broadcast(self, event: WorkerEvent) -> None:
        """Persist the event and fan it out to all WebSocket clients."""
        self._store(event)
        await self.connections.broadcast(event.to_dict())

    def emit_sync(self, event: WorkerEvent) -> None:
        """Store without broadcasting (for sync contexts)."""
        self._store(event)

    # ---- handlers ------------------------------------------------------------

    def add_handler(self, handler: Any) -> None:
        """Register a callable that receives every event dict."""
        self._handlers.append(handler)

    async def _run_handlers(self, event_dict: Dict[str, Any]) -> None:
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_dict)
                else:
                    handler(event_dict)
            except Exception:
                pass

    # ---- history -------------------------------------------------------------

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        events = list(self._history)
        events.reverse()
        return events[:limit]

    def clear(self) -> None:
        self._history.clear()
        self.connections = ConnectionManager()

    @property
    def connected_clients(self) -> int:
        return self.connections.count


# Global singleton — imported by the Engine and the WebSocket router
event_bus = EventBus()
