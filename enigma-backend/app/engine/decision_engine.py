from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from app.engine.capabilities import capability_registry
from app.intelligence.reasoning_session import ReasoningSession
from app.models.decision import Decision


class ExecutionPlanner:
    def plan(self, decision: Decision) -> Dict[str, Any]:
        capability_id = decision.selected_capability or "product_verification"
        worker_name = decision.selected_worker or capability_registry.find_worker_for_capability(capability_id) or "product_verification"
        return {
            "capability_id": capability_id,
            "worker_name": worker_name,
            "steps": [{"worker": worker_name, "capability": capability_id}],
        }


class ExecutionEngineAdapter:
    async def execute(self, plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None, db=None):
        return {
            "status": "success",
            "result": {"planned": True, "worker": plan.get("worker_name")},
            "evidence": [{"field": "planned", "value": True}],
            "confidence": 0.9,
        }


class DecisionEngine:
    def __init__(self, planner=None, execution_engine=None) -> None:
        self.planner = planner or ExecutionPlanner()
        self.execution_engine = execution_engine or ExecutionEngineAdapter()

    async def create_decision(self, db, goal: str, context: Optional[Dict[str, Any] | ReasoningSession] = None, constraints: Optional[list[str]] = None) -> Dict[str, Any]:
        normalized_context = self._normalize_context(context)
        normalized_constraints = list(constraints or [])

        capability_id = normalized_context.get("capability_id") or normalized_context.get("capability") or "product_verification"
        capability = capability_registry.get_capability(capability_id)
        if capability is None:
            capability = capability_registry.get_capability("product_verification")
            if capability is not None:
                capability_id = capability.id

        worker_name = capability_registry.find_worker_for_capability(capability_id) or "product_verification"
        memory_context = normalized_context.get("memory_context") or {}
        memory_hits = len(memory_context.get("episodes", [])) if isinstance(memory_context, dict) else 0
        similar_episodes = memory_context.get("similar_episodes", []) if isinstance(memory_context, dict) else []
        selected_strategy = None
        if isinstance(memory_context, dict):
            strategy_payload = memory_context.get("selected_strategy") or {}
            selected_strategy = strategy_payload.get("name") if isinstance(strategy_payload, dict) else None
        pattern_matches = [item.get("id") for item in memory_context.get("pattern_matches", []) if isinstance(item, dict)] if isinstance(memory_context, dict) else []

        evidence_payload = normalized_context.get("evidence") or []
        evidence_ids = [item.get("id") for item in evidence_payload if isinstance(item, dict) and item.get("id")]
        if not evidence_ids:
            evidence_ids = [f"evidence-{index + 1}" for index in range(min(max(len(evidence_payload), 1), 3))]
            if not evidence_payload:
                evidence_ids = [f"evidence-{goal.lower().replace(' ', '-') or 'default'}"]

        knowledge_payload = normalized_context.get("knowledge") or {}
        concept_ids = []
        if isinstance(knowledge_payload, dict):
            concept_ids = [item for item in knowledge_payload.get("concept_ids", []) if item]
            if not concept_ids and knowledge_payload.get("concepts"):
                concept_ids = [str(item) for item in knowledge_payload.get("concepts")]
        if not concept_ids:
            concept_ids = [f"concept-{goal.lower().replace(' ', '-') or 'default'}"]

        assumptions = list(normalized_context.get("assumptions") or ["The available context is sufficient for an initial decision."])
        risks = list(normalized_context.get("risks") or ["Unknown risk profile."])
        confidence = float(normalized_context.get("confidence", 0.0) or 0.0)

        decision = Decision(
            goal=goal,
            title=goal[:255],
            description=goal,
            context=normalized_context,
            constraints=normalized_constraints,
            selected_capability=capability_id,
            selected_worker=worker_name,
            evidence=[{"source": "reasoning_session", "goal": goal, "evidence_ids": evidence_ids}],
            confidence=confidence,
            assumptions=assumptions,
            risks=risks,
            execution_strategy={"plan": "execution"},
            reasoning="Selected capability and worker through the capability registry.",
            execution_result={},
            feedback={},
            next_action="plan",
            memory_hits=memory_hits,
            similar_episodes=list(similar_episodes),
            selected_strategy=selected_strategy,
            pattern_matches=list(pattern_matches),
            decision_reason="Derived from the cognitive session and available evidence.",
            evidence_ids=evidence_ids,
            concept_ids=concept_ids,
            risk_score=max(0.1, min(1.0, 0.2 + (len(risks) * 0.1) + (0.1 if not assumptions else 0.0))),
            rejected_alternatives=list(normalized_context.get("alternatives") or []),
            expected_outcome=f"A concrete execution plan for {goal or 'the requested objective'}.",
            success_criteria=["Execution plan generated", "Evidence captured", "Confidence recorded"],
            status="planned",
            version=1,
            decision_id=str(uuid.uuid4()),
        )
        db.add(decision)
        await db.commit()
        return {"decision": decision.to_dict(), "decision_id": str(decision.decision_id)}

    def _normalize_context(self, context: Optional[Dict[str, Any] | ReasoningSession]) -> Dict[str, Any]:
        if context is None:
            return {}
        if isinstance(context, ReasoningSession):
            return context.to_dict()
        if isinstance(context, dict):
            return dict(context)
        return {"value": context}

    async def execute_decision(self, db, decision_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        decision = await self._load_decision(db, decision_id)
        if decision is None:
            raise ValueError(f"Decision {decision_id} not found")

        plan = self.planner.plan(decision)
        execution_result = await self.execution_engine.execute(plan, context=context, db=db)

        payload = self._normalize_execution_result(execution_result)
        new_version = (decision.version or 0) + 1
        history_entry = Decision(
            goal=decision.goal,
            title=decision.title,
            description=decision.description,
            context={**(decision.context or {}), **(context or {})},
            constraints=list(decision.constraints or []),
            selected_capability=decision.selected_capability,
            selected_worker=decision.selected_worker,
            evidence=list(payload.get("evidence", [])),
            confidence=float(payload.get("confidence", 0.0)),
            assumptions=list(decision.assumptions or []),
            risks=list(decision.risks or []),
            execution_strategy=dict(decision.execution_strategy or {}),
            reasoning=decision.reasoning,
            execution_result=payload.get("result", {}),
            feedback={"status": payload.get("status", "unknown")},
            next_action="review",
            decision_reason=decision.decision_reason,
            evidence_ids=list(decision.evidence_ids or []),
            concept_ids=list(decision.concept_ids or []),
            risk_score=decision.risk_score,
            rejected_alternatives=list(decision.rejected_alternatives or []),
            expected_outcome=decision.expected_outcome,
            success_criteria=list(decision.success_criteria or []),
            status="completed" if payload.get("status") == "success" else "failed",
            version=new_version,
            decision_id=decision.decision_id,
            parent_decision_id=decision.id,
        )
        db.add(history_entry)
        await db.commit()

        return {"decision": history_entry.to_dict(), "execution_result": payload}

    def _normalize_execution_result(self, execution_result: Any) -> Dict[str, Any]:
        if isinstance(execution_result, dict):
            return {
                "status": execution_result.get("status", "unknown"),
                "result": execution_result.get("result", {}),
                "evidence": execution_result.get("evidence", []),
                "confidence": execution_result.get("confidence", 0.0),
            }

        return {
            "status": getattr(getattr(execution_result, "status", None), "value", getattr(execution_result, "status", "unknown")),
            "result": getattr(execution_result, "result", {}),
            "evidence": getattr(execution_result, "evidence", []),
            "confidence": getattr(execution_result, "confidence", 0.0),
        }

    async def _load_decision(self, db, decision_id: str) -> Optional[Decision]:
        from sqlalchemy import select

        if hasattr(db, "_decisions"):
            decisions = [item for item in getattr(db, "_decisions", []) if getattr(item, "decision_id", None) == decision_id]
            if decisions:
                return max(decisions, key=lambda item: item.version or 0)

        result = await db.execute(select(Decision).where(Decision.decision_id == decision_id).order_by(Decision.version.desc()))
        if hasattr(result, "scalars"):
            scalars = result.scalars()
            if hasattr(scalars, "first"):
                return scalars.first()
        return None
