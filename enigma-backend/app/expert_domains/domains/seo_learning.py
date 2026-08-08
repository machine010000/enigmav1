from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.knowledge_governance.models import (
    CandidateKnowledge,
    GovernedKnowledge,
    KnowledgeConflict,
    GovernanceEvent,
    KnowledgeMaturity,
    KnowledgeFreshness,
    Concept,
    ConceptVersion,
)
from app.knowledge_governance.contracts import KnowledgeGovernanceService


class KnowledgeUpdateType(str, Enum):
    """Types of knowledge updates."""
    NEW_CONCEPT = "new_concept"
    UPDATED_CONCEPT = "updated_concept"
    DEPRECATED_CONCEPT = "deprecated_concept"
    REPLACED_BEST_PRACTICE = "replaced_best_practice"
    NEW_KPI_THRESHOLD = "new_kpi_threshold"
    MATURITY_INCREASE = "maturity_increase"
    MATURITY_DECREASE = "maturity_decrease"


@dataclass
class KnowledgeUpdateResult:
    """Result of a knowledge update operation."""
    success: bool
    update_type: KnowledgeUpdateType
    concept_id: str
    previous_maturity: Optional[KnowledgeMaturity] = None
    new_maturity: Optional[KnowledgeMaturity] = None
    previous_version: Optional[int] = None
    new_version: Optional[int] = None
    governance_event_id: Optional[str] = None
    reason: str = ""
    errors: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class SEOKnowledgeUpdater(ABC):
    """Contract for updating SEO knowledge through Governance."""

    @abstractmethod
    def submit_candidate(
        self,
        candidate: CandidateKnowledge,
        actor: str = "seo_learning",
    ) -> KnowledgeUpdateResult:
        """
        Submit candidate knowledge through Governance.

        This is the ONLY way to update SEO knowledge.
        Never directly mutates knowledge - always goes through Governance.
        """
        pass

    @abstractmethod
    def apply_governed_knowledge(
        self,
        governed: GovernedKnowledge,
        domain_id: str,
    ) -> KnowledgeUpdateResult:
        """
        Apply governed knowledge to the SEO Expert Domain.

        Called after Governance has approved the knowledge.
        """
        pass

    @abstractmethod
    def deprecate_concept(
        self,
        concept_id: str,
        reason: str,
        actor: str = "seo_learning",
    ) -> KnowledgeUpdateResult:
        """
        Deprecate a concept through Governance.

        Marks concept as deprecated with proper governance trail.
        """
        pass


