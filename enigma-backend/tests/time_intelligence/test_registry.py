"""
Test Timezone Registry

Tests for timezone mappings and configurations.
"""

import pytest

from app.time_intelligence.registry import TimezoneRegistry


class TestTimezoneRegistry:
    """Test TimezoneRegistry."""
    
    def test_get_timezone_for_country(self):
        """Test getting timezone for country."""
        tz = TimezoneRegistry.get_timezone_for_country("Canada")
        assert tz == "America/Toronto"
        
        tz = TimezoneRegistry.get_timezone_for_country("Egypt")
        assert tz == "Africa/Cairo"
        
        tz = TimezoneRegistry.get_timezone_for_country("USA")
        assert tz == "America/New_York"
    
    def test_get_timezone_for_city(self):
        """Test getting timezone for city."""
        tz = TimezoneRegistry.get_timezone_for_city("Toronto")
        assert tz == "America/Toronto"
        
        tz = TimezoneRegistry.get_timezone_for_city("New York")
        assert tz == "America/New_York"
        
        tz = TimezoneRegistry.get_timezone_for_city("Cairo")
        assert tz == "Africa/Cairo"
    
    def test_get_timezone_for_platform(self):
        """Test getting timezone for platform."""
        tz = TimezoneRegistry.get_timezone_for_platform("upwork_ca")
        assert tz == "America/Toronto"
        
        tz = TimezoneRegistry.get_timezone_for_platform("upwork_us")
        assert tz == "America/New_York"
    
    def test_get_timezone_for_country_case_insensitive(self):
        """Test country lookup is case insensitive."""
        tz1 = TimezoneRegistry.get_timezone_for_country("canada")
        tz2 = TimezoneRegistry.get_timezone_for_country("CANADA")
        tz3 = TimezoneRegistry.get_timezone_for_country("Canada")
        
        assert tz1 == tz2 == tz3
    
    def test_get_timezone_for_city_case_insensitive(self):
        """Test city lookup is case insensitive."""
        tz1 = TimezoneRegistry.get_timezone_for_city("toronto")
        tz2 = TimezoneRegistry.get_timezone_for_city("TORONTO")
        tz3 = TimezoneRegistry.get_timezone_for_city("Toronto")
        
        assert tz1 == tz2 == tz3
    
    def test_get_timezone_for_country_not_found(self):
        """Test getting timezone for unknown country."""
        tz = TimezoneRegistry.get_timezone_for_country("UnknownCountry")
        assert tz is None
    
    def test_get_timezone_for_city_not_found(self):
        """Test getting timezone for unknown city."""
        tz = TimezoneRegistry.get_timezone_for_city("UnknownCity")
        assert tz is None
    
    def test_get_timezone_for_platform_not_found(self):
        """Test getting timezone for unknown platform."""
        tz = TimezoneRegistry.get_timezone_for_platform("unknown_platform")
        assert tz is None
    
    def test_get_all_countries(self):
        """Test getting all supported countries."""
        countries = TimezoneRegistry.get_all_countries()
        assert isinstance(countries, list)
        assert len(countries) > 0
        assert "canada" in countries
        assert "egypt" in countries
    
    def test_get_all_cities(self):
        """Test getting all supported cities."""
        cities = TimezoneRegistry.get_all_cities()
        assert isinstance(cities, list)
        assert len(cities) > 0
        assert "toronto" in cities
        assert "cairo" in cities
    
    def test_get_all_platforms(self):
        """Test getting all supported platforms."""
        platforms = TimezoneRegistry.get_all_platforms()
        assert isinstance(platforms, list)
        assert len(platforms) > 0
        assert "upwork_ca" in platforms
    
    def test_search_timezone(self):
        """Test searching for timezone."""
        results = TimezoneRegistry.search_timezone("toronto")
        assert len(results) > 0
        assert "America/Toronto" in results
        
        results = TimezoneRegistry.search_timezone("canada")
        assert len(results) > 0
        assert "America/Toronto" in results
