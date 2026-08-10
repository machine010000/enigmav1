"""
Negative Tests for Creativity Engine

Tests that ensure creativity engine cannot:
- Fabricate evidence
- Bypass economics
- Bypass knowledge governance
- Approve applications directly
- Leak domain dependencies
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
from app.creativity.strategies import StrategyLibrary


class TestNoFakeEvidence:
    """Test that creativity cannot fabricate evidence."""
    
    def test_no_portfolio_no_fake_portfolio_strategy(self):
        """Test that no portfolio constraint does not generate fake portfolio strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.1,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends fake portfolio
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "fake" not in description
            assert "fabricate" not in description
            assert "invent" not in description
            assert "create fake" not in description
    
    def test_no_reviews_no_fake_testimonials_strategy(self):
        """Test that no reviews constraint does not generate fake testimonials strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            review_strength=0.1,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends fake testimonials
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "fake testimonial" not in description
            assert "fabricate review" not in description
            assert "invent review" not in description
    
    def test_low_evidence_no_fake_evidence_strategy(self):
        """Test that low evidence constraint does not generate fake evidence strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            evidence_readiness=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends fake evidence
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "fake evidence" not in description
            assert "fabricate evidence" not in description
            assert "invent evidence" not in description
    
    def test_strategy_library_no_fake_strategies(self):
        """Test that strategy library contains no fake evidence strategies."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            description = strategy.description.lower()
            assert "fake" not in description
            assert "fabricate" not in description
            assert "invent" not in description
            assert "create fake" not in description


class TestNoEconomicsBypass:
    """Test that creativity cannot bypass economics."""
    
    def test_poor_economics_no_apply_strategy(self):
        """Test that poor economics does not generate blind apply strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            application_cost=50.0,
            expected_value=40.0,  # Poor economics
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends applying despite poor economics
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            # Should not recommend applying anyway
            assert "apply anyway" not in description
            assert "ignore cost" not in description
            assert "bypass economics" not in description
    
    def test_high_application_cost_no_bypass_strategy(self):
        """Test that high application cost does not generate bypass strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            application_cost=30.0,
            expected_value=100.0,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends ignoring application cost
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "ignore cost" not in description
            assert "bypass cost" not in description
    
    def test_low_budget_no_spend_anyway_strategy(self):
        """Test that low budget does not generate spend anyway strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            budget=10.0,
            application_cost=8.0,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends spending despite low budget
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "spend anyway" not in description
            assert "ignore budget" not in description


class TestNoKnowledgeBypass:
    """Test that creativity cannot bypass knowledge governance."""
    
    def test_stale_knowledge_no_pretend_fresh_strategy(self):
        """Test that stale knowledge does not generate pretend fresh strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            knowledge_freshness=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends pretending knowledge is fresh
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "pretend" not in description
            assert "claim current" not in description
            assert "ignore staleness" not in description
    
    def test_knowledge_gap_no_fake_knowledge_strategy(self):
        """Test that knowledge gap does not generate fake knowledge strategy."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            knowledge_readiness=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Check that no strategy recommends faking knowledge
        for strategy in result.candidate_strategies:
            description = strategy.description.lower()
            assert "fake knowledge" not in description
            assert "claim expertise" not in description
            assert "pretend know" not in description
    
    def test_stale_knowledge_recommends_research(self):
        """Test that stale knowledge recommends research instead of bypass."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            knowledge_freshness=0.2,
        )
        
        result = engine.generate_strategies(context)
        
        # Should recommend research
        assert result.research_required is True
        
        # Check for research-first strategy
        research_strategies = [
            s for s in result.candidate_strategies
            if s.category == StrategyCategory.RESEARCH_FIRST
        ]
        assert len(research_strategies) > 0


class TestNoDecisionBypass:
    """Test that creativity cannot approve applications directly."""
    
    def test_creativity_result_not_final_approval(self):
        """Test that CreativityResult is not a final application approval."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.5,
        )
        
        result = engine.generate_strategies(context)
        
        # CreativityResult should not have approval fields
        assert not hasattr(result, "approved")
        assert not hasattr(result, "rejected")
        assert not hasattr(result, "final_decision")
    
    def test_engine_returns_strategies_not_decision(self):
        """Test that engine returns strategies, not decision."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.5,
        )
        
        result = engine.generate_strategies(context)
        
        # Should return strategies, not a decision
        assert hasattr(result, "ranked_strategies")
        assert hasattr(result, "candidate_strategies")
        assert not hasattr(result, "decision")
    
    def test_strategies_are_recommendations_not_commands(self):
        """Test that strategies are recommendations, not commands."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            description = strategy.description.lower()
            # Should be recommendations, not commands
            assert not description.startswith("must")
            assert not description.startswith("require")
            assert "you must" not in description
            assert "you have to" not in description


