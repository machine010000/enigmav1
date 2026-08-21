"""
Creativity Engine

Main creativity engine that generates strategies for opportunities.
"""

from typing import List, Optional, Set
from dataclasses import dataclass

from app.creativity.contracts import (
    CreativityResult,
    CreativeOpportunityContext,
    CreativeStrategy,
    StrategyEvaluation,
    CreativityEngineContract,
    ConstraintType,
)
from app.creativity.constraints import ConstraintDetector
from app.creativity.strategies import StrategyLibrary
from app.creativity.evaluation import StrategyEvaluator
from app.creativity.ranking import StrategyRanker


class CreativityEngine(CreativityEngineContract):
    """
    Main creativity engine implementation.
    
    Generates creative strategies for opportunities based on
    constraints, economics, and other context factors.
    """
    
    def __init__(self, ai_service=None):
        """Initialize the creativity engine."""
        self.engine_id = "rule_based_creativity_v1"
        self.name = "Rule-Based Creativity Engine"
        self.description = "Deterministic rule-based creativity engine for generating opportunity strategies"
        self.version = "1.0.0"
        
        self.constraint_detector = ConstraintDetector()
        self.strategy_evaluator = StrategyEvaluator()
        self.strategy_ranker = StrategyRanker()
        self._ai_service = ai_service

    async def generate_for_task(self, *, task: str, project_context: dict):
        """Generate structured AI options while preserving the rule-based API."""
        if self._ai_service is None:
            from app.creativity.ai_service import CreativityAIService
            self._ai_service = CreativityAIService()
        return await self._ai_service.generate(task=task, project_context=project_context)
    
    def generate_strategies(
        self,
        context: CreativeOpportunityContext,
    ) -> CreativityResult:
        """
        Generate creative strategies for the given context.
        
        Args:
            context: Opportunity context for reasoning
            
        Returns:
            CreativityResult with candidate and ranked strategies
        """
        # Detect constraints if not already provided
        constraints = context.constraints if context.constraints else self.constraint_detector.detect_constraints(context)
        
        # Get all available strategies
        all_strategies = StrategyLibrary.get_all_strategies()
        
        # Filter strategies by context compatibility
        candidate_strategies = self._filter_strategies_by_context(all_strategies, context)
        
        # Evaluate each candidate strategy
        evaluations = []
        for strategy in candidate_strategies:
            evaluation = self.strategy_evaluator.evaluate(strategy, context)
            evaluations.append(evaluation)
        
        # Rank strategies
        ranked_strategies = self.strategy_ranker.rank(evaluations)
        
        # Filter to top strategies (score >= 0.4)
        top_strategies = self.strategy_ranker.rank_with_threshold(evaluations, min_score=0.4)
        
        # Determine unresolved constraints
        unresolved_constraints = self._get_unresolved_constraints(constraints, top_strategies)
        
        # Determine research/learning/clarification requirements
        research_required = any(s.strategy.requires_research for s in top_strategies)
        learning_required = any(s.strategy.requires_learning for s in top_strategies)
        clarification_required = any(s.strategy.requires_clarification for s in top_strategies)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(top_strategies, context)
        
        # Generate explanation
        explanation = self._generate_explanation(
            constraints,
            top_strategies,
            research_required,
            learning_required,
            clarification_required,
        )
        
        return CreativityResult(
            opportunity_context=context,
            candidate_strategies=list(candidate_strategies),
            ranked_strategies=top_strategies,
            constraints=constraints,
            unresolved_constraints=unresolved_constraints,
            research_required=research_required,
            learning_required=learning_required,
            clarification_required=clarification_required,
            confidence=confidence,
            explanation=explanation,
        )
    
    def _filter_strategies_by_context(
        self,
        strategies: List[CreativeStrategy],
        context: CreativeOpportunityContext,
    ) -> List[CreativeStrategy]:
        """
        Filter strategies by context compatibility.
        
        Args:
            strategies: All available strategies
            context: Opportunity context
            
        Returns:
            Filtered list of strategies
        """
        filtered = []
        
        for strategy in strategies:
            # Skip deprecated strategies
            if strategy.status.value == "deprecated":
                continue
            
            # Check domain compatibility
            if strategy.domain_compatibility and context.expert_domain:
                if context.expert_domain not in strategy.domain_compatibility:
                    continue
            
            # Check platform compatibility
            if strategy.platform_compatibility and context.platform_economics:
                if context.platform_economics.platform not in strategy.platform_compatibility:
                    continue
            
            # Check if strategy addresses any constraints
            context_constraint_types = {c.constraint_type for c in context.constraints}
            if not (strategy.target_constraints & context_constraint_types):
                # If no constraints match, still include if it's a general strategy
                # (e.g., research_first for stale knowledge)
                pass
            
            filtered.append(strategy)
        
        return filtered
    
    def _get_unresolved_constraints(
        self,
        constraints: List,
        strategies: List[StrategyEvaluation],
    ) -> List:
        """
        Get constraints not addressed by any strategy.
        
        Args:
            constraints: All constraints
            strategies: Ranked strategies
            
        Returns:
            List of unresolved constraints
        """
        if not strategies:
            return constraints
        
        # Get all addressed constraint types
        addressed_types = set()
        for evaluation in strategies:
            addressed_types.update(evaluation.addressed_constraints)
        
        # Filter to unresolved
        unresolved = [c for c in constraints if c.constraint_type not in addressed_types]
        return unresolved
    
    def _calculate_confidence(
        self,
        strategies: List[StrategyEvaluation],
        context: CreativeOpportunityContext,
    ) -> float:
        """
        Calculate overall confidence in the result.
        
        Args:
            strategies: Ranked strategies
            context: Opportunity context
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not strategies:
            return 0.3
        
        # Base confidence on number and quality of strategies
        strategy_count = len(strategies)
        avg_score = sum(s.overall_score for s in strategies) / strategy_count if strategy_count > 0 else 0
        
        # Adjust for context confidence
        context_confidence = context.confidence_score
        
        # Combine factors
        confidence = (avg_score * 0.6) + (context_confidence * 0.4)
        
        return max(0.0, min(1.0, confidence))
    
    def _generate_explanation(
        self,
        constraints: List,
        strategies: List[StrategyEvaluation],
        research_required: bool,
        learning_required: bool,
        clarification_required: bool,
    ) -> str:
        """
        Generate explanation for the creativity result.
        
        Args:
            constraints: Detected constraints
            strategies: Ranked strategies
            research_required: Whether research is required
            learning_required: Whether learning is required
            clarification_required: Whether clarification is required
            
        Returns:
            Explanation string
        """
        parts = []
        
        # Constraint summary
        if constraints:
            constraint_count = len(constraints)
            blocking_count = sum(1 for c in constraints if c.blocking)
            parts.append(f"Identified {constraint_count} constraints ({blocking_count} blocking)")
        
        # Strategy summary
        if strategies:
            strategy_count = len(strategies)
            top_strategy = strategies[0]
            parts.append(f"Generated {strategy_count} viable strategies")
            parts.append(f"Top strategy: {top_strategy.strategy.name} (score: {top_strategy.overall_score:.2f})")
        else:
            parts.append("No viable strategies generated")
        
        # Requirements
        requirements = []
        if research_required:
            requirements.append("research")
        if learning_required:
            requirements.append("learning")
        if clarification_required:
            requirements.append("clarification")
        
        if requirements:
            parts.append(f"Requires: {', '.join(requirements)}")
        
        return "; ".join(parts)
