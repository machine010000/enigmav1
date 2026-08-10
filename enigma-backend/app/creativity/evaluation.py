"""
Strategy Evaluation

Deterministic evaluation of creative strategies against opportunity context.
"""

from typing import List, Set, Optional
from dataclasses import dataclass

from app.creativity.contracts import (
    CreativeStrategy,
    StrategyEvaluation,
    CreativeOpportunityContext,
    ConstraintType,
)
from app.marketplace.economics import EconomicsValue, VerificationStatus


class StrategyEvaluator:
    """
    Evaluates strategies against opportunity context.
    
    Provides deterministic scoring and explanation for strategy
    recommendation or rejection.
    """
    
    def evaluate(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> StrategyEvaluation:
        """
        Evaluate a strategy against the given context.
        
        Args:
            strategy: Strategy to evaluate
            context: Opportunity context
            
        Returns:
            StrategyEvaluation with scores and explanation
        """
        # Calculate individual scores
        benefit_score = self._calculate_benefit_score(strategy, context)
        feasibility_score = self._calculate_feasibility_score(strategy, context)
        economic_viability_score = self._calculate_economic_viability_score(strategy, context)
        risk_score = self._calculate_risk_score(strategy, context)
        confidence_score = self._calculate_confidence_score(strategy, context)
        evidence_alignment_score = self._calculate_evidence_alignment_score(strategy, context)
        knowledge_alignment_score = self._calculate_knowledge_alignment_score(strategy, context)
        execution_fit_score = self._calculate_execution_fit_score(strategy, context)
        reversibility_score = self._calculate_reversibility_score(strategy, context)
        complexity_score = self._calculate_complexity_score(strategy, context)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            benefit_score,
            feasibility_score,
            economic_viability_score,
            risk_score,
            confidence_score,
            evidence_alignment_score,
            knowledge_alignment_score,
            execution_fit_score,
            reversibility_score,
            complexity_score,
        )
        
        # Determine addressed constraints
        addressed_constraints = self._get_addressed_constraints(strategy, context)
        
        # Determine introduced risks
        introduced_risks = self._get_introduced_risks(strategy, context)
        
        # Generate recommendation and penalty reasons
        recommendation_reason, penalty_reasons = self._generate_explanation(
            strategy,
            context,
            benefit_score,
            feasibility_score,
            economic_viability_score,
            risk_score,
            addressed_constraints,
            introduced_risks,
        )
        
        return StrategyEvaluation(
            strategy=strategy,
            benefit_score=benefit_score,
            feasibility_score=feasibility_score,
            economic_viability_score=economic_viability_score,
            risk_score=risk_score,
            confidence_score=confidence_score,
            evidence_alignment_score=evidence_alignment_score,
            knowledge_alignment_score=knowledge_alignment_score,
            execution_fit_score=execution_fit_score,
            reversibility_score=reversibility_score,
            complexity_score=complexity_score,
            overall_score=overall_score,
            addressed_constraints=addressed_constraints,
            introduced_risks=introduced_risks,
            recommendation_reason=recommendation_reason,
            penalty_reasons=penalty_reasons,
        )
    
    def _calculate_benefit_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate benefit score based on expected benefit and constraint impact."""
        base_score = strategy.expected_benefit
        
        # Adjust based on how many constraints are addressed
        addressed_count = len(strategy.target_constraints & {c.constraint_type for c in context.constraints})
        if addressed_count > 0:
            base_score += 0.1 * addressed_count
        
        return min(1.0, base_score)
    
    def _calculate_feasibility_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate feasibility score based on capabilities and readiness."""
        # Check if required capabilities are available
        capability_match = len(strategy.required_capabilities & context.required_capabilities)
        capability_ratio = capability_match / len(strategy.required_capabilities) if strategy.required_capabilities else 1.0
        
        # Adjust for execution readiness
        readiness_factor = context.execution_readiness
        
        return min(1.0, capability_ratio * readiness_factor)
    
    def _calculate_economic_viability_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate economic viability score."""
        # If no economics data, assume neutral
        if not context.expected_value or not context.application_cost:
            return 0.5
        
        # Check if strategy improves economic viability
        if strategy.economic_effect and strategy.economic_effect.value:
            # Negative economic effect reduces viability
            if strategy.economic_effect.value < -0.3:
                return 0.2
            elif strategy.economic_effect.value < -0.1:
                return 0.4
            elif strategy.economic_effect.value > 0.1:
                return 0.8
        
        # Check base economic viability
        if context.application_cost > context.expected_value * 0.5:
            return 0.3
        
        return 0.6
    
    def _calculate_risk_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate risk score (lower is better)."""
        base_risk = context.risk_score
        
        # Adjust based on strategy risk effect
        if strategy.risk_effect and strategy.risk_effect.value:
            base_risk += strategy.risk_effect.value
        
        # Adjust for complexity
        base_risk += strategy.implementation_complexity * 0.1
        
        return max(0.0, min(1.0, base_risk))
    
    def _calculate_confidence_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate confidence score."""
        base_confidence = context.confidence_score
        
        # Adjust based on strategy confidence effect
        if strategy.confidence_effect and strategy.confidence_effect.value:
            base_confidence += strategy.confidence_effect.value
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_evidence_alignment_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate evidence alignment score."""
        # If strategy requires evidence, check if available
        if strategy.required_evidence:
            evidence_ratio = context.evidence_readiness
            return evidence_ratio
        
        # If strategy builds evidence, it's aligned
        if strategy.category.value == "evidence_building":
            return 0.8
        
        return 0.5
    
    def _calculate_knowledge_alignment_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate knowledge alignment score."""
        # If strategy requires knowledge, check if available
        if strategy.required_knowledge:
            knowledge_ratio = context.knowledge_readiness
            return knowledge_ratio
        
        # If strategy is research-first, it's aligned with stale knowledge
        if strategy.category.value == "research_first" and context.knowledge_freshness < 0.5:
            return 0.9
        
        # Check knowledge freshness
        if context.knowledge_freshness < 0.5:
            return 0.3
        
        return 0.7
    
    def _calculate_execution_fit_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate execution fit score."""
        # Based on execution readiness and complexity
        execution_factor = context.execution_readiness
        complexity_penalty = strategy.implementation_complexity * 0.3
        
        return max(0.0, min(1.0, execution_factor - complexity_penalty))
    
    def _calculate_reversibility_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate reversibility score."""
        return strategy.reversibility
    
    def _calculate_complexity_score(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> float:
        """Calculate complexity score (lower is better)."""
        return strategy.implementation_complexity
    
    def _calculate_overall_score(
        self,
        benefit_score: float,
        feasibility_score: float,
        economic_viability_score: float,
        risk_score: float,
        confidence_score: float,
        evidence_alignment_score: float,
        knowledge_alignment_score: float,
        execution_fit_score: float,
        reversibility_score: float,
        complexity_score: float,
    ) -> float:
        """
        Calculate overall score.
        
        Formula:
        Score = Benefit + Feasibility + Economic Viability + Confidence + 
                Execution Fit + Evidence Alignment + Knowledge Alignment + 
                Reversibility - Risk - Complexity
        """
        positive_factors = (
            benefit_score +
            feasibility_score +
            economic_viability_score +
            confidence_score +
            execution_fit_score +
            evidence_alignment_score +
            knowledge_alignment_score +
            reversibility_score
        )
        
        negative_factors = risk_score + complexity_score
        
        overall = (positive_factors - negative_factors) / 8.0
        
        return max(0.0, min(1.0, overall))
    
    def _get_addressed_constraints(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> Set[ConstraintType]:
        """Get constraints addressed by this strategy."""
        context_constraint_types = {c.constraint_type for c in context.constraints}
        return strategy.target_constraints & context_constraint_types
    
    def _get_introduced_risks(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
    ) -> Set[str]:
        """Get risks introduced by this strategy."""
        risks = set()
        
        # High complexity introduces execution risk
        if strategy.implementation_complexity > 0.7:
            risks.add("high_complexity_risk")
        
        # Negative economic effect introduces financial risk
        if strategy.economic_effect and strategy.economic_effect.value < -0.2:
            risks.add("financial_risk")
        
        # Low reversibility introduces commitment risk
        if strategy.reversibility < 0.3:
            risks.add("commitment_risk")
        
        return risks
    
    def _generate_explanation(
        self,
        strategy: CreativeStrategy,
        context: CreativeOpportunityContext,
        benefit_score: float,
        feasibility_score: float,
        economic_viability_score: float,
        risk_score: float,
        addressed_constraints: Set[ConstraintType],
        introduced_risks: Set[str],
    ) -> tuple[str, List[str]]:
        """Generate recommendation reason and penalty reasons."""
        recommendation_parts = []
        penalty_reasons = []
        
        # Benefit explanation
        if benefit_score > 0.6:
            recommendation_parts.append(f"High expected benefit ({benefit_score:.2f})")
        elif benefit_score < 0.3:
            penalty_reasons.append(f"Low expected benefit ({benefit_score:.2f})")
        
        # Feasibility explanation
        if feasibility_score > 0.7:
            recommendation_parts.append(f"High feasibility ({feasibility_score:.2f})")
        elif feasibility_score < 0.4:
            penalty_reasons.append(f"Low feasibility ({feasibility_score:.2f})")
        
        # Economic viability explanation
        if economic_viability_score > 0.6:
            recommendation_parts.append(f"Economically viable ({economic_viability_score:.2f})")
        elif economic_viability_score < 0.3:
            penalty_reasons.append(f"Poor economic viability ({economic_viability_score:.2f})")
        
        # Risk explanation
        if risk_score < 0.3:
            recommendation_parts.append(f"Low risk ({risk_score:.2f})")
        elif risk_score > 0.7:
            penalty_reasons.append(f"High risk ({risk_score:.2f})")
        
        # Addressed constraints
        if addressed_constraints:
            constraint_names = [c.value for c in addressed_constraints]
            recommendation_parts.append(f"Addresses constraints: {', '.join(constraint_names)}")
        
        # Introduced risks
        if introduced_risks:
            penalty_reasons.extend([f"Introduces risk: {risk}" for risk in introduced_risks])
        
        # Build recommendation
        if recommendation_parts:
            recommendation = "; ".join(recommendation_parts)
        else:
            recommendation = "Strategy has moderate potential"
        
        return recommendation, penalty_reasons
