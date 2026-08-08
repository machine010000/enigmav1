import uuid
from datetime import datetime, time
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Float, Boolean, Date, Time, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    positioning = Column(Text, nullable=True)
    messaging = Column(Text, nullable=True)
    content_strategy = Column(JSON, default=dict)
    growth_strategy = Column(JSON, default=dict)
    phases = Column(JSON, default=list)
    success_rate = Column(Float, nullable=True)
    adjusted_from = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)

class ExecutionPlan(Base):
    __tablename__ = "execution_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(50), default="pending")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("execution_plans.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(Time, nullable=True)
    impact = Column(String(20), default="medium")
    status = Column(String(50), default="pending")
    platform = Column(String(50), nullable=True)
    auto_execute = Column(Boolean, default=False)
    content_template = Column(Text, nullable=True)
    media_urls = Column(ARRAY(String), default=list)
    result_data = Column(JSON, default=dict)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
