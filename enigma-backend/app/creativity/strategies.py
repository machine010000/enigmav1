"""
Strategy Definitions

Initial strategy types for the creativity engine.
These are domain-agnostic strategies that can be applied
across different expert domains.
"""

from typing import Set, Optional
from dataclasses import dataclass

from app.creativity.contracts import (
    CreativeStrategy,
    StrategyCategory,
    StrategyStatus,
    ConstraintType,
)
from app.marketplace.economics import EconomicsValue, VerificationStatus
from app.marketplace.contracts import MarketplacePlatform


class StrategyLibrary:
    """
    Library of predefined creative strategies.
    
    Contains domain-agnostic strategies that address common
    constraints across different expert domains.
    """
    
    @staticmethod
    def get_all_strategies() -> List[CreativeStrategy]:
        """
        Get all available strategies.
        
        Returns:
            List of all defined strategies
        """
        return [
            StrategyLibrary.price_adjustment_strategy(),
            StrategyLibrary.scope_reduction_strategy(),
            StrategyLibrary.proof_of_work_strategy(),
            StrategyLibrary.positioning_change_strategy(),
            StrategyLibrary.target_selection_strategy(),
            StrategyLibrary.proposal_strategy(),
            StrategyLibrary.research_first_strategy(),
            StrategyLibrary.learning_first_strategy(),
            StrategyLibrary.evidence_building_strategy(),
            StrategyLibrary.risk_reduction_strategy(),
            StrategyLibrary.deliverable_redesign_strategy(),
            StrategyLibrary.clarification_first_strategy(),
        ]
    
    @staticmethod
    def price_adjustment_strategy() -> CreativeStrategy:
        """
        PRICE_ADJUSTMENT strategy.
        
        Used when: low trust, no reviews, high competition
        """
        return CreativeStrategy(
            strategy_id="price_adjustment_v1",
            name="Strategic Price Adjustment",
            description="Offer a strategically lower introductory price to improve competitiveness, subject to platform rules and economic viability",
            category=StrategyCategory.PRICE_ADJUSTMENT,
            target_constraints={
                ConstraintType.NO_REVIEWS,
                ConstraintType.HIGH_COMPETITION,
                ConstraintType.WEAK_POSITIONING,
            },
            required_capabilities={"pricing_analysis", "market_research"},
            optional_capabilities={"negotiation"},
            economic_effect=EconomicsValue(
                value=-0.2,  # Reduces revenue
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            risk_effect=EconomicsValue(
                value=0.1,  # Slightly increases risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            confidence_effect=EconomicsValue(
                value=0.1,  # Slightly increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            expected_benefit=0.4,
            implementation_complexity=0.3,
            reversibility=0.7,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting"},
            requires_research=True,
            requires_learning=False,
            requires_clarification=True,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def scope_reduction_strategy() -> CreativeStrategy:
        """
        SCOPE_REDUCTION strategy.
        
        Used when: high risk, execution gap, unclear scope
        """
        return CreativeStrategy(
            strategy_id="scope_reduction_v1",
            name="Scope Reduction",
            description="Reduce project scope to match execution capabilities and reduce risk",
            category=StrategyCategory.SCOPE_REDUCTION,
            target_constraints={
                ConstraintType.EXECUTION_GAP,
                ConstraintType.UNCLEAR_SCOPE,
                ConstraintType.HIGH_APPLICATION_COST,
            },
            required_capabilities={"scope_analysis", "requirements_breakdown"},
            optional_capabilities={"negotiation"},
            economic_effect=EconomicsValue(
                value=-0.3,  # Reduces revenue
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            risk_effect=EconomicsValue(
                value=-0.4,  # Significantly reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            confidence_effect=EconomicsValue(
                value=0.3,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            expected_benefit=0.5,
            implementation_complexity=0.5,
            reversibility=0.4,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.MOSTAQL,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_clarification=True,
            requires_learning=False,
            requires_research=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def proof_of_work_strategy() -> CreativeStrategy:
        """
        PROOF_OF_WORK strategy.
        
        Used when: no portfolio, no reviews, low evidence
        """
        return CreativeStrategy(
            strategy_id="proof_of_work_v1",
            name="Proof of Work Sample",
            description="Create a small relevant demonstration/sample that does not misrepresent previous client work",
            category=StrategyCategory.PROOF_OF_WORK,
            target_constraints={
                ConstraintType.NO_PORTFOLIO,
                ConstraintType.NO_REVIEWS,
                ConstraintType.LOW_EVIDENCE,
            },
            required_capabilities={"sample_creation", "domain_expertise"},
            optional_capabilities=set(),
            economic_effect=EconomicsValue(
                value=-0.1,  # Small time cost
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            risk_effect=EconomicsValue(
                value=0.0,  # Neutral risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            confidence_effect=EconomicsValue(
                value=0.4,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            expected_benefit=0.6,
            implementation_complexity=0.6,
            reversibility=0.9,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.FIVERR,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=False,
            requires_learning=False,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def positioning_change_strategy() -> CreativeStrategy:
        """
        POSITIONING_CHANGE strategy.
        
        Used when: weak positioning, high competition
        """
        return CreativeStrategy(
            strategy_id="positioning_change_v1",
            name="Strategic Positioning Adjustment",
            description="Adjust positioning to emphasize unique strengths and differentiate from competition",
            category=StrategyCategory.POSITIONING_CHANGE,
            target_constraints={
                ConstraintType.WEAK_POSITIONING,
                ConstraintType.HIGH_COMPETITION,
            },
            required_capabilities={"positioning_analysis", "value_proposition"},
            optional_capabilities={"market_research"},
            economic_effect=EconomicsValue(
                value=0.0,  # Neutral economic effect
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.5,
            ),
            risk_effect=EconomicsValue(
                value=0.0,  # Neutral risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            confidence_effect=EconomicsValue(
                value=0.2,  # Slightly increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            expected_benefit=0.3,
            implementation_complexity=0.4,
            reversibility=0.8,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.FIVERR,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting"},
            requires_research=True,
            requires_learning=False,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def target_selection_strategy() -> CreativeStrategy:
        """
        TARGET_SELECTION strategy.
        
        Used when: high competition, low profile strength
        """
        return CreativeStrategy(
            strategy_id="target_selection_v1",
            name="Strategic Target Selection",
            description="Prefer opportunities with stronger capability match and lower evidence requirements",
            category=StrategyCategory.TARGET_SELECTION,
            target_constraints={
                ConstraintType.HIGH_COMPETITION,
                ConstraintType.NO_PORTFOLIO,
                ConstraintType.NO_REVIEWS,
            },
            required_capabilities={"opportunity_screening", "capability_matching"},
            optional_capabilities={"market_analysis"},
            economic_effect=EconomicsValue(
                value=0.1,  # Improves economic efficiency
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            risk_effect=EconomicsValue(
                value=-0.2,  # Reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            confidence_effect=EconomicsValue(
                value=0.3,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            expected_benefit=0.5,
            implementation_complexity=0.2,
            reversibility=0.9,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.FIVERR,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=True,
            requires_learning=False,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def proposal_strategy() -> CreativeStrategy:
        """
        PROPOSAL_STRATEGY strategy.
        
        Used when: weak positioning, low confidence
        """
        return CreativeStrategy(
            strategy_id="proposal_strategy_v1",
            name="Enhanced Proposal Strategy",
            description="Improve proposal structure and content to better communicate value and capability",
            category=StrategyCategory.PROPOSAL_STRATEGY,
            target_constraints={
                ConstraintType.WEAK_POSITIONING,
                ConstraintType.LOW_CONFIDENCE,
            },
            required_capabilities={"proposal_writing", "value_communication"},
            optional_capabilities={"storytelling"},
            economic_effect=EconomicsValue(
                value=0.0,  # Neutral economic effect
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.5,
            ),
            risk_effect=EconomicsValue(
                value=0.0,  # Neutral risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            confidence_effect=EconomicsValue(
                value=0.2,  # Slightly increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            expected_benefit=0.3,
            implementation_complexity=0.5,
            reversibility=0.9,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting"},
            requires_research=False,
            requires_learning=False,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def research_first_strategy() -> CreativeStrategy:
        """
        RESEARCH_FIRST strategy.
        
        Used when: stale knowledge, low confidence, knowledge gap
        """
        return CreativeStrategy(
            strategy_id="research_first_v1",
            name="Research-First Approach",
            description="Trigger targeted research before making a final decision to ensure knowledge currency",
            category=StrategyCategory.RESEARCH_FIRST,
            target_constraints={
                ConstraintType.STALE_KNOWLEDGE,
                ConstraintType.KNOWLEDGE_GAP,
                ConstraintType.LOW_CONFIDENCE,
            },
            required_capabilities={"research", "information_synthesis"},
            optional_capabilities={"domain_expertise"},
            economic_effect=EconomicsValue(
                value=-0.1,  # Time cost for research
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            risk_effect=EconomicsValue(
                value=-0.3,  # Reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            confidence_effect=EconomicsValue(
                value=0.5,  # Significantly increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            expected_benefit=0.6,
            implementation_complexity=0.4,
            reversibility=0.9,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.FIVERR,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=True,
            requires_learning=False,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def learning_first_strategy() -> CreativeStrategy:
        """
        LEARNING_FIRST strategy.
        
        Used when: knowledge gap, execution gap
        """
        return CreativeStrategy(
            strategy_id="learning_first_v1",
            name="Learning-First Approach",
            description="Acquire necessary knowledge or skills before pursuing the opportunity",
            category=StrategyCategory.LEARNING_FIRST,
            target_constraints={
                ConstraintType.KNOWLEDGE_GAP,
                ConstraintType.EXECUTION_GAP,
            },
            required_capabilities={"learning", "skill_acquisition"},
            optional_capabilities=set(),
            economic_effect=EconomicsValue(
                value=-0.3,  # Time cost for learning
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            risk_effect=EconomicsValue(
                value=-0.4,  # Reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            confidence_effect=EconomicsValue(
                value=0.6,  # Significantly increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            expected_benefit=0.7,
            implementation_complexity=0.7,
            reversibility=0.6,
            platform_compatibility=set(),  # Platform-agnostic
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=True,
            requires_learning=True,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def evidence_building_strategy() -> CreativeStrategy:
        """
        EVIDENCE_BUILDING strategy.
        
        Used when: low evidence, no portfolio
        """
        return CreativeStrategy(
            strategy_id="evidence_building_v1",
            name="Evidence Building",
            description="Build evidence through smaller projects or personal work before pursuing larger opportunities",
            category=StrategyCategory.EVIDENCE_BUILDING,
            target_constraints={
                ConstraintType.LOW_EVIDENCE,
                ConstraintType.NO_PORTFOLIO,
                ConstraintType.NO_REVIEWS,
            },
            required_capabilities={"project_execution", "evidence_collection"},
            optional_capabilities={"portfolio_building"},
            economic_effect=EconomicsValue(
                value=-0.2,  # Opportunity cost
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            risk_effect=EconomicsValue(
                value=-0.1,  # Slightly reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            confidence_effect=EconomicsValue(
                value=0.4,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            expected_benefit=0.5,
            implementation_complexity=0.6,
            reversibility=0.5,
            platform_compatibility=set(),  # Platform-agnostic
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=False,
            requires_learning=False,
            requires_clarification=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def risk_reduction_strategy() -> CreativeStrategy:
        """
        RISK_REDUCTION strategy.
        
        Used when: high risk, execution gap
        """
        return CreativeStrategy(
            strategy_id="risk_reduction_v1",
            name="Risk Reduction",
            description="Implement risk mitigation strategies such as phased delivery, clear milestones, or contingency planning",
            category=StrategyCategory.RISK_REDUCTION,
            target_constraints={
                ConstraintType.EXECUTION_GAP,
                ConstraintType.UNCLEAR_SCOPE,
            },
            required_capabilities={"risk_management", "project_planning"},
            optional_capabilities={"contingency_planning"},
            economic_effect=EconomicsValue(
                value=-0.1,  # Planning overhead
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            risk_effect=EconomicsValue(
                value=-0.5,  # Significantly reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.8,
            ),
            confidence_effect=EconomicsValue(
                value=0.3,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            expected_benefit=0.5,
            implementation_complexity=0.5,
            reversibility=0.7,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.MOSTAQL,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=False,
            requires_learning=False,
            requires_clarification=True,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def deliverable_redesign_strategy() -> CreativeStrategy:
        """
        DELIVERABLE_REDESIGN strategy.
        
        Used when: execution gap, unclear scope
        """
        return CreativeStrategy(
            strategy_id="deliverable_redesign_v1",
            name="Deliverable Redesign",
            description="Redesign deliverables to better match capabilities and reduce execution complexity",
            category=StrategyCategory.DELIVERABLE_REDESIGN,
            target_constraints={
                ConstraintType.EXECUTION_GAP,
                ConstraintType.UNCLEAR_SCOPE,
            },
            required_capabilities={"deliverable_design", "requirements_analysis"},
            optional_capabilities={"ux_design"},
            economic_effect=EconomicsValue(
                value=-0.2,  # May reduce revenue
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.6,
            ),
            risk_effect=EconomicsValue(
                value=-0.3,  # Reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            confidence_effect=EconomicsValue(
                value=0.4,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            expected_benefit=0.5,
            implementation_complexity=0.6,
            reversibility=0.4,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.MOSTAQL,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting"},
            requires_clarification=True,
            requires_learning=False,
            requires_research=False,
            status=StrategyStatus.ACTIVE,
        )
    
    @staticmethod
    def clarification_first_strategy() -> CreativeStrategy:
        """
        CLARIFICATION_FIRST strategy.
        
        Used when: unclear scope, low confidence
        """
        return CreativeStrategy(
            strategy_id="clarification_first_v1",
            name="Clarification-First Approach",
            description="Request clarification from client before committing to the opportunity",
            category=StrategyCategory.CLARIFICATION_FIRST,
            target_constraints={
                ConstraintType.UNCLEAR_SCOPE,
                ConstraintType.LOW_CONFIDENCE,
            },
            required_capabilities={"communication", "requirements_gathering"},
            optional_capabilities={"negotiation"},
            economic_effect=EconomicsValue(
                value=0.0,  # Neutral economic effect
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.5,
            ),
            risk_effect=EconomicsValue(
                value=-0.2,  # Reduces risk
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            confidence_effect=EconomicsValue(
                value=0.3,  # Increases confidence
                status=VerificationStatus.UNKNOWN,
                source="strategy_library",
                confidence=0.7,
            ),
            expected_benefit=0.4,
            implementation_complexity=0.2,
            reversibility=0.9,
            platform_compatibility={
                MarketplacePlatform.UPWORK,
                MarketplacePlatform.FREELANCER,
                MarketplacePlatform.FIVERR,
                MarketplacePlatform.MOSTAQL,
                MarketplacePlatform.KHAMSAT,
            },
            domain_compatibility={"seo", "ads", "branding", "copywriting", "analytics"},
            requires_research=False,
            requires_learning=False,
            requires_clarification=True,
            status=StrategyStatus.ACTIVE,
        )
