from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.expert_domains.models import DomainLearning


class LearningManager:
    """Manages learning behavior for expert domains."""

    def __init__(self, domain_id: str):
        self.domain_id = domain_id
        self.learning = DomainLearning(domain_id)

    def record_new_knowledge(
        self,
        concept_id: str,
        knowledge: str,
        source: str,
    ) -> None:
        """Record acquisition of new knowledge."""
        self.learning.record_new_knowledge(concept_id, knowledge, source)

    def record_evidence_update(
        self,
        evidence_id: str,
        update_type: str,
    ) -> None:
        """Record an evidence update."""
        self.learning.record_evidence_update(evidence_id, update_type)

    def record_concept_update(
        self,
        concept_id: str,
        update_type: str,
    ) -> None:
        """Record a concept update."""
        self.learning.record_concept_update(concept_id, update_type)

    def record_rule_update(
        self,
        rule_id: str,
        update_type: str,
    ) -> None:
        """Record a rule update."""
        self.learning.record_rule_update(rule_id, update_type)

    def record_reflection(
        self,
        reflection: str,
        outcome: str,
    ) -> None:
        """Record a reflection on execution."""
        self.learning.record_reflection(reflection, outcome)

    def record_maturity_update(
        self,
        concept_id: str,
        old_maturity: int,
        new_maturity: int,
    ) -> None:
        """Record a maturity level update."""
        self.learning.record_maturity_update(concept_id, old_maturity, new_maturity)

    def get_learning_history(self) -> List[Dict[str, Any]]:
        """Return the learning history."""
        return self.learning.get_learning_history()

    def get_recent_learning(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Return learning events from the last N hours."""
        return self.learning.get_recent_learning(hours)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get a summary of learning activity."""
        history = self.get_learning_history()
        recent = self.get_recent_learning(24)

        # Count by type
        type_counts: Dict[str, int] = {}
        for event in history:
            event_type = event.get("type", "unknown")
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        return {
            "domain_id": self.domain_id,
            "total_learning_events": len(history),
            "recent_learning_events": len(recent),
            "learning_by_type": type_counts,
        }

    def should_trigger_reflection(self) -> bool:
        """Determine if reflection should be triggered."""
        recent = self.get_recent_learning(24)
        # Trigger reflection if there are enough recent learning events
        return len(recent) >= 5

    def get_learning_recommendations(self) -> List[str]:
        """Get recommendations for learning improvements."""
        recommendations = []
        summary = self.get_learning_summary()

        if summary["total_learning_events"] == 0:
            recommendations.append("No learning activity recorded. Start capturing knowledge and evidence.")

        if summary["recent_learning_events"] < 5:
            recommendations.append("Low recent learning activity. Increase knowledge acquisition.")

        type_counts = summary["learning_by_type"]
        if type_counts.get("reflection", 0) == 0:
            recommendations.append("No reflections recorded. Add reflection after executions.")

        if type_counts.get("maturity_update", 0) == 0:
            recommendations.append("No maturity updates. Track concept maturity improvements.")

        return recommendations
