from __future__ import annotations

from app.profession.models import (
    Profession,
    ProfessionPack,
    ProfessionKnowledge,
    Skill,
    ProfessionTask,
    DecisionPattern,
    ProfessionDetector,
)


class MarketingSocialSellingDetector(ProfessionDetector):
    """Detector for Marketing & Social Selling profession."""

    KEYWORDS = [
        "marketing", "social", "selling", "audience", "content", "campaign",
        "engagement", "leads", "conversion", "brand", "social media",
        "advertising", "promotion", "growth", "reach", "followers"
    ]

    def detect(self, goal: str) -> Profession | None:
        """Detect if goal relates to marketing & social selling."""
        goal_lower = goal.lower()
        matches = sum(1 for keyword in self.KEYWORDS if keyword in goal_lower)

        if matches >= 2:
            return Profession(
                id="marketing-social-selling",
                name="Marketing & Social Selling",
                description="Professional marketing and social media selling strategies for audience growth and conversion",
                category="Marketing",
                version="1.0.0",
                status="active",
            )
        return None

    def get_confidence(self, goal: str, profession: Profession) -> float:
        """Calculate confidence score for marketing profession detection."""
        if profession.id != "marketing-social-selling":
            return 0.0

        goal_lower = goal.lower()
        matches = sum(1 for keyword in self.KEYWORDS if keyword in goal_lower)
        confidence = min(1.0, matches / len(self.KEYWORDS) * 2)
        return confidence


def create_marketing_social_selling_pack() -> ProfessionPack:
    """Create the reference Marketing & Social Selling profession pack."""

    profession = Profession(
        id="marketing-social-selling",
        name="Marketing & Social Selling",
        description="Professional marketing and social media selling strategies for audience growth and conversion",
        category="Marketing",
        version="1.0.0",
        status="active",
    )

    knowledge = ProfessionKnowledge(
        profession_id="marketing-social-selling",
        concepts=[
            "audience_segmentation",
            "content_strategy",
            "social_selling",
            "engagement_metrics",
            "conversion_funnel",
            "brand_positioning",
            "lead_generation",
            "customer_journey",
        ],
        evidence_sources=[
            "marketing_frameworks",
            "case_studies",
            "industry_benchmarks",
        ],
        maturity="initial",
        confidence=0.8,
    )

    skills = [
        Skill(
            id="audience_research",
            name="Audience Research",
            description="Identify and analyze target audience segments",
            category="Research",
        ),
        Skill(
            id="content_strategy",
            name="Content Strategy",
            description="Develop strategic content plans for engagement",
            category="Strategy",
        ),
        Skill(
            id="audience_segmentation",
            name="Audience Segmentation",
            description="Segment audiences based on behavior and demographics",
            category="Analysis",
        ),
        Skill(
            id="product_positioning",
            name="Product Positioning",
            description="Position products effectively in the market",
            category="Strategy",
        ),
        Skill(
            id="social_selling",
            name="Social Selling",
            description="Sell through social media platforms",
            category="Sales",
        ),
    ]

    tasks = [
        ProfessionTask(
            id="audience_analysis",
            name="Audience Analysis",
            description="Analyze target audience demographics and behavior",
            required_skills=["audience_research", "audience_segmentation"],
            required_knowledge=["audience_segmentation", "customer_journey"],
            expected_deliverables=["audience_report", "segmentation_map"],
            success_criteria=["audience_segments_identified", "key_demographics_mapped"],
        ),
        ProfessionTask(
            id="content_plan",
            name="Content Plan",
            description="Create strategic content calendar and plan",
            required_skills=["content_strategy", "audience_research"],
            required_knowledge=["content_strategy", "engagement_metrics"],
            expected_deliverables=["content_calendar", "content_guidelines"],
            success_criteria=["content_topics_defined", "publishing_schedule_set"],
        ),
        ProfessionTask(
            id="product_positioning",
            name="Product Positioning",
            description="Position product in the market effectively",
            required_skills=["product_positioning", "audience_research"],
            required_knowledge=["brand_positioning", "conversion_funnel"],
            expected_deliverables=["positioning_statement", "value_proposition"],
            success_criteria=["unique_value_defined", "competitive_advantage_identified"],
        ),
    ]

    decision_patterns = [
        DecisionPattern(
            id="keyword_selection_pattern",
            name="Keyword Selection Pattern",
            description="Select keywords based on competition and authority",
            condition="IF high competition AND low authority",
            action="THEN prefer lower-competition opportunities",
            rationale="Low authority sites cannot compete for high-competition keywords initially",
            category="Strategy",
        ),
        DecisionPattern(
            id="content_frequency_pattern",
            name="Content Frequency Pattern",
            description="Determine content posting frequency",
            condition="IF building new audience AND limited resources",
            action="THEN prioritize quality over quantity",
            rationale="Quality content builds trust faster than volume when starting",
            category="Strategy",
        ),
    ]

    kpis = [
        "Reach",
        "Engagement Rate",
        "Leads Generated",
        "Conversion Rate",
        "Follower Growth",
        "Content Performance",
    ]

    deliverables = [
        "Audience Report",
        "Content Calendar",
        "Campaign Strategy",
        "Performance Reports",
        "Positioning Documents",
    ]

    common_mistakes = [
        "Targeting too broad an audience",
        "Ignoring engagement metrics",
        "Inconsistent posting schedule",
        "Focusing on vanity metrics",
        "Not adapting to platform changes",
    ]

    best_practices = [
        "Define clear audience segments",
        "Create platform-specific content",
        "Monitor and respond to engagement",
        "Test and iterate strategies",
        "Align content with business goals",
    ]

    tools = [
        "Ahrefs",
        "Semrush",
        "Google Search Console",
        "Buffer",
        "Hootsuite",
        "Canva",
    ]

    return ProfessionPack(
        profession=profession,
        knowledge=knowledge,
        skills=skills,
        tasks=tasks,
        decision_patterns=decision_patterns,
        kpis=kpis,
        deliverables=deliverables,
        common_mistakes=common_mistakes,
        best_practices=best_practices,
        tools=tools,
    )
