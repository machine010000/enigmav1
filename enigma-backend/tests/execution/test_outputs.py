"""
Tests for Execution Outputs module.

Tests output building, output types, and output metadata.
"""

import pytest

from app.execution.contracts import (
    ExecutionStep,
    StepState,
    StepType,
    ExecutionOutput,
    OutputType,
)
from app.execution.outputs import (
    BaseOutputBuilder,
    EvidenceOutputBuilder,
    ReportOutputBuilder,
    MetricOutputBuilder,
    CompositeOutputBuilder,
    CallbackOutputBuilder,
)


class TestBaseOutputBuilder:
    """Test BaseOutputBuilder."""

    def test_register_builder(self):
        """Test registering an output builder."""
        builder = BaseOutputBuilder()
        
        def custom_builder(step, result, context):
            return []
        
        builder.register_builder("task", custom_builder)
        
        assert "task" in builder._builders

    def test_build_outputs_from_dict_result(self):
        """Test building outputs from dict result."""
        builder = BaseOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {"data": "value", "key": "value2"}
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].content_type == "json"

    def test_build_outputs_from_string_result(self):
        """Test building outputs from string result."""
        builder = BaseOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = "Test output"
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].content_type == "text"

    def test_build_outputs_from_execution_output(self):
        """Test building outputs when result is already ExecutionOutput."""
        builder = BaseOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        existing_output = ExecutionOutput(
            output_id="output_001",
            step_id="step_001",
            session_id="session_001",
            output_type=OutputType.ARTIFACT,
            name="Existing Output",
            description="Already an output",
        )
        
        outputs = builder.build_outputs(step, existing_output, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].output_id == "output_001"

    def test_build_outputs_from_list_of_outputs(self):
        """Test building outputs when result is list of ExecutionOutput."""
        builder = BaseOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        existing_outputs = [
            ExecutionOutput(
                output_id="output_001",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="Output 1",
                description="First output",
            ),
            ExecutionOutput(
                output_id="output_002",
                step_id="step_001",
                session_id="session_001",
                output_type=OutputType.ARTIFACT,
                name="Output 2",
                description="Second output",
            ),
        ]
        
        outputs = builder.build_outputs(step, existing_outputs, {"session_id": "session_001"})
        
        assert len(outputs) == 2

    def test_build_outputs_with_registered_builder(self):
        """Test building outputs with registered builder."""
        builder = BaseOutputBuilder()
        
        def custom_builder(step, result, context):
            return [
                ExecutionOutput(
                    output_id="custom_output",
                    step_id=step.step_id,
                    session_id=context.get("session_id", ""),
                    output_type=OutputType.ARTIFACT,
                    name="Custom Output",
                    description="From custom builder",
                    content={"custom": True},
                )
            ]
        
        builder.register_builder("task", custom_builder)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = builder.build_outputs(step, {"data": "value"}, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].name == "Custom Output"

    def test_build_outputs_builder_failure(self):
        """Test building outputs when builder fails."""
        builder = BaseOutputBuilder()
        
        def failing_builder(step, result, context):
            raise ValueError("Builder failed")
        
        builder.register_builder("task", failing_builder)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = builder.build_outputs(step, {"data": "value"}, {"session_id": "session_001"})
        
        # Should create error output
        assert len(outputs) == 1
        assert "error" in outputs[0].name.lower()


class TestEvidenceOutputBuilder:
    """Test EvidenceOutputBuilder."""

    def test_build_evidence_outputs(self):
        """Test building evidence outputs."""
        builder = EvidenceOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {
            "evidence": {"key": "value", "source": "test"},
        }
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].output_type == OutputType.EVIDENCE

    def test_build_evidence_outputs_no_evidence(self):
        """Test building evidence outputs without evidence."""
        builder = EvidenceOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {"data": "value"}
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 0


class TestReportOutputBuilder:
    """Test ReportOutputBuilder."""

    def test_build_report_outputs(self):
        """Test building report outputs."""
        builder = ReportOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {
            "report": {"title": "Test Report", "content": "Report content"},
        }
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].output_type == OutputType.REPORT

    def test_build_report_outputs_no_report(self):
        """Test building report outputs without report."""
        builder = ReportOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {"data": "value"}
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 0


class TestMetricOutputBuilder:
    """Test MetricOutputBuilder."""

    def test_build_metric_outputs(self):
        """Test building metric outputs."""
        builder = MetricOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {
            "metrics": {"score": 0.85, "count": 100},
        }
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].output_type == OutputType.METRIC

    def test_build_metric_outputs_no_metrics(self):
        """Test building metric outputs without metrics."""
        builder = MetricOutputBuilder()
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        execution_result = {"data": "value"}
        
        outputs = builder.build_outputs(step, execution_result, {"session_id": "session_001"})
        
        assert len(outputs) == 0


class TestCompositeOutputBuilder:
    """Test CompositeOutputBuilder."""

    def test_composite_builder(self):
        """Test composite output builder."""
        builder = CompositeOutputBuilder()
        
        def builder1(step, result, context):
            return [
                ExecutionOutput(
                    output_id="output_1",
                    step_id=step.step_id,
                    session_id=context.get("session_id", ""),
                    output_type=OutputType.ARTIFACT,
                    name="Output 1",
                    description="From builder 1",
                )
            ]
        
        def builder2(step, result, context):
            return [
                ExecutionOutput(
                    output_id="output_2",
                    step_id=step.step_id,
                    session_id=context.get("session_id", ""),
                    output_type=OutputType.ARTIFACT,
                    name="Output 2",
                    description="From builder 2",
                )
            ]
        
        builder.add_builder(builder1)
        builder.add_builder(builder2)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = builder.build_outputs(step, {"data": "value"}, {"session_id": "session_001"})
        
        assert len(outputs) == 2

    def test_composite_builder_with_failure(self):
        """Test composite builder when one builder fails."""
        builder = CompositeOutputBuilder()
        
        def failing_builder(step, result, context):
            raise ValueError("Builder failed")
        
        def working_builder(step, result, context):
            return [
                ExecutionOutput(
                    output_id="output_1",
                    step_id=step.step_id,
                    session_id=context.get("session_id", ""),
                    output_type=OutputType.ARTIFACT,
                    name="Output 1",
                    description="From working builder",
                )
            ]
        
        builder.add_builder(failing_builder)
        builder.add_builder(working_builder)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = builder.build_outputs(step, {"data": "value"}, {"session_id": "session_001"})
        
        # Should continue with working builder
        assert len(outputs) == 1


class TestCallbackOutputBuilder:
    """Test CallbackOutputBuilder."""

    def test_callback_builder(self):
        """Test callback output builder."""
        def callback(step, result, context):
            return [
                ExecutionOutput(
                    output_id="callback_output",
                    step_id=step.step_id,
                    session_id=context.get("session_id", ""),
                    output_type=OutputType.ARTIFACT,
                    name="Callback Output",
                    description="From callback",
                )
            ]
        
        builder = CallbackOutputBuilder(callback)
        
        step = ExecutionStep(
            step_id="step_001",
            step_type=StepType.TASK,
            name="Task 1",
            description="First task",
        )
        
        outputs = builder.build_outputs(step, {"data": "value"}, {"session_id": "session_001"})
        
        assert len(outputs) == 1
        assert outputs[0].name == "Callback Output"
