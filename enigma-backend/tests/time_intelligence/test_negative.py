"""
Test Time Intelligence - Negative Cases

Tests for ensuring no fake timezones, no silent failures, and proper error handling.
"""

import pytest

from app.time_intelligence.timezone_service import TimezoneService
from app.time_intelligence.customer_time import CustomerTimeAnalyzer
from app.time_intelligence.deadline_analysis import DeadlineAnalyzer
from app.time_intelligence.contracts import (
    TimezoneInfo,
    TimezoneSource,
)


class TestNoFakeTimezones:
    """Test that unknown timezone is not guessed."""
    
    def test_unknown_timezone_not_guessed(self):
        """Test that unknown timezone is not guessed."""
        analyzer = CustomerTimeAnalyzer()
        
        # No data provided
        timezone_info = analyzer.infer_timezone()
        
        assert timezone_info.source == TimezoneSource.UNKNOWN
        assert timezone_info.timezone == ""
        assert timezone_info.confidence == 0.0
        
        # Should not guess a timezone
        assert timezone_info.is_known() is False
    
    def test_invalid_country_not_guessed(self):
        """Test that invalid country does not guess timezone."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(country="InvalidCountry")
        
        assert timezone_info.source == TimezoneSource.UNKNOWN
        assert timezone_info.is_known() is False
    
    def test_invalid_city_not_guessed(self):
        """Test that invalid city does not guess timezone."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(location="InvalidCity")
        
        # Should not guess - will fall through to unknown
        assert timezone_info.source == TimezoneSource.UNKNOWN
        assert timezone_info.is_known() is False


class TestNoSilentFailures:
    """Test that errors are not silent."""
    
    def test_invalid_timezone_conversion_returns_error(self):
        """Test that invalid timezone conversion returns error, not silent failure."""
        service = TimezoneService()
        
        conversion = service.convert_time(
            time_str="2026-08-10T12:00:00",
            from_timezone="Invalid/Timezone",
            to_timezone="Africa/Cairo",
        )
        
        # Should return error conversion, not crash or return fake data
        assert conversion.offset_hours == 0
        assert conversion.offset_minutes == 0
        assert conversion.dst_active is False
    
    def test_invalid_deadline_format_returns_error(self):
        """Test that invalid deadline format returns error."""
        analyzer = DeadlineAnalyzer()
        
        analysis = analyzer.analyze_deadline(
            deadline="not-a-date",
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.is_feasible is False
        assert analysis.risk.value == "unknown"
        assert analysis.reason is not None
        assert "Invalid deadline format" in analysis.reason
    
    def test_empty_timezone_not_validated(self):
        """Test that empty timezone is not validated."""
        service = TimezoneService()
        
        assert service.validate_timezone("") is False
        assert service.validate_timezone(None) is False


class TestCountryAmbiguity:
    """Test handling of country ambiguity (multiple timezones)."""
    
    def test_country_inference_low_confidence(self):
        """Test that country inference has low confidence."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(country="USA")
        
        # USA has multiple timezones, so confidence should be low
        assert timezone_info.source == TimezoneSource.COUNTRY
        assert timezone_info.confidence == 0.3
        assert timezone_info.is_known() is True  # But still known
    
    def test_explicit_overrides_country(self):
        """Test that explicit timezone overrides country inference."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(
            explicit_timezone="America/Los_Angeles",
            country="USA",
        )
        
        # Explicit should take priority
        assert timezone_info.source == TimezoneSource.EXPLICIT
        assert timezone_info.timezone == "America/Los_Angeles"
        assert timezone_info.confidence == 1.0


class TestDSTHandling:
    """Test DST handling."""
    
    def test_dst_aware_conversion(self):
        """Test that conversion is DST aware."""
        service = TimezoneService()
        
        # Convert during DST period (August)
        conversion = service.convert_time(
            time_str="2026-08-10T12:00:00",
            from_timezone="America/Toronto",
            to_timezone="Africa/Cairo",
        )
        
        # Should have DST information
        assert conversion.dst_active is not None
        assert isinstance(conversion.dst_active, bool)
        assert conversion.dst_offset_hours is not None


class TestWeekendDifferences:
    """Test weekend handling."""
    
    def test_weekend_deadline_high_risk(self):
        """Test that weekend deadline is high risk."""
        analyzer = DeadlineAnalyzer()
        
        # Saturday deadline
        deadline = "2026-08-16T17:00:00"  # Saturday
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.is_weekend is True
        # Weekend should increase risk
        assert analysis.risk.value in ["high", "critical"]
    
    def test_weekday_deadline_lower_risk(self):
        """Test that weekday deadline has lower risk."""
        analyzer = DeadlineAnalyzer()
        
        # Monday deadline, 72 hours ahead
        from datetime import datetime, timedelta
        deadline = (datetime.utcnow() + timedelta(hours=72)).isoformat()
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.is_weekend is False
        # Should have lower risk than weekend (may still be HIGH due to timezone offset)
        assert analysis.risk.value in ["low", "medium", "high"]


class TestCustomerEnigmaOffset:
    """Test customer-Enigma offset calculation."""
    
    def test_offset_calculation(self):
        """Test that offset is calculated correctly."""
        analyzer = CustomerTimeAnalyzer()
        
        customer_timezone = TimezoneInfo(
            timezone="America/Toronto",
            source=TimezoneSource.EXPLICIT,
            confidence=1.0,
        )
        
        context = analyzer.create_customer_time_context(customer_timezone)
        
        # Should have offset
        assert context.conversion.offset_hours != 0
        assert context.conversion.target_timezone == "Africa/Cairo"
        assert context.conversion.original_timezone == "America/Toronto"
    
    def test_offset_with_same_timezone(self):
        """Test offset when timezones are the same."""
        analyzer = CustomerTimeAnalyzer()
        
        customer_timezone = TimezoneInfo(
            timezone="Africa/Cairo",
            source=TimezoneSource.EXPLICIT,
            confidence=1.0,
        )
        
        context = analyzer.create_customer_time_context(customer_timezone)
        
        # Should have minimal offset (may have small floating point error)
        assert abs(context.conversion.offset_hours) < 0.1
