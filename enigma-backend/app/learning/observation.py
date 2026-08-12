"""
Execution Observation Contract

Represents what ENIGMA learned from an execution.
This is the learning loop's observation contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class ObservationStatus(str, Enum):
    """Status of the observation."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass
class ExecutionObservation:
    """
    Internal observation representing what ENIGMA learned from an execution.
    
    This is NOT the full WorkerResult - it's a focused learning observation.
    """
    execution_id: str
    user_id: str
    capability: str
    worker: str
    target_id: Optional[str] = None  # product_id, etc.
    status: ObservationStatus = ObservationStatus.SUCCESS
    
    # Learning-relevant data
    result_summary: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    issues: List[str] = field(default_factory=list)
    
    # Metadata
    error_category: Optional[str] = None  # For failures: controlled error category
    execution_time: float = 0.0
    llm_calls: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "capability": self.capability,
            "worker": self.worker,
            "target_id": self.target_id,
            "status": self.status.value,
            "result_summary": self.result_summary,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "issues": self.issues,
            "error_category": self.error_category,
            "execution_time": self.execution_time,
            "llm_calls": self.llm_calls,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_worker_result(
        cls,
        execution_id: str,
        user_id: str,
        capability: str,
        worker: str,
        worker_result: Dict[str, Any],
        target_id: Optional[str] = None,
    ) -> "ExecutionObservation":
        """
        Create an observation from a WorkerResult.
        
        Args:
            execution_id: Execution ID
            user_id: User ID
            capability: Capability ID
            worker: Worker name
            worker_result: WorkerResult.to_dict() output
            target_id: Optional target (product_id, etc.)
            
        Returns:
            ExecutionObservation
        """
        status = ObservationStatus.SUCCESS
        if worker_result.get("status") == "failed":
            status = ObservationStatus.FAILURE
        elif worker_result.get("status") == "partial":
            status = ObservationStatus.PARTIAL
        
        return cls(
            execution_id=execution_id,
            user_id=user_id,
            capability=capability,
            worker=worker,
            target_id=target_id,
            status=status,
            result_summary=worker_result.get("result", {}),
            evidence=worker_result.get("evidence", []),
            confidence=worker_result.get("confidence", 0.0),
            issues=worker_result.get("result", {}).get("issues", []),
            execution_time=worker_result.get("execution_time", 0.0),
            llm_calls=worker_result.get("llm_calls", 0),
        )
