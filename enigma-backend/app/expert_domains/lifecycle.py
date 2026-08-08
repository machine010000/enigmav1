from __future__ import annotations

from app.expert_domains.models import DomainLifecycle, DomainLifecycleStage


class LifecycleManager:
    """Manages lifecycle transitions for expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.lifecycle = DomainLifecycle()

    def get_current_stage(self) -> DomainLifecycleStage:
        """Get the current lifecycle stage."""
        return self.lifecycle.get_current_stage()

    def can_advance_to(self, stage: DomainLifecycleStage) -> bool:
        """Check if the domain can advance to the given stage."""
        return self.lifecycle.can_advance_to(stage)

    def advance_to(self, stage: DomainLifecycleStage) -> bool:
        """Advance the domain to the given lifecycle stage."""
        return self.lifecycle.advance_to(stage)

    def get_stage_history(self) -> list:
        """Get the history of lifecycle stage transitions."""
        return self.lifecycle.get_stage_history()

    def get_transition_requirements(self, stage: DomainLifecycleStage) -> list:
        """Get requirements to advance to a given stage."""
        # Placeholder: define requirements for each stage
        requirements = {
            DomainLifecycleStage.LEARNING: [
                "knowledge_areas_defined",
                "basic_concepts_defined",
            ],
            DomainLifecycleStage.GROWING: [
                "multiple_evidence_sources",
                "practical_applications",
            ],
            DomainLifecycleStage.OPERATIONAL: [
                "high_quality_evidence",
                "proven_success_rate",
            ],
            DomainLifecycleStage.EXPERT: [
                "published_work",
                "peer_recognition",
            ],
            DomainLifecycleStage.SELF_IMPROVING: [
                "continuous_innovation",
                "industry_leadership",
            ],
        }
        return requirements.get(stage, [])

    def get_stage_description(self, stage: DomainLifecycleStage) -> str:
        """Get a description of a lifecycle stage."""
        descriptions = {
            DomainLifecycleStage.UNKNOWN: "Domain is not yet initialized",
            DomainLifecycleStage.LEARNING: "Domain is in learning phase",
            DomainLifecycleStage.GROWING: "Domain is growing capabilities",
            DomainLifecycleStage.OPERATIONAL: "Domain is operational and reliable",
            DomainLifecycleStage.EXPERT: "Domain has achieved expert status",
            DomainLifecycleStage.SELF_IMPROVING: "Domain is continuously improving",
        }
        return descriptions.get(stage, "Unknown stage")
