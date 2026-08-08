from app.academy.academy_models import AcademyModule


class SocialMediaAcademyProvider:
    def load(self) -> AcademyModule:
        return AcademyModule(
            id="social_media_core",
            name="Social Media Academy",
            version="1.0.0",
            description="Social media knowledge module for channels, engagement, and content strategy.",
            topics=["Social Strategy", "Community Growth", "Content Planning"],
            capabilities=["social_media_guidance"],
            confidence=0.8,
        )

    def metadata(self) -> dict:
        return {"name": "Social Media Academy", "version": "1.0.0", "topics": ["Social Strategy", "Community Growth", "Content Planning"]}

    def health(self) -> str:
        return "healthy"

    def version(self) -> str:
        return "1.0.0"
