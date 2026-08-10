"""
Strategy Ranking

Deterministic ranking of evaluated strategies.
"""

from typing import List
from dataclasses import dataclass

from app.creativity.contracts import (
    StrategyEvaluation,
    CreativeStrategy,
    CreativeOpportunityContext,
)


class StrategyRanker:
    """
    Ranks evaluated strategies deterministically.
    
    Sorts strategies by overall score and provides explainable
    ranking results.
    """
    
    def rank(
        self,
        evaluations: List[StrategyEvaluation],
    ) -> List[StrategyEvaluation]:
        """
        Rank strategies by overall score.
        
        Args:
            evaluations: List of evaluated strategies
            
        Returns:
            List of evaluations sorted by overall score (descending)
        """
        # Sort by overall score descending
        ranked = sorted(
            evaluations,
            key=lambda e: e.overall_score,
            reverse=True,
        )
        
        return ranked
    
    def rank_with_threshold(
        self,
        evaluations: List[StrategyEvaluation],
        min_score: float = 0.4,
    ) -> List[StrategyEvaluation]:
        """
        Rank strategies and filter by minimum score.
        
        Args:
            evaluations: List of evaluated strategies
            min_score: Minimum overall score threshold
            
        Returns:
            List of evaluations sorted by score, filtered by threshold
        """
        ranked = self.rank(evaluations)
        return [e for e in ranked if e.overall_score >= min_score]
    
    def rank_by_category(
        self,
        evaluations: List[StrategyEvaluation],
    ) -> dict:
        """
        Rank strategies by category.
        
        Args:
            evaluations: List of evaluated strategies
            
        Returns:
            Dictionary mapping categories to ranked evaluations
        """
        from collections import defaultdict
        
        by_category = defaultdict(list)
        
        for evaluation in evaluations:
            category = evaluation.strategy.category.value
            by_category[category].append(evaluation)
        
        # Rank each category
        ranked_by_category = {}
        for category, category_evals in by_category.items():
            ranked_by_category[category] = self.rank(category_evals)
        
        return ranked_by_category
    
    def get_top_strategies(
        self,
        evaluations: List[StrategyEvaluation],
        count: int = 3,
    ) -> List[StrategyEvaluation]:
        """
        Get top N strategies.
        
        Args:
            evaluations: List of evaluated strategies
            count: Number of top strategies to return
            
        Returns:
            List of top N evaluations
        """
        ranked = self.rank(evaluations)
        return ranked[:count]
