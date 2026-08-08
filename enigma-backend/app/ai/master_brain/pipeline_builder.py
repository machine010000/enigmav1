from typing import Dict, List


class PipelineBuilder:
    def __init__(self):
        self.rules: Dict[str, List[str]] = {
            "affiliate_seller": ["source_discovery", "product_verification"],
            "own_brand": ["product_verification"],
            "service_provider": ["service_definition", "product_verification"],
            "content_creator": ["audience_definition", "content_strategy"],
            "investor": ["market_analysis", "opportunity_evaluation"],
        }

    def build(self, context) -> List[str]:
        scenario = (getattr(getattr(context, "business_context", None), "scenario", None) or getattr(getattr(context, "business_context", None), "mode", None) or "default").lower()
        if scenario in self.rules:
            return self.rules[scenario]
        if getattr(getattr(context, "product_context", None), "product", {}).get("type") == "physical":
            return ["product_verification"]
        return ["source_discovery", "product_verification"]

    def extend(self, scenario: str, pipeline: List[str]) -> None:
        self.rules[scenario.lower()] = pipeline
