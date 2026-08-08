"""
Domain Event Enum — emitted by Workers.

These represent business-level events produced during worker execution:
    product_verified, category_detected, attributes_extracted,
    keywords_found, audience_discovered, etc.

Workers emit DomainEvent values via ``context.emit()``.
The Engine emits SystemEvent values (see app/engine/system_events.py).

This separation is enforced by the ExecutionEngine: the emit callable
injected into the context validates that every event is a DomainEvent.
"""
from __future__ import annotations

from enum import Enum


class DomainEvent(Enum):
    # Worker lifecycle events (domain-level, not system-level)
    WORKER_PROGRESS = "progress"

    # Product Intelligence Pipeline domain events
    PRODUCT_VERIFIED = "product_verified"
    CATEGORY_DETECTED = "category_detected"
    ATTRIBUTES_EXTRACTED = "attributes_extracted"
    KEYWORDS_FOUND = "keywords_found"
    AUDIENCE_DISCOVERED = "audience_discovered"
    COMPETITORS_FOUND = "competitors_found"
    TRENDS_IDENTIFIED = "trends_identified"
    COMMUNITY_INSIGHTS_FOUND = "community_insights_found"
    RESEARCH_COMPLETED = "research_completed"
    INTELLIGENCE_REPORT_READY = "intelligence_report_ready"

    # Generic fallback
    RESULT_READY = "result_ready"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check whether *value* is a valid DomainEvent string."""
        return value in (e.value for e in cls)
