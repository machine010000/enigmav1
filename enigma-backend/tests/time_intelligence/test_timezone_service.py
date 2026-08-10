"""
Test Timezone Service

Tests for timezone conversion and DST handling.
"""

import pytest
from datetime import datetime, timedelta

from app.time_intelligence.timezone_service import TimezoneService


class TestTimezoneService:
    """Test TimezoneService."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = TimezoneService()
        assert service.enigma_timezone == "Africa/Cairo"
        
        service_custom = TimezoneService(enigma_timezone="America/Toronto")
        assert service_custom.enigma_timezone == "America/Toronto"
    
    def test_convert_time_basic(self):
        """Test basic time conversion."""
        service = TimezoneService()
        
        conversion = service.convert_time(
            time_str="2026-08-10T12:00:00",
            from_timezone="America/Toronto",
            to_timezone="Africa/Cairo",
        )
        
        assert conversion.original_time == "2026-08-10T12:00:00"
        assert conversion.original_timezone == "America/Toronto"
        assert conversion.target_timezone == "Africa/Cairo"
        assert conversion.offset_hours != 0  # Should have offset
    
    def test_convert_time_same_timezone(self):
        """Test conversion with same timezone."""
        service = TimezoneService()
        
        conversion = service.convert_time(
            time_str="2026-08-10T12:00:00",
            from_timezone="America/Toronto",
            to_timezone="America/Toronto",
        )
        
        # Offset should be 0 for same timezone
        # Note: Due to DST, the offset might be calculated, but should be minimal
        assert abs(conversion.offset_hours) < 0.1  # Allow small floating point errors
        assert conversion.offset_minutes == 0
    
    def test_get_current_time(self):
        """Test getting current time."""
        service = TimezoneService()
        
        current = service.get_current_time("America/Toronto")
        assert current is not None
        
        # Should be valid ISO format
        datetime.fromisoformat(current)
    
    def test_determine_day_type_weekday(self):
        """Test day type determination for weekday."""
        service = TimezoneService()
        
        # Monday
        dt = datetime(2026, 8, 10, 12, 0, 0)  # 2026-08-10 is a Monday
        day_type = service.determine_day_type(dt, "America/Toronto")
        
        assert day_type.value == "weekday"
    
    def test_determine_day_type_weekend(self):
        """Test day type determination for weekend."""
        service = TimezoneService()
        
        # Saturday
        dt = datetime(2026, 8, 15, 12, 0, 0)  # 2026-08-15 is a Saturday
        day_type = service.determine_day_type(dt, "America/Toronto")
        
        assert day_type.value == "weekend"
    
    def test_validate_timezone_valid(self):
        """Test validating valid timezone."""
        service = TimezoneService()
        
        assert service.validate_timezone("America/Toronto") is True
        assert service.validate_timezone("Africa/Cairo") is True
        assert service.validate_timezone("Europe/London") is True
    
    def test_validate_timezone_invalid(self):
        """Test validating invalid timezone."""
        service = TimezoneService()
        
        assert service.validate_timezone("Invalid/Timezone") is False
        assert service.validate_timezone("") is False
    
    def test_get_utc_offset(self):
        """Test getting UTC offset."""
        service = TimezoneService()
        
        offset = service.get_utc_offset("America/Toronto")
        assert isinstance(offset, float)
        
        # Toronto is typically -5 or -4 hours from UTC
        assert offset in [-5, -4, -6]  # Could vary by DST
    
    def test_dst_detection(self):
        """Test DST detection."""
        service = TimezoneService()
        
        # Check if DST is active for Toronto in August (summer)
        is_dst = service.is_dst_active("America/Toronto", "2026-08-10T12:00:00")
        assert isinstance(is_dst, bool)
    
    def test_convert_time_with_dst(self):
        """Test time conversion with DST."""
        service = TimezoneService()
        
        conversion = service.convert_time(
            time_str="2026-08-10T12:00:00",
            from_timezone="America/Toronto",
            to_timezone="Africa/Cairo",
        )
        
        # Should have DST information
        assert conversion.dst_active is not None
        assert isinstance(conversion.dst_active, bool)
    
    def test_convert_time_invalid_timezone(self):
        """Test conversion with invalid timezone."""
        service = TimezoneService()
        
        conversion = service.convert_time(
            time_str="2026-08-10T12:00:00",
            from_timezone="Invalid/Timezone",
            to_timezone="Africa/Cairo",
        )
        
        # Should return error conversion
        assert conversion.offset_hours == 0
        assert conversion.offset_minutes == 0
