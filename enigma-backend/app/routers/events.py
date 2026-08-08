"""
Live Console WebSocket Router — TASK-006

Streams WorkerEvents in real time to connected frontend clients.

    ws://host:port/ws/events

Events flow:
    Worker -> ExecutionEngine -> EventBus -> WebSocket clients

Example event:
    {"worker_name": "product_verification", "type": "progress",
     "message": "Analysing product title/name…", "data": {...},
     "timestamp": "2025-01-01T12:00:00", "execution_id": "uuid"}
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.engine.events import event_bus
from app.engine.contracts import WorkerEvent

logger = logging.getLogger("enigma.ws")

router = APIRouter(tags=["events"])


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        while True:
            # Keep the connection alive; events are server-pushed.
            # A no-op recv keeps the socket open and detects client disconnects.
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception) as exc:
        event_bus.disconnect(websocket)
        logger.info("WebSocket client disconnected: %s", type(exc).__name__)
