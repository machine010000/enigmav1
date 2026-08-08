from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class EngagementModel:
    """Model representing engagement information."""
    engagement_id: str
    work_specification_id: str
    client_id: Optional[str] = None
    marketplace_id: Optional[str] = None
    engagement_type: str = "expert"  # expert, marketplace, direct
    engagement_stage: str = "initial"  # initial, negotiation, execution, delivery, completion
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EngagementMetrics:
    """Metrics for engagement analysis."""
    engagement_id: str
    total_engagements: int = 0
    successful_engagements: int = 0
    failed_engagements: int = 0
    average_duration: Optional[str] = None
    average_profitability: float = 0.0
    client_satisfaction: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
