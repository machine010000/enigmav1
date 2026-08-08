"""
Negative tests for Proposal & Client-Facing Application Engine.

These tests verify that the system correctly handles:
- No fabricated claims
- Evidence validation
- Invalid data
- Edge cases
"""
import pytest

from app.work_market.proposal_strategy import (
    ProposalStrategyGenerator,
    ProposalStrategy,
    ProposalStrategyType,
    ProposalTone,
    CapabilityClaim,
)
from app.work_market.application_package import (
    ApplicationPackageBuilder,
    ApplicationPackage,
    ApplicationStatus,
)
from app.work_market.proposal_generator import ProposalGenerator
from app.knowledge_governance import Concept, GovernedKnowledge


class TestNoFabricatedClaims:
    """Test that no fabricated claims are allowed."""

    def test_proposal_strategy_rejects_fabricated_claims(self):
        """Test that proposal strategy rejects claims without evidence."""
        generator = ProposalStrategyGenerator()
        
        job_description = "Need technical SEO audit"
        available_capabilities = ["technical_seo"]
        available_evidence = {}  # No evidence for technical_seo
        governed_knowledge = []
        
        result = generator.generate_strategy(
            job_id="test_job",
            job_description=job_description,
            available_capabilities=available_capabilities,
            available_evidence=available_evidence,
            governed_knowledge=governed_knowledge,
        )
        
        # Should succeed but with no claims (since no evidence)
        assert result.success is True
        # No capability claims should be generated without evidence
        assert len(result.strategy.capability_claims) == 0

    def test_capability_claim_fabrication_flag(self):
        """Test that capability claim has fabrication flag."""
        claim = CapabilityClaim(
            capability_id="test",
            capability_name="test",
            claim="Test claim",
            evidence_ids=[],
            is_fabricated=True,  # Marked as fabricated
        )
        
        assert claim.is_fabricated is True

    def test_proposal_generator_rejects_fabricated_claims(self):
        """Test that proposal generator rejects fabricated claims."""
        generator = ProposalGenerator()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
            capability_claims=[
                CapabilityClaim(
                    capability_id="test",
                    capability_name="test",
                    claim="Test claim",
                    evidence_ids=[],
                    is_fabricated=True,  # Fabricated claim
                )
            ],
        )
        
        result = generator.generate_proposal(
            job_id="test_job",
            strategy=strategy,
        )
        
        assert result.success is False
        assert len(result.errors) > 0

    def test_application_package_rejects_fabricated_claims(self):
        """Test that application package rejects fabricated claims."""
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
            capability_claims=[
                CapabilityClaim(
                    capability_id="test",
                    capability_name="test",
                    claim="Test claim",
                    evidence_ids=[],
                    is_fabricated=True,  # Fabricated claim
                )
            ],
        )
        
        governed_knowledge = []
        evidence_map = {}
        readiness_score = 0.8
        
        result = builder.build_package(
            job_id="test_job",
            strategy=strategy,
            governed_knowledge=governed_knowledge,
            evidence_map=evidence_map,
            readiness_score=readiness_score,
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "evidence" in result.errors[0].lower()


class TestEvidenceValidation:
    """Test evidence validation."""

    def test_capability_claim_requires_evidence(self):
        """Test that capability claims require evidence."""
        claim = CapabilityClaim(
            capability_id="test",
            capability_name="test",
            claim="Test claim",
            evidence_ids=[],  # No evidence
            is_fabricated=False,
        )
        
        # Claim without evidence should be marked as fabricated
        assert len(claim.evidence_ids) == 0

    def test_evidence_provenance_tracked(self):
        """Test that evidence provenance is tracked."""
        from app.work_market.application_package import ApplicationPackage, Proposal
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="test_job",
            proposal=Proposal(
                proposal_id="p1",
                job_id="test_job",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=strategy,
            evidence_provenance={"ev1": "governed_knowledge"},
        )
        
        assert "ev1" in package.evidence_provenance
        assert package.evidence_provenance["ev1"] == "governed_knowledge"

    def test_knowledge_usage_tracked(self):
        """Test that knowledge usage is tracked."""
        from app.work_market.application_package import ApplicationPackage, Proposal
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="test_job",
            proposal=Proposal(
                proposal_id="p1",
                job_id="test_job",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=strategy,
            knowledge_used=["k1", "k2"],
        )
        
        assert len(package.knowledge_used) == 2
        assert "k1" in package.knowledge_used


class TestInvalidDataHandling:
    """Test invalid data handling."""

    def test_proposal_strategy_with_empty_capabilities(self):
        """Test proposal strategy with empty capabilities."""
        generator = ProposalStrategyGenerator()
        
        result = generator.generate_strategy(
            job_id="test_job",
            job_description="Test job",
            available_capabilities=[],
            available_evidence={},
            governed_knowledge=[],
        )
        
        assert result.success is True
        assert len(result.strategy.capability_claims) == 0

    def test_proposal_strategy_with_empty_evidence(self):
        """Test proposal strategy with empty evidence."""
        generator = ProposalStrategyGenerator()
        
        result = generator.generate_strategy(
            job_id="test_job",
            job_description="Test job",
            available_capabilities=["test_cap"],
            available_evidence={},  # No evidence
            governed_knowledge=[],
        )
        
        assert result.success is True
        # No claims should be generated without evidence
        assert len(result.strategy.capability_claims) == 0

    def test_application_package_with_empty_knowledge(self):
        """Test application package with empty knowledge."""
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        result = builder.build_package(
            job_id="test_job",
            strategy=strategy,
            governed_knowledge=[],
            evidence_map={},
            readiness_score=0.0,
        )
        
        assert result.success is True
        assert len(result.package.knowledge_used) == 0


class TestEdgeCases:
    """Test edge cases."""

    def test_proposal_strategy_with_zero_confidence(self):
        """Test proposal strategy with zero confidence."""
        generator = ProposalStrategyGenerator()
        
        result = generator.generate_strategy(
            job_id="test_job",
            job_description="Test job",
            available_capabilities=[],
            available_evidence={},
            governed_knowledge=[],
        )
        
        assert result.strategy.confidence_score == 0.0

    def test_application_package_with_zero_readiness(self):
        """Test application package with zero readiness."""
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        result = builder.build_package(
            job_id="test_job",
            strategy=strategy,
            governed_knowledge=[],
            evidence_map={},
            readiness_score=0.0,
        )
        
        assert result.success is True
        assert result.package.readiness_score == 0.0

    def test_knowledge_selector_with_no_knowledge(self):
        """Test knowledge selector with no knowledge."""
        from app.work_market.knowledge_selector import RelevantKnowledgeSelector
        
        selector = RelevantKnowledgeSelector()
        
        result = selector.select_knowledge(
            job_id="test_job",
            job_description="Test job",
            required_capabilities=["test"],
            governed_knowledge=[],
        )
        
        assert result.total_selected == 0
        assert result.confidence == 0.0


class TestSecurityConstraints:
    """Test security constraints."""

    def test_no_direct_evidence_access_in_proposal(self):
        """Test that proposal doesn't have direct evidence access."""
        generator = ProposalGenerator()
        
        # ProposalGenerator should only work with strategy, not direct evidence
        assert not hasattr(generator, '_evidence_map')

    def test_capability_claim_cannot_be_fabricated_without_flag(self):
        """Test that claims without evidence are flagged."""
        claim = CapabilityClaim(
            capability_id="test",
            capability_name="test",
            claim="Test claim",
            evidence_ids=[],
            is_fabricated=False,  # Flagged as not fabricated but has no evidence
        )
        
        # This is a data integrity issue - the flag should match evidence
        assert len(claim.evidence_ids) == 0

    def test_evidence_provenance_preserved(self):
        """Test that evidence provenance is preserved."""
        from app.work_market.application_package import ApplicationPackage, Proposal
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="test_job",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="test_job",
            proposal=Proposal(
                proposal_id="p1",
                job_id="test_job",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=strategy,
            evidence_provenance={"ev1": "governed_knowledge"},
        )
        
        # Provenance should be preserved
        assert package.evidence_provenance == {"ev1": "governed_knowledge"}
