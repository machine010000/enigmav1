"""
Test Creativity Registry
"""

import pytest

from app.creativity.contracts import (
    ConstraintType,
    StrategyCategory,
    CreativeStrategy,
)
from app.creativity.registry import CreativityRegistry, get_registry, initialize_registry


class TestCreativityRegistry:
    """Test creativity registry."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = CreativityRegistry()
        
        assert registry is not None
        assert len(registry._strategies) == 0
        assert len(registry._strategies_by_constraint) == 0
        assert len(registry._strategies_by_category) == 0
    
    def test_register_strategy(self):
        """Test registering a strategy."""
        registry = CreativityRegistry()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        registry.register_strategy(strategy)
        
        assert "test_strategy" in registry._strategies
        assert registry._strategies["test_strategy"] == strategy
    
    def test_register_strategy_indexes_by_constraint(self):
        """Test that strategy is indexed by constraint."""
        registry = CreativityRegistry()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO, ConstraintType.NO_REVIEWS},
        )
        
        registry.register_strategy(strategy)
        
        assert ConstraintType.NO_PORTFOLIO in registry._strategies_by_constraint
        assert "test_strategy" in registry._strategies_by_constraint[ConstraintType.NO_PORTFOLIO]
        assert ConstraintType.NO_REVIEWS in registry._strategies_by_constraint
        assert "test_strategy" in registry._strategies_by_constraint[ConstraintType.NO_REVIEWS]
    
    def test_register_strategy_indexes_by_category(self):
        """Test that strategy is indexed by category."""
        registry = CreativityRegistry()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        registry.register_strategy(strategy)
        
        assert StrategyCategory.PROOF_OF_WORK in registry._strategies_by_category
        assert "test_strategy" in registry._strategies_by_category[StrategyCategory.PROOF_OF_WORK]
    
    def test_register_strategy_indexes_by_domain(self):
        """Test that strategy is indexed by domain."""
        registry = CreativityRegistry()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            domain_compatibility={"seo", "ads"},
        )
        
        registry.register_strategy(strategy)
        
        assert "seo" in registry._strategies_by_domain
        assert "test_strategy" in registry._strategies_by_domain["seo"]
        assert "ads" in registry._strategies_by_domain
        assert "test_strategy" in registry._strategies_by_domain["ads"]
    
    def test_get_strategy(self):
        """Test getting a strategy by ID."""
        registry = CreativityRegistry()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        registry.register_strategy(strategy)
        
        retrieved = registry.get_strategy("test_strategy")
        
        assert retrieved is not None
        assert retrieved.strategy_id == "test_strategy"
    
    def test_get_strategy_not_found(self):
        """Test getting a non-existent strategy."""
        registry = CreativityRegistry()
        
        retrieved = registry.get_strategy("nonexistent")
        
        assert retrieved is None
    
    def test_list_strategies(self):
        """Test listing all strategies."""
        registry = CreativityRegistry()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        strategy2 = CreativeStrategy(
            strategy_id="strategy_2",
            name="Strategy 2",
            description="Strategy 2",
            category=StrategyCategory.RESEARCH_FIRST,
            target_constraints={ConstraintType.STALE_KNOWLEDGE},
        )
        
        registry.register_strategy(strategy1)
        registry.register_strategy(strategy2)
        
        strategies = registry.list_strategies()
        
        assert len(strategies) == 2
        assert strategy1 in strategies
        assert strategy2 in strategies
    
    def test_get_strategies_for_constraint(self):
        """Test getting strategies for a specific constraint."""
        registry = CreativityRegistry()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        strategy2 = CreativeStrategy(
            strategy_id="strategy_2",
            name="Strategy 2",
            description="Strategy 2",
            category=StrategyCategory.TARGET_SELECTION,
            target_constraints={ConstraintType.NO_PORTFOLIO, ConstraintType.HIGH_COMPETITION},
        )
        
        strategy3 = CreativeStrategy(
            strategy_id="strategy_3",
            name="Strategy 3",
            description="Strategy 3",
            category=StrategyCategory.RESEARCH_FIRST,
            target_constraints={ConstraintType.STALE_KNOWLEDGE},
        )
        
        registry.register_strategy(strategy1)
        registry.register_strategy(strategy2)
        registry.register_strategy(strategy3)
        
        portfolio_strategies = registry.get_strategies_for_constraint(ConstraintType.NO_PORTFOLIO)
        
        assert len(portfolio_strategies) == 2
        assert strategy1 in portfolio_strategies
        assert strategy2 in portfolio_strategies
        assert strategy3 not in portfolio_strategies
    
    def test_get_strategies_for_domain(self):
        """Test getting strategies for a specific domain."""
        registry = CreativityRegistry()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            domain_compatibility={"seo", "ads"},
        )
        
        strategy2 = CreativeStrategy(
            strategy_id="strategy_2",
            name="Strategy 2",
            description="Strategy 2",
            category=StrategyCategory.RESEARCH_FIRST,
            target_constraints={ConstraintType.STALE_KNOWLEDGE},
            domain_compatibility={"analytics"},
        )
        
        registry.register_strategy(strategy1)
        registry.register_strategy(strategy2)
        
        seo_strategies = registry.get_strategies_for_domain("seo")
        
        assert len(seo_strategies) == 1
        assert strategy1 in seo_strategies
        assert strategy2 not in seo_strategies
    
    def test_get_strategies_by_category(self):
        """Test getting strategies by category."""
        registry = CreativityRegistry()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        strategy2 = CreativeStrategy(
            strategy_id="strategy_2",
            name="Strategy 2",
            description="Strategy 2",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_REVIEWS},
        )
        
        strategy3 = CreativeStrategy(
            strategy_id="strategy_3",
            name="Strategy 3",
            description="Strategy 3",
            category=StrategyCategory.RESEARCH_FIRST,
            target_constraints={ConstraintType.STALE_KNOWLEDGE},
        )
        
        registry.register_strategy(strategy1)
        registry.register_strategy(strategy2)
        registry.register_strategy(strategy3)
        
        proof_strategies = registry.get_strategies_by_category(StrategyCategory.PROOF_OF_WORK)
        
        assert len(proof_strategies) == 2
        assert strategy1 in proof_strategies
        assert strategy2 in proof_strategies
        assert strategy3 not in proof_strategies
    
    def test_register_strategy_provider(self):
        """Test registering a strategy provider."""
        registry = CreativityRegistry()
        
        def provider_func():
            return []
        
        registry.register_strategy_provider("test_provider", provider_func)
        
        assert "test_provider" in registry._strategy_providers
        assert registry._strategy_providers["test_provider"] == provider_func
    
    def test_global_registry(self):
        """Test global registry instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2
    
    def test_initialize_registry(self):
        """Test initializing registry with default strategies."""
        initialize_registry()
        
        registry = get_registry()
        
        strategies = registry.list_strategies()
        
        # Should have registered default strategies
        assert len(strategies) >= 10


class TestGlobalRegistry:
    """Test global registry functions."""
    
    def test_get_registry_singleton(self):
        """Test that get_registry returns singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert id(registry1) == id(registry2)
    
    def test_initialize_registry_idempotent(self):
        """Test that initialize_registry can be called multiple times."""
        initialize_registry()
        registry1 = get_registry()
        count1 = len(registry1.list_strategies())
        
        initialize_registry()
        registry2 = get_registry()
        count2 = len(registry2.list_strategies())
        
        # Should be the same instance
        assert id(registry1) == id(registry2)
        # Count should not decrease (strategies may be re-registered)
        assert count2 >= count1
