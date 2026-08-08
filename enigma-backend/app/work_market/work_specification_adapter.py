from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

from app.work_market.models import FreelanceJob
from app.work_market.contracts import WorkSpecificationProvider


class WorkSpecificationAdapter(WorkSpecificationProvider):
    """
    Adapter that bridges Freelancing layer with Work Specification framework.
    
    This adapter implements the WorkSpecificationProvider contract using
    the existing Work Specification framework without modifying it.
    """

    def __init__(self, work_spec_service: Optional[Any] = None) -> None:
        self._work_spec_service = work_spec_service
        self._specifications: Dict[str, Dict[str, Any]] = {}

    def transform_job_to_specification(self, job: FreelanceJob) -> Dict[str, Any]:
        """
        Transform a marketplace job into a work specification.
        
        Returns:
        - work_specification_id
        - requirements
        - deliverables
        - acceptance_criteria
        - success_metrics
        - constraints
        """
        if self._work_spec_service:
            try:
                # Try to use real work specification service
                spec = self._work_spec_service.create_from_job(job)
                return spec
            except Exception:
                pass
        
        # Generate work specification from job
        spec_id = str(uuid4())
        
        # Extract requirements from job description and skills
        requirements = self._extract_requirements(job)
        
        # Generate deliverables based on requirements
        deliverables = self._generate_deliverables(job, requirements)
        
        # Define acceptance criteria
        acceptance_criteria = self._define_acceptance_criteria(job, deliverables)
        
        # Define success metrics
        success_metrics = self._define_success_metrics(job)
        
        # Define constraints
        constraints = self._define_constraints(job)
        
        specification = {
            "work_specification_id": spec_id,
            "job_id": job.job_id,
            "source": job.source.value,
            "title": job.title,
            "requirements": requirements,
            "deliverables": deliverables,
            "acceptance_criteria": acceptance_criteria,
            "success_metrics": success_metrics,
            "constraints": constraints,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self._specifications[spec_id] = specification
        return specification

    def _extract_requirements(self, job: FreelanceJob) -> List[Dict[str, Any]]:
        """Extract requirements from job description and skills."""
        requirements = []
        
        # Add skill-based requirements
        for skill in job.skills:
            requirements.append({
                "id": f"req-{skill.lower().replace(' ', '-')}",
                "type": "skill",
                "description": f"Proficiency in {skill}",
                "priority": "high" if skill in job.skills[:3] else "medium",
            })
        
        # Add description-based requirements
        if "audit" in job.description.lower():
            requirements.append({
                "id": "req-audit",
                "type": "task",
                "description": "Conduct comprehensive audit",
                "priority": "high",
            })
        
        if "analysis" in job.description.lower():
            requirements.append({
                "id": "req-analysis",
                "type": "task",
                "description": "Perform detailed analysis",
                "priority": "high",
            })
        
        if "report" in job.description.lower():
            requirements.append({
                "id": "req-report",
                "type": "deliverable",
                "description": "Provide detailed report",
                "priority": "high",
            })
        
        return requirements

    def _generate_deliverables(
        self,
        job: FreelanceJob,
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate deliverables based on requirements."""
        deliverables = []
        
        # Generate deliverables from requirements
        for req in requirements:
            if req["type"] in ["task", "deliverable"]:
                deliverable_id = f"del-{req['id']}"
                deliverables.append({
                    "id": deliverable_id,
                    "name": req["description"].title(),
                    "type": "document" if "report" in req["description"].lower() else "service",
                    "description": req["description"],
                    "estimated_effort": "medium",
                    "priority": req["priority"],
                })
        
        # Add standard deliverables
        deliverables.append({
            "id": "del-summary",
            "name": "Executive Summary",
            "type": "document",
            "description": "Summary of work performed",
            "estimated_effort": "low",
            "priority": "medium",
        })
        
        return deliverables

    def _define_acceptance_criteria(
        self,
        job: FreelanceJob,
        deliverables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Define acceptance criteria for deliverables."""
        criteria = []
        
        for deliverable in deliverables:
            criteria.append({
                "id": f"ac-{deliverable['id']}",
                "deliverable_id": deliverable["id"],
                "criterion": f"{deliverable['name']} meets quality standards",
                "measurement": "Client review and approval",
                "priority": deliverable["priority"],
            })
        
        return criteria

    def _define_success_metrics(self, job: FreelanceJob) -> List[Dict[str, Any]]:
        """Define success metrics for the job."""
        metrics = []
        
        metrics.append({
            "id": "sm-timeliness",
            "name": "Timeliness",
            "description": "Work completed within agreed timeline",
            "target": "100%",
            "measurement": "On-time delivery",
        })
        
        metrics.append({
            "id": "sm-quality",
            "name": "Quality",
            "description": "Deliverables meet client requirements",
            "target": "95%",
            "measurement": "Client satisfaction rating",
        })
        
        if job.budget:
            metrics.append({
                "id": "sm-budget",
                "name": "Budget Adherence",
                "description": "Work completed within budget",
                "target": "100%",
                "measurement": "Budget variance",
            })
        
        return metrics

    def _define_constraints(self, job: FreelanceJob) -> List[Dict[str, Any]]:
        """Define constraints for the job."""
        constraints = []
        
        if job.deadline:
            constraints.append({
                "id": "con-deadline",
                "type": "time",
                "description": f"Complete by {job.deadline}",
                "priority": "high",
            })
        
        if job.budget:
            constraints.append({
                "id": "con-budget",
                "type": "financial",
                "description": f"Budget limit: {job.budget} {job.currency}",
                "priority": "high",
            })
        
        constraints.append({
            "id": "con-scope",
            "type": "scope",
            "description": "Work within defined scope",
            "priority": "medium",
        })
        
        return constraints

    def get_specification(self, spec_id: str) -> Optional[Dict[str, Any]]:
        """Get a work specification by ID."""
        return self._specifications.get(spec_id)


class MockWorkSpecificationProvider(WorkSpecificationProvider):
    """
    Mock implementation of WorkSpecificationProvider for testing.
    
    This provides static work specification logic for development when the real
    Work Specification framework is not fully configured.
    """

    def __init__(self) -> None:
        self._specifications: Dict[str, Dict[str, Any]] = {}

    def transform_job_to_specification(self, job: FreelanceJob) -> Dict[str, Any]:
        """Return a mock work specification."""
        from uuid import uuid4
        from datetime import datetime
        
        spec_id = str(uuid4())
        
        specification = {
            "work_specification_id": spec_id,
            "job_id": job.job_id,
            "source": job.source.value,
            "title": job.title,
            "requirements": [
                {
                    "id": "req-1",
                    "type": "skill",
                    "description": f"Proficiency in {job.skills[0] if job.skills else 'required skill'}",
                    "priority": "high",
                },
            ],
            "deliverables": [
                {
                    "id": "del-1",
                    "name": "Work Output",
                    "type": "service",
                    "description": "Complete the required work",
                    "estimated_effort": "medium",
                    "priority": "high",
                },
            ],
            "acceptance_criteria": [
                {
                    "id": "ac-1",
                    "deliverable_id": "del-1",
                    "criterion": "Deliverable meets client requirements",
                    "measurement": "Client approval",
                    "priority": "high",
                },
            ],
            "success_metrics": [
                {
                    "id": "sm-1",
                    "name": "Quality",
                    "description": "High quality deliverables",
                    "target": "95%",
                    "measurement": "Client rating",
                },
            ],
            "constraints": [
                {
                    "id": "con-1",
                    "type": "time",
                    "description": "Complete within agreed timeline",
                    "priority": "high",
                },
            ],
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self._specifications[spec_id] = specification
        return specification

    def get_specification(self, spec_id: str) -> Optional[Dict[str, Any]]:
        """Get a work specification by ID."""
        return self._specifications.get(spec_id)
