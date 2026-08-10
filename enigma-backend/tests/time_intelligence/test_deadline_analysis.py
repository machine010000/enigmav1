"""
Test Deadline Analysis

Tests for deadline feasibility and risk analysis.
"""

import pytest
from datetime import datetime, timedelta

from app.time_intelligence.deadline_analysis import DeadlineAnalyzer
from app.time_intelligence.contracts import (
    DeadlineRisk,
    DayType,
)


class TestDeadlineAnalyzer:
    """Test DeadlineAnalyzer."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = DeadlineAnalyzer()
        assert analyzer is not None
        assert analyzer.timezone_service is not None
    
    def test_analyze_deadline_feasible(self):
        """Test analyzing a feasible deadline."""
        analyzer = DeadlineAnalyzer()
        
        # Deadline 72 hours in the future (more feasible)
        deadline = (datetime.utcnow() + timedelta(hours=72)).isoformat()
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.deadline == deadline
        assert analysis.risk in [DeadlineRisk.LOW, DeadlineRisk.MEDIUM, DeadlineRisk.HIGH]
        assert analysis.is_feasible is True
    
    def test_analyze_deadline_critical(self):
        """Test analyzing a critical deadline."""
        analyzer = DeadlineAnalyzer()
        
        # Deadline 1 hour in the future
        deadline = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.risk == DeadlineRisk.CRITICAL
        assert analysis.is_feasible is False
    
    def test_analyze_deadline_weekend(self):
        """Test analyzing a deadline on weekend."""
        analyzer = DeadlineAnalyzer()
        
        # Saturday
        deadline = datetime(2026, 8, 16, 17, 0, 0).isoformat()  # 2026-08-16 is a Saturday
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.is_weekend is True
        assert analysis.risk in [DeadlineRisk.HIGH, DeadlineRisk.CRITICAL]
    
    def test_analyze_deadline_offset(self):
        """Test deadline offset calculation."""
        analyzer = DeadlineAnalyzer()
        
        deadline = "2026-08-10T17:00:00"
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
            enigma_timezone="Africa/Cairo",
        )
        
        assert analysis.offset_hours != 0
        assert analysis.enigma_deadline != deadline
    
    def test_calculate_response_time_feasibility(self):
        """Test response time feasibility check."""
        analyzer = DeadlineAnalyzer()
        
        # Deadline 4 hours in the future, requires 2 hours
        deadline = (datetime.utcnow() + timedelta(hours=4)).isoformat()
        
        feasible = analyzer.calculate_response_time_feasibility(
            deadline=deadline,
            deadline_timezone="America/Toronto",
            required_hours=2,
        )
        
        assert feasible is True
        
        # Deadline 1 hour in the future, requires 2 hours
        deadline_short = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        feasible_short = analyzer.calculate_response_time_feasibility(
            deadline=deadline_short,
            deadline_timezone="America/Toronto",
            required_hours=2,
        )
        
        assert feasible_short is False
    
    def test_analyze_deadline_invalid_format(self):
        """Test analyzing deadline with invalid format."""
        analyzer = DeadlineAnalyzer()
        
        analysis = analyzer.analyze_deadline(
            deadline="invalid-date",
            deadline_timezone="America/Toronto",
        )
        
        assert analysis.is_feasible is False
        assert analysis.risk == DeadlineRisk.UNKNOWN
        assert "Invalid deadline format" in analysis.reason
    
    def test_analyze_deadline_recommendations(self):
        """Test that analysis includes recommendations."""
        analyzer = DeadlineAnalyzer()
        
        # Critical deadline
        deadline = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        analysis = analyzer.analyze_deadline(
            deadline=deadline,
            deadline_timezone="America/Toronto",
        )
        
        assert len(analysis.recommendations) > 0
