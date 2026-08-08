from __future__ import annotations

from typing import Dict, List, Optional

from app.profession.models import (
    Profession,
    ProfessionDetector,
    ProfessionPack,
    ProfessionRegistry,
)
from app.profession.reference_professions import (
    MarketingSocialSellingDetector,
    create_marketing_social_selling_pack,
)


class ProfessionService:
    """Service for profession detection and knowledge loading."""

    def __init__(self) -> None:
        self.registry = ProfessionRegistry()
        self.detectors: List[ProfessionDetector] = []
        self._initialize_default_professions()

    def _initialize_default_professions(self) -> None:
        """Initialize default profession packs and detectors."""
        # Register reference profession
        marketing_pack = create_marketing_social_selling_pack()
        self.registry.register(marketing_pack)

        # Register detector
        self.detectors.append(MarketingSocialSellingDetector())

    def detect_profession(self, goal: str) -> Optional[Profession]:
        """Detect profession from goal using registered detectors."""
        for detector in self.detectors:
            profession = detector.detect(goal)
            if profession:
                return profession
        return None

    def get_profession_confidence(self, goal: str, profession: Profession) -> float:
        """Get confidence score for profession detection."""
        for detector in self.detectors:
            confidence = detector.get_confidence(goal, profession)
            if confidence > 0:
                return confidence
        return 0.0

    def get_profession_pack(self, profession_id: str) -> Optional[ProfessionPack]:
        """Get profession pack by ID."""
        return self.registry.get(profession_id)

    def get_profession_pack_by_name(self, name: str) -> Optional[ProfessionPack]:
        """Get profession pack by name."""
        return self.registry.find_by_name(name)

    def list_professions(self) -> List[Profession]:
        """List all registered professions."""
        return self.registry.list_all()

    def list_active_professions(self) -> List[Profession]:
        """List only active professions."""
        return self.registry.list_active()

    def enrich_session_with_profession(
        self, goal: str, session_dict: Dict
    ) -> Dict:
        """Enrich reasoning session with profession knowledge."""
        profession = self.detect_profession(goal)

        if profession:
            pack = self.get_profession_pack(profession.id)
            if pack:
                confidence = self.get_profession_confidence(goal, profession)
                session_dict["profession"] = {
                    "profession": pack.profession.to_dict(),
                    "knowledge": pack.knowledge.to_dict(),
                    "skills": [skill.to_dict() for skill in pack.skills],
                    "tasks": [task.to_dict() for task in pack.tasks],
                    "decision_patterns": [
                        pattern.to_dict() for pattern in pack.decision_patterns
                    ],
                    "kpis": pack.kpis,
                    "deliverables": pack.deliverables,
                    "common_mistakes": pack.common_mistakes,
                    "best_practices": pack.best_practices,
                    "tools": pack.tools,
                    "detection_confidence": confidence,
                }

        return session_dict


# Global service instance
profession_service = ProfessionService()
