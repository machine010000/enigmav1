"""
Test Creativity Contracts
"""

import pytest
from dataclasses import FrozenInstanceError

from app.creativity.contracts import (
    ConstraintType,
    ConstraintSeverity,
    CreativeConstraint,
    StrategyCategory,
    StrategyStatus,
    CreativeStrategy,
    StrategyEvaluation,
    CreativeOpportunityContext,
    CreativityResult,
)
from app.marketplace.economics import EconomicsValue, VerificationStatus
from app.marketplace.contracts import MarketplacePlatform


class TestConstraintType:
    """Test ConstraintType enum."""
    
    def test_constraint_type_values(self):
        """Test that constraint types have expected values."""
        assert ConstraintType.NO_PORTFOLIO.value == "no_portfolio"
        assert ConstraintType.NO_REVIEWS.value == "no_reviews"
        assert ConstraintType.LOW_EVIDENCE.value == "low_evidence"
        assert ConstraintType.HIGH_COMPETITION.value == "high_competition"
    
    def test_constraint_type_count(self):
        """Test that we have the expected number of constraint types."""
        # Should have at least the basic types
        assert len(ConstraintType) >= 10


class TestConstraintSeverity:
    """Test ConstraintSeverity enum."""
    
    def test_severity_values(self):
        """Test that severity levels have expected values."""
        assert ConstraintSeverity.BLOCKING.value == "blocking"
        assert ConstraintSeverity.HIGH.value == "high"
        assert ConstraintSeverity.MEDIUM.value == "medium"
        assert ConstraintSeverity.LOW.value == "low"
    
    def test_severity_ordering(self):
        """Test that severity levels are properly ordered."""
        severities = [ConstraintSeverity.BLOCKING, ConstraintSeverity.HIGH, 
                     ConstraintSeverity.MEDIUM, ConstraintSeverity.LOW]
        assert len(severities) == 4


class TestCreativeConstraint:
    """Test CreativeConstraint dataclass."""
    
    def test_constraint_creation(self):
        """Test creating a constraint."""
        constraint = CreativeConstraint(
            constraint_type=ConstraintType.NO_PORTFOLIO,
            severity=ConstraintSeverity.HIGH,
            impact="Reduces client trust",
            source="portfolio_analysis",
            confidence=0.9,
            blocking=False,
            description="Weak portfolio limits capability demonstration",
        )
        
        assert constraint.constraint_type == ConstraintType.NO_PORTFOLIO
        assert constraint.severity == ConstraintSeverity.HIGH
        assert constraint.impact == "Reduces client trust"
        assert constraint.confidence == 0.9
        assert constraint.blocking is False
    
    def test_constraint_immutability(self):
        """Test that constraints are immutable."""
        constraint = CreativeConstraint(
            constraint_type=ConstraintType.NO_PORTFOLIO,
            severity=ConstraintSeverity.HIGH,
            impact="Reduces client trust",
            source="portfolio_analysis",
            confidence=0.9,
            blocking=False,
            description="Weak portfolio limits capability demonstration",
        )
        
        with pytest.raises(FrozenInstanceError):
            constraint.confidence = 0.8
    
    def test_constraint_to_dict(self):
        """Test constraint serialization."""
        constraint = CreativeConstraint(
            constraint_type=ConstraintType.NO_PORTFOLIO,
            severity=ConstraintSeverity.HIGH,
            impact="Reduces client trust",
            source="portfolio_analysis",
            confidence=0.9,
            blocking=False,
            description="Weak portfolio limits capability demonstration",
        )
        
        data = constraint.to_dict()
        
        assert data["constraint_type"] == "no_portfolio"
        assert data["severity"] == "high"
        assert data["confidence"] == 0.9
        assert data["blocking"] is False


class TestStrategyCategory:
    """Test StrategyCategory enum."""
    
    def test_category_values(self):
        """Test that strategy categories have expected values."""
        assert StrategyCategory.PRICE_ADJUSTMENT.value == "price_adjustment"
        assert StrategyCategory.SCOPE_REDUCTION.value == "scope_reduction"
        assert StrategyCategory.PROOF_OF_WORK.value == "proof_of_work"
        assert StrategyCategory.RESEARCH_FIRST.value == "research_first"
    
    def test_category_count(self):
        """Test that we have the expected number of categories."""
        assert len(StrategyCategory) >= 10


class TestCreativeStrategy:
    """Test CreativeStrategy dataclass."""
    
    def test_strategy_creation(self):
        """Test creating a strategy."""
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        assert strategy.strategy_id == "test_strategy"
        assert strategy.name == "Test Strategy"
        assert strategy.category == StrategyCategory.PROOF_OF_WORK
        assert ConstraintType.NO_PORTFOLIO in strategy.target_constraints
    
    def test_strategy_immutability(self):
        """Test that strategies are immutable."""
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        with pytest.raises(FrozenInstanceError):
            strategy.name = "Updated Name"
    
    def test_strategy_with_economics(self):
        """Test strategy with economic effects."""
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PRICE_ADJUSTMENT,
            target_constraints={ConstraintType.NO_REVIEWS},
            economic_effect=EconomicsValue(
                value=-0.2,
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
        )
        
        assert strategy.economic_effect is not None
        assert strategy.economic_effect.value == -0.2
    
    def test_strategy_to_dict(self):
        """Test strategy serialization."""
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        data = strategy.to_dict()
        
        assert data["strategy_id"] == "test_strategy"
        assert data["name"] == "Test Strategy"
        assert data["category"] == "proof_of_work"
        assert "no_portfolio" in data["target_constraints"]


