import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id = Column(String(255), nullable=True, index=True)
    parent_decision_id = Column(UUID(as_uuid=True), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=False, default="")
    context = Column(JSON, default=dict)
    constraints = Column(JSON, default=list)
    selected_capability = Column(String(255), nullable=True)
    selected_worker = Column(String(255), nullable=True)
    evidence = Column(JSON, default=list)
    confidence = Column(Float, default=0.0)
    assumptions = Column(JSON, default=list)
    risks = Column(JSON, default=list)
    execution_strategy = Column(JSON, default=dict)
    reasoning = Column(Text, nullable=True)
    decision_reason = Column(Text, nullable=True)
    evidence_ids = Column(JSON, default=list)
    concept_ids = Column(JSON, default=list)
    risk_score = Column(Float, default=0.0)
    rejected_alternatives = Column(JSON, default=list)
    expected_outcome = Column(Text, nullable=True)
    success_criteria = Column(JSON, default=list)
    execution_result = Column(JSON, default=dict)
    feedback = Column(JSON, default=dict)
    next_action = Column(Text, nullable=True)
    memory_hits = Column(Integer, nullable=True, default=0)
    similar_episodes = Column(JSON, default=list)
    selected_strategy = Column(String(255), nullable=True)
    pattern_matches = Column(JSON, default=list)
    status = Column(String(50), nullable=False, default="planned")
    version = Column(Integer, nullable=False, default=1)
    source_research_id = Column(UUID(as_uuid=True), nullable=True)
    validated = Column(Boolean, default=False)
    validation_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "decision_id": self.decision_id,
            "parent_decision_id": str(self.parent_decision_id) if self.parent_decision_id else None,
            "goal": self.goal,
            "title": self.title,
            "description": self.description,
            "context": self.context or {},
            "constraints": self.constraints or [],
            "selected_capability": self.selected_capability,
            "selected_worker": self.selected_worker,
            "evidence": self.evidence or [],
            "confidence": self.confidence,
            "assumptions": self.assumptions or [],
            "risks": self.risks or [],
            "execution_strategy": self.execution_strategy or {},
            "reasoning": self.reasoning,
            "decision_reason": self.decision_reason,
            "evidence_ids": self.evidence_ids or [],
            "concept_ids": self.concept_ids or [],
            "risk_score": self.risk_score,
            "rejected_alternatives": self.rejected_alternatives or [],
            "expected_outcome": self.expected_outcome,
            "success_criteria": self.success_criteria or [],
            "execution_result": self.execution_result or {},
            "feedback": self.feedback or {},
            "next_action": self.next_action,
            "memory_hits": self.memory_hits or 0,
            "similar_episodes": self.similar_episodes or [],
            "selected_strategy": self.selected_strategy,
            "pattern_matches": self.pattern_matches or [],
            "status": self.status,
            "version": self.version or 1,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
