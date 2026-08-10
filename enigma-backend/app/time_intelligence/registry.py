"""
Timezone Registry

Registry for timezone mappings and configurations.
"""

from typing import Dict, List, Optional


class TimezoneRegistry:
    """
    Registry for timezone mappings and common configurations.
    
    Provides timezone mappings for countries, cities, and platforms.
    """
    
    # Country to timezone mappings (most common timezone)
    COUNTRY_TIMEZONES: Dict[str, str] = {
        "egypt": "Africa/Cairo",
        "canada": "America/Toronto",
        "usa": "America/New_York",
        "united states": "America/New_York",
        "uk": "Europe/London",
        "united kingdom": "Europe/London",
        "australia": "Australia/Sydney",
        "india": "Asia/Kolkata",
        "china": "Asia/Shanghai",
        "germany": "Europe/Berlin",
        "france": "Europe/Paris",
        "japan": "Asia/Tokyo",
        "uae": "Asia/Dubai",
        "united arab emirates": "Asia/Dubai",
        "saudi arabia": "Asia/Riyadh",
        "brazil": "America/Sao_Paulo",
        "mexico": "America/Mexico_City",
        "argentina": "America/Argentina/Buenos_Aires",
        "south africa": "Africa/Johannesburg",
        "russia": "Europe/Moscow",
        "italy": "Europe/Rome",
        "spain": "Europe/Madrid",
        "netherlands": "Europe/Amsterdam",
        "switzerland": "Europe/Zurich",
        "sweden": "Europe/Stockholm",
        "norway": "Europe/Oslo",
        "denmark": "Europe/Copenhagen",
        "finland": "Europe/Helsinki",
        "poland": "Europe/Warsaw",
        "turkey": "Europe/Istanbul",
        "greece": "Europe/Athens",
        "south korea": "Asia/Seoul",
        "singapore": "Asia/Singapore",
        "thailand": "Asia/Bangkok",
        "vietnam": "Asia/Ho_Chi_Minh",
        "indonesia": "Asia/Jakarta",
        "philippines": "Asia/Manila",
        "malaysia": "Asia/Kuala_Lumpur",
        "new zealand": "Pacific/Auckland",
    }
    
    # City to timezone mappings
    CITY_TIMEZONES: Dict[str, str] = {
        # Canada
        "toronto": "America/Toronto",
        "montreal": "America/Toronto",
        "vancouver": "America/Vancouver",
        "calgary": "America/Edmonton",
        "ottawa": "America/Toronto",
        "edmonton": "America/Edmonton",
        # USA
        "new york": "America/New_York",
        "los angeles": "America/Los_Angeles",
        "chicago": "America/Chicago",
        "houston": "America/Chicago",
        "phoenix": "America/Phoenix",
        "san francisco": "America/Los_Angeles",
        "seattle": "America/Los_Angeles",
        "boston": "America/New_York",
        "miami": "America/New_York",
        "atlanta": "America/New_York",
        "denver": "America/Denver",
        "dallas": "America/Chicago",
        # UK
        "london": "Europe/London",
        "manchester": "Europe/London",
        "birmingham": "Europe/London",
        # Europe
        "paris": "Europe/Paris",
        "berlin": "Europe/Berlin",
        "rome": "Europe/Rome",
        "madrid": "Europe/Madrid",
        "amsterdam": "Europe/Amsterdam",
        "vienna": "Europe/Vienna",
        "prague": "Europe/Prague",
        "warsaw": "Europe/Warsaw",
        # Middle East
        "cairo": "Africa/Cairo",
        "dubai": "Asia/Dubai",
        "riyadh": "Asia/Riyadh",
        "tel aviv": "Asia/Jerusalem",
        "istanbul": "Europe/Istanbul",
        # Asia
        "tokyo": "Asia/Tokyo",
        "seoul": "Asia/Seoul",
        "beijing": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "hong kong": "Asia/Hong_Kong",
        "singapore": "Asia/Singapore",
        "bangkok": "Asia/Bangkok",
        "jakarta": "Asia/Jakarta",
        "manila": "Asia/Manila",
        "kuala lumpur": "Asia/Kuala_Lumpur",
        "mumbai": "Asia/Kolkata",
        "delhi": "Asia/Kolkata",
        # Australia
        "sydney": "Australia/Sydney",
        "melbourne": "Australia/Melbourne",
        "brisbane": "Australia/Brisbane",
        "perth": "Australia/Perth",
        # South America
        "sao paulo": "America/Sao_Paulo",
        "buenos aires": "America/Argentina/Buenos_Aires",
        "mexico city": "America/Mexico_City",
        # Africa
        "johannesburg": "Africa/Johannesburg",
        "lagos": "Africa/Lagos",
        "nairobi": "Africa/Nairobi",
    }
    
    # Platform-specific timezone hints
    PLATFORM_TIMEZONES: Dict[str, str] = {
        "upwork_ca": "America/Toronto",
        "upwork_us": "America/New_York",
        "upwork_uk": "Europe/London",
        "upwork_au": "Australia/Sydney",
        "freelancer_ca": "America/Toronto",
        "freelancer_us": "America/New_York",
        "freelancer_uk": "Europe/London",
    }
    
    @classmethod
    def get_timezone_for_country(cls, country: str) -> Optional[str]:
        """
        Get timezone for a country.
        
        Args:
            country: Country name
            
        Returns:
            Timezone identifier or None
        """
        return cls.COUNTRY_TIMEZONES.get(country.lower())
    
    @classmethod
    def get_timezone_for_city(cls, city: str) -> Optional[str]:
        """
        Get timezone for a city.
        
        Args:
            city: City name
            
        Returns:
            Timezone identifier or None
        """
        return cls.CITY_TIMEZONES.get(city.lower())
    
    @classmethod
    def get_timezone_for_platform(cls, platform: str) -> Optional[str]:
        """
        Get timezone for a platform.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Timezone identifier or None
        """
        return cls.PLATFORM_TIMEZONES.get(platform.lower())
    
    @classmethod
    def get_all_countries(cls) -> List[str]:
        """Get list of all supported countries."""
        return list(cls.COUNTRY_TIMEZONES.keys())
    
    @classmethod
    def get_all_cities(cls) -> List[str]:
        """Get list of all supported cities."""
        return list(cls.CITY_TIMEZONES.keys())
    
    @classmethod
    def get_all_platforms(cls) -> List[str]:
        """Get list of all supported platforms."""
        return list(cls.PLATFORM_TIMEZONES.keys())
    
    @classmethod
    def search_timezone(cls, query: str) -> List[str]:
        """
        Search for timezone by query.
        
        Args:
            query: Search query (country, city, or platform)
            
        Returns:
            List of matching timezone identifiers
        """
        query_lower = query.lower()
        results = []
        
        # Search countries
        for country, tz in cls.COUNTRY_TIMEZONES.items():
            if query_lower in country:
                results.append(tz)
        
        # Search cities
        for city, tz in cls.CITY_TIMEZONES.items():
            if query_lower in city:
                results.append(tz)
        
        # Search platforms
        for platform, tz in cls.PLATFORM_TIMEZONES.items():
            if query_lower in platform:
                results.append(tz)
        
        return list(set(results))  # Remove duplicates
