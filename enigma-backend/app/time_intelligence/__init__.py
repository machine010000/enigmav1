"""
Time Intelligence Package

Domain-independent timezone intelligence and customer time analysis.
"""

from app.time_intelligence.contracts import (
    TimezoneSource,
    TimezoneInfo,
    TimeConversion,
    DeadlineRisk,
    WorkingHourStatus,
    DayType,
    CustomerTimeContext,
    WorkingHours,
    WorkingHourOverlap,
    DeadlineAnalysis,
    AvailabilityWindow,
)
from app.time_intelligence.timezone_service import TimezoneService
from app.time_intelligence.customer_time import CustomerTimeAnalyzer
from app.time_intelligence.deadline_analysis import DeadlineAnalyzer
from app.time_intelligence.availability import AvailabilityAnalyzer
from app.time_intelligence.working_hours import WorkingHoursAnalyzer
from app.time_intelligence.registry import TimezoneRegistry

__all__ = [
    # Contracts
    "TimezoneSource",
    "TimezoneInfo",
    "TimeConversion",
    "DeadlineRisk",
    "WorkingHourStatus",
    "DayType",
    "CustomerTimeContext",
    "WorkingHours",
    "WorkingHourOverlap",
    "DeadlineAnalysis",
    "AvailabilityWindow",
    # Services
    "TimezoneService",
    "CustomerTimeAnalyzer",
    "DeadlineAnalyzer",
    "AvailabilityAnalyzer",
    "WorkingHoursAnalyzer",
    "TimezoneRegistry",
]
