"""
Test Strategy Definitions
"""

import pytest

from app.creativity.contracts import (
    ConstraintType,
    StrategyCategory,
    StrategyStatus,
)
from app.marketplace.economics import EconomicsValue, VerificationStatus
from app.creativity.strategies import StrategyLibrary
from app.marketplace.contracts import MarketplacePlatform


class TestStrategyLibrary:
    """Test strategy library."""
    
    def test_get_all_strategies(self):
        """Test getting all strategies."""
        strategies = StrategyLibrary.get_all_strategies()
        
        assert len(strategies) >= 10
        assert all(s.strategy_id for s in strategies)
        assert all(s.name for s in strategies)
        assert all(s.description for s in strategies)
    
    def test_price_adjustment_strategy(self):
        """Test price adjustment strategy."""
        strategy = StrategyLibrary.price_adjustment_strategy()
        
        assert strategy.category == StrategyCategory.PRICE_ADJUSTMENT
        assert ConstraintType.NO_REVIEWS in strategy.target_constraints
        assert ConstraintType.HIGH_COMPETITION in strategy.target_constraints
        assert strategy.economic_effect is not None
        assert strategy.economic_effect.value < 0  # Reduces revenue
        assert strategy.requires_research is True
    
    def test_scope_reduction_strategy(self):
        """Test scope reduction strategy."""
        strategy = StrategyLibrary.scope_reduction_strategy()
        
        assert strategy.category == StrategyCategory.SCOPE_REDUCTION
        assert ConstraintType.EXECUTION_GAP in strategy.target_constraints
        assert ConstraintType.UNCLEAR_SCOPE in strategy.target_constraints
        assert strategy.risk_effect is not None
        assert strategy.risk_effect.value < 0  # Reduces risk
        assert strategy.requires_clarification is True
    
    def test_proof_of_work_strategy(self):
        """Test proof of work strategy."""
        strategy = StrategyLibrary.proof_of_work_strategy()
        
        assert strategy.category == StrategyCategory.PROOF_OF_WORK
        assert ConstraintType.NO_PORTFOLIO in strategy.target_constraints
        assert ConstraintType.NO_REVIEWS in strategy.target_constraints
        assert ConstraintType.LOW_EVIDENCE in strategy.target_constraints
        assert strategy.confidence_effect is not None
        assert strategy.confidence_effect.value > 0  # Increases confidence
        assert strategy.reversibility > 0.8  # Highly reversible
    
    def test_positioning_change_strategy(self):
        """Test positioning change strategy."""
        strategy = StrategyLibrary.positioning_change_strategy()
        
        assert strategy.category == StrategyCategory.POSITIONING_CHANGE
        assert ConstraintType.WEAK_POSITIONING in strategy.target_constraints
        assert ConstraintType.HIGH_COMPETITION in strategy.target_constraints
        assert strategy.requires_research is True
    
    def test_target_selection_strategy(self):
        """Test target selection strategy."""
        strategy = StrategyLibrary.target_selection_strategy()
        
        assert strategy.category == StrategyCategory.TARGET_SELECTION
        assert ConstraintType.HIGH_COMPETITION in strategy.target_constraints
        assert strategy.economic_effect is not None
        assert strategy.economic_effect.value > 0  # Improves economic efficiency
        assert strategy.implementation_complexity < 0.3  # Low complexity
    
    def test_proposal_strategy(self):
        """Test proposal strategy."""
        strategy = StrategyLibrary.proposal_strategy()
        
        assert strategy.category == StrategyCategory.PROPOSAL_STRATEGY
        assert ConstraintType.WEAK_POSITIONING in strategy.target_constraints
        assert ConstraintType.LOW_CONFIDENCE in strategy.target_constraints
        assert strategy.implementation_complexity == 0.5
    
    def test_research_first_strategy(self):
        """Test research first strategy."""
        strategy = StrategyLibrary.research_first_strategy()
        
        assert strategy.category == StrategyCategory.RESEARCH_FIRST
        assert ConstraintType.STALE_KNOWLEDGE in strategy.target_constraints
        assert ConstraintType.KNOWLEDGE_GAP in strategy.target_constraints
        assert strategy.requires_research is True
        assert strategy.confidence_effect is not None
        assert strategy.confidence_effect.value > 0.4  # Significantly increases confidence
    
    def test_learning_first_strategy(self):
        """Test learning first strategy."""
        strategy = StrategyLibrary.learning_first_strategy()
        
        assert strategy.category == StrategyCategory.LEARNING_FIRST
        assert ConstraintType.KNOWLEDGE_GAP in strategy.target_constraints
        assert ConstraintType.EXECUTION_GAP in strategy.target_constraints
        assert strategy.requires_learning is True
        assert strategy.implementation_complexity > 0.6  # High complexity
    
    def test_evidence_building_strategy(self):
        """Test evidence building strategy."""
        strategy = StrategyLibrary.evidence_building_strategy()
        
        assert strategy.category == StrategyCategory.EVIDENCE_BUILDING
        assert ConstraintType.LOW_EVIDENCE in strategy.target_constraints
        assert ConstraintType.NO_PORTFOLIO in strategy.target_constraints
        assert strategy.implementation_complexity > 0.5  # Medium-high complexity
    
    def test_risk_reduction_strategy(self):
        """Test risk reduction strategy."""
        strategy = StrategyLibrary.risk_reduction_strategy()
        
        assert strategy.category == StrategyCategory.RISK_REDUCTION
        assert ConstraintType.EXECUTION_GAP in strategy.target_constraints
        assert ConstraintType.UNCLEAR_SCOPE in strategy.target_constraints
        assert strategy.risk_effect is not None
        assert strategy.risk_effect.value < -0.4  # Significantly reduces risk
    
    def test_deliverable_redesign_strategy(self):
        """Test deliverable redesign strategy."""
        strategy = StrategyLibrary.deliverable_redesign_strategy()
        
        assert strategy.category == StrategyCategory.DELIVERABLE_REDESIGN
        assert ConstraintType.EXECUTION_GAP in strategy.target_constraints
        assert ConstraintType.UNCLEAR_SCOPE in strategy.target_constraints
        assert strategy.reversibility < 0.5  # Low reversibility
    
    def test_clarification_first_strategy(self):
        """Test clarification first strategy."""
        strategy = StrategyLibrary.clarification_first_strategy()
        
        assert strategy.category == StrategyCategory.CLARIFICATION_FIRST
        assert ConstraintType.UNCLEAR_SCOPE in strategy.target_constraints
        assert ConstraintType.LOW_CONFIDENCE in strategy.target_constraints
        assert strategy.requires_clarification is True
        assert strategy.implementation_complexity < 0.3  # Low complexity
    
    def test_strategy_platform_compatibility(self):
        """Test that strategies have platform compatibility."""
        strategy = StrategyLibrary.price_adjustment_strategy()
        
        assert len(strategy.platform_compatibility) > 0
        assert MarketplacePlatform.UPWORK in strategy.platform_compatibility
    
    def test_strategy_domain_compatibility(self):
        """Test that strategies have domain compatibility."""
        strategy = StrategyLibrary.price_adjustment_strategy()
        
        assert len(strategy.domain_compatibility) > 0
        assert "seo" in strategy.domain_compatibility
    
    def test_strategy_status(self):
        """Test that strategies have active status."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            assert strategy.status == StrategyStatus.ACTIVE
    
    def test_strategy_required_capabilities(self):
        """Test that strategies define required capabilities."""
        strategy = StrategyLibrary.price_adjustment_strategy()
        
        assert len(strategy.required_capabilities) > 0
        assert "pricing_analysis" in strategy.required_capabilities
    
    def test_strategy_economic_effects(self):
        """Test that strategies have economic effects."""
        strategy = StrategyLibrary.price_adjustment_strategy()
        
        assert strategy.economic_effect is not None
        assert strategy.economic_effect.status == VerificationStatus.UNKNOWN
        assert 0.0 <= strategy.economic_effect.confidence <= 1.0
    
    def test_strategy_scores(self):
        """Test that strategy scores are in valid range."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            assert 0.0 <= strategy.expected_benefit <= 1.0
            assert 0.0 <= strategy.implementation_complexity <= 1.0
            assert 0.0 <= strategy.reversibility <= 1.0
