from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.expert_domains.work.work_specification import (
    WorkSpecification,
    WorkCapabilityMapping,
    WorkTaskMapping,
)
from app.work_market.job_classifier import SEOJobCategory


class MappingType(str, Enum):
    """Types of capability and task mappings."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    RECOMMENDED = "recommended"
    SUGGESTED = "suggested"


class MappingImportance(str, Enum):
    """Importance levels for mappings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CapabilityMappingResult:
    """Result of capability mapping."""
    work_id: str
    required_capabilities: List[str] = field(default_factory=list)
    optional_capabilities: List[str] = field(default_factory=list)
    recommended_capabilities: List[str] = field(default_factory=list)
    mapping_justifications: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    mapped_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskMappingResult:
    """Result of task mapping."""
    work_id: str
    required_tasks: List[str] = field(default_factory=list)
    optional_tasks: List[str] = field(default_factory=list)
    suggested_tasks: List[str] = field(default_factory=list)
    task_order: List[str] = field(default_factory=list)
    mapping_justifications: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    mapped_at: datetime = field(default_factory=datetime.utcnow)


class JobCapabilityMapper(ABC):
    """Contract for mapping work specifications to capabilities."""

    @abstractmethod
    def map_capabilities(self, work_spec: WorkSpecification) -> CapabilityMappingResult:
        """
        Map work specification to SEO capabilities.

        Analyzes:
        - Job category
        - Business goal
        - Complexity
        - Industry

        Returns mapped capabilities with justifications.
        """
        pass


class JobTaskMapper(ABC):
    """Contract for mapping work specifications to tasks."""

    @abstractmethod
    def map_tasks(self, work_spec: WorkSpecification) -> TaskMappingResult:
        """
        Map work specification to SEO tasks.

        Analyzes:
        - Job category
        - Required capabilities
        - Complexity
        - Timeline

        Returns mapped tasks with execution order.
        """
        pass


