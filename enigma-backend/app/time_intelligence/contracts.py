"""
Time Intelligence Contracts

Core contracts for timezone intelligence and customer time analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class TimezoneSource(str, Enum):
    """Source of timezone information."""
    EXPLICIT = "explicit"  # Customer provided explicitly
    LOCATION = "location"  # Inferred from customer location
    PLATFORM = "platform"  # Known from platform metadata
    COUNTRY = "country"  # Inferred from country
    UNKNOWN = "unknown"  # Cannot be determined


class DeadlineRisk(str, Enum):
    """Risk level for deadlines."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class WorkingHourStatus(str, Enum):
    """Status of working hour overlap."""
    OVERLAP = "overlap"
    NO_OVERLAP = "no_overlap"
    PARTIAL_OVERLAP = "partial_overlap"
    UNKNOWN = "unknown"


class DayType(str, Enum):
    """Type of day."""
    WEEKDAY = "weekday"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    UNKNOWN = "unknown"


@dataclass
class TimezoneInfo:
    """
    Timezone information for a customer or Enigma.
    """
    timezone: str  # IANA timezone identifier (e.g., "America/Toronto")
    source: TimezoneSource
    confidence: float = 0.5  # 0.0 to 1.0
    last_verified: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_known(self) -> bool:
        """Check if timezone is known."""
        return self.source != TimezoneSource.UNKNOWN and self.timezone is not None


@dataclass
class TimeConversion:
    """
    Result of time conversion between timezones.
    """
    original_time: str  # ISO format
    original_timezone: str
    target_time: str  # ISO format
    target_timezone: str
    offset_hours: float
    offset_minutes: int
    dst_active: bool = False
    dst_offset_hours: float = 0.0


@dataclass
class CustomerTimeContext:
    """
    Customer time context including current time and timezone.
    """
    customer_timezone: TimezoneInfo
    customer_current_time: str  # ISO format
    enigma_timezone: TimezoneInfo
    enigma_current_time: str  # ISO format
    utc_time: str  # ISO format
    conversion: TimeConversion
    day_type: DayType = DayType.UNKNOWN
    is_customer_working_hours: bool = False
    is_enigma_working_hours: bool = False


@dataclass
class WorkingHours:
    """
    Working hours configuration.
    """
    start_hour: int  # 0-23
    end_hour: int  # 0-23
    timezone: str
    days: list = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Monday=0 to Sunday=6
    
    def is_within_hours(self, dt: datetime) -> bool:
        """Check if datetime is within working hours."""
        if dt.weekday() not in self.days:
            return False
        return self.start_hour <= dt.hour < self.end_hour


@dataclass
class WorkingHourOverlap:
    """
    Analysis of working hour overlap between customer and Enigma.
    """
    status: WorkingHourStatus
    overlap_hours: float  # Number of overlapping hours
    customer_working_hours: WorkingHours
    enigma_working_hours: WorkingHours
    analysis_date: str  # ISO format
    recommendations: list = field(default_factory=list)


@dataclass
class DeadlineAnalysis:
    """
    Analysis of deadline feasibility and risk.
    """
    deadline: str  # ISO format
    deadline_timezone: str
    enigma_deadline: str  # ISO format
    offset_hours: float
    risk: DeadlineRisk
    is_feasible: bool
    is_working_hours: bool
    is_weekend: bool
    reason: Optional[str] = None
    recommendations: list = field(default_factory=list)


@dataclass
class AvailabilityWindow:
    """
    Available time window for communication or work.
    """
    start: str  # ISO format
    end: str  # ISO format
    timezone: str
    is_customer_available: bool
    is_enigma_available: bool
    both_available: bool
