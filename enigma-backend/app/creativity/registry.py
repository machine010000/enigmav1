"""
Creativity Registry

Registry for managing creative strategies and strategy providers.
"""

from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass

from app.creativity.contracts import (
    CreativeStrategy,
    ConstraintType,
    StrategyCategory,
)


class CreativityRegistry:
    """
    Registry for creative strategies and strategy providers.
    
    Manages strategy registration and retrieval without becoming
    a global business-logic container.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._strategies: Dict[str, CreativeStrategy] = {}
        self._strategies_by_constraint: Dict[ConstraintType, Set[str]] = {}
        self._strategies_by_category: Dict[StrategyCategory, Set[str]] = {}
        self._strategies_by_domain: Dict[str, Set[str]] = {}
        self._strategy_providers: Dict[str, Callable] = {}
    
    def register_strategy(self, strategy: CreativeStrategy) -> None:
        """
        Register a creative strategy.
        
        Args:
            strategy: Strategy to register
        """
        # Store by ID
        self._strategies[strategy.strategy_id] = strategy
        
        # Index by constraint
        for constraint_type in strategy.target_constraints:
            if constraint_type not in self._strategies_by_constraint:
                self._strategies_by_constraint[constraint_type] = set()
            self._strategies_by_constraint[constraint_type].add(strategy.strategy_id)
        
        # Index by category
        if strategy.category not in self._strategies_by_category:
            self._strategies_by_category[strategy.category] = set()
        self._strategies_by_category[strategy.category].add(strategy.strategy_id)
        
        # Index by domain
        for domain in strategy.domain_compatibility:
            if domain not in self._strategies_by_domain:
                self._strategies_by_domain[domain] = set()
            self._strategies_by_domain[domain].add(strategy.strategy_id)
    
    def get_strategy(self, strategy_id: str) -> Optional[CreativeStrategy]:
        """
        Get a strategy by ID.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Strategy if found, None otherwise
        """
        return self._strategies.get(strategy_id)
    
    def list_strategies(self) -> List[CreativeStrategy]:
        """
        List all registered strategies.
        
        Returns:
            List of all strategies
        """
        return list(self._strategies.values())
    
    def register_strategy_provider(
        self,
        provider_id: str,
        provider_func: Callable,
    ) -> None:
        """
        Register a strategy provider function.
        
        Args:
            provider_id: Provider identifier
            provider_func: Function that returns strategies
        """
        self._strategy_providers[provider_id] = provider_func
    
    def get_strategies_for_constraint(
        self,
        constraint_type: ConstraintType,
    ) -> List[CreativeStrategy]:
        """
        Get strategies that address a specific constraint.
        
        Args:
            constraint_type: Constraint type
            
        Returns:
            List of strategies addressing the constraint
        """
        strategy_ids = self._strategies_by_constraint.get(constraint_type, set())
        return [self._strategies[sid] for sid in strategy_ids if sid in self._strategies]
    
    def get_strategies_for_domain(self, domain: str) -> List[CreativeStrategy]:
        """
        Get strategies compatible with a specific domain.
        
        Args:
            domain: Domain identifier
            
        Returns:
            List of strategies compatible with the domain
        """
        strategy_ids = self._strategies_by_domain.get(domain, set())
        return [self._strategies[sid] for sid in strategy_ids if sid in self._strategies]
    
    def get_strategies_by_category(
        self,
        category: StrategyCategory,
    ) -> List[CreativeStrategy]:
        """
        Get strategies by category.
        
        Args:
            category: Strategy category
            
        Returns:
            List of strategies in the category
        """
        strategy_ids = self._strategies_by_category.get(category, set())
        return [self._strategies[sid] for sid in strategy_ids if sid in self._strategies]


# Global registry instance
_global_registry: Optional[CreativityRegistry] = None


def get_registry() -> CreativityRegistry:
    """
    Get the global creativity registry.
    
    Returns:
        Global registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = CreativityRegistry()
    return _global_registry


def initialize_registry() -> None:
    """
    Initialize the global registry with default strategies.
    """
    from app.creativity.strategies import StrategyLibrary
    
    registry = get_registry()
    
    # Register all default strategies
    for strategy in StrategyLibrary.get_all_strategies():
        registry.register_strategy(strategy)
