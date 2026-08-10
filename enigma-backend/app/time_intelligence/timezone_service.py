"""
Timezone Service

Core service for timezone operations and conversions.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo

from app.time_intelligence.contracts import (
    TimezoneInfo,
    TimezoneSource,
    TimeConversion,
    DayType,
)


class TimezoneService:
    """
    Service for timezone operations and conversions.
    
    Provides timezone conversion, DST handling, and time analysis.
    """
    
    def __init__(self, enigma_timezone: str = "Africa/Cairo"):
        """
        Initialize timezone service.
        
        Args:
            enigma_timezone: Enigma's local timezone (default: Africa/Cairo)
        """
        self.enigma_timezone = enigma_timezone
        self._timezone_cache: Dict[str, ZoneInfo] = {}
    
    def convert_time(
        self,
        time_str: str,
        from_timezone: str,
        to_timezone: str,
    ) -> TimeConversion:
        """
        Convert time from one timezone to another.
        
        Args:
            time_str: ISO format time string
            from_timezone: Source timezone (IANA identifier)
            to_timezone: Target timezone (IANA identifier)
            
        Returns:
            TimeConversion result
        """
        try:
            from_tz = self._get_timezone(from_timezone)
            to_tz = self._get_timezone(to_timezone)
            
            # Parse time as naive datetime, then localize
            dt = datetime.fromisoformat(time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=from_tz)
            
            # Convert to target timezone
            target_dt = dt.astimezone(to_tz)
            
            # Calculate offset between timezones (target - source)
            source_offset = dt.utcoffset()
            target_offset = target_dt.utcoffset()
            
            if source_offset and target_offset:
                offset = target_offset - source_offset
            else:
                offset = timedelta(0)
            
            offset_hours = offset.total_seconds() / 3600
            offset_minutes = int(offset.total_seconds() % 3600 / 60)
            
            # Check DST
            dst_active = target_dt.dst() != timedelta(0)
            dst_offset = target_dt.dst().total_seconds() / 3600 if dst_active else 0.0
            
            return TimeConversion(
                original_time=time_str,
                original_timezone=from_timezone,
                target_time=target_dt.isoformat(),
                target_timezone=to_timezone,
                offset_hours=offset_hours,
                offset_minutes=offset_minutes,
                dst_active=dst_active,
                dst_offset_hours=dst_offset,
            )
        except Exception as e:
            # Return error conversion
            return TimeConversion(
                original_time=time_str,
                original_timezone=from_timezone,
                target_time=time_str,
                target_timezone=to_timezone,
                offset_hours=0,
                offset_minutes=0,
                dst_active=False,
                dst_offset_hours=0.0,
            )
    
    def get_current_time(self, timezone: str) -> str:
        """
        Get current time in specified timezone.
        
        Args:
            timezone: IANA timezone identifier
            
        Returns:
            ISO format time string
        """
        try:
            tz = self._get_timezone(timezone)
            return datetime.now(tz).isoformat()
        except Exception:
            return datetime.utcnow().isoformat()
    
    def determine_day_type(self, dt: datetime, timezone: str) -> DayType:
        """
        Determine if a datetime is weekday, weekend, or holiday.
        
        Args:
            dt: Datetime to check
            timezone: Timezone for the datetime
            
        Returns:
            DayType
        """
        try:
            tz = self._get_timezone(timezone)
            localized_dt = dt if dt.tzinfo else dt.replace(tzinfo=tz)
            
            # Monday=0, Sunday=6
            weekday = localized_dt.weekday()
            
            if weekday >= 5:  # Saturday, Sunday
                return DayType.WEEKEND
            
            return DayType.WEEKDAY
        except Exception:
            return DayType.UNKNOWN
    
    def is_dst_active(self, timezone: str, time_str: Optional[str] = None) -> bool:
        """
        Check if DST is active for a timezone at a given time.
        
        Args:
            timezone: IANA timezone identifier
            time_str: ISO format time string (default: current time)
            
        Returns:
            True if DST is active, False otherwise
        """
        try:
            tz = self._get_timezone(timezone)
            
            if time_str:
                dt = datetime.fromisoformat(time_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tz)
            else:
                dt = datetime.now(tz)
            
            return dt.dst() != timedelta(0)
        except Exception:
            return False
    
    def get_utc_offset(self, timezone: str, time_str: Optional[str] = None) -> float:
        """
        Get UTC offset for a timezone at a given time.
        
        Args:
            timezone: IANA timezone identifier
            time_str: ISO format time string (default: current time)
            
        Returns:
            Offset in hours
        """
        try:
            tz = self._get_timezone(timezone)
            
            if time_str:
                dt = datetime.fromisoformat(time_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tz)
            else:
                dt = datetime.now(tz)
            
            offset = dt.utcoffset()
            return offset.total_seconds() / 3600 if offset else 0.0
        except Exception:
            return 0.0
    
    def _get_timezone(self, timezone: str) -> ZoneInfo:
        """
        Get ZoneInfo object with caching.
        
        Args:
            timezone: IANA timezone identifier
            
        Returns:
            ZoneInfo object
        """
        if timezone not in self._timezone_cache:
            self._timezone_cache[timezone] = ZoneInfo(timezone)
        return self._timezone_cache[timezone]
    
    def validate_timezone(self, timezone: str) -> bool:
        """
        Validate if a timezone identifier is valid.
        
        Args:
            timezone: IANA timezone identifier
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ZoneInfo(timezone)
            return True
        except Exception:
            return False
