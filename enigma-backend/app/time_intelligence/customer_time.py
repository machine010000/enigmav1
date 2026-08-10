"""
Customer Time

Customer time context and analysis.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from app.time_intelligence.contracts import (
    TimezoneInfo,
    TimezoneSource,
    CustomerTimeContext,
    TimeConversion,
    DayType,
)
from app.time_intelligence.timezone_service import TimezoneService


class CustomerTimeAnalyzer:
    """
    Analyzer for customer time context.
    
    Provides current time analysis, timezone context, and time conversion.
    """
    
    def __init__(self, timezone_service: Optional[TimezoneService] = None):
        """
        Initialize customer time analyzer.
        
        Args:
            timezone_service: Timezone service instance
        """
        self.timezone_service = timezone_service or TimezoneService()
        self._customer_timezones: Dict[str, TimezoneInfo] = {}
    
    def register_customer_timezone(self, customer_id: str, timezone_info: TimezoneInfo) -> None:
        """
        Register customer timezone information.
        
        Args:
            customer_id: Customer identifier
            timezone_info: Timezone information
        """
        self._customer_timezones[customer_id] = timezone_info
    
    def get_customer_timezone(self, customer_id: str) -> Optional[TimezoneInfo]:
        """
        Get customer timezone information.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            TimezoneInfo or None if not registered
        """
        return self._customer_timezones.get(customer_id)
    
    def infer_timezone(
        self,
        explicit_timezone: Optional[str] = None,
        location: Optional[str] = None,
        platform: Optional[str] = None,
        country: Optional[str] = None,
    ) -> TimezoneInfo:
        """
        Infer timezone from available information.
        
        Priority: explicit > location > platform > country > unknown
        
        Args:
            explicit_timezone: Explicitly provided timezone
            location: Customer location
            platform: Platform metadata
            country: Country
            
        Returns:
            TimezoneInfo
        """
        # Priority 1: Explicit timezone
        if explicit_timezone and self.timezone_service.validate_timezone(explicit_timezone):
            return TimezoneInfo(
                timezone=explicit_timezone,
                source=TimezoneSource.EXPLICIT,
                confidence=1.0,
            )
        
        # Priority 2: Location-based inference
        if location:
            inferred = self._infer_from_location(location)
            if inferred:
                return inferred
        
        # Priority 3: Platform-based inference
        if platform:
            inferred = self._infer_from_platform(platform)
            if inferred:
                return inferred
        
        # Priority 4: Country-based inference
        if country:
            inferred = self._infer_from_country(country)
            if inferred:
                return inferred
        
        # Unknown
        return TimezoneInfo(
            timezone="",
            source=TimezoneSource.UNKNOWN,
            confidence=0.0,
        )
    
    def _infer_from_location(self, location: str) -> Optional[TimezoneInfo]:
        """
        Infer timezone from location.
        
        Args:
            location: Location string
            
        Returns:
            TimezoneInfo or None
        """
        # Location to timezone mapping (simplified)
        location_map = {
            "toronto": "America/Toronto",
            "montreal": "America/Toronto",
            "vancouver": "America/Vancouver",
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "cairo": "Africa/Cairo",
            "dubai": "Asia/Dubai",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
        }
        
        location_lower = location.lower()
        for loc, tz in location_map.items():
            if loc in location_lower:
                if self.timezone_service.validate_timezone(tz):
                    return TimezoneInfo(
                        timezone=tz,
                        source=TimezoneSource.LOCATION,
                        confidence=0.7,
                    )
        
        return None
    
    def _infer_from_platform(self, platform: str) -> Optional[TimezoneInfo]:
        """
        Infer timezone from platform metadata.
        
        Args:
            platform: Platform name
            
        Returns:
            TimezoneInfo or None
        """
        # Platform-specific timezone hints (simplified)
        platform_map = {
            "upwork_ca": "America/Toronto",
            "upwork_us": "America/New_York",
            "upwork_uk": "Europe/London",
        }
        
        if platform in platform_map:
            tz = platform_map[platform]
            if self.timezone_service.validate_timezone(tz):
                return TimezoneInfo(
                    timezone=tz,
                    source=TimezoneSource.PLATFORM,
                    confidence=0.5,
                )
        
        return None
    
    def _infer_from_country(self, country: str) -> Optional[TimezoneInfo]:
        """
        Infer timezone from country.
        
        Note: Countries can have multiple timezones, so this is low confidence.
        
        Args:
            country: Country name
            
        Returns:
            TimezoneInfo or None
        """
        # Country to timezone mapping (using most common timezone)
        country_map = {
            "canada": "America/Toronto",
            "usa": "America/New_York",
            "united states": "America/New_York",
            "uk": "Europe/London",
            "united kingdom": "Europe/London",
            "egypt": "Africa/Cairo",
            "australia": "Australia/Sydney",
            "india": "Asia/Kolkata",
            "china": "Asia/Shanghai",
            "germany": "Europe/Berlin",
            "france": "Europe/Paris",
            "japan": "Asia/Tokyo",
        }
        
        country_lower = country.lower()
        if country_lower in country_map:
            tz = country_map[country_lower]
            if self.timezone_service.validate_timezone(tz):
                return TimezoneInfo(
                    timezone=tz,
                    source=TimezoneSource.COUNTRY,
                    confidence=0.3,  # Low confidence due to multiple timezones
                )
        
        return None
    
    def create_customer_time_context(
        self,
        customer_timezone: TimezoneInfo,
        enigma_timezone: Optional[TimezoneInfo] = None,
    ) -> CustomerTimeContext:
        """
        Create customer time context.
        
        Args:
            customer_timezone: Customer timezone information
            enigma_timezone: Enigma timezone information (default: service default)
            
        Returns:
            CustomerTimeContext
        """
        if enigma_timezone is None:
            enigma_timezone = TimezoneInfo(
                timezone=self.timezone_service.enigma_timezone,
                source=TimezoneSource.EXPLICIT,
                confidence=1.0,
            )
        
        # Get current times
        customer_current = self.timezone_service.get_current_time(customer_timezone.timezone)
        enigma_current = self.timezone_service.get_current_time(enigma_timezone.timezone)
        utc_current = self.timezone_service.get_current_time("UTC")
        
        # Create conversion
        conversion = self.timezone_service.convert_time(
            customer_current,
            customer_timezone.timezone,
            enigma_timezone.timezone,
        )
        
        # Determine day type
        customer_dt = datetime.fromisoformat(customer_current)
        day_type = self.timezone_service.determine_day_type(
            customer_dt,
            customer_timezone.timezone,
        )
        
        return CustomerTimeContext(
            customer_timezone=customer_timezone,
            customer_current_time=customer_current,
            enigma_timezone=enigma_timezone,
            enigma_current_time=enigma_current,
            utc_time=utc_current,
            conversion=conversion,
            day_type=day_type,
            is_customer_working_hours=False,  # Will be set by working hours module
            is_enigma_working_hours=False,  # Will be set by working hours module
        )
