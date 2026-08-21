"""Reusable Product Verification gate for proposal and delivery workflows."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus
from app.workers.product_verification import ProductVerificationWorker


class VerificationStage(str, Enum):
    PROPOSAL_SUBMISSION = "proposal_submission"
    FINAL_DELIVERY = "final_delivery"


@dataclass(frozen=True)
class VerificationGateDecision:
    stage: VerificationStage
    recommendation: str
    allowed: bool
    confidence: float
    risks: List[str]
    missing_information: List[str]
    evidence_context: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        data = self.__dict__.copy()
        data["stage"] = self.stage.value
        return data


class ProductVerificationGate:
    def __init__(self, worker: Optional[ProductVerificationWorker] = None) -> None:
        self.worker = worker or ProductVerificationWorker()

    async def verify(self, context: ExecutionContext, stage: VerificationStage) -> VerificationGateDecision:
        return self.evaluate(await self.worker.run(context), stage)

    def evaluate(self, result: WorkerResult, stage: VerificationStage) -> VerificationGateDecision:
        data = result.result if isinstance(result.result, dict) else {}
        recommendation = str(data.get("recommendation") or "review").lower()
        confidence = max(0.0, min(1.0, float(data.get("confidence", result.confidence or 0.0))))
        # A gate never auto-allows an unsuccessful or ambiguous verification.
        allowed = result.status == WorkerStatus.SUCCESS and recommendation == "pass"
        return VerificationGateDecision(
            stage=stage, recommendation=recommendation, allowed=allowed, confidence=confidence,
            risks=list(data.get("risks") or data.get("issues") or []),
            missing_information=list(data.get("missing_information") or []),
            evidence_context=list(data.get("evidence_context") or result.evidence or []),
        )
