"""Capability evidence freshness policy, independent from capability status."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Iterable, Optional

from app.engine.capability_catalog import CapabilityCatalog, capability_catalog


class EvidenceFreshness(str, Enum):
    FRESH = "fresh"
    DUE = "due_for_revalidation"
    STALE = "stale"


@dataclass(frozen=True)
class FreshnessAssessment:
    state: EvidenceFreshness
    capability_status: str
    reference_time: Optional[datetime]
    age_days: Optional[int]
    interval_days: int
    diversity_count: int
    required_diversity: int
    reason: str


class CapabilityRevalidationPolicy:
    """Interprets existing timestamps and training metadata without changing status."""

    def __init__(self, catalog: Optional[CapabilityCatalog] = None) -> None:
        self.catalog = catalog or capability_catalog

    def assess(self, capability: str, progress: Any,
               attempts: Iterable[Dict[str, Any]], *,
               now: Optional[datetime] = None) -> FreshnessAssessment:
        entry = self.catalog.get(capability)
        interval = (entry.revalidation_interval_days if entry else None) or 90
        required_diversity = (entry.minimum_revalidation_diversity if entry else 1)
        now = now or datetime.utcnow()
        successful = [
            a for a in attempts
            if a.get("mode") in {"advanced_training", "revalidation_training"}
            and a.get("evaluation", {}).get("passed")
        ]
        diversity = len({a.get("task_id") for a in successful if a.get("task_id")})

        timestamps = [getattr(progress, "last_verified", None),
                      getattr(progress, "last_success_at", None)]
        for attempt in successful:
            raw = attempt.get("recorded_at")
            if raw:
                try:
                    timestamps.append(datetime.fromisoformat(raw))
                except (TypeError, ValueError):
                    pass
        valid_times = [value for value in timestamps if isinstance(value, datetime)]
        reference = max(valid_times) if valid_times else None
        age_days = (now - reference).days if reference else None
        status = getattr(progress, "capability_status", "unknown")

        if reference is None or (age_days is not None and age_days > interval * 2):
            state, reason = EvidenceFreshness.STALE, "latest successful validation exceeds stale horizon"
        elif age_days is not None and age_days > interval:
            state, reason = EvidenceFreshness.DUE, "latest successful validation exceeds revalidation interval"
        elif diversity < required_diversity:
            state, reason = EvidenceFreshness.DUE, "successful evidence lacks required task diversity"
        else:
            state, reason = EvidenceFreshness.FRESH, "recent and sufficiently diverse successful evidence"

        return FreshnessAssessment(state, status, reference, age_days, interval,
                                   diversity, required_diversity, reason)
