"""
Autonomous Run Contracts

Defines the run-level orchestration contracts for controlled multi-step autonomy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from app.ai.master_brain.models import BrainDecision, BrainAction


class RunStatus(str, Enum):
    """Status of an autonomous run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Status of an autonomous step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class StopReason(str, Enum):
    """Reason for stopping an autonomous run."""
    FINISHED = "finished"
    STEP_LIMIT_REACHED = "step_limit_reached"
    DUPLICATE_ACTION = "duplicate_action"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    AUTHENTICATION_FAILURE = "authentication_failure"
    OWNERSHIP_FAILURE = "ownership_failure"
    CAPABILITY_NOT_AVAILABLE = "capability_not_available"
    CONFIGURATION_ERROR = "configuration_error"
    USER_CANCELLED = "user_cancelled"


@dataclass
class AutonomousStep:
    """
    Represents a single step in an autonomous run.
    
    This is an in-memory contract for orchestration.
    Step details are persisted via WorkerExecution (existing table).
    """
    step_number: int
    decision: BrainDecision
    capability: Optional[str] = None
    worker: Optional[str] = None
    execution_id: Optional[str] = None
    observation_id: Optional[str] = None  # Reference to ExecutionObservation
    status: StepStatus = StepStatus.PENDING
    outcome: Optional[Dict[str, Any]] = None
    next_decision: Optional[BrainDecision] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "step_number": self.step_number,
            "decision": self.decision.to_dict() if self.decision else None,
            "capability": self.capability,
            "worker": self.worker,
            "execution_id": self.execution_id,
            "status": self.status.value,
            "outcome": self.outcome,
            "next_decision": self.next_decision.to_dict() if self.next_decision else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


@dataclass
class AutonomousRun:
    """
    Represents a bounded autonomous run.
    
    This is an in-memory contract for orchestration.
    Run metadata can be persisted via WorkerExecution or a new table if needed.
    For now, we use in-memory orchestration with WorkerExecution for step persistence.
    """
    run_id: str
    user_id: str
    target_id: Optional[str] = None  # product_id, etc.
    module: str = "seller"  # seller, content_creator, service_provider
    original_goal: str = ""
    status: RunStatus = RunStatus.PENDING
    current_step: int = 0
    max_steps: int = 3  # Default max steps
    steps: List[AutonomousStep] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stop_reason: Optional[StopReason] = None
    final_response: Optional[str] = None
    final_decision: Optional[BrainDecision] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "target_id": self.target_id,
            "module": self.module,
            "original_goal": self.original_goal,
            "status": self.status.value,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "steps": [step.to_dict() for step in self.steps],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "stop_reason": self.stop_reason.value if self.stop_reason else None,
            "final_response": self.final_response,
            "final_decision": self.final_decision.to_dict() if self.final_decision else None,
        }
    
    def add_step(self, step: AutonomousStep) -> None:
        """Add a step to the run."""
        self.steps.append(step)
        self.current_step = len(self.steps)
    
    def can_execute_next_step(self) -> bool:
        """Check if another step can be executed."""
        return (
            self.status == RunStatus.RUNNING
            and self.current_step < self.max_steps
            and self.stop_reason is None
        )
    
    def stop(self, reason: StopReason, final_response: Optional[str] = None) -> None:
        """Stop the run with a reason."""
        self.status = RunStatus.STOPPED if reason != StopReason.FINISHED else RunStatus.COMPLETED
        self.stop_reason = reason
        self.completed_at = datetime.utcnow()
        self.final_response = final_response


@dataclass
class CapabilityPolicy:
    """
    Policy for validating capability execution.
    
    This defines the rules for whether a capability can be executed.
    """
    capability: str
    module: str  # Which module this capability belongs to
    allowed: bool = True
    requires_ownership: bool = True
    requires_target: bool = True
    max_confidence: float = 1.0
    min_confidence: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    
    def validate(
        self,
        user_id: str,
        target_id: Optional[str] = None,
        ownership_valid: bool = True,
        confidence: float = 0.0,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if capability can be executed.
        
        Returns:
            (is_valid, error_reason)
        """
        if not self.allowed:
            return False, f"Capability '{self.capability}' is not allowed"
        
        if self.module not in ["seller", "content_creator", "service_provider"]:
            return False, f"Module '{self.module}' is not supported"
        
        if self.requires_ownership and not ownership_valid:
            return False, "Ownership validation failed"
        
        if self.requires_target and not target_id:
            return False, "Target ID is required"
        
        if confidence < self.min_confidence:
            return False, f"Confidence {confidence} below minimum {self.min_confidence}"
        
        if confidence > self.max_confidence:
            return False, f"Confidence {confidence} above maximum {self.max_confidence}"
        
        return True, None


@dataclass
class ActionFingerprint:
    """
    Fingerprint for detecting duplicate actions.
    
    Used for loop protection to prevent repeated identical executions.
    """
    capability: str
    target: Optional[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    state_version: Optional[str] = None  # Version of state/evidence
    
    def to_hash(self) -> str:
        """Generate a hash for comparison."""
        import hashlib
        import json
        
        fingerprint_data = {
            "capability": self.capability,
            "target": self.target,
            "parameters": self.parameters,
            "state_version": self.state_version,
        }
        
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def matches(self, other: "ActionFingerprint") -> bool:
        """Check if this fingerprint matches another."""
        return self.to_hash() == other.to_hash()
