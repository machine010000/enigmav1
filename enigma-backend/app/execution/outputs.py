from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import uuid

from app.execution.contracts import (
    ExecutionStep,
    ExecutionOutput,
    OutputType,
    OutputBuilder,
)


@dataclass
class OutputMetadata:
    """Metadata for execution outputs."""
    output_id: str
    step_id: str
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseOutputBuilder:
    """
    Base implementation of Output Builder.
    
    This builder constructs outputs from execution results without
    containing domain-specific logic. It delegates to registered builders.
    """

    def __init__(self) -> None:
        self._builders: Dict[str, Callable[[ExecutionStep, Any, Dict[str, Any]], List[ExecutionOutput]]] = {}

    def register_builder(
        self,
        output_type: str,
        builder: Callable[[ExecutionStep, Any, Dict[str, Any]], List[ExecutionOutput]],
    ) -> None:
        """Register an output builder for a specific type."""
        self._builders[output_type] = builder

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """
        Build outputs from execution result.
        
        Args:
            step: The step that was executed
            execution_result: Result from the step execution
            context: Additional context
            
        Returns:
            List of execution outputs
        """
        outputs = []
        
        # Try type-specific builder
        step_type_str = step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type)
        builder = self._builders.get(step_type_str)
        
        if builder:
            try:
                outputs = builder(step, execution_result, context)
            except Exception as e:
                # Create error output if builder fails
                outputs = [
                    ExecutionOutput(
                        output_id=f"error_output_{uuid.uuid4().hex[:8]}",
                        step_id=step.step_id,
                        session_id=context.get("session_id", ""),
                        output_type=OutputType.ARTIFACT,
                        name="Error Output",
                        description=f"Output builder failed: {str(e)}",
                        content={"error": str(e)},
                        content_type="json",
                    )
                ]
        else:
            # Use default output builder
            outputs = self._build_default_outputs(step, execution_result, context)
        
        return outputs

    def _build_default_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build default outputs from execution result."""
        outputs = []
        
        # If execution result is already a list of outputs
        if isinstance(execution_result, list) and all(isinstance(o, ExecutionOutput) for o in execution_result):
            return execution_result
        
        # If execution result is a single output
        if isinstance(execution_result, ExecutionOutput):
            return [execution_result]
        
        # Create default output from result
        output = ExecutionOutput(
            output_id=f"output_{uuid.uuid4().hex[:8]}",
            step_id=step.step_id,
            session_id=context.get("session_id", ""),
            output_type=OutputType.ARTIFACT,
            name=f"Output for {step.name}",
            description=f"Output from step: {step.name}",
            content=execution_result,
            content_type=self._infer_content_type(execution_result),
        )
        outputs.append(output)
        
        return outputs

    def _infer_content_type(self, content: Any) -> str:
        """Infer content type from content."""
        if isinstance(content, dict):
            return "json"
        elif isinstance(content, list):
            return "json"
        elif isinstance(content, str):
            return "text"
        elif isinstance(content, (int, float)):
            return "text"
        else:
            return "text"


class EvidenceOutputBuilder:
    """
    Builder for evidence outputs.
    
    This builder creates evidence outputs from execution results.
    """

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build evidence outputs."""
        outputs = []
        
        # Extract evidence from execution result
        evidence_data = self._extract_evidence(execution_result)
        
        if evidence_data:
            output = ExecutionOutput(
                output_id=f"evidence_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.EVIDENCE,
                name=f"Evidence for {step.name}",
                description=f"Evidence generated by step: {step.name}",
                content=evidence_data,
                content_type="json",
                metadata={"evidence_type": "execution_evidence"},
            )
            outputs.append(output)
        
        return outputs

    def _extract_evidence(self, execution_result: Any) -> Optional[Dict[str, Any]]:
        """Extract evidence from execution result."""
        if isinstance(execution_result, dict):
            return execution_result.get("evidence")
        return None


class ReportOutputBuilder:
    """
    Builder for report outputs.
    
    This builder creates report outputs from execution results.
    """

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build report outputs."""
        outputs = []
        
        # Extract report data from execution result
        report_data = self._extract_report(execution_result)
        
        if report_data:
            output = ExecutionOutput(
                output_id=f"report_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.REPORT,
                name=f"Report for {step.name}",
                description=f"Report generated by step: {step.name}",
                content=report_data,
                content_type="json",
                metadata={"report_type": "execution_report"},
            )
            outputs.append(output)
        
        return outputs

    def _extract_report(self, execution_result: Any) -> Optional[Dict[str, Any]]:
        """Extract report from execution result."""
        if isinstance(execution_result, dict):
            return execution_result.get("report")
        return None


class MetricOutputBuilder:
    """
    Builder for metric outputs.
    
    This builder creates metric outputs from execution results.
    """

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build metric outputs."""
        outputs = []
        
        # Extract metrics from execution result
        metrics_data = self._extract_metrics(execution_result)
        
        if metrics_data:
            output = ExecutionOutput(
                output_id=f"metric_{uuid.uuid4().hex[:8]}",
                step_id=step.step_id,
                session_id=context.get("session_id", ""),
                output_type=OutputType.METRIC,
                name=f"Metrics for {step.name}",
                description=f"Metrics generated by step: {step.name}",
                content=metrics_data,
                content_type="json",
                metadata={"metric_type": "execution_metrics"},
            )
            outputs.append(output)
        
        return outputs

    def _extract_metrics(self, execution_result: Any) -> Optional[Dict[str, Any]]:
        """Extract metrics from execution result."""
        if isinstance(execution_result, dict):
            return execution_result.get("metrics")
        return None


class CompositeOutputBuilder:
    """
    Composite output builder that combines multiple builders.
    
    This builder allows multiple output types to be generated
    from a single execution result.
    """

    def __init__(self) -> None:
        self._builders: List[Callable[[ExecutionStep, Any, Dict[str, Any]], List[ExecutionOutput]]] = []

    def add_builder(
        self,
        builder: Callable[[ExecutionStep, Any, Dict[str, Any]], List[ExecutionOutput]],
    ) -> None:
        """Add a builder to the composite."""
        self._builders.append(builder)

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build outputs using all registered builders."""
        all_outputs = []
        
        for builder in self._builders:
            try:
                outputs = builder(step, execution_result, context)
                all_outputs.extend(outputs)
            except Exception:
                # Continue with other builders if one fails
                pass
        
        return all_outputs


class CallbackOutputBuilder:
    """
    Output builder that uses a callback function.
    
    This allows custom output building logic to be injected without
    creating a full builder class.
    """

    def __init__(
        self,
        build_callback: Callable[
            [ExecutionStep, Any, Dict[str, Any]],
            List[ExecutionOutput],
        ],
    ) -> None:
        self._build_callback = build_callback

    def build_outputs(
        self,
        step: ExecutionStep,
        execution_result: Any,
        context: Dict[str, Any],
    ) -> List[ExecutionOutput]:
        """Build outputs using callback."""
        return self._build_callback(step, execution_result, context)


# Default output builder instance
default_output_builder = BaseOutputBuilder()
