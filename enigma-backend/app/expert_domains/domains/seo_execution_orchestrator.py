from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from app.execution.contracts import (
    ExecutionPlan,
    ExecutionStep,
    StepState,
    StepType,
    ExecutionSession,
    SessionState,
    SessionPriority,
    ExecutionOutput,
    OutputType,
    ValidationResult,
    ValidationStatus,
    ExecutionReflection,
)
from app.execution.runtime import ExecutionRuntime
from app.execution.planner import TemplateBasedPlanner
from app.execution.scheduler import PriorityExecutionScheduler
from app.execution.executor import BaseExecutor, ExecutionContext, ExecutionResult
from app.execution.validation import BaseValidator
from app.execution.outputs import BaseOutputBuilder
from app.execution.registry import ExecutionRegistry
from app.expert_domains.execution import ExecutionTemplate, ExecutionStepType
from app.expert_domains.domains.seo_workers import (
    SEOTechnicalAuditWorker,
    SEOKeywordResearchWorker,
    SEOReportGenerationWorker,
    seo_worker_registry,
)
from app.expert_domains.domains.seo_outputs import seo_output_builder
from app.expert_domains.domains.seo_reflection_generator import seo_reflection_generator
from app.expert_domains.domains.seo_knowledge_integration import (
    SEOKnowledgeIntegration,
    SEOEvidenceIntegration,
    SEOReadinessIntegration,
    seo_knowledge_integration,
    seo_evidence_integration,
    seo_readiness_integration,
)


