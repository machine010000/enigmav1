from app.academy.academy_models import AcademyModule


class BusinessAcademyProvider:
    def load(self) -> AcademyModule:
        return AcademyModule(
            id="business_core",
            name="Business Academy",
            version="1.0.0",
            description="Business knowledge foundation for operations, strategy, and growth.",
            topics=["Strategy", "Business Model", "Operations"],
            capabilities=["business_frameworks"],
            confidence=0.8,
        )

    def metadata(self) -> dict:
        return {"name": "Business Academy", "version": "1.0.0", "topics": ["Strategy", "Business Model", "Operations"]}

    def health(self) -> str:
        return "healthy"

    def version(self) -> str:
        return "1.0.0"
