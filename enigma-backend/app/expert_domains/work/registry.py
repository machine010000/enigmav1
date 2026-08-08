from __future__ import annotations

from typing import Dict, List, Optional

from app.expert_domains.work.work_specification import (
    WorkSpecification,
    WorkCapabilityMapping,
    WorkTaskMapping,
)
from app.expert_domains.work.requirements import (
    ClientRequirements,
    Requirement,
    BudgetConstraint,
    TimelineConstraint,
    PlatformConstraint,
    ComplianceRequirement,
)
from app.expert_domains.work.deliverables import (
    Deliverable,
    DeliverableInstance,
    DeliverableRequirement,
)
from app.expert_domains.work.acceptance import (
    AcceptanceCriterion,
    AcceptanceCriteriaSet,
    AcceptanceResult,
    AcceptanceChecklist,
)
from app.expert_domains.work.review import (
    Review,
    ReviewChecklist,
    ReviewValidationRule,
    ReviewApproval,
    ReviewPolicy,
)


class WorkRegistry:
    """Registry for work specifications and related components."""

    def __init__(self) -> None:
        self._work_specifications: Dict[str, WorkSpecification] = {}
        self._capability_mappings: Dict[str, WorkCapabilityMapping] = {}
        self._task_mappings: Dict[str, WorkTaskMapping] = {}
        self._client_requirements: Dict[str, ClientRequirements] = {}
        self._deliverables: Dict[str, Deliverable] = {}
        self._deliverable_instances: Dict[str, DeliverableInstance] = {}
        self._acceptance_criteria_sets: Dict[str, AcceptanceCriteriaSet] = {}
        self._acceptance_results: Dict[str, AcceptanceResult] = {}
        self._acceptance_checklists: Dict[str, AcceptanceChecklist] = {}
        self._reviews: Dict[str, Review] = {}
        self._review_checklists: Dict[str, ReviewChecklist] = {}
        self._review_policies: Dict[str, ReviewPolicy] = {}

    # Work Specifications
    def register_work_specification(self, spec: WorkSpecification) -> bool:
        """Register a work specification."""
        if spec.work_id in self._work_specifications:
            return False
        self._work_specifications[spec.work_id] = spec
        return True

    def get_work_specification(self, work_id: str) -> Optional[WorkSpecification]:
        """Get a work specification by ID."""
        return self._work_specifications.get(work_id)

    def list_work_specifications(self) -> List[WorkSpecification]:
        """List all work specifications."""
        return list(self._work_specifications.values())

    # Capability Mappings
    def register_capability_mapping(self, mapping: WorkCapabilityMapping) -> bool:
        """Register a capability mapping."""
        if mapping.mapping_id in self._capability_mappings:
            return False
        self._capability_mappings[mapping.mapping_id] = mapping
        return True

    def get_capability_mappings_for_work(self, work_id: str) -> List[WorkCapabilityMapping]:
        """Get capability mappings for a work specification."""
        return [
            m for m in self._capability_mappings.values()
            if m.work_id == work_id
        ]

    # Task Mappings
    def register_task_mapping(self, mapping: WorkTaskMapping) -> bool:
        """Register a task mapping."""
        if mapping.mapping_id in self._task_mappings:
            return False
        self._task_mappings[mapping.mapping_id] = mapping
        return True

    def get_task_mappings_for_work(self, work_id: str) -> List[WorkTaskMapping]:
        """Get task mappings for a work specification."""
        return [
            m for m in self._task_mappings.values()
            if m.work_id == work_id
        ]

    # Client Requirements
    def register_client_requirements(self, requirements: ClientRequirements) -> bool:
        """Register client requirements."""
        if requirements.requirements_id in self._client_requirements:
            return False
        self._client_requirements[requirements.requirements_id] = requirements
        return True

    def get_client_requirements(self, requirements_id: str) -> Optional[ClientRequirements]:
        """Get client requirements by ID."""
        return self._client_requirements.get(requirements_id)

    def get_requirements_for_work(self, work_id: str) -> Optional[ClientRequirements]:
        """Get requirements for a work specification."""
        for req in self._client_requirements.values():
            if req.work_id == work_id:
                return req
        return None

    # Deliverables
    def register_deliverable(self, deliverable: Deliverable) -> bool:
        """Register a deliverable."""
        if deliverable.deliverable_id in self._deliverables:
            return False
        self._deliverables[deliverable.deliverable_id] = deliverable
        return True

    def get_deliverable(self, deliverable_id: str) -> Optional[Deliverable]:
        """Get a deliverable by ID."""
        return self._deliverables.get(deliverable_id)

    def list_deliverables(self) -> List[Deliverable]:
        """List all deliverables."""
        return list(self._deliverables.values())

    # Deliverable Instances
    def register_deliverable_instance(self, instance: DeliverableInstance) -> bool:
        """Register a deliverable instance."""
        if instance.instance_id in self._deliverable_instances:
            return False
        self._deliverable_instances[instance.instance_id] = instance
        return True

    def get_deliverable_instance(self, instance_id: str) -> Optional[DeliverableInstance]:
        """Get a deliverable instance by ID."""
        return self._deliverable_instances.get(instance_id)

    def get_instances_for_work(self, work_id: str) -> List[DeliverableInstance]:
        """Get deliverable instances for a work specification."""
        return [
            i for i in self._deliverable_instances.values()
            if i.work_id == work_id
        ]

    # Acceptance Criteria
    def register_acceptance_criteria_set(self, criteria_set: AcceptanceCriteriaSet) -> bool:
        """Register an acceptance criteria set."""
        if criteria_set.criteria_set_id in self._acceptance_criteria_sets:
            return False
        self._acceptance_criteria_sets[criteria_set.criteria_set_id] = criteria_set
        return True

    def get_acceptance_criteria_set(self, criteria_set_id: str) -> Optional[AcceptanceCriteriaSet]:
        """Get an acceptance criteria set by ID."""
        return self._acceptance_criteria_sets.get(criteria_set_id)

    def register_acceptance_result(self, result: AcceptanceResult) -> bool:
        """Register an acceptance result."""
        if result.result_id in self._acceptance_results:
            return False
        self._acceptance_results[result.result_id] = result
        return True

    def get_acceptance_result(self, result_id: str) -> Optional[AcceptanceResult]:
        """Get an acceptance result by ID."""
        return self._acceptance_results.get(result_id)

    # Reviews
    def register_review(self, review: Review) -> bool:
        """Register a review."""
        if review.review_id in self._reviews:
            return False
        self._reviews[review.review_id] = review
        return True

    def get_review(self, review_id: str) -> Optional[Review]:
        """Get a review by ID."""
        return self._reviews.get(review_id)

    def get_reviews_for_target(self, target_type: str, target_id: str) -> List[Review]:
        """Get reviews for a target."""
        return [
            r for r in self._reviews.values()
            if r.target_type == target_type and r.target_id == target_id
        ]

    def register_review_checklist(self, checklist: ReviewChecklist) -> bool:
        """Register a review checklist."""
        if checklist.checklist_id in self._review_checklists:
            return False
        self._review_checklists[checklist.checklist_id] = checklist
        return True

    def get_review_checklist(self, checklist_id: str) -> Optional[ReviewChecklist]:
        """Get a review checklist by ID."""
        return self._review_checklists.get(checklist_id)

    def register_review_policy(self, policy: ReviewPolicy) -> bool:
        """Register a review policy."""
        if policy.policy_id in self._review_policies:
            return False
        self._review_policies[policy.policy_id] = policy
        return True

    def get_review_policy(self, policy_id: str) -> Optional[ReviewPolicy]:
        """Get a review policy by ID."""
        return self._review_policies.get(policy_id)

    # Validation
    def validate_work_requirements(self, work_id: str) -> Dict[str, bool]:
        """Validate that a work specification has required components."""
        validation = {
            "valid": True,
            "has_specification": False,
            "has_requirements": False,
            "has_capability_mappings": False,
            "has_task_mappings": False,
            "has_deliverables": False,
        }

        if work_id in self._work_specifications:
            validation["has_specification"] = True
        else:
            validation["valid"] = False

        if self.get_requirements_for_work(work_id):
            validation["has_requirements"] = True
        else:
            validation["valid"] = False

        if self.get_capability_mappings_for_work(work_id):
            validation["has_capability_mappings"] = True
        else:
            validation["valid"] = False

        if self.get_task_mappings_for_work(work_id):
            validation["has_task_mappings"] = True
        else:
            validation["valid"] = False

        # Check if work has associated deliverables
        if self.get_instances_for_work(work_id):
            validation["has_deliverables"] = True
        else:
            validation["valid"] = False

        return validation


# Global work registry instance
work_registry = WorkRegistry()