@dataclass
class ExecutionReport:
    """Comprehensive execution report."""
    session_id: str
    work_specification_id: str
    domain_id: str
    execution_status: str
    success: bool
    steps_completed: int
    steps_total: int
    outputs_generated: int
    validation_passed: bool
    reflection: Optional[ExecutionReflection] = None
    knowledge_update: Optional[Dict[str, Any]] = None
    evidence_update: Optional[Dict[str, Any]] = None
    readiness_update: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SEOExecutionOrchestrator:
    """
    End-to-end SEO execution orchestrator.
    
    Orchestrates the complete SEO execution pipeline:
    1. Work Specification → Execution Plan (using SEO Domain templates)
    2. Execution Plan → Runtime Session
    3. Runtime → Worker Execution (SEO-specific workers)
    4. Worker Results → Outputs (SEO-specific builders)
    5. Outputs → Validation
    6. Validation → Reflection (SEO-specific)
    7. Reflection → Knowledge Update
    8. Knowledge Update → Evidence Update
    9. Evidence Update → Readiness Update
    """

    def __init__(self) -> None:
        # Initialize execution components
        self._runtime = ExecutionRuntime()
        self._planner = TemplateBasedPlanner()
        self._scheduler = PriorityExecutionScheduler()
        self._executor = BaseExecutor()
        self._validator = BaseValidator()
        
        # Initialize SEO-specific components
        self._output_builder = seo_output_builder
        self._reflection_generator = seo_reflection_generator
        self._knowledge_integration = seo_knowledge_integration
        self._evidence_integration = seo_evidence_integration
        self._readiness_integration = seo_readiness_integration
        
        # Register SEO workers
        self._register_seo_workers()
        
        # Store execution templates (from SEO Domain)
        self._execution_templates: Dict[str, ExecutionTemplate] = {}

    def register_execution_template(self, template: ExecutionTemplate) -> None:
        """Register an execution template from SEO Domain."""
        self._execution_templates[template.template_id] = template

    def _register_seo_workers(self) -> None:
        """Register SEO-specific workers with executor."""
        for worker_name, worker in seo_worker_registry.items():
            self._executor.register_worker(worker)

    def execute_work_specification(
        self,
        work_specification_id: str,
        work_specification: Dict[str, Any],
        domain_id: str = "seo",
        template_id: Optional[str] = None,
    ) -> ExecutionReport:
        """
        Execute a work specification through the complete pipeline.
        
        Args:
            work_specification_id: ID of the work specification
            work_specification: Work specification data
            domain_id: Domain ID (default: seo)
            template_id: Optional template ID to use
            
        Returns:
            ExecutionReport with complete execution results
        """
        report = ExecutionReport(
            session_id=f"session_{uuid.uuid4().hex[:8]}",
            work_specification_id=work_specification_id,
            domain_id=domain_id,
            execution_status="in_progress",
            success=False,
            steps_completed=0,
            steps_total=0,
            outputs_generated=0,
            validation_passed=False,
            metadata={
                "work_specification": work_specification,
                "template_id": template_id,
            },
        )

        try:
            # Step 1: Create execution session
            session = self._create_session(report.session_id, work_specification_id, domain_id)
            
            # Step 2: Create execution plan from template
            plan = self._create_execution_plan(
                report.session_id,
                work_specification_id,
                domain_id,
                template_id,
                work_specification,
            )
            report.steps_total = len(plan.steps)
            
            # Step 3: Register plan with runtime
            self._runtime.register_plan(plan)
            
            # Step 4: Execute plan steps
            execution_results = self._execute_plan(
                report.session_id,
                plan,
                work_specification,
            )
            report.steps_completed = len([s for s in plan.steps if execution_results["step_states"].get(s.step_id) == StepState.DONE])
            
            # Step 5: Build outputs
            all_outputs = self._build_outputs(plan, execution_results, report.session_id)
            report.outputs_generated = len(all_outputs)
            
            # Step 6: Validate outputs
            validation_result = self._validate_execution(plan, all_outputs, report.session_id)
            report.validation_passed = validation_result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]
            
            # Step 7: Generate reflection
            reflection = self._reflection_generator.generate_reflection(
                report.session_id,
                plan,
                execution_results,
            )
            report.reflection = reflection
            
            # Step 8: Update knowledge
            knowledge_update = self._knowledge_integration.update_knowledge_from_outputs(
                all_outputs,
                report.session_id,
                domain_id,
            )
            report.knowledge_update = {
                "candidates_submitted": knowledge_update.candidates_submitted,
                "candidates_accepted": knowledge_update.candidates_accepted,
                "candidates_rejected": knowledge_update.candidates_rejected,
            }
            
            # Step 9: Update evidence
            evidence_update = self._evidence_integration.register_evidence(
                all_outputs,
                report.session_id,
                domain_id,
            )
            report.evidence_update = {
                "evidence_registered": evidence_update["evidence_registered"],
                "evidence_ids": evidence_update["evidence_ids"],
            }
            
            # Step 10: Update readiness
            readiness_update = self._readiness_integration.update_readiness(
                report.session_id,
                domain_id,
                execution_success=report.steps_completed == report.steps_total,
                quality_score=0.8 if report.validation_passed else 0.5,
                evidence_collected=evidence_update["evidence_registered"],
                knowledge_generated=knowledge_update.candidates_accepted,
            )
            report.readiness_update = readiness_update
            
            # Complete session
            self._runtime.complete_session(report.session_id, SessionState.COMPLETED)
            
            # Update report status
            report.execution_status = "completed"
            report.success = report.steps_completed == report.steps_total and report.validation_passed
            report.completed_at = datetime.utcnow()
            
        except Exception as e:
            report.execution_status = "failed"
            report.errors.append(f"Execution failed: {str(e)}")
            report.completed_at = datetime.utcnow()
            self._runtime.complete_session(report.session_id, SessionState.FAILED)

        return report

    def _create_session(
        self,
        session_id: str,
        work_specification_id: str,
        domain_id: str,
    ) -> ExecutionSession:
        """Create execution session."""
        return self._runtime.create_session(
            session_id=session_id,
            work_specification_id=work_specification_id,
            decision_id=f"decision_{uuid.uuid4().hex[:8]}",
            domain_id=domain_id,
            priority=SessionPriority.MEDIUM,
        )

    def _create_execution_plan(
        self,
        session_id: str,
        work_specification_id: str,
        domain_id: str,
        template_id: Optional[str],
        work_specification: Dict[str, Any],
    ) -> ExecutionPlan:
        """Create execution plan from SEO Domain template."""
        # Convert SEO Domain ExecutionTemplate to ExecutionPlan
        if template_id and template_id in self._execution_templates:
            seo_template = self._execution_templates[template_id]
            return self._convert_template_to_plan(seo_template, session_id, work_specification_id, domain_id)
        
        # Default to technical SEO audit template
        default_template = self._get_default_template()
        return self._convert_template_to_plan(default_template, session_id, work_specification_id, domain_id)

    def _convert_template_to_plan(
        self,
        template: ExecutionTemplate,
        session_id: str,
        work_specification_id: str,
        domain_id: str,
    ) -> ExecutionPlan:
        """Convert SEO Domain ExecutionTemplate to ExecutionPlan."""
        steps = []
        step_order = []
        quality_gates = []
        milestones = []
        
        for seo_step in template.execution_steps:
            step = ExecutionStep(
                step_id=seo_step.step_id,
                step_type=self._convert_step_type(seo_step.step_type),
                name=seo_step.name,
                description=seo_step.description,
                dependencies=seo_step.required_inputs,  # Use inputs as dependencies
                expected_outputs=seo_step.expected_outputs,
                retry_count=0,
                max_retries=3,
            )
            steps.append(step)
            step_order.append(seo_step.step_id)
            
            # Mark quality gates and milestones
            if seo_step.quality_gates:
                quality_gates.append(seo_step.step_id)
            if seo_step.step_type == ExecutionStepType.ANALYSIS:
                milestones.append(seo_step.step_id)
        
        return ExecutionPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            work_specification_id=work_specification_id,
            domain_id=domain_id,
            steps=steps,
            step_order=step_order,
            quality_gates=quality_gates,
            milestones=milestones,
        )

    def _convert_step_type(self, seo_step_type: ExecutionStepType) -> StepType:
        """Convert SEO Domain step type to Execution Framework step type."""
        mapping = {
            ExecutionStepType.PREPARATION: StepType.CAPABILITY,
            ExecutionStepType.ANALYSIS: StepType.CAPABILITY,
            ExecutionStepType.EXECUTION: StepType.TASK,
            ExecutionStepType.VALIDATION: StepType.VALIDATION,
            ExecutionStepType.COMPLETION: StepType.DELIVERABLE,
            ExecutionStepType.CLEANUP: StepType.TASK,
        }
        return mapping.get(seo_step_type, StepType.TASK)

    def _get_default_template(self) -> ExecutionTemplate:
        """Get default SEO execution template."""
        # Return technical SEO audit template as default
        from app.expert_domains.execution import ExecutionStep, ExecutionStepType
        
        return ExecutionTemplate(
            template_id="technical_seo_audit_default",
            name="Technical SEO Audit (Default)",
            description="Default technical SEO audit template",
            execution_steps=[
                ExecutionStep(
                    step_id="technical_analysis",
                    step_type=ExecutionStepType.ANALYSIS,
                    name="Technical SEO Analysis",
                    description="Perform technical SEO analysis",
                    order=1,
                    required_inputs=["url"],
                    expected_outputs=["technical_findings", "issues_list"],
                    required_capabilities=["technical_seo_audit_capability"],
                ),
                ExecutionStep(
                    step_id="recommendation_generation",
                    step_type=ExecutionStepType.EXECUTION,
                    name="Generate Recommendations",
                    description="Generate SEO recommendations",
                    order=2,
                    required_inputs=["issues_list"],
                    expected_outputs=["recommendations"],
                    required_capabilities=["technical_seo_audit_capability"],
                ),
                ExecutionStep(
                    step_id="report_generation",
                    step_type=ExecutionStepType.COMPLETION,
                    name="Generate Report",
                    description="Generate comprehensive audit report",
                    order=3,
                    required_inputs=["technical_findings", "recommendations"],
                    expected_outputs=["audit_report"],
                    required_capabilities=["technical_seo_audit_capability"],
                ),
            ],
            inputs=["url"],
            outputs=["audit_report", "issues_list", "recommendations"],
            deliverables=["audit_report"],
            quality_gates=["report_generation"],
            required_capabilities=["technical_seo_audit_capability"],
        )

    def _execute_plan(
        self,
        session_id: str,
        plan: ExecutionPlan,
        work_specification: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute execution plan steps."""
        step_states: Dict[str, StepState] = {}
        outputs: Dict[str, List[ExecutionOutput]] = {}
        errors: Dict[str, str] = {}
        
        for step in plan.steps:
            # Update step state to running
            self._runtime.update_step_state(session_id, step.step_id, StepState.RUNNING)
            step_states[step.step_id] = StepState.RUNNING
            
            try:
                # Execute step
                context = ExecutionContext(
                    session_id=session_id,
                    step_id=step.step_id,
                    inputs=work_specification,
                    metadata={"step_name": step.name},
                )
                
                result = self._executor.execute_step(step, context)
                
                if result.success:
                    step_states[step.step_id] = StepState.DONE
                    outputs[step.step_id] = result.outputs
                else:
                    step_states[step.step_id] = StepState.FAILED
                    errors[step.step_id] = result.error_message or "Execution failed"
                    
            except Exception as e:
                step_states[step.step_id] = StepState.FAILED
                errors[step.step_id] = str(e)
        
        return {
            "step_states": step_states,
            "outputs": outputs,
            "errors": errors,
            "url": work_specification.get("url", ""),
            "audit_type": work_specification.get("audit_type", "technical_seo_audit"),
        }

    def _build_outputs(
        self,
        plan: ExecutionPlan,
        execution_results: Dict[str, Any],
        session_id: str,
    ) -> List[ExecutionOutput]:
        """Build outputs from execution results."""
        all_outputs = []
        
        for step in plan.steps:
            step_outputs = execution_results["outputs"].get(step.step_id, [])
            
            # Use SEO output builder to enhance outputs
            enhanced_outputs = self._output_builder.build_outputs(
                step,
                {"findings": execution_results.get("findings", {}), "issues": [], "recommendations": [], "metrics": {}},
                {"session_id": session_id, "url": execution_results.get("url", "")},
            )
            
            all_outputs.extend(step_outputs)
            all_outputs.extend(enhanced_outputs)
        
        return all_outputs

    def _validate_execution(
        self,
        plan: ExecutionPlan,
        outputs: List[ExecutionOutput],
        session_id: str,
    ) -> ValidationResult:
        """Validate execution outputs."""
        # Validate each step's outputs
        all_passed = True
        checks_passed = 0
        checks_total = 0
        
        for step in plan.steps:
            step_outputs = [o for o in outputs if o.step_id == step.step_id]
            result = self._validator.validate_step(step, step_outputs, {"session_id": session_id})
            
            checks_total += result.checks_total
            checks_passed += result.checks_passed
            
            if result.status == ValidationStatus.FAILED:
                all_passed = False
        
        return ValidationResult(
            validation_id=f"validation_{uuid.uuid4().hex[:8]}",
            step_id="execution",
            session_id=session_id,
            status=ValidationStatus.PASSED if all_passed else ValidationStatus.FAILED,
            checks_passed=checks_passed,
            checks_total=checks_total,
        )


# Default SEO execution orchestrator instance
seo_execution_orchestrator = SEOExecutionOrchestrator()
