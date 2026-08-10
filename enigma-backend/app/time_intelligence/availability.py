"""
Availability

Analysis of availability windows for communication and work.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from app.time_intelligence.contracts import (
    AvailabilityWindow,
    WorkingHours,
)
from app.time_intelligence.timezone_service import TimezoneService


class AvailabilityAnalyzer:
    """
    Analyzer for availability windows.
    
    Determines when both customer and Enigma are available for communication.
    """
    
    def __init__(self, timezone_service: Optional[TimezoneService] = None):
        """
        Initialize availability analyzer.
        
        Args:
            timezone_service: Timezone service instance
        """
        self.timezone_service = timezone_service or TimezoneService()
    
    def find_availability_windows(
        self,
        customer_timezone: str,
        enigma_timezone: Optional[str] = None,
        customer_working_hours: Optional[WorkingHours] = None,
        enigma_working_hours: Optional[WorkingHours] = None,
        start_date: Optional[str] = None,
        window_hours: int = 24,
    ) -> List[AvailabilityWindow]:
        """
        Find availability windows for communication.
        
        Args:
            customer_timezone: Customer timezone
            enigma_timezone: Enigma timezone (default: service default)
            customer_working_hours: Customer working hours
            enigma_working_hours: Enigma working hours
            start_date: Start date in ISO format (default: now)
            window_hours: Hours to analyze ahead
            
        Returns:
            List of availability windows
        """
        if enigma_timezone is None:
            enigma_timezone = self.timezone_service.enigma_timezone
        
        if customer_working_hours is None:
            customer_working_hours = WorkingHours(
                start_hour=9,
                end_hour=18,
                timezone=customer_timezone,
            )
        
        if enigma_working_hours is None:
            enigma_working_hours = WorkingHours(
                start_hour=9,
                end_hour=18,
                timezone=enigma_timezone,
            )
        
        if start_date is None:
            start_date = self.timezone_service.get_current_time(customer_timezone)
        
        windows = []
        current_dt = datetime.fromisoformat(start_date)
        end_dt = current_dt + timedelta(hours=window_hours)
        
        # Analyze hour by hour
        while current_dt < end_dt:
            window = self._analyze_hour(
                current_dt,
                customer_timezone,
                enigma_timezone,
                customer_working_hours,
                enigma_working_hours,
            )
            windows.append(window)
            current_dt += timedelta(hours=1)
        
        return windows
    
    def _analyze_hour(
        self,
        dt: datetime,
        customer_timezone: str,
        enigma_timezone: str,
        customer_working_hours: WorkingHours,
        enigma_working_hours: WorkingHours,
    ) -> AvailabilityWindow:
        """
        Analyze availability for a specific hour.
        
        Args:
            dt: Datetime to analyze
            customer_timezone: Customer timezone
            enigma_timezone: Enigma timezone
            customer_working_hours: Customer working hours
            enigma_working_hours: Enigma working hours
            
        Returns:
            AvailabilityWindow
        """
        # Convert to respective timezones
        customer_tz = self.timezone_service._get_timezone(customer_timezone)
        enigma_tz = self.timezone_service._get_timezone(enigma_timezone)
        
        customer_dt = dt.astimezone(customer_tz) if dt.tzinfo else dt.replace(tzinfo=customer_tz)
        enigma_dt = dt.astimezone(enigma_tz) if dt.tzinfo else dt.replace(tzinfo=enigma_tz)
        
        # Check availability
        is_customer_available = customer_working_hours.is_within_hours(customer_dt)
        is_enigma_available = enigma_working_hours.is_within_hours(enigma_dt)
        both_available = is_customer_available and is_enigma_available
        
        return AvailabilityWindow(
            start=dt.isoformat(),
            end=(dt + timedelta(hours=1)).isoformat(),
            timezone=enigma_timezone,
            is_customer_available=is_customer_available,
            is_enigma_available=is_enigma_available,
            both_available=both_available,
        )
    
    def get_next_available_window(
        self,
        customer_timezone: str,
        enigma_timezone: Optional[str] = None,
        customer_working_hours: Optional[WorkingHours] = None,
        enigma_working_hours: Optional[WorkingHours] = None,
        max_hours_ahead: int = 168,  # 1 week
    ) -> Optional[AvailabilityWindow]:
        """
        Get the next available window for both parties.
        
        Args:
            customer_timezone: Customer timezone
            enigma_timezone: Enigma timezone
            customer_working_hours: Customer working hours
            enigma_working_hours: Enigma working hours
            max_hours_ahead: Maximum hours to look ahead
            
        Returns:
            AvailabilityWindow or None if no availability found
        """
        windows = self.find_availability_windows(
            customer_timezone=customer_timezone,
            enigma_timezone=enigma_timezone,
            customer_working_hours=customer_working_hours,
            enigma_working_hours=enigma_working_hours,
            window_hours=max_hours_ahead,
        )
        
        for window in windows:
            if window.both_available:
                return window
        
        return None
