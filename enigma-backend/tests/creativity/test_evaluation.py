"""
Test Strategy Evaluation
"""

import pytest

from app.creativity.contracts import (
    ConstraintType,
    StrategyCategory,
    CreativeStrategy,
    CreativeOpportunityContext,
)
from app.marketplace.economics import EconomicsValue, VerificationStatus
from app.creativity.evaluation import StrategyEvaluator


class TestStrategyEvaluator:
    """Test strategy evaluation."""
    
    def test_evaluate_strategy(self):
        """Test basic strategy evaluation."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.6,
            implementation_complexity=0.5,
            reversibility=0.7,
        )
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
            execution_readiness=0.7,
            confidence_score=0.6,
            risk_score=0.4,
            evidence_readiness=0.5,
            knowledge_readiness=0.7,
            knowledge_freshness=0.7,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.strategy == strategy
        assert 0.0 <= evaluation.overall_score <= 1.0
        assert 0.0 <= evaluation.benefit_score <= 1.0
        assert 0.0 <= evaluation.feasibility_score <= 1.0
    
    def test_benefit_score_calculation(self):
        """Test benefit score calculation."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.8,
        )
        
        context = CreativeOpportunityContext(
            constraints=[],
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.benefit_score >= 0.7  # High expected benefit
    
    def test_benefit_score_with_addressed_constraints(self):
        """Test benefit score increases with addressed constraints."""
        evaluator = StrategyEvaluator()
        
        from app.creativity.contracts import CreativeConstraint, ConstraintSeverity
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.5,
        )
        
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
        
        evaluation = evaluator.evaluate(strategy, context)
        
        # Should be higher than base expected benefit due to addressing constraint
        assert evaluation.benefit_score >= 0.5
    
    def test_feasibility_score_calculation(self):
        """Test feasibility score calculation."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            required_capabilities={"sample_creation"},
            expected_benefit=0.5,
        )
        
        context = CreativeOpportunityContext(
            required_capabilities={"sample_creation"},
            execution_readiness=0.8,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.feasibility_score >= 0.7  # High feasibility
    
    def test_feasibility_score_low_capability_match(self):
        """Test feasibility score with low capability match."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            required_capabilities={"sample_creation", "advanced_design"},
            expected_benefit=0.5,
        )
        
        context = CreativeOpportunityContext(
            required_capabilities={"sample_creation"},  # Only one of two
            execution_readiness=0.8,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.feasibility_score < 0.8  # Lower due to partial capability match
    
    def test_economic_viability_score_good(self):
        """Test economic viability score with good economics."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.5,
        )
        
        context = CreativeOpportunityContext(
            expected_value=100.0,
            application_cost=5.0,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.economic_viability_score >= 0.5  # Good viability
    
    def test_economic_viability_score_poor(self):
        """Test economic viability score with poor economics."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PRICE_ADJUSTMENT,
            target_constraints={ConstraintType.NO_REVIEWS},
            expected_benefit=0.5,
            economic_effect=EconomicsValue(
                value=-0.4,  # Significant negative effect
                status=VerificationStatus.UNKNOWN,
                source="test",
                confidence=0.7,
            ),
        )
        
        context = CreativeOpportunityContext(
            expected_value=100.0,
            application_cost=60.0,  # High cost relative to value
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.economic_viability_score < 0.5  # Poor viability
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.5,
            implementation_complexity=0.3,
        )
        
        context = CreativeOpportunityContext(
            risk_score=0.3,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert 0.0 <= evaluation.risk_score <= 1.0
        assert evaluation.risk_score < 0.5  # Low risk
    
    def test_risk_score_high_complexity(self):
        """Test risk score increases with complexity."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.LEARNING_FIRST,
            target_constraints={ConstraintType.KNOWLEDGE_GAP},
            expected_benefit=0.5,
            implementation_complexity=0.8,
        )
        
        context = CreativeOpportunityContext(
            risk_score=0.4,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.risk_score > 0.4  # Higher risk due to complexity
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.5,
            confidence_effect=EconomicsValue(
                value=0.3,
                status=VerificationStatus.UNKNOWN,
                source="test",
                confidence=0.7,
            ),
        )
        
        context = CreativeOpportunityContext(
            confidence_score=0.5,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.confidence_score > 0.5  # Increased by strategy effect
    
    def test_knowledge_alignment_score_stale(self):
        """Test knowledge alignment with stale knowledge."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.RESEARCH_FIRST,
            target_constraints={ConstraintType.STALE_KNOWLEDGE},
            expected_benefit=0.5,
        )
        
        context = CreativeOpportunityContext(
            knowledge_freshness=0.3,  # Stale
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.knowledge_alignment_score > 0.7  # Research-first is aligned
    
    def test_knowledge_alignment_score_good(self):
        """Test knowledge alignment with fresh knowledge."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.5,
        )
        
        context = CreativeOpportunityContext(
            knowledge_freshness=0.8,  # Fresh
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.knowledge_alignment_score >= 0.5  # Good alignment
    
    def test_execution_fit_score_calculation(self):
        """Test execution fit score calculation."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.5,
            implementation_complexity=0.3,
        )
        
        context = CreativeOpportunityContext(
            execution_readiness=0.8,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.execution_fit_score >= 0.6  # Good fit
    
    def test_addressed_constraints(self):
        """Test that addressed constraints are identified."""
        evaluator = StrategyEvaluator()
        
        from app.creativity.contracts import CreativeConstraint, ConstraintSeverity
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO, ConstraintType.NO_REVIEWS},
            expected_benefit=0.5,
        )
        
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
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert ConstraintType.NO_PORTFOLIO in evaluation.addressed_constraints
        assert ConstraintType.NO_REVIEWS not in evaluation.addressed_constraints
    
    def test_introduced_risks(self):
        """Test that introduced risks are identified."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.LEARNING_FIRST,
            target_constraints={ConstraintType.KNOWLEDGE_GAP},
            expected_benefit=0.5,
            implementation_complexity=0.8,
            economic_effect=EconomicsValue(
                value=-0.3,
                status=VerificationStatus.UNKNOWN,
                source="test",
                confidence=0.7,
            ),
            reversibility=0.2,
        )
        
        context = CreativeOpportunityContext()
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert len(evaluation.introduced_risks) > 0
        assert "high_complexity_risk" in evaluation.introduced_risks
    
    def test_recommendation_reason_generation(self):
        """Test that recommendation reason is generated."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
            expected_benefit=0.8,
            implementation_complexity=0.3,
        )
        
        context = CreativeOpportunityContext(
            execution_readiness=0.8,
            risk_score=0.2,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        assert evaluation.recommendation_reason
        assert len(evaluation.recommendation_reason) > 0
    
    def test_penalty_reasons_generation(self):
        """Test that penalty reasons are generated."""
        evaluator = StrategyEvaluator()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.LEARNING_FIRST,
            target_constraints={ConstraintType.KNOWLEDGE_GAP},
            expected_benefit=0.2,  # Low benefit
            implementation_complexity=0.9,  # High complexity
            economic_effect=EconomicsValue(
                value=-0.5,
                status=VerificationStatus.UNKNOWN,
                source="test",
                confidence=0.7,
            ),
        )
        
        context = CreativeOpportunityContext(
            risk_score=0.8,
        )
        
        evaluation = evaluator.evaluate(strategy, context)
        
        # Should have penalty reasons due to low benefit, high complexity, high risk
        assert len(evaluation.penalty_reasons) > 0
