from app.academy.academy_models import AcademyModule


class PsychologyAcademyProvider:
    def load(self) -> AcademyModule:
        return AcademyModule(
            id="psychology_core",
            name="Psychology Academy",
            version="1.0.0",
            description="Psychology knowledge layer for decision-making, motivation, and behavior.",
            topics=["Cognitive Bias", "Motivation", "Persuasion"],
            capabilities=["behavioral_insights"],
            confidence=0.8,
        )

    def metadata(self) -> dict:
        return {"name": "Psychology Academy", "version": "1.0.0", "topics": ["Cognitive Bias", "Motivation", "Persuasion"]}

    def health(self) -> str:
        return "healthy"

    def version(self) -> str:
        return "1.0.0"
