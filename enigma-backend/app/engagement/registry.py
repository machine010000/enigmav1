from __future__ import annotations

from typing import Dict, List, Optional

from app.engagement.contracts import (
    DecisionRecord,
    DecisionStatus,
    DecisionPriority,
    DecisionGate,
    DecisionRequirement,
)

from app.engagement.risk import (
    RiskFactor,
    RiskAssessment,
    RiskThreshold,
    RiskType,
)

from app.engagement.scope import (
    ScopeIssue,
    ScopeValidation,
    ScopeRequirement,
)

from app.engagement.pricing import (
    PricingModel,
    PricingProposal,
    PricingComponent,
    PricingAdjustment,
)

from app.engagement.negotiation import (
    NegotiationItem,
    NegotiationRecord,
    NegotiationTemplate,
)

from app.engagement.decision import DecisionEngine, DecisionInput


class EngagementRegistry:
    """Registry for engagement components."""

    def __init__(self) -> None:
        self._decision_records: Dict[str, DecisionRecord] = {}
        self._risk_assessments: Dict[str, RiskAssessment] = {}
        self._scope_validations: Dict[str, ScopeValidation] = {}
        self._pricing_models: Dict[str, PricingModel] = {}
        self._pricing_proposals: Dict[str, PricingProposal] = {}
        self._negotiation_records: Dict[str, NegotiationRecord] = {}
        self._negotiation_templates: Dict[str, NegotiationTemplate] = {}
        self._decision_engine = DecisionEngine()

    def __init__(self) -> None:
        self._decision_records: Dict[str, DecisionRecord] = {}
        self._risk_assessments: Dict[str, RiskAssessment] = {}
        self._scope_validations: Dict[str, ScopeValidation] = {}
        self._pricing_models: Dict[str, PricingModel] = {}
        self._pricing_proposals: Dict[str, PricingProposal] = {}
        self._negotiation_records: Dict[str, NegotiationRecord] = {}
        self._negotiation_templates: Dict[str, NegotiationTemplate] = {}
        self._decision_engine = DecisionEngine()

    # Decision Records
    def register_decision_record(self, record: DecisionRecord) -> bool:
        """Register a decision record."""
        if record.decision_id in self._decision_records:
            return False
        self._decision_records[record.decision_id] = record
        return True

    def get_decision_record(self, decision_id: str) -> Optional[DecisionRecord]:
        """Get a decision record by ID."""
        return self._decision_records.get(decision_id)

    def get_decision_for_work(self, work_specification_id: str) -> Optional[DecisionRecord]:
        """Get the latest decision for a work specification."""
        return self._decision_engine.get_decision_for_work(work_specification_id)

    # Risk Assessments
    def register_risk_assessment(self, assessment: RiskAssessment) -> bool:
        """Register a risk assessment."""
        if assessment.assessment_id in self._risk_assessments:
            return False
        self._risk_assessments[assessment.assessment_id] = assessment
        return True

    def get_risk_assessment(self, assessment_id: str) -> Optional[RiskAssessment]:
        """Get a risk assessment by ID."""
        return self._risk_assessments.get(assessment_id)

    def get_risk_assessment_for_work(self, work_specification_id: str) -> Optional[RiskAssessment]:
        """Get risk assessment for a work specification."""
        for assessment in self._risk_assessments.values():
            if assessment.work_specification_id == work_specification_id:
                return assessment
        return None

    # Scope Validations
    def register_scope_validation(self, validation: ScopeValidation) -> bool:
        """Register a scope validation."""
        if validation.validation_id in self._scope_validations:
            return False
        self._scope_validations[validation.validation_id] = validation
        return True

    def get_scope_validation(self, validation_id: str) -> Optional[ScopeValidation]:
        """Get a scope validation by ID."""
        return self._scope_validations.get(validation_id)

    def get_scope_validation_for_work(self, work_specification_id: str) -> Optional[ScopeValidation]:
        """Get scope validation for a work specification."""
        for validation in self._scope_validations.values():
            if validation.work_specification_id == work_specification_id:
                return validation
        return None

    # Pricing
    def register_pricing_model(self, model: PricingModel) -> bool:
        """Register a pricing model."""
        if model.model_id in self._pricing_models:
            return False
        self._pricing_models[model.model_id] = model
        return True

    def get_pricing_model(self, model_id: str) -> Optional[PricingModel]:
        """Get a pricing model by ID."""
        return self._pricing_models.get(model_id)

    def register_pricing_proposal(self, proposal: PricingProposal) -> bool:
        """Register a pricing proposal."""
        if proposal.proposal_id in self._pricing_proposals:
            return False
        self._pricing_proposals[proposal.proposal_id] = proposal
        return True

    def get_pricing_proposal(self, proposal_id: str) -> Optional[PricingProposal]:
        """Get a pricing proposal by ID."""
        return self._pricing_proposals.get(proposal_id)

    # Negotiation
    def register_negotiation_record(self, record: NegotiationRecord) -> bool:
        """Register a negotiation record."""
        if record.record_id in self._negotiation_records:
            return False
        self._negotiation_records[record.record_id] = record
        return True

    def get_negotiation_record(self, record_id: str) -> Optional[NegotiationRecord]:
        """Get a negotiation record by ID."""
        return self._negotiation_records.get(record_id)

    def get_negotiation_for_work(self, work_specification_id: str) -> Optional[NegotiationRecord]:
        """Get negotiation for a work specification."""
        for record in self._negotiation_records.values():
            if record.work_specification_id == work_specification_id and record.status == "active":
                return record
        return None

    def register_negotiation_template(self, template: NegotiationTemplate) -> bool:
        """Register a negotiation template."""
        if template.template_id in self._negotiation_templates:
            return False
        self._negotiation_templates[template.template_id] = template
        return True

    def get_negotiation_template(self, template_id: str) -> Optional[NegotiationTemplate]:
        """Get a negotiation template by ID."""
        return self._negotiation_templates.get(template_id)

    # Decision Engine Access
    def make_decision(self, input_data: DecisionInput) -> DecisionRecord:
        """Make a decision using the decision engine."""
        return self._decision_engine.make_decision(input_data)

    def can_proceed(self, decision_id: str) -> bool:
        """Check if execution can proceed based on a decision."""
        return self._decision_engine.can_proceed(decision_id)

    def get_blocking_issues(self, decision_id: str) -> List[str]:
        """Get blocking issues for a decision."""
        return self._decision_engine.get_blocking_issues(decision_id)

    def get_required_actions(self, decision_id: str) -> List[str]:
        """Get required actions for a decision."""
        return self._decision_engine.get_required_actions(decision_id)


# Global engagement registry instance
engagement_registry = EngagementRegistry()
