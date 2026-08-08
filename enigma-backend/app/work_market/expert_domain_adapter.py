from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.expert_domains import (
    ExpertDomainContract,
    DomainIdentity,
    KnowledgeArea,
    DomainConcept,
    ReasoningPattern,
    DecisionRule,
    DomainKPI,
    ExecutionStandard,
    EvaluationResult,
    ReadinessScore,
    DomainLifecycleStage,
    CapabilityContract,
    TaskContract,
    ExecutionTemplate,
    SEODomain,
    expert_domain_registry,
)
from app.expert_domains.capabilities import CapabilityPurpose
from app.expert_domains.tasks import TaskCategory
from app.expert_domains.work.work_specification import WorkSpecification


class ExpertDomainAdapter:
    """
    Adapter that bridges Freelancing layer with Expert Domain framework.
    
    This adapter uses the real Expert Domain framework and provides
    a simplified interface for the freelancing runtime.
    """

    def __init__(self, domain_id: Optional[str] = None) -> None:
        self._domain_id = domain_id or "seo"
        self._domain = expert_domain_registry.get(self._domain_id)
        
        if not self._domain:
            # Fallback to creating SEO domain if not registered
            self._domain = SEODomain()
            expert_domain_registry.register(self._domain)

    def get_domain_capabilities(self, profession: str = "default") -> List[str]:
        """
        Get capabilities for the domain.
        
        Returns list of capability names that the domain can perform.
        """
        if not self._domain:
            return []
        
        capabilities = self._domain.get_capabilities()
        return [cap.name for cap in capabilities]

    def get_domain_readiness(self, profession: str = "default") -> ReadinessScore:
        """
        Get readiness score for the domain.
        
        Returns readiness across knowledge, execution, evidence, and learning.
        """
        if not self._domain:
            return ReadinessScore(
                domain_id=self._domain_id,
                knowledge_readiness=0.0,
                execution_readiness=0.0,
                evidence_readiness=0.0,
                learning_readiness=0.0,
                overall_readiness=0.0,
            )
        
        return self._domain.get_readiness()

    def get_capability_details(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific capability."""
        if not self._domain:
            return None
        
        capabilities = self._domain.get_capabilities()
        for cap in capabilities:
            if cap.capability_id == capability_id:
                return {
                    "capability_id": cap.capability_id,
                    "name": cap.name,
                    "description": cap.description,
                    "purpose": cap.purpose.value,
                    "required_knowledge_areas": cap.required_knowledge_areas,
                    "required_concepts": cap.required_concepts,
                    "supported_tasks": cap.supported_tasks,
                }
        return None

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific task."""
        if not self._domain:
            return None
        
        tasks = self._domain.get_tasks()
        for task in tasks:
            if task.task_id == task_id:
                return {
                    "task_id": task.task_id,
                    "name": task.name,
                    "description": task.description,
                    "goal": task.goal,
                    "category": task.category.value,
                    "required_capabilities": task.required_capabilities,
                    "inputs": task.inputs,
                    "outputs": task.outputs,
                    "deliverables": task.deliverables,
                    "estimated_duration": task.estimated_duration,
                    "priority": task.priority,
                }
        return None

    def consume_work_specification(self, work_spec: WorkSpecification) -> Dict[str, Any]:
        """
        Consume a WorkSpecification and map it to domain capabilities and tasks.
        
        This method integrates with the Expert Domain's WorkSpecification consumption
        to map client work requests to domain capabilities and tasks.
        """
        if not self._domain:
            return {
                "work_id": work_spec.work_id,
                "domain_id": self._domain_id,
                "capability_mappings": [],
                "task_mappings": [],
                "template_mappings": [],
                "readiness": 0.0,
                "can_execute": False,
                "error": "Domain not available",
            }
        
        return self._domain.consume_work_specification(work_spec)

    def get_reasoning_patterns(self) -> List[Dict[str, Any]]:
        """Get reasoning patterns for the domain."""
        if not self._domain:
            return []
        
        patterns = self._domain.get_reasoning_patterns()
        return [
            {
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type.value,
                "name": p.name,
                "description": p.description,
                "required_inputs": p.required_inputs,
                "expected_outputs": p.expected_outputs,
            }
            for p in patterns
        ]

    def get_decision_rules(self) -> List[Dict[str, Any]]:
        """Get decision rules for the domain."""
        if not self._domain:
            return []
        
        rules = self._domain.get_decision_rules()
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "preconditions": r.preconditions,
                "success_criteria": r.success_criteria,
            }
            for r in rules
        ]

    def get_execution_templates(self) -> List[Dict[str, Any]]:
        """Get execution templates for the domain."""
        if not self._domain:
            return []
        
        templates = self._domain.get_execution_templates()
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "supported_tasks": t.supported_tasks,
                "estimated_duration": t.estimated_duration,
            }
            for t in templates
        ]

    def get_kpis(self) -> List[Dict[str, Any]]:
        """Get KPIs for the domain."""
        if not self._domain:
            return []
        
        kpis = self._domain.get_kpis()
        return [
            {
                "kpi_id": k.kpi_id,
                "metric": k.metric,
                "target": k.target,
                "threshold": k.threshold,
                "importance": k.importance,
                "unit": k.unit,
            }
            for k in kpis
        ]


class MockExpertDomainAdapter(ExpertDomainAdapter):
    """
    Mock implementation of ExpertDomainAdapter for testing.
    
    This provides static capability and readiness data for development when the real
    Expert Domain framework is not fully configured.
    """

    def __init__(self) -> None:
        # Don't call parent init to avoid real domain lookup
        self._domain_id = "seo"
        self._domain = None

    def get_domain_capabilities(self, profession: str = "default") -> List[str]:
        """Return mock capabilities."""
        return [
            "Technical SEO Audit",
            "Keyword Research",
            "On-Page Optimization",
            "Link Building",
            "SEO Analytics",
            "Content Optimization",
            "Local SEO",
            "Competitor Analysis",
        ]

    def get_domain_readiness(self, profession: str = "default") -> ReadinessScore:
        """Return mock readiness score."""
        return ReadinessScore(
            domain_id=self._domain_id,
            knowledge_readiness=0.85,
            execution_readiness=0.80,
            evidence_readiness=0.75,
            learning_readiness=0.90,
            overall_readiness=0.82,
        )
