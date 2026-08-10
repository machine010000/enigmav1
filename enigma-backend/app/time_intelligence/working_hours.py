"""
Working Hours

Working hours configuration and overlap analysis.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from app.time_intelligence.contracts import (
    WorkingHours,
    WorkingHourOverlap,
    WorkingHourStatus,
)
from app.time_intelligence.timezone_service import TimezoneService


class WorkingHoursAnalyzer:
    """
    Analyzer for working hours and overlap.
    
    Analyzes working hour overlap between customer and Enigma.
    """
    
    def __init__(self, timezone_service: Optional[TimezoneService] = None):
        """
        Initialize working hours analyzer.
        
        Args:
            timezone_service: Timezone service instance
        """
        self.timezone_service = timezone_service or TimezoneService()
    
    def analyze_overlap(
        self,
        customer_working_hours: WorkingHours,
        enigma_working_hours: Optional[WorkingHours] = None,
        analysis_date: Optional[str] = None,
    ) -> WorkingHourOverlap:
        """
        Analyze working hour overlap.
        
        Args:
            customer_working_hours: Customer working hours
            enigma_working_hours: Enigma working hours (default: 9-18 Cairo)
            analysis_date: Date to analyze (default: today)
            
        Returns:
            WorkingHourOverlap
        """
        if enigma_working_hours is None:
            enigma_working_hours = WorkingHours(
                start_hour=9,
                end_hour=18,
                timezone=self.timezone_service.enigma_timezone,
            )
        
        if analysis_date is None:
            analysis_date = self.timezone_service.get_current_time("UTC")
        
        # Calculate overlap
        overlap_hours = self._calculate_overlap_hours(
            customer_working_hours,
            enigma_working_hours,
        )
        
        # Determine status
        status = self._determine_status(overlap_hours)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            status,
            overlap_hours,
            customer_working_hours,
            enigma_working_hours,
        )
        
        return WorkingHourOverlap(
            status=status,
            overlap_hours=overlap_hours,
            customer_working_hours=customer_working_hours,
            enigma_working_hours=enigma_working_hours,
            analysis_date=analysis_date,
            recommendations=recommendations,
        )
    
    def _calculate_overlap_hours(
        self,
        customer_hours: WorkingHours,
        enigma_hours: WorkingHours,
    ) -> float:
        """
        Calculate overlapping working hours.
        
        Args:
            customer_hours: Customer working hours
            enigma_hours: Enigma working hours
            
        Returns:
            Overlapping hours
        """
        # Get timezone offsets
        customer_offset = self.timezone_service.get_utc_offset(customer_hours.timezone)
        enigma_offset = self.timezone_service.get_utc_offset(enigma_hours.timezone)
        
        # Convert customer hours to Enigma timezone for comparison
        customer_start_enigma = (customer_hours.start_hour - customer_offset + enigma_offset) % 24
        customer_end_enigma = (customer_hours.end_hour - customer_offset + enigma_offset) % 24
        
        # Calculate overlap
        enigma_start = enigma_hours.start_hour
        enigma_end = enigma_hours.end_hour
        
        # Handle overnight working hours
        if customer_start_enigma > customer_end_enigma:
            # Customer works overnight
            overlap_1 = max(0, min(enigma_end, 24) - max(enigma_start, customer_start_enigma))
            overlap_2 = max(0, min(customer_end_enigma, 24) - max(customer_start_enigma, 0))
            overlap = overlap_1 + overlap_2
        else:
            # Normal working hours
            overlap_start = max(enigma_start, customer_start_enigma)
            overlap_end = min(enigma_end, customer_end_enigma)
            overlap = max(0, overlap_end - overlap_start)
        
        return float(overlap)
    
    def _determine_status(self, overlap_hours: float) -> WorkingHourStatus:
        """
        Determine overlap status.
        
        Args:
            overlap_hours: Overlapping hours
            
        Returns:
            WorkingHourStatus
        """
        if overlap_hours <= 0:
            return WorkingHourStatus.NO_OVERLAP
        elif overlap_hours < 2:
            return WorkingHourStatus.PARTIAL_OVERLAP
        else:
            return WorkingHourStatus.OVERLAP
    
    def _generate_recommendations(
        self,
        status: WorkingHourStatus,
        overlap_hours: float,
        customer_hours: WorkingHours,
        enigma_hours: WorkingHours,
    ) -> List[str]:
        """
        Generate recommendations based on overlap analysis.
        
        Args:
            status: Overlap status
            overlap_hours: Overlapping hours
            customer_hours: Customer working hours
            enigma_hours: Enigma working hours
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if status == WorkingHourStatus.NO_OVERLAP:
            recommendations.append("No working hour overlap - consider flexible scheduling")
            recommendations.append("Schedule communications outside normal working hours")
        elif status == WorkingHourStatus.PARTIAL_OVERLAP:
            recommendations.append(f"Limited overlap ({overlap_hours:.1f} hours) - plan carefully")
            recommendations.append("Prioritize communications during overlap window")
        
        return recommendations
    
    def is_customer_working_now(
        self,
        customer_timezone: str,
        customer_working_hours: Optional[WorkingHours] = None,
    ) -> bool:
        """
        Check if customer is currently working.
        
        Args:
            customer_timezone: Customer timezone
            customer_working_hours: Customer working hours
            
        Returns:
            True if customer is working, False otherwise
        """
        if customer_working_hours is None:
            customer_working_hours = WorkingHours(
                start_hour=9,
                end_hour=18,
                timezone=customer_timezone,
            )
        
        current_time = self.timezone_service.get_current_time(customer_timezone)
        current_dt = datetime.fromisoformat(current_time)
        
        return customer_working_hours.is_within_hours(current_dt)
