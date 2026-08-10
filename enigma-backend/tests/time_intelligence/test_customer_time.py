"""
Test Customer Time

Tests for customer time context and timezone inference.
"""

import pytest

from app.time_intelligence.customer_time import CustomerTimeAnalyzer
from app.time_intelligence.contracts import (
    TimezoneInfo,
    TimezoneSource,
)


class TestCustomerTimeAnalyzer:
    """Test CustomerTimeAnalyzer."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = CustomerTimeAnalyzer()
        assert analyzer is not None
        assert analyzer.timezone_service is not None
    
    def test_register_customer_timezone(self):
        """Test registering customer timezone."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = TimezoneInfo(
            timezone="America/Toronto",
            source=TimezoneSource.EXPLICIT,
            confidence=1.0,
        )
        
        analyzer.register_customer_timezone("customer_1", timezone_info)
        
        retrieved = analyzer.get_customer_timezone("customer_1")
        assert retrieved is not None
        assert retrieved.timezone == "America/Toronto"
    
    def test_infer_timezone_explicit(self):
        """Test timezone inference with explicit timezone."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(
            explicit_timezone="America/Toronto",
        )
        
        assert timezone_info.source == TimezoneSource.EXPLICIT
        assert timezone_info.timezone == "America/Toronto"
        assert timezone_info.confidence == 1.0
    
    def test_infer_timezone_location(self):
        """Test timezone inference from location."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(
            location="Toronto",
        )
        
        assert timezone_info.source == TimezoneSource.LOCATION
        assert timezone_info.timezone == "America/Toronto"
        assert timezone_info.confidence == 0.7
    
    def test_infer_timezone_country(self):
        """Test timezone inference from country."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone(
            country="Canada",
        )
        
        assert timezone_info.source == TimezoneSource.COUNTRY
        assert timezone_info.timezone == "America/Toronto"
        assert timezone_info.confidence == 0.3  # Low confidence
    
    def test_infer_timezone_unknown(self):
        """Test timezone inference with insufficient data."""
        analyzer = CustomerTimeAnalyzer()
        
        timezone_info = analyzer.infer_timezone()
        
        assert timezone_info.source == TimezoneSource.UNKNOWN
        assert timezone_info.timezone == ""
        assert timezone_info.confidence == 0.0
    
    def test_infer_timezone_priority(self):
        """Test timezone inference priority order."""
        analyzer = CustomerTimeAnalyzer()
        
        # Explicit should take priority over location
        timezone_info = analyzer.infer_timezone(
            explicit_timezone="America/Toronto",
            location="New York",
        )
        
        assert timezone_info.source == TimezoneSource.EXPLICIT
        assert timezone_info.timezone == "America/Toronto"
    
    def test_create_customer_time_context(self):
        """Test creating customer time context."""
        analyzer = CustomerTimeAnalyzer()
        
        customer_timezone = TimezoneInfo(
            timezone="America/Toronto",
            source=TimezoneSource.EXPLICIT,
            confidence=1.0,
        )
        
        context = analyzer.create_customer_time_context(customer_timezone)
        
        assert context.customer_timezone.timezone == "America/Toronto"
        assert context.customer_current_time is not None
        assert context.enigma_current_time is not None
        assert context.utc_time is not None
        assert context.conversion is not None
    
    def test_timezone_info_is_known(self):
        """Test TimezoneInfo.is_known method."""
        known_info = TimezoneInfo(
            timezone="America/Toronto",
            source=TimezoneSource.EXPLICIT,
            confidence=1.0,
        )
        
        assert known_info.is_known() is True
        
        unknown_info = TimezoneInfo(
            timezone="",
            source=TimezoneSource.UNKNOWN,
            confidence=0.0,
        )
        
        assert unknown_info.is_known() is False
    
    def test_get_customer_timezone_not_registered(self):
        """Test getting timezone for unregistered customer."""
        analyzer = CustomerTimeAnalyzer()
        
        retrieved = analyzer.get_customer_timezone("nonexistent")
        assert retrieved is None
