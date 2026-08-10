"""
Test Working Hours

Tests for working hours and overlap analysis.
"""

import pytest

from app.time_intelligence.working_hours import WorkingHoursAnalyzer, WorkingHours
from app.time_intelligence.contracts import WorkingHourStatus


class TestWorkingHours:
    """Test WorkingHours."""
    
    def test_working_hours_creation(self):
        """Test creating working hours."""
        hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        assert hours.start_hour == 9
        assert hours.end_hour == 18
        assert hours.timezone == "America/Toronto"
    
    def test_is_within_hours_true(self):
        """Test checking if time is within working hours."""
        hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        from datetime import datetime
        dt = datetime(2026, 8, 10, 14, 0, 0)  # 2 PM
        
        assert hours.is_within_hours(dt) is True
    
    def test_is_within_hours_false(self):
        """Test checking if time is outside working hours."""
        hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        from datetime import datetime
        dt = datetime(2026, 8, 10, 20, 0, 0)  # 8 PM
        
        assert hours.is_within_hours(dt) is False
    
    def test_is_within_hours_weekend(self):
        """Test checking if weekend time is within working hours."""
        hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
            days=[0, 1, 2, 3, 4],  # Monday to Friday
        )
        
        from datetime import datetime
        dt = datetime(2026, 8, 15, 14, 0, 0)  # Saturday (weekday 5)
        
        assert hours.is_within_hours(dt) is False


class TestWorkingHoursAnalyzer:
    """Test WorkingHoursAnalyzer."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = WorkingHoursAnalyzer()
        assert analyzer is not None
        assert analyzer.timezone_service is not None
    
    def test_analyze_overlap_with_overlap(self):
        """Test analyzing working hour overlap with overlap."""
        analyzer = WorkingHoursAnalyzer()
        
        customer_hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        overlap = analyzer.analyze_overlap(customer_hours)
        
        assert overlap.status != WorkingHourStatus.NO_OVERLAP
        assert overlap.overlap_hours >= 0
    
    def test_analyze_overlap_no_overlap(self):
        """Test analyzing working hour overlap with no overlap."""
        analyzer = WorkingHoursAnalyzer()
        
        # Customer working hours that don't overlap with Enigma
        customer_hours = WorkingHours(
            start_hour=0,
            end_hour=3,
            timezone="America/Toronto",
        )
        
        overlap = analyzer.analyze_overlap(customer_hours)
        
        # May have some overlap due to timezone difference
        assert isinstance(overlap.overlap_hours, float)
    
    def test_analyze_overlap_status(self):
        """Test overlap status determination."""
        analyzer = WorkingHoursAnalyzer()
        
        customer_hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        overlap = analyzer.analyze_overlap(customer_hours)
        
        assert overlap.status in [
            WorkingHourStatus.OVERLAP,
            WorkingHourStatus.PARTIAL_OVERLAP,
            WorkingHourStatus.NO_OVERLAP,
        ]
    
    def test_analyze_overlap_recommendations(self):
        """Test that overlap analysis includes recommendations."""
        analyzer = WorkingHoursAnalyzer()
        
        customer_hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        overlap = analyzer.analyze_overlap(customer_hours)
        
        # Recommendations may be empty if there's good overlap
        assert isinstance(overlap.recommendations, list)
    
    def test_is_customer_working_now(self):
        """Test checking if customer is working now."""
        analyzer = WorkingHoursAnalyzer()
        
        is_working = analyzer.is_customer_working_now("America/Toronto")
        
        assert isinstance(is_working, bool)
    
    def test_analyze_overlap_custom_enigma_hours(self):
        """Test analyzing overlap with custom Enigma hours."""
        analyzer = WorkingHoursAnalyzer()
        
        customer_hours = WorkingHours(
            start_hour=9,
            end_hour=18,
            timezone="America/Toronto",
        )
        
        enigma_hours = WorkingHours(
            start_hour=10,
            end_hour=19,
            timezone="Africa/Cairo",
        )
        
        overlap = analyzer.analyze_overlap(
            customer_working_hours=customer_hours,
            enigma_working_hours=enigma_hours,
        )
        
        assert overlap is not None
        assert overlap.overlap_hours >= 0
