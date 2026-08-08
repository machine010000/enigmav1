from __future__ import annotations

from typing import Any, Dict, Optional, List
from enum import Enum

from app.work_market.contracts import DecisionProvider
from app.expert_domains import expert_domain_registry, ReadinessScore


class DecisionType(str, Enum):
    """Types of decisions for freelancing."""
    ACCEPT = "accept"
    REJECT = "reject"
    NEED_LEARNING = "need_learning"
    NEED_RESEARCH = "need_research"
    NEED_NEGOTIATION = "need_negotiation"
    NEED_CLARIFICATION = "need_clarification"


class DecisionAdapter(DecisionProvider):
    """
    Adapter that bridges Freelancing layer with Decision Engine.
    
    This adapter implements the DecisionProvider contract using
    the existing Decision Engine framework without modifying it.
    Integrates with Expert Domain framework for domain-aware decisions.
    """

    def __init__(self, decision_engine: Optional[Any] = None) -> None:
        self._decision_engine = decision_engine

    def request_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request a decision from the decision engine.
        
        Returns decision record with:
        - decision: ACCEPT, REJECT, NEED_LEARNING, etc.
        - confidence: Decision confidence score
        - reasoning: Decision reasoning
        - blockers: Any blockers
        - requirements: Any requirements
        - selected_domain: Expert domain selected for the work
        """
        if not self._decision_engine:
            # Return a mock decision for development
            return self._mock_decision(context)
        
        try:
            # Try to get decision from real decision engine
            decision = self._decision_engine.decide(context)
            return {
                "decision": decision.get("decision", "accept"),
                "confidence": decision.get("confidence", 0.5),
                "reasoning": decision.get("reasoning", ""),
                "blockers": decision.get("blockers", []),
                "requirements": decision.get("requirements", []),
                "selected_domain": decision.get("selected_domain"),
            }
        except Exception:
            # Fallback to mock decision
            return self._mock_decision(context)

    def _mock_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a mock decision for development/testing.
        
        Enhanced to consider Expert Domain readiness and selection.
        """
        job_id = context.get("job_id", "unknown")
        readiness = context.get("readiness", 0.5)
        blockers = context.get("blockers", [])
        task = context.get("task", "")
        
        # Select appropriate expert domain based on task
        selected_domain = self._select_expert_domain(context)
        
        # Get domain readiness if available
        domain_readiness = 0.0
        if selected_domain:
            domain = expert_domain_registry.get(selected_domain)
            if domain:
                domain_readiness = domain.get_readiness().overall_readiness
        
        # Enhanced decision logic considering domain readiness
        combined_readiness = (readiness + domain_readiness) / 2 if domain_readiness > 0 else readiness
        
        if combined_readiness >= 0.8 and not blockers:
            return {
                "decision": DecisionType.ACCEPT.value,
                "confidence": 0.85,
                "reasoning": f"High readiness ({combined_readiness:.2f}) with no blockers. Selected domain: {selected_domain}",
                "blockers": [],
                "requirements": [],
                "selected_domain": selected_domain,
            }
        elif blockers:
            return {
                "decision": DecisionType.NEED_LEARNING.value,
                "confidence": 0.7,
                "reasoning": f"Blockers present: {', '.join(blockers[:3])}. Domain: {selected_domain}",
                "blockers": blockers,
                "requirements": ["Resolve blockers before proceeding"],
                "selected_domain": selected_domain,
            }
        elif combined_readiness >= 0.6:
            return {
                "decision": DecisionType.NEED_RESEARCH.value,
                "confidence": 0.6,
                "reasoning": f"Moderate readiness ({combined_readiness:.2f}) - requires research. Domain: {selected_domain}",
                "blockers": [],
                "requirements": ["Conduct research to improve readiness"],
                "selected_domain": selected_domain,
            }
        else:
            return {
                "decision": DecisionType.REJECT.value,
                "confidence": 0.75,
                "reasoning": f"Low readiness ({combined_readiness:.2f}). Domain: {selected_domain}",
                "blockers": blockers,
                "requirements": [],
                "selected_domain": selected_domain,
            }

    def _select_expert_domain(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Select the most appropriate expert domain for the work.
        
        Uses business intelligence from registered expert domains.
        """
        task = context.get("task", "").lower()
        profession = context.get("profession", "").lower()
        skills = context.get("skills", [])
        
        # Get all registered domains
        domains = expert_domain_registry.list_all()
        if not domains:
            return "seo"  # Default to SEO
        
        # Score each domain based on context
        domain_scores = {}
        for domain in domains:
            identity = domain.get_identity()
            capabilities = domain.get_capabilities()
            
            score = 0.0
            
            # Check if domain name matches profession/task
            if identity.name.lower() in profession or identity.domain_id in profession:
                score += 0.5
            
            # Check if capabilities match task/skills
            for cap in capabilities:
                cap_name = cap.name.lower()
                if any(skill.lower() in cap_name for skill in skills):
                    score += 0.2
                if task in cap_name:
                    score += 0.3
            
            # Consider domain readiness
            readiness = domain.get_readiness()
            score += readiness.overall_readiness * 0.2
            
            domain_scores[identity.domain_id] = score
        
        # Select highest scoring domain
        if domain_scores:
            selected = max(domain_scores, key=domain_scores.get)
            return selected if domain_scores[selected] > 0.3 else "seo"
        
        return "seo"

    def can_proceed(self, decision_record: Dict[str, Any]) -> bool:
        """Check if a decision allows proceeding."""
        decision = decision_record.get("decision", "")
        return decision == DecisionType.ACCEPT.value

    def get_available_domains(self) -> List[Dict[str, Any]]:
        """
        Get list of available expert domains for decision making.
        
        Returns domain information including readiness.
        """
        domains = expert_domain_registry.list_all()
        domain_info = []
        
        for domain in domains:
            identity = domain.get_identity()
            readiness = domain.get_readiness()
            lifecycle = domain.get_lifecycle_stage()
            
            domain_info.append({
                "domain_id": identity.domain_id,
                "name": identity.name,
                "description": identity.description,
                "version": identity.version,
                "readiness": readiness.overall_readiness,
                "lifecycle_stage": lifecycle.value,
                "capabilities_count": len(domain.get_capabilities()),
                "tasks_count": len(domain.get_tasks()),
            })
        
        return domain_info


class MockDecisionProvider(DecisionProvider):
    """
    Mock implementation of DecisionProvider for testing.
    
    This provides static decision logic for development when the real
    Decision Engine is not fully configured.
    """

    def request_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a mock decision."""
        readiness = context.get("readiness", 0.5)
        blockers = context.get("blockers", [])
        
        if readiness >= 0.8 and not blockers:
            return {
                "decision": DecisionType.ACCEPT.value,
                "confidence": 0.85,
                "reasoning": "High readiness with no blockers",
                "blockers": [],
                "requirements": [],
            }
        elif blockers:
            return {
                "decision": DecisionType.NEED_LEARNING.value,
                "confidence": 0.7,
                "reasoning": f"Blockers present: {', '.join(blockers[:3])}",
                "blockers": blockers,
                "requirements": ["Resolve blockers"],
            }
        else:
            return {
                "decision": DecisionType.REJECT.value,
                "confidence": 0.6,
                "reasoning": "Low readiness",
                "blockers": blockers,
                "requirements": [],
            }

    def can_proceed(self, decision_record: Dict[str, Any]) -> bool:
        """Check if a decision allows proceeding."""
        return decision_record.get("decision") == DecisionType.ACCEPT.value
