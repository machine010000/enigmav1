import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class ResearchSession(Base):
    __tablename__ = "research_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    status = Column(String(50), default="pending")
    customer_questions = Column(JSON, default=list)
    pain_points = Column(JSON, default=list)
    opportunities = Column(JSON, default=list)
    competitor_analysis = Column(JSON, default=dict)
    audience_insights = Column(JSON, default=dict)
    sources = Column(JSON, default=list)
    patterns_detected = Column(JSON, default=dict)
    applied_knowledge = Column(ARRAY(UUID(as_uuid=True)), default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ResearchSource(Base):
    __tablename__ = "research_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id"), nullable=False)
    source_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    results_count = Column(Integer, default=0)
    data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
