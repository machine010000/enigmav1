"""
Integration tests for Proposal & Client-Facing Application Engine.

These tests verify the end-to-end pipeline:
SEO Job → READY → Proposal → Application → WAITING_FOR_APPROVAL
"""
import pytest
from datetime import datetime

from app.work_market.proposal_engine import (
    ProposalEngine,
    ProposalEngineResult,
    ProposalEngineStatus,
)
from app.work_market.proposal_strategy import ProposalStrategyType, ProposalTone
from app.work_market.application_package import ApplicationStatus, ApprovalDecision
from app.knowledge_governance import Concept, GovernedKnowledge


class TestSEOJobToApplicationIntegration:
    """Test SEO Job → READY → Proposal → Application integration scenario."""

    def test_proposal_strategy_generation_with_evidence(self):
        """Test proposal strategy generation with evidence-backed claims."""
        from app.work_market.proposal_strategy import ProposalStrategyGenerator
        
        generator = ProposalStrategyGenerator()
        
        job_description = "Need technical SEO audit for e-commerce site"
        available_capabilities = ["technical_seo", "site_speed"]
        available_evidence = {
            "technical_seo": ["ev1", "ev2"],
            "site_speed": ["ev3"],
        }
        governed_knowledge = []
        
        result = generator.generate_strategy(
            job_id="seo_job_001",
            job_description=job_description,
            available_capabilities=available_capabilities,
            available_evidence=available_evidence,
            governed_knowledge=governed_knowledge,
        )
        
        assert result.success is True
        assert result.strategy is not None
        assert len(result.strategy.capability_claims) > 0
        
        # All claims should have evidence
        for claim in result.strategy.capability_claims:
            assert claim.is_fabricated is False
            assert len(claim.evidence_ids) > 0

    def test_knowledge_selection_for_seo_job(self):
        """Test knowledge selection for SEO job."""
        from app.work_market.knowledge_selector import RelevantKnowledgeSelector
        from app.knowledge_governance import Concept
        
        selector = RelevantKnowledgeSelector()
        
        job_description = "Need technical SEO audit for e-commerce site"
        required_capabilities = ["technical_seo", "site_speed"]
        
        governed_knowledge = [
            GovernedKnowledge(
                concept=Concept(
                    id="k1",
                    name="technical_seo",
                    definition="SEO optimization techniques",
                )
            ),
            GovernedKnowledge(
                concept=Concept(
                    id="k2",
                    name="site_speed",
                    definition="Website speed optimization",
                )
            ),
        ]
        
        result = selector.select_knowledge(
            job_id="seo_job_001",
            job_description=job_description,
            required_capabilities=required_capabilities,
            governed_knowledge=governed_knowledge,
        )
        
        assert result.total_selected > 0
        assert result.confidence > 0
        assert len(result.selections) > 0

    def test_proposal_generation_from_strategy(self):
        """Test proposal generation from strategy."""
        from app.work_market.proposal_generator import ProposalGenerator
        from app.work_market.proposal_strategy import (
            ProposalStrategy,
            ProposalStrategyType,
            ProposalTone,
        )
        
        generator = ProposalGenerator()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="seo_job_001",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
            confidence_score=0.8,
        )
        
        result = generator.generate_proposal(
            job_id="seo_job_001",
            strategy=strategy,
        )
        
        assert result.success is True
        assert result.generated is not None
        assert result.generated.proposal is not None
        assert len(result.generated.proposal.sections) > 0

    def test_application_package_building(self):
        """Test application package building."""
        from app.work_market.application_package import ApplicationPackageBuilder
        from app.work_market.proposal_strategy import (
            ProposalStrategy,
            ProposalStrategyType,
            ProposalTone,
        )
        
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="seo_job_001",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
            confidence_score=0.8,
        )
        
        governed_knowledge = []
        evidence_map = {}
        readiness_score = 0.8
        
        result = builder.build_package(
            job_id="seo_job_001",
            strategy=strategy,
            governed_knowledge=governed_knowledge,
            evidence_map=evidence_map,
            readiness_score=readiness_score,
        )
        
        assert result.success is True
        assert result.package is not None
        assert result.package.status == ApplicationStatus.WAITING_FOR_APPROVAL
        assert result.package.approval_decision == ApprovalDecision.PENDING

    def test_full_proposal_engine_pipeline(self):
        """Test the complete proposal engine pipeline."""
        engine = ProposalEngine()
        
        job_id = "seo_job_001"
        job_description = "Need technical SEO audit for e-commerce site"
        required_capabilities = ["technical_seo", "site_speed"]
        available_capabilities = ["technical_seo", "site_speed"]
        available_evidence = {
            "technical_seo": ["ev1", "ev2"],
            "site_speed": ["ev3"],
        }
        governed_knowledge = [
            GovernedKnowledge(
                concept=Concept(
                    id="k1",
                    name="technical_seo",
                    definition="SEO optimization techniques",
                )
            ),
        ]
        evidence_map = {}
        readiness_score = 0.8
        
        result = engine.generate_application(
            job_id=job_id,
            job_description=job_description,
            required_capabilities=required_capabilities,
            available_capabilities=available_capabilities,
            available_evidence=available_evidence,
            governed_knowledge=governed_knowledge,
            evidence_map=evidence_map,
            readiness_score=readiness_score,
        )
        
        assert result.status == ProposalEngineStatus.COMPLETED
        assert result.application_package is not None
        assert result.application_package.status == ApplicationStatus.WAITING_FOR_APPROVAL
        assert result.strategy_result is not None
        assert result.strategy_result.success is True
        assert result.proposal_generation is not None
        assert result.proposal_generation.success is True
        assert result.package_result is not None
        assert result.package_result.success is True

    def test_application_approval_workflow(self):
        """Test application approval workflow."""
        from app.work_market.application_package import (
            ApplicationPackageBuilder,
            ApplicationPackage,
        )
        from app.work_market.proposal_strategy import (
            ProposalStrategy,
            ProposalStrategyType,
            ProposalTone,
        )
        
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="seo_job_001",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        from app.work_market.application_package import Proposal
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="seo_job_001",
            proposal=Proposal(
                proposal_id="p1",
                job_id="seo_job_001",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=strategy,
            status=ApplicationStatus.WAITING_FOR_APPROVAL,
        )
        
        # Approve
        approved = builder.approve_application(
            package,
            approved_by="user",
            notes="Looks good",
        )
        
        assert approved.status == ApplicationStatus.APPROVED
        assert approved.approval_decision == ApprovalDecision.APPROVED
        assert approved.approved_by == "user"
        assert approved.approved_at is not None

    def test_application_rejection_workflow(self):
        """Test application rejection workflow."""
        from app.work_market.application_package import (
            ApplicationPackageBuilder,
            ApplicationPackage,
        )
        from app.work_market.proposal_strategy import (
            ProposalStrategy,
            ProposalStrategyType,
            ProposalTone,
        )
        
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="seo_job_001",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        from app.work_market.application_package import Proposal
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="seo_job_001",
            proposal=Proposal(
                proposal_id="p1",
                job_id="seo_job_001",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=strategy,
            status=ApplicationStatus.WAITING_FOR_APPROVAL,
        )
        
        # Reject
        rejected = builder.reject_application(
            package,
            approved_by="user",
            notes="Not suitable",
        )
        
        assert rejected.status == ApplicationStatus.REJECTED
        assert rejected.approval_decision == ApprovalDecision.REJECTED
        assert rejected.approved_by == "user"
        assert rejected.approval_notes == "Not suitable"

    def test_application_revision_request_workflow(self):
        """Test application revision request workflow."""
        from app.work_market.application_package import (
            ApplicationPackageBuilder,
            ApplicationPackage,
        )
        from app.work_market.proposal_strategy import (
            ProposalStrategy,
            ProposalStrategyType,
            ProposalTone,
        )
        
        builder = ApplicationPackageBuilder()
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="seo_job_001",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
        )
        
        from app.work_market.application_package import Proposal
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="seo_job_001",
            proposal=Proposal(
                proposal_id="p1",
                job_id="seo_job_001",
                job_understanding="Test",
                proposed_approach="Test",
            ),
            strategy=strategy,
            status=ApplicationStatus.WAITING_FOR_APPROVAL,
        )
        
        # Request revision
        revision = builder.request_revision(
            package,
            approved_by="user",
            notes="Need more details",
        )
        
        assert revision.status == ApplicationStatus.READY_FOR_REVIEW
        assert revision.approval_decision == ApprovalDecision.REVISION_REQUESTED
        assert revision.approved_by == "user"
        assert revision.approval_notes == "Need more details"

    def test_application_summary_generation(self):
        """Test application summary generation."""
        from app.work_market.application_package import (
            ApplicationPackage,
            ApplicationStatus,
        )
        from app.work_market.proposal_strategy import (
            ProposalStrategy,
            ProposalStrategyType,
            ProposalTone,
        )
        
        strategy = ProposalStrategy(
            strategy_id="s1",
            job_id="seo_job_001",
            strategy_type=ProposalStrategyType.VALUE_FOCUSED,
            tone=ProposalTone.PROFESSIONAL,
            confidence_score=0.8,
        )
        
        from app.work_market.application_package import Proposal
        
        package = ApplicationPackage(
            application_id="app1",
            job_id="seo_job_001",
            proposal=Proposal(
                proposal_id="p1",
                job_id="seo_job_001",
                job_understanding="Test",
                proposed_approach="Test",
                confidence_score=0.8,
            ),
            strategy=strategy,
            status=ApplicationStatus.WAITING_FOR_APPROVAL,
            readiness_score=0.8,
            knowledge_used=["k1", "k2"],
        )
        
        engine = ProposalEngine()
        summary = engine.get_application_summary(package)
        
        assert summary["application_id"] == "app1"
        assert summary["job_id"] == "seo_job_001"
        assert summary["status"] == "waiting_for_approval"
        assert summary["readiness_score"] == 0.8
        assert summary["proposal_confidence"] == 0.8
        assert summary["knowledge_used"] == 2
