from app.academy.academy_models import AcademyModule


class SalesAcademyProvider:
    def load(self) -> AcademyModule:
        return AcademyModule(
            id="sales_core",
            name="Sales Academy",
            version="1.0.0",
            description="Sales knowledge module for outreach, negotiation, and conversion.",
            topics=["Sales Process", "Negotiation", "Conversion"],
            capabilities=["sales_frameworks"],
            confidence=0.8,
        )

    def metadata(self) -> dict:
        return {"name": "Sales Academy", "version": "1.0.0", "topics": ["Sales Process", "Negotiation", "Conversion"]}

    def health(self) -> str:
        return "healthy"

    def version(self) -> str:
        return "1.0.0"