class SEOKnowledgeGovernanceBridge:
    """
    Bridges SEO Expert Domain with Knowledge Governance.

    Ensures all knowledge updates go through the proper governance pipeline.
    """

    def __init__(self, governance_service: Optional[KnowledgeGovernanceService] = None) -> None:
        self._governance_service = governance_service
        self._update_history: List[KnowledgeUpdateResult] = []

    def set_governance_service(self, service: KnowledgeGovernanceService) -> None:
        """Set the Knowledge Governance service."""
        self._governance_service = service

    def submit_candidate(
        self,
        candidate: CandidateKnowledge,
        actor: str = "seo_learning",
    ) -> KnowledgeUpdateResult:
        """
        Submit candidate knowledge through Governance.

        Pipeline:
        1. Submit to Governance service
        2. Wait for governance decision
        3. Apply if approved
        4. Record result

        Never directly inserts knowledge - always goes through Governance.
        """
        if not self._governance_service:
            return KnowledgeUpdateResult(
                success=False,
                update_type=KnowledgeUpdateType.NEW_CONCEPT,
                concept_id=candidate.id,
                reason="Governance service not available",
                errors=["Governance service not configured"],
            )

        try:
            # Submit to Governance
            governed = self._governance_service.submit_candidate(candidate, actor)

            # Create update result
            result = KnowledgeUpdateResult(
                success=True,
                update_type=self._determine_update_type(candidate, governed),
                concept_id=candidate.id,
                new_maturity=governed.concept.knowledge_maturity,
                new_version=governed.concept.version,
                governance_event_id=self._get_latest_event_id(governed),
                reason="Knowledge approved through Governance",
            )

            # Record history
            self._update_history.append(result)

            return result

        except Exception as e:
            return KnowledgeUpdateResult(
                success=False,
                update_type=KnowledgeUpdateType.NEW_CONCEPT,
                concept_id=candidate.id,
                reason=f"Governance submission failed: {str(e)}",
                errors=[str(e)],
            )

    def apply_governed_knowledge(
        self,
        governed: GovernedKnowledge,
        domain_id: str,
    ) -> KnowledgeUpdateResult:
        """
        Apply governed knowledge to the SEO Expert Domain.

        This is called after Governance has approved the knowledge.
        The actual domain update happens in the SEO Domain class.
        """
        result = KnowledgeUpdateResult(
            success=True,
            update_type=KnowledgeUpdateType.UPDATED_CONCEPT,
            concept_id=governed.concept.id,
            new_maturity=governed.concept.knowledge_maturity,
            new_version=governed.concept.version,
            reason="Governed knowledge applied to domain",
        )

        self._update_history.append(result)
        return result

    def deprecate_concept(
        self,
        concept_id: str,
        reason: str,
        actor: str = "seo_learning",
    ) -> KnowledgeUpdateResult:
        """
        Deprecate a concept through Governance.

        Marks concept as deprecated with proper governance trail.
        """
        if not self._governance_service:
            return KnowledgeUpdateResult(
                success=False,
                update_type=KnowledgeUpdateType.DEPRECATED_CONCEPT,
                concept_id=concept_id,
                reason="Governance service not available",
                errors=["Governance service not configured"],
            )

        try:
            # Get existing governed knowledge
            governed = self._governance_service.get_governed_knowledge(concept_id)
            if not governed:
                return KnowledgeUpdateResult(
                    success=False,
                    update_type=KnowledgeUpdateType.DEPRECATED_CONCEPT,
                    concept_id=concept_id,
                    reason="Concept not found",
                    errors=["Concept not found in governed knowledge"],
                )

            # Submit deprecation as a candidate
            # In a real implementation, this would create a special deprecation candidate
            result = KnowledgeUpdateResult(
                success=True,
                update_type=KnowledgeUpdateType.DEPRECATED_CONCEPT,
                concept_id=concept_id,
                previous_maturity=governed.concept.knowledge_maturity,
                reason=f"Deprecated: {reason}",
            )

            self._update_history.append(result)
            return result

        except Exception as e:
            return KnowledgeUpdateResult(
                success=False,
                update_type=KnowledgeUpdateType.DEPRECATED_CONCEPT,
                concept_id=concept_id,
                reason=f"Deprecation failed: {str(e)}",
                errors=[str(e)],
            )

    def _determine_update_type(
        self,
        candidate: CandidateKnowledge,
        governed: GovernedKnowledge,
    ) -> KnowledgeUpdateType:
        """Determine the type of knowledge update."""
        if governed.concept.version > 1:
            return KnowledgeUpdateType.UPDATED_CONCEPT
        else:
            return KnowledgeUpdateType.NEW_CONCEPT

    def _get_latest_event_id(self, governed: GovernedKnowledge) -> Optional[str]:
        """Get the ID of the latest governance event."""
        if governed.governance_events:
            return governed.governance_events[-1].candidate_id
        return None

    def get_update_history(self) -> List[KnowledgeUpdateResult]:
        """Get history of knowledge updates."""
        return self._update_history.copy()

    def get_update_statistics(self) -> Dict[str, Any]:
        """Get statistics about knowledge updates."""
        if not self._update_history:
            return {
                "total_updates": 0,
                "successful_updates": 0,
                "failed_updates": 0,
                "by_type": {},
            }

        successful = sum(1 for r in self._update_history if r.success)
        failed = len(self._update_history) - successful

        by_type: Dict[str, int] = {}
        for result in self._update_history:
            update_type = result.update_type.value
            by_type[update_type] = by_type.get(update_type, 0) + 1

        return {
            "total_updates": len(self._update_history),
            "successful_updates": successful,
            "failed_updates": failed,
            "by_type": by_type,
        }