class TestNoDomainLeakage:
    """Test that generic creativity engine has no domain leakage."""
    
    def test_engine_no_seo_import(self):
        """Test that creativity engine does not import SEO domain."""
        import sys
        
        # Check that SEO domain is not imported in creativity modules
        creativity_modules = [
            "app.creativity.engine",
            "app.creativity.contracts",
            "app.creativity.constraints",
            "app.creativity.strategies",
            "app.creativity.evaluation",
            "app.creativity.ranking",
            "app.creativity.registry",
        ]
        
        for module_name in creativity_modules:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                # Check for SEO imports
                assert "seo" not in str(module.__dict__).lower()
    
    def test_strategies_domain_agnostic(self):
        """Test that strategies are domain-agnostic."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            # Should not reference specific domains in description
            description = strategy.description.lower()
            # These are generic terms, not domain-specific
            assert "seo-specific" not in description
            assert "ads-specific" not in description
    
    def test_engine_works_without_seo(self):
        """Test that engine works without SEO domain available."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            expert_domain="analytics",  # Different domain
            portfolio_strength=0.3,
        )
        
        result = engine.generate_strategies(context)
        
        # Should still generate strategies
        assert len(result.candidate_strategies) > 0


class TestNetworkIndependence:
    """Test that creativity tests run without network dependencies."""
    
    def test_constraint_detection_no_network(self):
        """Test that constraint detection does not require network."""
        from app.creativity.constraints import ConstraintDetector
        
        detector = ConstraintDetector()
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
        )
        
        # Should work without network
        constraints = detector.detect_constraints(context)
        assert len(constraints) > 0
    
    def test_strategy_evaluation_no_network(self):
        """Test that strategy evaluation does not require network."""
        from app.creativity.evaluation import StrategyEvaluator
        from app.creativity.strategies import StrategyLibrary
        
        evaluator = StrategyEvaluator()
        strategy = StrategyLibrary.proof_of_work_strategy()
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
        )
        
        # Should work without network
        evaluation = evaluator.evaluate(strategy, context)
        assert evaluation is not None
    
    def test_engine_no_network_required(self):
        """Test that engine does not require network."""
        engine = CreativityEngine()
        
        context = CreativeOpportunityContext(
            portfolio_strength=0.2,
        )
        
        # Should work without network
        result = engine.generate_strategies(context)
        assert result is not None


class TestGovernanceCompliance:
    """Test that creativity respects governance constraints."""
    
    def test_no_strategy_violates_truthfulness(self):
        """Test that no strategy violates truthfulness."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            description = strategy.description.lower()
            # Should not recommend dishonesty
            assert " lie " not in description  # Word boundary
            assert "mislead" not in description
            assert "deceive" not in description
    
    def test_no_strategy_violates_evidence_governance(self):
        """Test that no strategy violates evidence governance."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            description = strategy.description.lower()
            # Should not recommend fabricating evidence
            assert "fabricate" not in description
            assert "forge" not in description
            assert "counterfeit" not in description
    
    def test_no_strategy_violates_knowledge_governance(self):
        """Test that no strategy violates knowledge governance."""
        strategies = StrategyLibrary.get_all_strategies()
        
        for strategy in strategies:
            description = strategy.description.lower()
            # Should not recommend claiming knowledge that doesn't exist
            assert "claim knowledge" not in description
            assert "fake expertise" not in description
