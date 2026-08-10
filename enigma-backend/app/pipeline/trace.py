"""
Pipeline Trace

Trace of pipeline execution for debugging and auditing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.pipeline.context import PipelineStage


class TraceStatus(str, Enum):
    """Status of a trace entry."""
    STARTED = "started"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TraceEntry:
    """
    Single entry in the pipeline trace.
    
    Records the execution of a single pipeline stage.
    """
    stage: PipelineStage
    status: TraceStatus
    timestamp: str
    input_reference: Optional[str] = None
    output_reference: Optional[str] = None
    blocking_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "input_reference": self.input_reference,
            "output_reference": self.output_reference,
            "blocking_reason": self.blocking_reason,
            "metadata": self.metadata,
        }


@dataclass
class PipelineTrace:
    """
    Complete trace of pipeline execution.
    
    Records all stages executed in order with their status.
    """
    pipeline_id: str
    job_id: str
    entries: List[TraceEntry] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    
    def add_entry(
        self,
        stage: PipelineStage,
        status: TraceStatus,
        input_reference: Optional[str] = None,
        output_reference: Optional[str] = None,
        blocking_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a trace entry.
        
        Args:
            stage: Pipeline stage
            status: Stage status
            input_reference: Reference to input data
            output_reference: Reference to output data
            blocking_reason: Reason if blocked
            metadata: Additional metadata
        """
        entry = TraceEntry(
            stage=stage,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            input_reference=input_reference,
            output_reference=output_reference,
            blocking_reason=blocking_reason,
            metadata=metadata or {},
        )
        self.entries.append(entry)
    
    def mark_completed(self) -> None:
        """Mark pipeline as completed."""
        self.completed_at = datetime.utcnow().isoformat()
    
    def get_entries_by_stage(self, stage: PipelineStage) -> List[TraceEntry]:
        """Get all entries for a specific stage."""
        return [e for e in self.entries if e.stage == stage]
    
    def get_blocking_entries(self) -> List[TraceEntry]:
        """Get all entries that blocked the pipeline."""
        return [e for e in self.entries if e.status == TraceStatus.BLOCKED]
    
    def get_failed_entries(self) -> List[TraceEntry]:
        """Get all entries that failed."""
        return [e for e in self.entries if e.status == TraceStatus.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "job_id": self.job_id,
            "entries": [e.to_dict() for e in self.entries],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
