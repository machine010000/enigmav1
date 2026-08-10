"""
Test Pipeline Trace
"""

import pytest

from app.pipeline.trace import PipelineTrace, TraceEntry, TraceStatus
from app.pipeline.context import PipelineStage


class TestTraceEntry:
    """Test trace entry."""
    
    def test_entry_creation(self):
        """Test trace entry creation."""
        entry = TraceEntry(
            stage=PipelineStage.JOB_RECEIVED,
            status=TraceStatus.COMPLETED,
            timestamp="2024-01-01T00:00:00",
        )
        
        assert entry.stage == PipelineStage.JOB_RECEIVED
        assert entry.status == TraceStatus.COMPLETED
        assert entry.timestamp == "2024-01-01T00:00:00"
    
    def test_entry_to_dict(self):
        """Test entry to_dict conversion."""
        entry = TraceEntry(
            stage=PipelineStage.JOB_RECEIVED,
            status=TraceStatus.COMPLETED,
            timestamp="2024-01-01T00:00:00",
            input_reference="job_data",
            output_reference="context",
            blocking_reason="test_reason",
        )
        
        result = entry.to_dict()
        
        assert result["stage"] == "job_received"
        assert result["status"] == "completed"
        assert result["timestamp"] == "2024-01-01T00:00:00"
        assert result["input_reference"] == "job_data"
        assert result["output_reference"] == "context"
        assert result["blocking_reason"] == "test_reason"


class TestPipelineTrace:
    """Test pipeline trace."""
    
    def test_trace_initialization(self):
        """Test trace initialization."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        assert trace.pipeline_id == "test_pipeline"
        assert trace.job_id == "test_job"
        assert len(trace.entries) == 0
        assert trace.started_at is not None
        assert trace.completed_at is None
    
    def test_add_entry(self):
        """Test adding trace entry."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        trace.add_entry(
            PipelineStage.JOB_RECEIVED,
            TraceStatus.COMPLETED,
            input_reference="job_data",
            output_reference="context",
        )
        
        assert len(trace.entries) == 1
        assert trace.entries[0].stage == PipelineStage.JOB_RECEIVED
        assert trace.entries[0].status == TraceStatus.COMPLETED
    
    def test_mark_completed(self):
        """Test marking trace as completed."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        assert trace.completed_at is None
        
        trace.mark_completed()
        
        assert trace.completed_at is not None
    
    def test_get_entries_by_stage(self):
        """Test getting entries by stage."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        trace.add_entry(PipelineStage.JOB_RECEIVED, TraceStatus.COMPLETED)
        trace.add_entry(PipelineStage.CLASSIFICATION, TraceStatus.COMPLETED)
        trace.add_entry(PipelineStage.JOB_RECEIVED, TraceStatus.BLOCKED)
        
        job_entries = trace.get_entries_by_stage(PipelineStage.JOB_RECEIVED)
        
        assert len(job_entries) == 2
        assert all(e.stage == PipelineStage.JOB_RECEIVED for e in job_entries)
    
    def test_get_blocking_entries(self):
        """Test getting blocking entries."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        trace.add_entry(PipelineStage.JOB_RECEIVED, TraceStatus.COMPLETED)
        trace.add_entry(PipelineStage.CLASSIFICATION, TraceStatus.BLOCKED)
        trace.add_entry(PipelineStage.WORK_SPECIFICATION, TraceStatus.COMPLETED)
        
        blocking_entries = trace.get_blocking_entries()
        
        assert len(blocking_entries) == 1
        assert blocking_entries[0].stage == PipelineStage.CLASSIFICATION
    
    def test_get_failed_entries(self):
        """Test getting failed entries."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        trace.add_entry(PipelineStage.JOB_RECEIVED, TraceStatus.COMPLETED)
        trace.add_entry(PipelineStage.CLASSIFICATION, TraceStatus.FAILED)
        trace.add_entry(PipelineStage.WORK_SPECIFICATION, TraceStatus.COMPLETED)
        
        failed_entries = trace.get_failed_entries()
        
        assert len(failed_entries) == 1
        assert failed_entries[0].stage == PipelineStage.CLASSIFICATION
    
    def test_to_dict(self):
        """Test trace to_dict conversion."""
        trace = PipelineTrace(pipeline_id="test_pipeline", job_id="test_job")
        
        trace.add_entry(PipelineStage.JOB_RECEIVED, TraceStatus.COMPLETED)
        trace.mark_completed()
        
        result = trace.to_dict()
        
        assert result["pipeline_id"] == "test_pipeline"
        assert result["job_id"] == "test_job"
        assert len(result["entries"]) == 1
        assert result["completed_at"] is not None
