from __future__ import annotations

from app.work_market.models import (
    FreelanceJob,
    JobSource,
    JobClassification,
    JobEvaluation,
    JobRecommendation,
    LearningRequirement,
    ApplicationDraft,
    WorkType,
    WorkContext,
    Platform,
    PlatformType,
    PlatformConnectionStatus,
    JobAssessment,
    Application,
    ApplicationStatus,
    ActiveWork,
)
from app.work_market.adapters import JobSourceAdapter, MockJobSource, JobDiscoveryQuery
from app.work_market.classifier import JobClassifier
from app.work_market.evaluator import JobEvaluator
from app.work_market.learning_analyzer import LearningAnalyzer
from app.work_market.application_draft_generator import ApplicationDraftGenerator
from app.work_market.profession_integrator import ProfessionIntegrator
from app.work_market.governance_integrator import KnowledgeGovernanceIntegrator
from app.work_market.platform_registry import PlatformRegistry
from app.work_market.readiness_service import FreelancingReadinessService
from app.work_market.contracts import (
    KnowledgeProvider,
    EvidenceProvider,
    ProfessionProvider,
    ExpertDomainProvider,
    DecisionProvider,
    WorkSpecificationProvider,
    PlatformRepository,
    JobRepository,
    JobClassificationRepository,
    JobEvaluationRepository,
    JobAssessmentRepository,
    ApplicationRepository,
    ActiveWorkRepository,
)
from app.work_market.repositories import (
    InMemoryPlatformRepository,
    InMemoryJobRepository,
    InMemoryJobClassificationRepository,
    InMemoryJobEvaluationRepository,
    InMemoryJobAssessmentRepository,
    InMemoryApplicationRepository,
    InMemoryActiveWorkRepository,
)
from app.work_market.knowledge_governance_adapter import KnowledgeGovernanceAdapter, MockKnowledgeProvider
from app.work_market.evidence_adapter import EvidenceAdapter, MockEvidenceProvider
from app.work_market.expert_domain_adapter import ExpertDomainAdapter, MockExpertDomainAdapter
from app.work_market.decision_adapter import DecisionAdapter, MockDecisionProvider
from app.work_market.work_specification_adapter import WorkSpecificationAdapter, MockWorkSpecificationProvider
from app.work_market.job_classifier import JobClassificationOrchestrator, SEOJobCategory, JobClassificationResult
from app.work_market.job_mapper import JobMappingOrchestrator, CapabilityMappingResult, TaskMappingResult
from app.work_market.job_analyzer import JobAnalysisOrchestrator, JobAnalysisResult
from app.work_market.job_readiness import JobReadinessOrchestrator, JobReadinessResult
from app.work_market.job_recommendation import JobRecommendationOrchestrator, JobRecommendationResult, JobRecommendation
from app.work_market.job_gap_analysis import JobGapAnalysisOrchestrator, GapAnalysisResult
from app.work_market.job_proposal_context import ProposalContextOrchestrator, ProposalContextResult
from app.work_market.job_intelligence_orchestrator import JobIntelligenceOrchestrator, JobIntelligenceResult, job_intelligence_orchestrator

__all__ = [
    # Models
    "FreelanceJob",
    "JobSource",
    "JobClassification",
    "JobEvaluation",
    "JobRecommendation",
    "LearningRequirement",
    "ApplicationDraft",
    "WorkType",
    "WorkContext",
    "Platform",
    "PlatformType",
    "PlatformConnectionStatus",
    "JobAssessment",
    "Application",
    "ApplicationStatus",
    "ActiveWork",
    # Adapters
    "JobSourceAdapter",
    "MockJobSource",
    "JobDiscoveryQuery",
    # Services
    "JobClassifier",
    "JobEvaluator",
    "LearningAnalyzer",
    "ApplicationDraftGenerator",
    # Integrators
    "ProfessionIntegrator",
    "KnowledgeGovernanceIntegrator",
    # Registry
    "PlatformRegistry",
    # Readiness
    "FreelancingReadinessService",
    # Contracts
    "KnowledgeProvider",
    "EvidenceProvider",
    "ProfessionProvider",
    "ExpertDomainProvider",
    "DecisionProvider",
    "WorkSpecificationProvider",
    "PlatformRepository",
    "JobRepository",
    "JobClassificationRepository",
    "JobEvaluationRepository",
    "JobAssessmentRepository",
    "ApplicationRepository",
    "ActiveWorkRepository",
    # Repository Implementations
    "InMemoryPlatformRepository",
    "InMemoryJobRepository",
    "InMemoryJobClassificationRepository",
    "InMemoryJobEvaluationRepository",
    "InMemoryJobAssessmentRepository",
    "InMemoryApplicationRepository",
    "InMemoryActiveWorkRepository",
    # Adapters
    "KnowledgeGovernanceAdapter",
    "MockKnowledgeProvider",
    "EvidenceAdapter",
    "MockEvidenceProvider",
    "ExpertDomainAdapter",
    "MockExpertDomainAdapter",
    "DecisionAdapter",
    "MockDecisionProvider",
    "WorkSpecificationAdapter",
    "MockWorkSpecificationProvider",
    # Job Intelligence
    "JobClassificationOrchestrator",
    "SEOJobCategory",
    "JobClassificationResult",
    "JobMappingOrchestrator",
    "CapabilityMappingResult",
    "TaskMappingResult",
    "JobAnalysisOrchestrator",
    "JobAnalysisResult",
    "JobReadinessOrchestrator",
    "JobReadinessResult",
    "JobRecommendationOrchestrator",
    "JobRecommendationResult",
    "JobRecommendation",
    "JobGapAnalysisOrchestrator",
    "GapAnalysisResult",
    "ProposalContextOrchestrator",
    "ProposalContextResult",
    "JobIntelligenceOrchestrator",
    "JobIntelligenceResult",
    "job_intelligence_orchestrator",
]