class SEOCapabilityMapper(JobCapabilityMapper):
    """
    Maps work specifications to SEO capabilities.

    Uses category-based mapping rules to determine required capabilities.
    """

    def __init__(self) -> None:
        self._capability_mappings = self._initialize_capability_mappings()

    def _initialize_capability_mappings(self) -> Dict[SEOJobCategory, Dict[str, Any]]:
        """Initialize capability mappings for each SEO category."""
        return {
            SEOJobCategory.SEO_AUDIT: {
                "required": [
                    "technical_seo_audit",
                    "site_speed_optimization",
                    "crawling_indexing",
                ],
                "optional": [
                    "mobile_optimization",
                    "schema_markup",
                ],
                "recommended": [
                    "keyword_research",
                    "on_page_optimization",
                ],
            },
            SEOJobCategory.KEYWORD_RESEARCH: {
                "required": [
                    "keyword_research",
                ],
                "optional": [
                    "competitor_analysis",
                    "search_intent_analysis",
                ],
                "recommended": [
                    "on_page_optimization",
                    "content_optimization",
                ],
            },
            SEOJobCategory.TECHNICAL_SEO: {
                "required": [
                    "technical_seo_audit",
                    "site_speed_optimization",
                    "mobile_optimization",
                ],
                "optional": [
                    "schema_markup",
                    "canonicalization",
                    "redirect_management",
                ],
                "recommended": [
                    "crawling_indexing",
                    "xml_sitemap",
                ],
            },
            SEOJobCategory.LOCAL_SEO: {
                "required": [
                    "google_business_profile",
                    "local_citations",
                ],
                "optional": [
                    "local_keywords",
                    "reviews_management",
                ],
                "recommended": [
                    "local_schema",
                    "on_page_optimization",
                ],
            },
            SEOJobCategory.ECOMMERCE_SEO: {
                "required": [
                    "technical_seo_audit",
                    "keyword_research",
                    "on_page_optimization",
                ],
                "optional": [
                    "schema_markup",
                    "site_speed_optimization",
                ],
                "recommended": [
                    "content_optimization",
                    "internal_linking",
                ],
            },
            SEOJobCategory.CONTENT_OPTIMIZATION: {
                "required": [
                    "on_page_optimization",
                    "content_optimization",
                ],
                "optional": [
                    "keyword_research",
                    "internal_linking",
                ],
                "recommended": [
                    "title_optimization",
                    "meta_description",
                ],
            },
            SEOJobCategory.LINK_BUILDING: {
                "required": [
                    "link_building",
                    "backlink_analysis",
                ],
                "optional": [
                    "anchor_text",
                    "domain_authority",
                ],
                "recommended": [
                    "outreach_strategy",
                    "content_creation",
                ],
            },
            SEOJobCategory.SEO_STRATEGY: {
                "required": [
                    "keyword_research",
                    "competitor_analysis",
                ],
                "optional": [
                    "technical_seo_audit",
                    "content_strategy",
                ],
                "recommended": [
                    "on_page_optimization",
                    "link_building",
                ],
            },
            SEOJobCategory.ON_PAGE_SEO: {
                "required": [
                    "on_page_optimization",
                    "title_optimization",
                    "meta_description",
                ],
                "optional": [
                    "header_tags",
                    "internal_linking",
                ],
                "recommended": [
                    "keyword_research",
                    "content_optimization",
                ],
            },
            SEOJobCategory.OFF_PAGE_SEO: {
                "required": [
                    "link_building",
                    "backlink_analysis",
                ],
                "optional": [
                    "social_signals",
                    "brand_mentions",
                ],
                "recommended": [
                    "domain_authority",
                    "outreach_strategy",
                ],
            },
        }

    def map_capabilities(self, work_spec: WorkSpecification) -> CapabilityMappingResult:
        """Map work specification to SEO capabilities."""
        # Get category from metadata
        category_str = work_spec.metadata.get("category", "seo_audit")
        try:
            category = SEOJobCategory(category_str)
        except ValueError:
            category = SEOJobCategory.SEO_AUDIT

        # Get base mappings for category
        mappings = self._capability_mappings.get(category, self._capability_mappings[SEOJobCategory.SEO_AUDIT])

        # Adjust based on complexity
        required = self._adjust_for_complexity(mappings["required"], work_spec.complexity)
        optional = self._adjust_for_complexity(mappings["optional"], work_spec.complexity)
        recommended = self._adjust_for_complexity(mappings["recommended"], work_spec.complexity)

        # Generate justifications
        justifications = self._generate_justifications(category, required, optional, recommended)

        # Calculate confidence
        confidence = self._calculate_confidence(category, work_spec)

        return CapabilityMappingResult(
            work_id=work_spec.work_id,
            required_capabilities=required,
            optional_capabilities=optional,
            recommended_capabilities=recommended,
            mapping_justifications=justifications,
            confidence=confidence,
        )

    def _adjust_for_complexity(self, capabilities: List[str], complexity: str) -> List[str]:
        """Adjust capability list based on complexity."""
        # Higher complexity may require more capabilities
        if complexity in ["complex", "very_complex"]:
            # Add additional capabilities for complex jobs
            additional = [
                "competitor_analysis",
                "risk_assessment",
                "performance_monitoring",
            ]
            return capabilities + [cap for cap in additional if cap not in capabilities]
        return capabilities

    def _generate_justifications(
        self,
        category: SEOJobCategory,
        required: List[str],
        optional: List[str],
        recommended: List[str],
    ) -> Dict[str, str]:
        """Generate justifications for capability mappings."""
        justifications = {}

        category_descriptions = {
            SEOJobCategory.SEO_AUDIT: "SEO audit requires comprehensive technical analysis",
            SEOJobCategory.KEYWORD_RESEARCH: "Keyword research is the foundation of SEO strategy",
            SEOJobCategory.TECHNICAL_SEO: "Technical SEO requires deep technical optimization",
            SEOJobCategory.LOCAL_SEO: "Local SEO focuses on geographic visibility",
            SEOJobCategory.ECOMMERCE_SEO: "Ecommerce SEO requires product-specific optimization",
            SEOJobCategory.CONTENT_OPTIMIZATION: "Content optimization improves search relevance",
            SEOJobCategory.LINK_BUILDING: "Link building builds domain authority",
            SEOJobCategory.SEO_STRATEGY: "SEO strategy requires comprehensive planning",
            SEOJobCategory.ON_PAGE_SEO: "On-page SEO optimizes page-level elements",
            SEOJobCategory.OFF_PAGE_SEO: "Off-page SEO improves external signals",
        }

        base_justification = category_descriptions.get(category, "SEO optimization work")

        for cap in required:
            justifications[cap] = f"{base_justification}. {cap} is critical for success."

        for cap in optional:
            justifications[cap] = f"{cap} provides additional value for this type of work."

        for cap in recommended:
            justifications[cap] = f"{cap} is recommended based on industry best practices."

        return justifications

    def _calculate_confidence(self, category: SEOJobCategory, work_spec: WorkSpecification) -> float:
        """Calculate confidence in the mapping."""
        # Base confidence
        confidence = 0.8

        # Increase if category is clearly defined
        if work_spec.metadata.get("classification_confidence", 0) > 0.7:
            confidence += 0.1

        # Decrease if complexity is very high (more uncertainty)
        if work_spec.complexity == "very_complex":
            confidence -= 0.1

        return min(1.0, max(0.0, confidence))