class TestCreativeOpportunityContext:
    """Test CreativeOpportunityContext dataclass."""
    
    def test_context_creation(self):
        """Test creating an opportunity context."""
        context = CreativeOpportunityContext(
            work_specification="SEO optimization project",
            profession="SEO Specialist",
            expert_domain="seo",
            portfolio_strength=0.3,
            review_strength=0.2,
            competition_level=0.7,
        )
        
        assert context.work_specification == "SEO optimization project"
        assert context.portfolio_strength == 0.3
        assert context.competition_level == 0.7
    
    def test_context_with_economics(self):
        """Test context with economics data."""
        context = CreativeOpportunityContext(
            budget=100.0,
            estimated_revenue=200.0,
            application_cost=8.0,
            expected_value=192.0,
        )
        
        assert context.budget == 100.0
        assert context.application_cost == 8.0
        assert context.expected_value == 192.0
    
    def test_context_with_constraints(self):
        """Test context with constraints."""
        constraint = CreativeConstraint(
            constraint_type=ConstraintType.NO_PORTFOLIO,
            severity=ConstraintSeverity.HIGH,
            impact="Reduces client trust",
            source="portfolio_analysis",
            confidence=0.9,
            blocking=False,
            description="Weak portfolio limits capability demonstration",
        )
        
        context = CreativeOpportunityContext(
            constraints=[constraint],
        )
        
        assert len(context.constraints) == 1
        assert context.constraints[0].constraint_type == ConstraintType.NO_PORTFOLIO
    
    def test_context_to_dict(self):
        """Test context serialization."""
        context = CreativeOpportunityContext(
            portfolio_strength=0.5,
            review_strength=0.5,
        )
        
        data = context.to_dict()
        
        assert data["portfolio_strength"] == 0.5
        assert data["review_strength"] == 0.5


class TestStrategyEvaluation:
    """Test StrategyEvaluation dataclass."""
    
    def test_evaluation_creation(self):
        """Test creating a strategy evaluation."""
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation = StrategyEvaluation(
            strategy=strategy,
            benefit_score=0.8,
            feasibility_score=0.7,
            economic_viability_score=0.6,
            risk_score=0.3,
            confidence_score=0.7,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.6,
            execution_fit_score=0.7,
            reversibility_score=0.8,
            complexity_score=0.4,
            overall_score=0.7,
            addressed_constraints={ConstraintType.NO_PORTFOLIO},
            introduced_risks=set(),
            recommendation_reason="High benefit and feasibility",
            penalty_reasons=[],
        )
        
        assert evaluation.overall_score == 0.7
        assert evaluation.benefit_score == 0.8
        assert ConstraintType.NO_PORTFOLIO in evaluation.addressed_constraints
    
    def test_evaluation_to_dict(self):
        """Test evaluation serialization."""
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation = StrategyEvaluation(
            strategy=strategy,
            benefit_score=0.8,
            feasibility_score=0.7,
            economic_viability_score=0.6,
            risk_score=0.3,
            confidence_score=0.7,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.6,
            execution_fit_score=0.7,
            reversibility_score=0.8,
            complexity_score=0.4,
            overall_score=0.7,
            addressed_constraints={ConstraintType.NO_PORTFOLIO},
            introduced_risks=set(),
            recommendation_reason="High benefit and feasibility",
            penalty_reasons=[],
        )
        
        data = evaluation.to_dict()
        
        assert data["overall_score"] == 0.7
        assert data["benefit_score"] == 0.8
        assert "no_portfolio" in data["addressed_constraints"]


class TestCreativityResult:
    """Test CreativityResult dataclass."""
    
    def test_result_creation(self):
        """Test creating a creativity result."""
        context = CreativeOpportunityContext()
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation = StrategyEvaluation(
            strategy=strategy,
            benefit_score=0.8,
            feasibility_score=0.7,
            economic_viability_score=0.6,
            risk_score=0.3,
            confidence_score=0.7,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.6,
            execution_fit_score=0.7,
            reversibility_score=0.8,
            complexity_score=0.4,
            overall_score=0.7,
            addressed_constraints={ConstraintType.NO_PORTFOLIO},
            introduced_risks=set(),
            recommendation_reason="High benefit and feasibility",
            penalty_reasons=[],
        )
        
        result = CreativityResult(
            opportunity_context=context,
            candidate_strategies=[strategy],
            ranked_strategies=[evaluation],
            constraints=[],
            unresolved_constraints=[],
            research_required=False,
            learning_required=False,
            clarification_required=False,
            confidence=0.7,
            explanation="Generated 1 viable strategy",
        )
        
        assert result.confidence == 0.7
        assert len(result.ranked_strategies) == 1
        assert result.research_required is False
    
    def test_result_to_dict(self):
        """Test result serialization."""
        context = CreativeOpportunityContext()
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation = StrategyEvaluation(
            strategy=strategy,
            benefit_score=0.8,
            feasibility_score=0.7,
            economic_viability_score=0.6,
            risk_score=0.3,
            confidence_score=0.7,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.6,
            execution_fit_score=0.7,
            reversibility_score=0.8,
            complexity_score=0.4,
            overall_score=0.7,
            addressed_constraints={ConstraintType.NO_PORTFOLIO},
            introduced_risks=set(),
            recommendation_reason="High benefit and feasibility",
            penalty_reasons=[],
        )
        
        result = CreativityResult(
            opportunity_context=context,
            candidate_strategies=[strategy],
            ranked_strategies=[evaluation],
            constraints=[],
            unresolved_constraints=[],
            research_required=False,
            learning_required=False,
            clarification_required=False,
            confidence=0.7,
            explanation="Generated 1 viable strategy",
        )
        
        data = result.to_dict()
        
        assert data["confidence"] == 0.7
        assert len(data["ranked_strategies"]) == 1
        assert data["research_required"] is False
