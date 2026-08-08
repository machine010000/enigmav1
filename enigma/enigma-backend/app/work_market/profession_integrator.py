from __future__ import annotations

from typing import Optional

from app.work_market.models import FreelanceJob, JobClassification


class ProfessionIntegrator:
    """Integrates job classification with the Profession layer."""

    def map_to_profession(self, classification: JobClassification) -> Optional[str]:
        """Map job classification to existing Profession."""
        try:
            from app.profession.service import profession_service
        except ImportError:
            return None

        # Try to find a matching profession by name
        # This is a simple mapping - in production would be more sophisticated
        profession_mapping = {
            "SEO Specialist": "Marketing",
            "Content Writer": "Marketing",
            "Social Media Manager": "Marketing",
            "Digital Marketer": "Marketing",
            "Web Developer": "Engineering",
        }

        return profession_mapping.get(classification.profession)

    def get_profession_knowledge(self, profession_name: str) -> Optional[dict]:
        """Get profession knowledge for a given profession."""
        try:
            from app.profession.service import profession_service
        except ImportError:
            return None

        # In production, this would call profession_service to get profession knowledge
        # For now, return None as we're not implementing full integration
        return None
