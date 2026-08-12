"""
Database models for execution tracking (Developer Dashboard + Live Console).

- WorkerExecution  : one row per worker execution (status, time, result, etc.)
- WorkerEventLog   : one row per emitted event (for the dashboard logs panel)

TASK-016: user_id added to WorkerExecution for per-user ownership enforcement.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class WorkerExecution(Base):
    __tablename__ = "worker_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # execution_id
    # TASK-016: ownership — every execution is owned by the requesting user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    worker_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="pending")
    result = Column(JSON, default=dict)
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.0)
    execution_time = Column(Float, default=0.0)
    llm_calls = Column(Integer, default=0)
    memory_usage_mb = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "worker_name": self.worker_name,
            "status": self.status,
            "result": self.result,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "execution_time": self.execution_time,
            "llm_calls": self.llm_calls,
            "memory_usage_mb": self.memory_usage_mb,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WorkerEventLog(Base):
    __tablename__ = "worker_event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("worker_executions.id"), nullable=True, index=True)
    worker_name = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    data = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "execution_id": str(self.execution_id) if self.execution_id else None,
            "worker_name": self.worker_name,
            "event_type": self.event_type,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
