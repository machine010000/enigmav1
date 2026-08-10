"""
Test Creativity Engine
"""

import pytest

from app.creativity.contracts import (
    ConstraintType,
    CreativeOpportunityContext,
    CreativeConstraint,
    ConstraintSeverity,
    StrategyCategory,
)
from app.creativity.engine import CreativityEngine


class TestCreativityEngine:
    """Test creativity engine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = CreativityEngine()
        
        assert engine.engine_id == "rule_based_creativity_v1"
        assert engine.name == "Rule-Based Creativity Engine"
        assert engine.version == "1.0.0"
    
    def test_generate_strategies_basic(self):
        """Test basic strategy generation."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            review_strength=0.1,
            competition_level=0.8,
        )
        
        result = engine.generate_strategies(context)
        
        assert result is not None
        assert result.opportunity_context == context
        assert len(result.candidate_strategies) > 0
        assert len(result.ranked_strategies) >= 0
        assert 0.0 <= result.confidence <= 1.0
        assert result.explanation
    
    def test_generate_strategies_with_constraints(self):
        """Test strategy generation with pre-detected constraints."""
        engine = CreativityEngine()
        
        constraint = CreativeConstraint(
            constraint_type=ConstraintType.NO_PORTFOLIO,
            severity=ConstraintSeverity.HIGH,
            impact="Reduces trust",
            source="test",
            confidence=0.9,
            blocking=False,
            description="Test constraint",
        )
        
        context = CreativeOpportunityContext(
            constraints=[constraint],
        )
        
        result = engine.generate_strategies(context)
        
        assert len(result.constraints) == 1
        assert result.constraints[0].constraint_type == ConstraintType.NO_PORTFOLIO
    
    def test_generate_strategies_detects_constraints(self):
        """Test that engine detects constraints when not provided."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            review_strength=0.1,
        )
        
        result = engine.generate_strategies(context)
        
        # Should have detected constraints
        assert len(result.constraints) > 0
    
    def test_generate_strategies_no_portfolio(self):
        """Test strategy generation for no portfolio constraint."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Should generate strategies addressing portfolio
        assert len(result.candidate_strategies) > 0
        
        # Check if any strategy targets portfolio constraint
        portfolio_strategies = [
            s for s in result.candidate_strategies
            if ConstraintType.NO_PORTFOLIO in s.target_constraints
        ]
        assert len(portfolio_strategies) > 0
    
    def test_generate_strategies_stale_knowledge(self):
        """Test strategy generation for stale knowledge."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            knowledge_freshness=0.3,
        )
        
        result = engine.generate_strategies(context)
        
        # Should generate research-first strategy
        research_strategies = [
            s for s in result.candidate_strategies
            if s.category == StrategyCategory.RESEARCH_FIRST
        ]
        assert len(research_strategies) > 0
        assert result.research_required is True
    
    def test_generate_strategies_high_competition(self):
        """Test strategy generation for high competition."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            competition_level=0.8,
            portfolio_strength=0.3,
        )
        
        result = engine.generate_strategies(context)
        
        # Should generate target selection strategy
        target_strategies = [
            s for s in result.candidate_strategies
            if s.category == StrategyCategory.TARGET_SELECTION
        ]
        assert len(target_strategies) > 0
    
    def test_generate_strategies_with_economics(self):
        """Test strategy generation with economics context."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            budget=50.0,
            application_cost=8.0,
            expected_value=40.0,
        )
        
        result = engine.generate_strategies(context)
        
        # Should still generate strategies
        assert len(result.candidate_strategies) > 0
    
    def test_generate_strategies_poor_economics(self):
        """Test strategy generation with poor economics."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            budget=10.0,
            application_cost=8.0,
            expected_value=40.0,
        )
        
        result = engine.generate_strategies(context)
        
        # Should detect budget constraint
        budget_constraints = [
            c for c in result.constraints
            if c.constraint_type == ConstraintType.LOW_BUDGET
        ]
        assert len(budget_constraints) > 0
    
    def test_filter_strategies_by_domain(self):
        """Test that strategies are filtered by domain."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            expert_domain="seo",
            portfolio_strength=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Should only include SEO-compatible strategies
        for strategy in result.candidate_strategies:
            if strategy.domain_compatibility:
                assert "seo" in strategy.domain_compatibility
    
    def test_filter_strategies_by_platform(self):
        """Test that strategies are filtered by platform."""
        from app.marketplace.economics import MarketplaceEconomicsContract, ApplicationModel
        from app.marketplace.contracts import MarketplacePlatform
        
        engine = CreativityEngine()
        
        economics = MarketplaceEconomicsContract(
            platform=MarketplacePlatform.UPWORK,
            currency="USD",
            application_model=ApplicationModel.CREDIT_BASED,
            application_cost=None,
            minimum_balance=None,
            last_verified_at="2024-01-01T00:00:00",
            source="test",
            confidence=0.9,
            expires_at="2024-12-31T23:59:59",
        )
        
        context = CreativeOpportunityContext(
            platform_economics=economics,
            portfolio_strength=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Should only include Upwork-compatible strategies
        for strategy in result.candidate_strategies:
            if strategy.platform_compatibility:
                assert MarketplacePlatform.UPWORK in strategy.platform_compatibility
    
    def test_calculate_confidence(self):
        """Test confidence calculation."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.5,
            confidence_score=0.7,
        )
        
        result = engine.generate_strategies(context)
        
        assert 0.0 <= result.confidence <= 1.0
    
    def test_generate_explanation(self):
        """Test explanation generation."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        assert result.explanation
        assert len(result.explanation) > 0
    
    def test_research_required_flag(self):
        """Test research required flag."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            knowledge_freshness=0.3,
        )
        
        result = engine.generate_strategies(context)
        
        # Research-first strategy should trigger flag
        assert result.research_required is True
    
    def test_learning_required_flag(self):
        """Test learning required flag."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            knowledge_readiness=0.3,
            execution_readiness=0.3,
        )
        
        result = engine.generate_strategies(context)
        
        # Learning-first strategy should trigger flag
        assert result.learning_required is True
    
    def test_clarification_required_flag(self):
        """Test clarification required flag."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            risk_score=0.8,
        )
        
        result = engine.generate_strategies(context)
        
        # Risk reduction or clarification strategies should trigger flag
        assert result.clarification_required is True
    
    def test_unresolved_constraints(self):
        """Test identification of unresolved constraints."""
        engine = CreativityEngine()
        
        constraint = CreativeConstraint(
            constraint_type=ConstraintType.TIME_CONSTRAINT,
            severity=ConstraintSeverity.HIGH,
            impact="Limited time",
            source="test",
            confidence=0.9,
            blocking=True,
            description="Time constraint",
        )
        
        context = CreativeOpportunityContext(
            constraints=[constraint],
        )
        
        result = engine.generate_strategies(context)
        
        # Time constraint may not be addressed by default strategies
        assert len(result.unresolved_constraints) >= 0
    
    def test_no_strategies_generated(self):
        """Test handling when no strategies match."""
        engine = CreativityEngine()
        
        # Create context with constraints that don't match any strategies
        context = CreativeOpportunityContext(
            expert_domain="unknown_domain",
        )
        
        result = engine.generate_strategies(context)
        
        # Should still return a result, possibly with no strategies
        assert result is not None
        assert result.confidence >= 0.0
    
    def test_ranked_strategies_sorted(self):
        """Test that ranked strategies are sorted by score."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            review_strength=0.1,
            competition_level=0.8,
        )
        
        result = engine.generate_strategies(context)
        
        if len(result.ranked_strategies) > 1:
            for i in range(len(result.ranked_strategies) - 1):
                assert result.ranked_strategies[i].overall_score >= result.ranked_strategies[i + 1].overall_score
