"""
Test Strategy Ranking
"""

import pytest

from app.creativity.contracts import (
    ConstraintType,
    StrategyCategory,
    CreativeStrategy,
    StrategyEvaluation,
    CreativeOpportunityContext,
)
from app.creativity.ranking import StrategyRanker


class TestStrategyRanker:
    """Test strategy ranking."""
    
    def test_rank_empty_list(self):
        """Test ranking empty list."""
        ranker = StrategyRanker()
        evaluations = []
        
        ranked = ranker.rank(evaluations)
        
        assert ranked == []
    
    def test_rank_single_strategy(self):
        """Test ranking single strategy."""
        ranker = StrategyRanker()
        
        strategy = CreativeStrategy(
            strategy_id="test_strategy",
            name="Test Strategy",
            description="A test strategy",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation = StrategyEvaluation(
            strategy=strategy,
            benefit_score=0.7,
            feasibility_score=0.7,
            economic_viability_score=0.7,
            risk_score=0.3,
            confidence_score=0.7,
            evidence_alignment_score=0.7,
            knowledge_alignment_score=0.7,
            execution_fit_score=0.7,
            reversibility_score=0.7,
            complexity_score=0.3,
            overall_score=0.7,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Good strategy",
            penalty_reasons=[],
        )
        
        ranked = ranker.rank([evaluation])
        
        assert len(ranked) == 1
        assert ranked[0] == evaluation
    
    def test_rank_multiple_strategies(self):
        """Test ranking multiple strategies."""
        ranker = StrategyRanker()
        
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
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        strategy3 = CreativeStrategy(
            strategy_id="strategy_3",
            name="Strategy 3",
            description="Strategy 3",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.5,
            feasibility_score=0.5,
            economic_viability_score=0.5,
            risk_score=0.5,
            confidence_score=0.5,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.5,
            execution_fit_score=0.5,
            reversibility_score=0.5,
            complexity_score=0.5,
            overall_score=0.5,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Medium strategy",
            penalty_reasons=[],
        )
        
        evaluation2 = StrategyEvaluation(
            strategy=strategy2,
            benefit_score=0.8,
            feasibility_score=0.8,
            economic_viability_score=0.8,
            risk_score=0.2,
            confidence_score=0.8,
            evidence_alignment_score=0.8,
            knowledge_alignment_score=0.8,
            execution_fit_score=0.8,
            reversibility_score=0.8,
            complexity_score=0.2,
            overall_score=0.8,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="High strategy",
            penalty_reasons=[],
        )
        
        evaluation3 = StrategyEvaluation(
            strategy=strategy3,
            benefit_score=0.3,
            feasibility_score=0.3,
            economic_viability_score=0.3,
            risk_score=0.7,
            confidence_score=0.3,
            evidence_alignment_score=0.3,
            knowledge_alignment_score=0.3,
            execution_fit_score=0.3,
            reversibility_score=0.3,
            complexity_score=0.7,
            overall_score=0.3,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Low strategy",
            penalty_reasons=[],
        )
        
        ranked = ranker.rank([evaluation1, evaluation2, evaluation3])
        
        assert len(ranked) == 3
        assert ranked[0].overall_score >= ranked[1].overall_score
        assert ranked[1].overall_score >= ranked[2].overall_score
        assert ranked[0].strategy.strategy_id == "strategy_2"
        assert ranked[2].strategy.strategy_id == "strategy_3"
    
    def test_rank_with_threshold(self):
        """Test ranking with minimum score threshold."""
        ranker = StrategyRanker()
        
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
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.5,
            feasibility_score=0.5,
            economic_viability_score=0.5,
            risk_score=0.5,
            confidence_score=0.5,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.5,
            execution_fit_score=0.5,
            reversibility_score=0.5,
            complexity_score=0.5,
            overall_score=0.5,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Medium strategy",
            penalty_reasons=[],
        )
        
        evaluation2 = StrategyEvaluation(
            strategy=strategy2,
            benefit_score=0.3,
            feasibility_score=0.3,
            economic_viability_score=0.3,
            risk_score=0.7,
            confidence_score=0.3,
            evidence_alignment_score=0.3,
            knowledge_alignment_score=0.3,
            execution_fit_score=0.3,
            reversibility_score=0.3,
            complexity_score=0.7,
            overall_score=0.3,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Low strategy",
            penalty_reasons=[],
        )
        
        ranked = ranker.rank_with_threshold([evaluation1, evaluation2], min_score=0.4)
        
        assert len(ranked) == 1
        assert ranked[0].overall_score >= 0.4
    
    def test_rank_with_threshold_all_pass(self):
        """Test ranking with threshold when all pass."""
        ranker = StrategyRanker()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.8,
            feasibility_score=0.8,
            economic_viability_score=0.8,
            risk_score=0.2,
            confidence_score=0.8,
            evidence_alignment_score=0.8,
            knowledge_alignment_score=0.8,
            execution_fit_score=0.8,
            reversibility_score=0.8,
            complexity_score=0.2,
            overall_score=0.8,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="High strategy",
            penalty_reasons=[],
        )
        
        ranked = ranker.rank_with_threshold([evaluation1], min_score=0.4)
        
        assert len(ranked) == 1
    
    def test_rank_with_threshold_none_pass(self):
        """Test ranking with threshold when none pass."""
        ranker = StrategyRanker()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.3,
            feasibility_score=0.3,
            economic_viability_score=0.3,
            risk_score=0.7,
            confidence_score=0.3,
            evidence_alignment_score=0.3,
            knowledge_alignment_score=0.3,
            execution_fit_score=0.3,
            reversibility_score=0.3,
            complexity_score=0.7,
            overall_score=0.3,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Low strategy",
            penalty_reasons=[],
        )
        
        ranked = ranker.rank_with_threshold([evaluation1], min_score=0.5)
        
        assert len(ranked) == 0
    
    def test_rank_by_category(self):
        """Test ranking by category."""
        ranker = StrategyRanker()
        
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
        
        strategy3 = CreativeStrategy(
            strategy_id="strategy_3",
            name="Strategy 3",
            description="Strategy 3",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.7,
            feasibility_score=0.7,
            economic_viability_score=0.7,
            risk_score=0.3,
            confidence_score=0.7,
            evidence_alignment_score=0.7,
            knowledge_alignment_score=0.7,
            execution_fit_score=0.7,
            reversibility_score=0.7,
            complexity_score=0.3,
            overall_score=0.7,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Good strategy",
            penalty_reasons=[],
        )
        
        evaluation2 = StrategyEvaluation(
            strategy=strategy2,
            benefit_score=0.6,
            feasibility_score=0.6,
            economic_viability_score=0.6,
            risk_score=0.4,
            confidence_score=0.6,
            evidence_alignment_score=0.6,
            knowledge_alignment_score=0.6,
            execution_fit_score=0.6,
            reversibility_score=0.6,
            complexity_score=0.4,
            overall_score=0.6,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Good strategy",
            penalty_reasons=[],
        )
        
        evaluation3 = StrategyEvaluation(
            strategy=strategy3,
            benefit_score=0.5,
            feasibility_score=0.5,
            economic_viability_score=0.5,
            risk_score=0.5,
            confidence_score=0.5,
            evidence_alignment_score=0.5,
            knowledge_alignment_score=0.5,
            execution_fit_score=0.5,
            reversibility_score=0.5,
            complexity_score=0.5,
            overall_score=0.5,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Medium strategy",
            penalty_reasons=[],
        )
        
        ranked_by_category = ranker.rank_by_category([evaluation1, evaluation2, evaluation3])
        
        assert "proof_of_work" in ranked_by_category
        assert "research_first" in ranked_by_category
        assert len(ranked_by_category["proof_of_work"]) == 2
        assert len(ranked_by_category["research_first"]) == 1
    
    def test_get_top_strategies(self):
        """Test getting top N strategies."""
        ranker = StrategyRanker()
        
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
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        strategy3 = CreativeStrategy(
            strategy_id="strategy_3",
            name="Strategy 3",
            description="Strategy 3",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.8,
            feasibility_score=0.8,
            economic_viability_score=0.8,
            risk_score=0.2,
            confidence_score=0.8,
            evidence_alignment_score=0.8,
            knowledge_alignment_score=0.8,
            execution_fit_score=0.8,
            reversibility_score=0.8,
            complexity_score=0.2,
            overall_score=0.8,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="High strategy",
            penalty_reasons=[],
        )
        
        evaluation2 = StrategyEvaluation(
            strategy=strategy2,
            benefit_score=0.6,
            feasibility_score=0.6,
            economic_viability_score=0.6,
            risk_score=0.4,
            confidence_score=0.6,
            evidence_alignment_score=0.6,
            knowledge_alignment_score=0.6,
            execution_fit_score=0.6,
            reversibility_score=0.6,
            complexity_score=0.4,
            overall_score=0.6,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Medium strategy",
            penalty_reasons=[],
        )
        
        evaluation3 = StrategyEvaluation(
            strategy=strategy3,
            benefit_score=0.4,
            feasibility_score=0.4,
            economic_viability_score=0.4,
            risk_score=0.6,
            confidence_score=0.4,
            evidence_alignment_score=0.4,
            knowledge_alignment_score=0.4,
            execution_fit_score=0.4,
            reversibility_score=0.4,
            complexity_score=0.6,
            overall_score=0.4,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="Low strategy",
            penalty_reasons=[],
        )
        
        top_2 = ranker.get_top_strategies([evaluation1, evaluation2, evaluation3], count=2)
        
        assert len(top_2) == 2
        assert top_2[0].overall_score >= top_2[1].overall_score
        assert top_2[0].strategy.strategy_id == "strategy_1"
        assert top_2[1].strategy.strategy_id == "strategy_2"
    
    def test_get_top_strategies_count_exceeds_list(self):
        """Test getting top strategies when count exceeds list size."""
        ranker = StrategyRanker()
        
        strategy1 = CreativeStrategy(
            strategy_id="strategy_1",
            name="Strategy 1",
            description="Strategy 1",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={ConstraintType.NO_PORTFOLIO},
        )
        
        evaluation1 = StrategyEvaluation(
            strategy=strategy1,
            benefit_score=0.8,
            feasibility_score=0.8,
            economic_viability_score=0.8,
            risk_score=0.2,
            confidence_score=0.8,
            evidence_alignment_score=0.8,
            knowledge_alignment_score=0.8,
            execution_fit_score=0.8,
            reversibility_score=0.8,
            complexity_score=0.2,
            overall_score=0.8,
            addressed_constraints=set(),
            introduced_risks=set(),
            recommendation_reason="High strategy",
            penalty_reasons=[],
        )
        
        top_5 = ranker.get_top_strategies([evaluation1], count=5)
        
        assert len(top_5) == 1
