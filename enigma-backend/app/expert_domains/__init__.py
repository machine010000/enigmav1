from __future__ import annotations

from app.expert_domains.contracts import (
    ExpertDomainContract,
    DomainIdentity,
    KnowledgeArea,
    DomainConcept,
    DomainEvidence,
    ReasoningPattern,
    DecisionRule,
    DomainKPI,
    ExecutionStandard,
    EvaluationResult,
    ReadinessScore,
    DomainLifecycleStage,
    ReasoningPatternType,
)

from app.expert_domains.models import (
    KnowledgeStructure,
    DomainLifecycle,
    DomainMaturity,
    DomainEvaluation,
    DomainReadiness,
    DomainLearning,
)

from app.expert_domains.registry import ExpertDomainRegistry, expert_domain_registry

from app.expert_domains.capabilities import (
    CapabilityContract,
    CapabilityPurpose,
    CapabilityRegistry,
)

from app.expert_domains.tasks import (
    TaskContract,
    TaskCategory,
    TaskStatus,
    TaskRegistry,
)

from app.expert_domains.execution import (
    ExecutionStep,
    ExecutionStepType,
    ExecutionTemplate,
    ExecutionTemplateRegistry,
)

from app.expert_domains.domains import SEODomain

# Register the SEO domain
expert_domain_registry.register(SEODomain())

from app.expert_domains.reasoning import (
    ReasoningInput,
    ReasoningOutput,
    ReasoningPattern,
    DiagnosisPattern,
    ComparisonPattern,
    OptimizationPattern,
    PredictionPattern,
    PlanningPattern,
    EvaluationPattern,
    RecommendationPattern,
)

from app.expert_domains.learning import LearningManager

from app.expert_domains.metadata import (
    DomainMetadata,
    DomainStatus,
    BusinessModule,
    Platform,
    DomainDependency,
    DomainMetadataRegistry,
)

from app.expert_domains.compatibility import (
    CompatibilityRelationship,
    CompatibilityType,
    CompatibilityMatrix,
    CompatibilityRegistry,
)

from app.expert_domains.mapping import (
    ProfessionMapping,
    MappingType,
    Profession,
    CapabilityTaskMapping,
    ProfessionMappingRegistry,
)

from app.expert_domains.work import (
    WorkSpecification,
    WorkPriority,
    WorkComplexity,
    WorkStatus,
    WorkCapabilityMapping,
    WorkTaskMapping,
    ClientRequirements,
    Requirement,
    RequirementType,
    RequirementPriority,
    BudgetConstraint,
    TimelineConstraint,
    PlatformConstraint,
    ComplianceRequirement,
    Deliverable,
    DeliverableType,
    DeliverableFormat,
    DeliverableStatus,
    DeliverableInstance,
    DeliverableRequirement,
    AcceptanceCriterion,
    AcceptancePriority,
    MeasurementType,
    ValidationMethod,
    AcceptanceCriteriaSet,
    AcceptanceResult,
    AcceptanceChecklist,
    Review,
    ReviewType,
    ReviewStatus,
    ReviewDecision,
    ReviewChecklistItem,
    ReviewChecklist,
    ReviewValidationRule,
    ReviewApproval,
    ReviewPolicy,
    WorkRegistry,
    work_registry,
)

__all__ = [
    # Contracts
    "ExpertDomainContract",
    "DomainIdentity",
    "KnowledgeArea",
    "DomainConcept",
    "DomainEvidence",
    "ReasoningPattern",
    "DecisionRule",
    "DomainKPI",
    "ExecutionStandard",
    "EvaluationResult",
    "ReadinessScore",
    "DomainLifecycleStage",
    "ReasoningPatternType",
    # Models
    "KnowledgeStructure",
    "DomainLifecycle",
    "DomainMaturity",
    "DomainEvaluation",
    "DomainReadiness",
    "DomainLearning",
    # Registry
    "ExpertDomainRegistry",
    "expert_domain_registry",
    # Frameworks
    "LifecycleManager",
    "MaturityManager",
    "EvaluationFramework",
    "ReadinessFramework",
    "LearningManager",
    # Reasoning
    "ReasoningInput",
    "ReasoningOutput",
    "ReasoningPattern",
    "DiagnosisPattern",
    "ComparisonPattern",
    "OptimizationPattern",
    "PredictionPattern",
    "PlanningPattern",
    "EvaluationPattern",
    "RecommendationPattern",
    # Capabilities
    "CapabilityContract",
    "CapabilityPurpose",
    "CapabilityRequirement",
    "CapabilityRegistry",
    # Tasks
    "TaskContract",
    "TaskCategory",
    "TaskStatus",
    "TaskRequirement",
    "TaskExecution",
    "TaskRegistry",
    # Execution
    "ExecutionStep",
    "ExecutionStepType",
    "ExecutionTemplate",
    "QualityGate",
    "ValidationCheckpoint",
    "ExecutionTemplateRegistry",
    # Metadata
    "DomainMetadata",
    "DomainStatus",
    "BusinessModule",
    "Platform",
    "DomainDependency",
    "DomainMetadataRegistry",
    # Compatibility
    "CompatibilityRelationship",
    "CompatibilityType",
    "CompatibilityMatrix",
    "CompatibilityRegistry",
    # Mapping
    "ProfessionMapping",
    "MappingType",
    "Profession",
    "CapabilityTaskMapping",
    "ProfessionMappingRegistry",
    # Work
    "WorkSpecification",
    "WorkPriority",
    "WorkComplexity",
    "WorkStatus",
    "WorkCapabilityMapping",
    "WorkTaskMapping",
    "ClientRequirements",
    "Requirement",
    "RequirementType",
    "RequirementPriority",
    "BudgetConstraint",
    "TimelineConstraint",
    "PlatformConstraint",
    "ComplianceRequirement",
    "Deliverable",
    "DeliverableType",
    "DeliverableFormat",
    "DeliverableStatus",
    "DeliverableInstance",
    "DeliverableRequirement",
    "AcceptanceCriterion",
    "AcceptancePriority",
    "MeasurementType",
    "ValidationMethod",
    "AcceptanceCriteriaSet",
    "AcceptanceResult",
    "AcceptanceChecklist",
    "Review",
    "ReviewType",
    "ReviewStatus",
    "ReviewDecision",
    "ReviewChecklistItem",
    "ReviewChecklist",
    "ReviewValidationRule",
    "ReviewApproval",
    "ReviewPolicy",
    "WorkRegistry",
    "work_registry",
    # Domains
    "SEODomain",
]