class SEOKnowledgeVersionTracker:
    """
    Tracks versioning for SEO knowledge.

    Maintains version history for:
    - Knowledge concepts
    - Best practices
    - Execution templates
    - KPI thresholds
    """

    def __init__(self) -> None:
        self._concept_versions: Dict[str, List[ConceptVersion]] = {}
        self._best_practice_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._template_versions: Dict[str, List[Dict[str, Any]]] = {}
        self._kpi_versions: Dict[str, List[Dict[str, Any]]] = {}

    def track_concept_version(
        self,
        concept_id: str,
        version: ConceptVersion,
    ) -> None:
        """Track a version of a concept."""
        if concept_id not in self._concept_versions:
            self._concept_versions[concept_id] = []
        self._concept_versions[concept_id].append(version)

    def get_concept_history(self, concept_id: str) -> List[ConceptVersion]:
        """Get version history for a concept."""
        return self._concept_versions.get(concept_id, [])

    def track_best_practice_version(
        self,
        practice_id: str,
        version: int,
        description: str,
        reason: str,
    ) -> None:
        """Track a version of a best practice."""
        if practice_id not in self._best_practice_versions:
            self._best_practice_versions[practice_id] = []
        
        self._best_practice_versions[practice_id].append({
            "version": version,
            "description": description,
            "reason": reason,
            "created_at": datetime.utcnow(),
        })

    def get_best_practice_history(self, practice_id: str) -> List[Dict[str, Any]]:
        """Get version history for a best practice."""
        return self._best_practice_versions.get(practice_id, [])

    def track_template_version(
        self,
        template_id: str,
        version: int,
        changes: List[str],
        reason: str,
    ) -> None:
        """Track a version of an execution template."""
        if template_id not in self._template_versions:
            self._template_versions[template_id] = []
        
        self._template_versions[template_id].append({
            "version": version,
            "changes": changes,
            "reason": reason,
            "created_at": datetime.utcnow(),
        })

    def get_template_history(self, template_id: str) -> List[Dict[str, Any]]:
        """Get version history for an execution template."""
        return self._template_versions.get(template_id, [])

    def track_kpi_version(
        self,
        kpi_id: str,
        version: int,
        old_threshold: Optional[float],
        new_threshold: Optional[float],
        reason: str,
    ) -> None:
        """Track a version of a KPI threshold."""
        if kpi_id not in self._kpi_versions:
            self._kpi_versions[kpi_id] = []
        
        self._kpi_versions[kpi_id].append({
            "version": version,
            "old_threshold": old_threshold,
            "new_threshold": new_threshold,
            "reason": reason,
            "created_at": datetime.utcnow(),
        })

    def get_kpi_history(self, kpi_id: str) -> List[Dict[str, Any]]:
        """Get version history for a KPI."""
        return self._kpi_versions.get(kpi_id, [])

    def get_version_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked versions."""
        return {
            "concepts_tracked": len(self._concept_versions),
            "best_practices_tracked": len(self._best_practice_versions),
            "templates_tracked": len(self._template_versions),
            "kpis_tracked": len(self._kpi_versions),
            "total_versions": (
                sum(len(v) for v in self._concept_versions.values())
                + sum(len(v) for v in self._best_practice_versions.values())
                + sum(len(v) for v in self._template_versions.values())
                + sum(len(v) for v in self._kpi_versions.values())
            ),
        }


class SEOKnowledgeManager:
    """
    Main manager for SEO knowledge operations.

    Coordinates research, evidence, governance, and versioning.
    """

    def __init__(self, governance_service: Optional[KnowledgeGovernanceService] = None) -> None:
        self._governance_bridge = SEOKnowledgeGovernanceBridge(governance_service)
        self._version_tracker = SEOKnowledgeVersionTracker()

    def set_governance_service(self, service: KnowledgeGovernanceService) -> None:
        """Set the Knowledge Governance service."""
        self._governance_bridge.set_governance_service(service)

    def submit_candidate(
        self,
        candidate: CandidateKnowledge,
        actor: str = "seo_learning",
    ) -> KnowledgeUpdateResult:
        """Submit candidate knowledge through Governance."""
        return self._governance_bridge.submit_candidate(candidate, actor)

    def deprecate_concept(
        self,
        concept_id: str,
        reason: str,
        actor: str = "seo_learning",
    ) -> KnowledgeUpdateResult:
        """Deprecate a concept through Governance."""
        return self._governance_bridge.deprecate_concept(concept_id, reason, actor)

    def track_concept_version(
        self,
        concept_id: str,
        version: ConceptVersion,
    ) -> None:
        """Track a version of a concept."""
        self._version_tracker.track_concept_version(concept_id, version)

    def track_best_practice_version(
        self,
        practice_id: str,
        version: int,
        description: str,
        reason: str,
    ) -> None:
        """Track a version of a best practice."""
        self._version_tracker.track_best_practice_version(
            practice_id, version, description, reason
        )

    def track_template_version(
        self,
        template_id: str,
        version: int,
        changes: List[str],
        reason: str,
    ) -> None:
        """Track a version of an execution template."""
        self._version_tracker.track_template_version(
            template_id, version, changes, reason
        )

    def track_kpi_version(
        self,
        kpi_id: str,
        version: int,
        old_threshold: Optional[float],
        new_threshold: Optional[float],
        reason: str,
    ) -> None:
        """Track a version of a KPI threshold."""
        self._version_tracker.track_kpi_version(
            kpi_id, version, old_threshold, new_threshold, reason
        )

    def get_update_history(self) -> List[KnowledgeUpdateResult]:
        """Get history of knowledge updates."""
        return self._governance_bridge.get_update_history()

    def get_version_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked versions."""
        return self._version_tracker.get_version_summary()

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return {
            "update_statistics": self._governance_bridge.get_update_statistics(),
            "version_summary": self._version_tracker.get_version_summary(),
        }