class SEOTaskMapper(JobTaskMapper):
    """
    Maps work specifications to SEO tasks.

    Uses capability mappings to determine required tasks.
    """

    def __init__(self) -> None:
        self._task_mappings = self._initialize_task_mappings()

    def _initialize_task_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize task mappings for capabilities."""
        return {
            "technical_seo_audit": {
                "tasks": ["run_technical_audit", "analyze_crawlability", "check_core_web_vitals"],
                "order": [1, 2, 3],
            },
            "site_speed_optimization": {
                "tasks": ["analyze_page_speed", "optimize_images", "minify_resources"],
                "order": [1, 2, 3],
            },
            "mobile_optimization": {
                "tasks": ["check_mobile_usability", "optimize_mobile_layout", "test_mobile_speed"],
                "order": [1, 2, 3],
            },
            "keyword_research": {
                "tasks": ["identify_target_keywords", "analyze_search_volume", "assess_competition"],
                "order": [1, 2, 3],
            },
            "on_page_optimization": {
                "tasks": ["optimize_title_tags", "optimize_meta_descriptions", "optimize_headers"],
                "order": [1, 2, 3],
            },
            "link_building": {
                "tasks": ["analyze_backlink_profile", "identify_link_opportunities", "execute_outreach"],
                "order": [1, 2, 3],
            },
            "content_optimization": {
                "tasks": ["audit_existing_content", "optimize_content_structure", "improve_content_quality"],
                "order": [1, 2, 3],
            },
            "google_business_profile": {
                "tasks": ["setup_gbp", "optimize_gbp_listing", "manage_reviews"],
                "order": [1, 2, 3],
            },
        }

    def map_tasks(self, work_spec: WorkSpecification) -> TaskMappingResult:
        """Map work specification to SEO tasks."""
        # Get required capabilities from work spec
        required_capabilities = work_spec.required_capabilities
        optional_capabilities = work_spec.optional_capabilities

        # Map capabilities to tasks
        required_tasks = []
        optional_tasks = []
        suggested_tasks = []

        for capability in required_capabilities:
            tasks = self._get_tasks_for_capability(capability)
            required_tasks.extend(tasks)

        for capability in optional_capabilities:
            tasks = self._get_tasks_for_capability(capability)
            optional_tasks.extend(tasks)

        # Add suggested tasks based on category
        category_str = work_spec.metadata.get("category", "seo_audit")
        suggested = self._get_suggested_tasks(category_str)
        suggested_tasks.extend(suggested)

        # Determine task order
        task_order = self._determine_task_order(required_tasks, optional_tasks)

        # Generate justifications
        justifications = self._generate_task_justifications(required_tasks, optional_tasks, suggested_tasks)

        # Calculate confidence
        confidence = self._calculate_task_confidence(work_spec)

        return TaskMappingResult(
            work_id=work_spec.work_id,
            required_tasks=list(set(required_tasks)),
            optional_tasks=list(set(optional_tasks)),
            suggested_tasks=list(set(suggested_tasks)),
            task_order=task_order,
            mapping_justifications=justifications,
            confidence=confidence,
        )

    def _get_tasks_for_capability(self, capability: str) -> List[str]:
        """Get tasks for a given capability."""
        mapping = self._task_mappings.get(capability)
        if mapping:
            return mapping["tasks"]
        # Generate default task if no mapping exists
        return [f"execute_{capability}"]

    def _get_suggested_tasks(self, category: str) -> List[str]:
        """Get suggested tasks based on category."""
        category_suggestions = {
            "seo_audit": ["generate_audit_report", "create_action_plan"],
            "keyword_research": ["create_keyword_strategy", "prioritize_keywords"],
            "technical_seo": ["implement_fixes", "monitor_performance"],
            "local_seo": ["build_local_citations", "optimize_local_content"],
            "ecommerce_seo": ["optimize_product_pages", "improve_site_structure"],
            "content_optimization": ["create_content_calendar", "optimize_blog_posts"],
            "link_building": ["create_link_strategy", "monitor_backlinks"],
            "seo_strategy": ["develop_roadmap", "set_kpis"],
        }
        return category_suggestions.get(category, [])

    def _determine_task_order(self, required_tasks: List[str], optional_tasks: List[str]) -> List[str]:
        """Determine execution order for tasks."""
        # Simple ordering: required first, then optional
        all_tasks = required_tasks + optional_tasks
        return list(dict.fromkeys(all_tasks))  # Remove duplicates while preserving order

    def _generate_task_justifications(
        self,
        required_tasks: List[str],
        optional_tasks: List[str],
        suggested_tasks: List[str],
    ) -> Dict[str, str]:
        """Generate justifications for task mappings."""
        justifications = {}

        for task in required_tasks:
            justifications[task] = "Required task for successful completion of work."

        for task in optional_tasks:
            justifications[task] = "Optional task that can enhance results."

        for task in suggested_tasks:
            justifications[task] = "Suggested task based on industry best practices."

        return justifications

    def _calculate_task_confidence(self, work_spec: WorkSpecification) -> float:
        """Calculate confidence in task mapping."""
        # Base confidence
        confidence = 0.7

        # Increase if capabilities are well-defined
        if work_spec.required_capabilities:
            confidence += 0.1

        # Decrease if complexity is very high
        if work_spec.complexity == "very_complex":
            confidence -= 0.1

        return min(1.0, max(0.0, confidence))


class JobMappingOrchestrator:
    """
    Orchestrates capability and task mapping for work specifications.
    """

    def __init__(self) -> None:
        self._capability_mapper = SEOCapabilityMapper()
        self._task_mapper = SEOTaskMapper()

    def map_work_specification(
        self,
        work_spec: WorkSpecification,
    ) -> tuple[CapabilityMappingResult, TaskMappingResult]:
        """
        Map work specification to capabilities and tasks.

        Returns both capability and task mapping results.
        """
        capability_result = self._capability_mapper.map_capabilities(work_spec)
        
        # Update work_spec with capabilities before mapping tasks
        work_spec_with_capabilities = WorkSpecification(
            work_id=work_spec.work_id,
            title=work_spec.title,
            description=work_spec.description,
            business_goal=work_spec.business_goal,
            business_context=work_spec.business_context,
            industry=work_spec.industry,
            target_audience=work_spec.target_audience,
            expected_outcome=work_spec.expected_outcome,
            constraints=work_spec.constraints,
            priority=work_spec.priority,
            complexity=work_spec.complexity,
            estimated_scope=work_spec.estimated_scope,
            required_capabilities=capability_result.required_capabilities,
            optional_capabilities=capability_result.optional_capabilities,
            recommended_capabilities=capability_result.recommended_capabilities,
            required_tasks=work_spec.required_tasks,
            optional_tasks=work_spec.optional_tasks,
            suggested_tasks=work_spec.suggested_tasks,
            status=work_spec.status,
            created_at=work_spec.created_at,
            updated_at=work_spec.updated_at,
            metadata=work_spec.metadata,
        )
        
        task_result = self._task_mapper.map_tasks(work_spec_with_capabilities)

        return capability_result, task_result

    def update_work_specification(
        self,
        work_spec: WorkSpecification,
        capability_result: CapabilityMappingResult,
        task_result: TaskMappingResult,
    ) -> WorkSpecification:
        """
        Update work specification with mapping results.

        Returns updated WorkSpecification with populated capabilities and tasks.
        """
        # Create updated work spec (since it's frozen, we need to create new)
        return WorkSpecification(
            work_id=work_spec.work_id,
            title=work_spec.title,
            description=work_spec.description,
            business_goal=work_spec.business_goal,
            business_context=work_spec.business_context,
            industry=work_spec.industry,
            target_audience=work_spec.target_audience,
            expected_outcome=work_spec.expected_outcome,
            constraints=work_spec.constraints,
            priority=work_spec.priority,
            complexity=work_spec.complexity,
            estimated_scope=work_spec.estimated_scope,
            required_capabilities=capability_result.required_capabilities,
            optional_capabilities=capability_result.optional_capabilities,
            recommended_capabilities=capability_result.recommended_capabilities,
            required_tasks=task_result.required_tasks,
            optional_tasks=task_result.optional_tasks,
            suggested_tasks=task_result.suggested_tasks,
            status=work_spec.status,
            created_at=work_spec.created_at,
            updated_at=datetime.utcnow(),
            metadata={
                **work_spec.metadata,
                "capability_mapping_confidence": capability_result.confidence,
                "task_mapping_confidence": task_result.confidence,
                "capability_justifications": capability_result.mapping_justifications,
                "task_justifications": task_result.mapping_justifications,
                "task_order": task_result.task_order,
            },
        )
