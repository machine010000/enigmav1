from app.academy.academy_models import AcademyModule


class ProgrammingAcademyProvider:
    def load(self) -> AcademyModule:
        return AcademyModule(
            id="programming_core",
            name="Programming Academy",
            version="1.0.0",
            description="Programming knowledge module for architecture, code quality, and deployment.",
            topics=["Software Architecture", "Development Workflow", "Testing"],
            capabilities=["technical_principles"],
            confidence=0.8,
        )

    def metadata(self) -> dict:
        return {"name": "Programming Academy", "version": "1.0.0", "topics": ["Software Architecture", "Development Workflow", "Testing"]}

    def health(self) -> str:
        return "healthy"

    def version(self) -> str:
        return "1.0.0"
