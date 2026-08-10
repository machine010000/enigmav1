"""
Test Constraint Detection
"""

import pytest

from app.creativity.contracts import (
    ConstraintType,
    ConstraintSeverity,
    CreativeConstraint,
    CreativeOpportunityContext,
)
from app.creativity.constraints import ConstraintDetector


class TestConstraintDetector:
    """Test constraint detection."""
    
    def test_detect_no_constraints(self):
        """Test context with no constraints."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            portfolio_strength=0.8,
            review_strength=0.8,
            evidence_readiness=0.8,
            knowledge_readiness=0.8,
            execution_readiness=0.8,
            competition_level=0.3,
            budget=100.0,
            application_cost=5.0,
            expected_value=95.0,
            knowledge_freshness=0.8,
            confidence_score=0.8,
            experience_strength=0.8,
            risk_score=0.3,
        )
        
        constraints = detector.detect_constraints(context)
        
        # Should have minimal or no constraints
        assert len(constraints) <= 2
    
    def test_detect_portfolio_constraint(self):
        """Test detection of portfolio constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
        )
        
        constraints = detector.detect_constraints(context)
        
        portfolio_constraints = [c for c in constraints if c.constraint_type == ConstraintType.NO_PORTFOLIO]
        assert len(portfolio_constraints) == 1
        assert portfolio_constraints[0].severity == ConstraintSeverity.HIGH
        assert portfolio_constraints[0].blocking is False
    
    def test_detect_review_constraint(self):
        """Test detection of review constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            review_strength=0.2,
        )
        
        constraints = detector.detect_constraints(context)
        
        review_constraints = [c for c in constraints if c.constraint_type == ConstraintType.NO_REVIEWS]
        assert len(review_constraints) == 1
        assert review_constraints[0].severity == ConstraintSeverity.HIGH
    
    def test_detect_evidence_constraint(self):
        """Test detection of evidence constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            evidence_readiness=0.3,
        )
        
        constraints = detector.detect_constraints(context)
        
        evidence_constraints = [c for c in constraints if c.constraint_type == ConstraintType.LOW_EVIDENCE]
        assert len(evidence_constraints) == 1
        assert evidence_constraints[0].severity == ConstraintSeverity.MEDIUM
    
    def test_detect_competition_constraint(self):
        """Test detection of competition constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            competition_level=0.8,
        )
        
        constraints = detector.detect_constraints(context)
        
        competition_constraints = [c for c in constraints if c.constraint_type == ConstraintType.HIGH_COMPETITION]
        assert len(competition_constraints) == 1
    
    def test_detect_budget_constraint(self):
        """Test detection of budget constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            budget=10.0,
            application_cost=8.0,
        )
        
        constraints = detector.detect_constraints(context)
        
        budget_constraints = [c for c in constraints if c.constraint_type == ConstraintType.LOW_BUDGET]
        assert len(budget_constraints) == 1
        assert budget_constraints[0].blocking is True
    
    def test_detect_application_cost_constraint(self):
        """Test detection of application cost constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            application_cost=15.0,
            expected_value=40.0,
        )
        
        constraints = detector.detect_constraints(context)
        
        cost_constraints = [c for c in constraints if c.constraint_type == ConstraintType.HIGH_APPLICATION_COST]
        assert len(cost_constraints) == 1
        assert cost_constraints[0].blocking is True
    
    def test_detect_stale_knowledge_constraint(self):
        """Test detection of stale knowledge constraint."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            knowledge_freshness=0.3,
        )
        
        constraints = detector.detect_constraints(context)
        
        stale_constraints = [c for c in constraints if c.constraint_type == ConstraintType.STALE_KNOWLEDGE]
        assert len(stale_constraints) == 1
    
    def test_detect_multiple_constraints(self):
        """Test detection of multiple constraints."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            review_strength=0.1,
            competition_level=0.8,
            knowledge_freshness=0.3,
        )
        
        constraints = detector.detect_constraints(context)
        
        # Should detect multiple constraints
        assert len(constraints) >= 3
        
        # Check specific constraints
        constraint_types = {c.constraint_type for c in constraints}
        assert ConstraintType.NO_PORTFOLIO in constraint_types
        assert ConstraintType.NO_REVIEWS in constraint_types
        assert ConstraintType.HIGH_COMPETITION in constraint_types
    
    def test_get_blocking_constraints(self):
        """Test filtering blocking constraints."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            budget=10.0,
            application_cost=8.0,
        )
        
        constraints = detector.detect_constraints(context)
        blocking = detector.get_blocking_constraints(constraints)
        
        assert len(blocking) >= 1
        assert all(c.blocking for c in blocking)
    
    def test_get_constraints_by_type(self):
        """Test filtering by constraint type."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            review_strength=0.2,
        )
        
        constraints = detector.detect_constraints(context)
        portfolio_constraints = detector.get_constraints_by_type(constraints, ConstraintType.NO_PORTFOLIO)
        
        assert len(portfolio_constraints) == 1
        assert portfolio_constraints[0].constraint_type == ConstraintType.NO_PORTFOLIO
    
    def test_get_constraints_by_severity(self):
        """Test filtering by severity."""
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            review_strength=0.2,
        )
        
        constraints = detector.detect_constraints(context)
        high_severity = detector.get_constraints_by_severity(constraints, ConstraintSeverity.HIGH)
        
        assert len(high_severity) >= 2
        assert all(c.severity == ConstraintSeverity.HIGH for c in high_severity)
