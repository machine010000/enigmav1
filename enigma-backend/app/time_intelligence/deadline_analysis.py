"""
Deadline Analysis

Analysis of deadline feasibility and risk.
"""

from datetime import datetime, timedelta
from typing import Optional, List

from app.time_intelligence.contracts import (
    DeadlineAnalysis,
    DeadlineRisk,
    DayType,
)
from app.time_intelligence.timezone_service import TimezoneService
from app.time_intelligence.customer_time import CustomerTimeAnalyzer


class DeadlineAnalyzer:
    """
    Analyzer for deadline feasibility and risk.
    
    Evaluates deadlines considering timezone differences, working hours,
    and time constraints.
    """
    
    def __init__(
        self,
        timezone_service: Optional[TimezoneService] = None,
        customer_time_analyzer: Optional[CustomerTimeAnalyzer] = None,
    ):
        """
        Initialize deadline analyzer.
        
        Args:
            timezone_service: Timezone service instance
            customer_time_analyzer: Customer time analyzer instance
        """
        self.timezone_service = timezone_service or TimezoneService()
        self.customer_time_analyzer = customer_time_analyzer or CustomerTimeAnalyzer(self.timezone_service)
    
    def analyze_deadline(
        self,
        deadline: str,
        deadline_timezone: str,
        enigma_timezone: Optional[str] = None,
        working_hours_start: int = 9,
        working_hours_end: int = 18,
    ) -> DeadlineAnalysis:
        """
        Analyze deadline feasibility and risk.
        
        Args:
            deadline: ISO format deadline string
            deadline_timezone: Timezone of the deadline
            enigma_timezone: Enigma's timezone (default: service default)
            working_hours_start: Start of working hours (0-23)
            working_hours_end: End of working hours (0-23)
            
        Returns:
            DeadlineAnalysis
        """
        if enigma_timezone is None:
            enigma_timezone = self.timezone_service.enigma_timezone
        
        # Convert deadline to Enigma timezone
        conversion = self.timezone_service.convert_time(deadline, deadline_timezone, enigma_timezone)
        enigma_deadline = conversion.target_time
        
        # Parse deadline datetime
        try:
            deadline_dt = datetime.fromisoformat(deadline)
            enigma_deadline_dt = datetime.fromisoformat(enigma_deadline)
        except ValueError:
            return DeadlineAnalysis(
                deadline=deadline,
                deadline_timezone=deadline_timezone,
                enigma_deadline=deadline,
                offset_hours=0,
                risk=DeadlineRisk.UNKNOWN,
                is_feasible=False,
                is_working_hours=False,
                is_weekend=False,
                reason="Invalid deadline format",
            )
        
        # Determine day type
        day_type = self.timezone_service.determine_day_type(deadline_dt, deadline_timezone)
        is_weekend = day_type == DayType.WEEKEND
        
        # Check if within working hours
        is_working_hours = working_hours_start <= deadline_dt.hour < working_hours_end
        
        # Calculate risk
        risk = self._calculate_risk(
            deadline_dt,
            enigma_deadline_dt,
            is_weekend,
            is_working_hours,
            conversion.offset_hours,
        )
        
        # Determine feasibility
        is_feasible = risk != DeadlineRisk.CRITICAL
        
        # Generate reason and recommendations
        reason, recommendations = self._generate_analysis(
            risk,
            is_weekend,
            is_working_hours,
            conversion.offset_hours,
        )
        
        return DeadlineAnalysis(
            deadline=deadline,
            deadline_timezone=deadline_timezone,
            enigma_deadline=enigma_deadline,
            offset_hours=conversion.offset_hours,
            risk=risk,
            is_feasible=is_feasible,
            is_working_hours=is_working_hours,
            is_weekend=is_weekend,
            reason=reason,
            recommendations=recommendations,
        )
    
    def _calculate_risk(
        self,
        deadline_dt: datetime,
        enigma_deadline_dt: datetime,
        is_weekend: bool,
        is_working_hours: bool,
        offset_hours: float,
    ) -> DeadlineRisk:
        """
        Calculate deadline risk level.
        
        Args:
            deadline_dt: Deadline in customer timezone
            enigma_deadline_dt: Deadline in Enigma timezone
            is_weekend: Whether deadline is on weekend
            is_working_hours: Whether deadline is within working hours
            offset_hours: Timezone offset
            
        Returns:
            DeadlineRisk
        """
        now = datetime.utcnow()
        time_remaining = (deadline_dt - now).total_seconds() / 3600  # hours
        
        # Critical: Very short time or overnight deadline
        if time_remaining < 2:
            return DeadlineRisk.CRITICAL
        
        # High: Short time, weekend, or outside working hours
        if time_remaining < 12 or is_weekend or not is_working_hours:
            return DeadlineRisk.HIGH
        
        # Medium: Moderate time with some constraints
        if time_remaining < 24 or abs(offset_hours) > 8:
            return DeadlineRisk.MEDIUM
        
        # Low: Sufficient time, good conditions
        return DeadlineRisk.LOW
    
    def _generate_analysis(
        self,
        risk: DeadlineRisk,
        is_weekend: bool,
        is_working_hours: bool,
        offset_hours: float,
    ) -> tuple[Optional[str], List[str]]:
        """
        Generate analysis reason and recommendations.
        
        Args:
            risk: Risk level
            is_weekend: Whether deadline is on weekend
            is_working_hours: Whether deadline is within working hours
            offset_hours: Timezone offset
            
        Returns:
            Tuple of (reason, recommendations)
        """
        reasons = []
        recommendations = []
        
        if risk == DeadlineRisk.CRITICAL:
            reasons.append("Critical deadline with insufficient time")
            recommendations.append("Immediate action required")
            recommendations.append("Consider requesting deadline extension")
        
        elif risk == DeadlineRisk.HIGH:
            if is_weekend:
                reasons.append("Deadline falls on weekend")
                recommendations.append("Plan for weekend work or request extension")
            if not is_working_hours:
                reasons.append("Deadline outside working hours")
                recommendations.append("Schedule work outside normal hours")
            if abs(offset_hours) > 8:
                reasons.append(f"Large timezone offset ({offset_hours:+.1f} hours)")
                recommendations.append("Account for timezone difference in planning")
        
        elif risk == DeadlineRisk.MEDIUM:
            if abs(offset_hours) > 4:
                reasons.append(f"Moderate timezone offset ({offset_hours:+.1f} hours)")
                recommendations.append("Consider timezone in communication timing")
        
        reason = "; ".join(reasons) if reasons else "Deadline appears feasible"
        
        return reason, recommendations
    
    def calculate_response_time_feasibility(
        self,
        deadline: str,
        deadline_timezone: str,
        required_hours: float = 2,
    ) -> bool:
        """
        Check if there's sufficient time to respond before deadline.
        
        Args:
            deadline: ISO format deadline string
            deadline_timezone: Timezone of the deadline
            required_hours: Hours required for response
            
        Returns:
            True if feasible, False otherwise
        """
        try:
            deadline_dt = datetime.fromisoformat(deadline)
            now = datetime.utcnow()
            time_remaining = (deadline_dt - now).total_seconds() / 3600
            
            return time_remaining >= required_hours
        except ValueError:
            return False
