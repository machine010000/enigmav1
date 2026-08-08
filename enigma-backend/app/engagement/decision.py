from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.engagement.contracts import (
    DecisionContract,
    DecisionRecord,
    DecisionStatus,
    DecisionPriority,
    DecisionGate,
    DecisionRequirement,
)

from app.engagement.risk import RiskAssessment, RiskType
from app.engagement.scope import ScopeValidation, ScopeStatus


@dataclass(frozen=True)
class DecisionInput:
    """Input for decision-making."""
    work_specification_id: str
    available_knowledge: List[str] = field(default_factory=list)
    available_evidence: List[str] = field(default_factory=list)
    available_capabilities: List[str] = field(default_factory=list)
    knowledge_readiness: float = 0.0  # 0.0 to 1.0
    capability_readiness: float = 0.0  # 0.0 to 1.0
    evidence_coverage: float = 0.0  # 0.0 to 1.0
    complexity: float = 0.0  # 0.0 to 1.0
    risk_score: float = 0.0  # 0.0 to 1.0
    client_quality: float = 0.0  # 0.0 to 1.0
    portfolio_match: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """Engine for making decisions about work requests."""

    def __init__(self):
        self._decision_records: Dict[str, DecisionRecord] = {}
        self._decision_gates: Dict[str, DecisionGate] = self._create_default_gates()
        self._decision_requirements: Dict[str, DecisionRequirement] = {}

    def _create_default_gates(self) -> Dict[str, DecisionGate]:
        """Create default decision gates."""
        return {
            "execution_gate": DecisionGate(
                gate_id="execution_gate",
                name="Execution Gate",
                description="Gate that controls whether execution can proceed",
                required_status=[DecisionStatus.ACCEPT, DecisionStatus.ACCEPT_WITH_CONDITIONS],
                blocked_status=[
                    DecisionStatus.REJECT,
                    DecisionStatus.NEED_RESEARCH,
                    DecisionStatus.NEED_LEARNING,
                    DecisionStatus.NEED_NEGOTIATION,
                    DecisionStatus.NEED_CLARIFICATION,
                    DecisionStatus.NEED_PORTFOLIO,
                ],
                requires_conditions=True,
                requires_approval=False,
            ),
        }

    def make_decision(
        self,
        input_data: DecisionInput,
    ) -> DecisionRecord:
        """Make a decision about a work request."""
        decision_id = f"decision_{input_data.work_specification_id}_{datetime.utcnow().timestamp()}"

        # Analyze inputs
        missing_knowledge = self._identify_missing_knowledge(input_data)
        missing_evidence = self._identify_missing_evidence(input_data)
        missing_capabilities = self._identify_missing_capabilities(input_data)

        # Determine decision status
        decision_status = self._determine_status(
            input_data,
            missing_knowledge,
            missing_evidence,
            missing_capabilities,
        )

        # Calculate decision confidence
        decision_confidence = self._calculate_confidence(
            input_data,
            decision_status,
        )

        # Calculate estimates
        estimated_risk = input_data.risk_score
        estimated_profitability = self._estimate_profitability(input_data)
        estimated_complexity = input_data.complexity
        estimated_success_probability = self._calculate_success_probability(
            input_data,
            decision_status,
        )

        # Build reasoning
        decision_reasoning = self._build_reasoning(
            decision_status,
            missing_knowledge,
            missing_evidence,
            missing_capabilities,
        )

        # Create decision record
        record = DecisionRecord(
            decision_id=decision_id,
            work_specification_id=input_data.work_specification_id,
            timestamp=datetime.utcnow(),
            decision_status=decision_status,
            decision_confidence=decision_confidence,
            decision_reasoning=decision_reasoning,
            missing_knowledge=missing_knowledge,
            missing_evidence=missing_evidence,
            missing_capabilities=missing_capabilities,
            required_research=[],
            estimated_risk=estimated_risk,
            estimated_profitability=estimated_profitability,
            estimated_complexity=estimated_complexity,
            estimated_success_probability=estimated_success_probability,
        )

        self._decision_records[decision_id] = record
        return record

    def _identify_missing_knowledge(self, input_data: DecisionInput) -> List[str]:
        """Identify missing knowledge."""
        # Placeholder: identify knowledge gaps
        if input_data.knowledge_readiness < 0.5:
            return ["Knowledge readiness below threshold"]
        return []

    def _identify_missing_evidence(self, input_data: DecisionInput) -> List[str]:
        """Identify missing evidence."""
        # Placeholder: identify evidence gaps
        if input_data.evidence_coverage < 0.5:
            return ["Evidence coverage below threshold"]
        return []

    def _identify_missing_capabilities(self, input_data: DecisionInput) -> List[str]:
        """Identify missing capabilities."""
        # Placeholder: identify capability gaps
        if input_data.capability_readiness < 0.5:
            return ["Capability readiness below threshold"]
        return []

    def _determine_status(
        self,
        input_data: DecisionInput,
        missing_knowledge: List[str],
        missing_evidence: List[str],
        missing_capabilities: List[str],
    ) -> DecisionStatus:
        """Determine the decision status."""
        # If critical missing elements, reject
        if missing_knowledge or missing_evidence or missing_capabilities:
            if input_data.knowledge_readiness < 0.3:
                return DecisionStatus.NEED_LEARNING
            if input_data.evidence_coverage < 0.3:
                return DecisionStatus.NEED_RESEARCH
            if input_data.capability_readiness < 0.3:
                return DecisionStatus.NEED_PORTFOLIO
            return DecisionStatus.REJECT

        # If risk is high, negotiate
        if input_data.risk_score > 0.7:
            return DecisionStatus.NEED_NEGOTIATION

        # If complexity is high, might need clarification
        if input_data.complexity > 0.8:
            return DecisionStatus.NEED_CLARIFICATION

        # Otherwise accept
        if input_data.client_quality < 0.5:
            return DecisionStatus.ACCEPT_WITH_CONDITIONS
        return DecisionStatus.ACCEPT

    def _calculate_confidence(
        self,
        input_data: DecisionInput,
        decision_status: DecisionStatus,
    ) -> float:
        """Calculate decision confidence."""
        # Placeholder: calculate confidence based on inputs
        base_confidence = 0.5

        if decision_status == DecisionStatus.ACCEPT:
            base_confidence = 0.8
        elif decision_status == DecisionStatus.ACCEPT_WITH_CONDITIONS:
            base_confidence = 0.6
        elif decision_status == DecisionStatus.REJECT:
            base_confidence = 0.9

        # Adjust based on knowledge/evidence/capability readiness
        avg_readiness = (
            input_data.knowledge_readiness
            + input_data.evidence_coverage
            + input_data.capability_readiness
        ) / 3.0

        return (base_confidence + avg_readiness) / 2.0

    def _estimate_profitability(self, input_data: DecisionInput) -> float:
        """Estimate profitability."""
        # Placeholder: estimate based on client quality and portfolio match
        return (input_data.client_quality + input_data.portfolio_match) / 2.0

    def _calculate_success_probability(
        self,
        input_data: DecisionInput,
        decision_status: DecisionStatus,
    ) -> float:
        """Calculate success probability."""
        # Placeholder: calculate based on inputs
        base_probability = 0.5

        if decision_status == DecisionStatus.ACCEPT:
            base_probability = 0.7
        elif decision_status == DecisionStatus.ACCEPT_WITH_CONDITIONS:
            base_probability = 0.6
        elif decision_status == DecisionStatus.REJECT:
            base_probability = 0.2

        # Adjust based on risk
        risk_adjustment = 1.0 - input_data.risk_score
        return max(0.0, min(1.0, base_probability * risk_adjustment))

    def _build_reasoning(
        self,
        decision_status: DecisionStatus,
        missing_knowledge: List[str],
        missing_evidence: List[str],
        missing_capabilities: List[str],
    ) -> List[str]:
        """Build decision reasoning."""
        reasoning = [f"Decision status: {decision_status.value}"]

        if missing_knowledge:
            reasoning.append(f"Missing knowledge: {', '.join(missing_knowledge)}")
        if missing_evidence:
            reasoning.append(f"Missing evidence: {', '.join(missing_evidence)}")
        if missing_capabilities:
            reasoning.append(f"Missing capabilities: {', '.join(missing_capabilities)}")

        return reasoning

    def can_proceed(self, decision_id: str) -> bool:
        """Check if execution can proceed based on a decision."""
        record = self._decision_records.get(decision_id)
        if not record:
            return False

        # Check against execution gate
        gate = self._decision_gates.get("execution_gate")
        if gate:
            if record.decision_status in gate.blocked_status:
                return False
            if record.decision_status not in gate.required_status:
                return False

        return True

    def get_blocking_issues(self, decision_id: str) -> List[str]:
        """Get blocking issues for a decision."""
        record = self._decision_records.get(decision_id)
        if not record:
            return []

        issues = []
        if record.decision_status == DecisionStatus.REJECT:
            issues.append("Decision status is REJECT")
        if record.decision_status == DecisionStatus.NEED_RESEARCH:
            issues.append("Research required before execution")
        if record.decision_status == DecisionStatus.NEED_LEARNING:
            issues.append("Learning required before execution")
        if record.decision_status == DecisionStatus.NEED_NEGOTIATION:
            issues.append("Negotiation required before execution")
        if record.decision_status == DecisionStatus.NEED_CLARIFICATION:
            issues.append("Clarification required before execution")
        if record.decision_status == DecisionStatus.NEED_PORTFOLIO:
            issues.append("Portfolio evidence required before execution")

        return issues

    def get_required_actions(self, decision_id: str) -> List[str]:
        """Get required actions for a decision."""
        record = self._decision_records.get(decision_id)
        if not record:
            return []

        actions = []
        if record.decision_status == DecisionStatus.NEED_RESEARCH:
            actions.extend(record.required_research)
        if record.missing_knowledge:
            actions.append("Acquire missing knowledge")
        if record.missing_evidence:
            actions.append("Gather missing evidence")
        if record.missing_capabilities:
            actions.append("Develop missing capabilities")
        if record.decision_status == DecisionStatus.ACCEPT_WITH_CONDITIONS:
            actions.extend(record.acceptance_conditions)

        return actions

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        """Get a decision record by ID."""
        return self._decision_records.get(decision_id)

    def get_decision_for_work(self, work_specification_id: str) -> Optional[DecisionRecord]:
        """Get the latest decision for a work specification."""
        # In a real implementation, we'd get the latest by timestamp
        for record in self._decision_records.values():
            if record.work_specification_id == work_specification_id:
                return record
        return None
