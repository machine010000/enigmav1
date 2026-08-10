"""
Pipeline Orchestrator

Central orchestration component for executing pipeline stages in correct order.
"""

from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

from app.pipeline.context import PipelineContext, PipelineStage, PipelineStatus
from app.pipeline.trace import PipelineTrace, TraceEntry, TraceStatus
from app.marketplace.economics import EconomicDecision
from app.marketplace.account_economics import AccountEconomicsEngine, EconomicSafetyStatus
from app.creativity.engine import CreativityEngine
from app.creativity.contracts import CreativeOpportunityContext
from app.time_intelligence import (
    CustomerTimeAnalyzer,
    DeadlineAnalyzer,
    WorkingHoursAnalyzer,
    WorkingHours,
)
from app.enigma_profile import EnigmaProfileManager


class PipelineGateException(Exception):
    """Exception raised when a pipeline gate blocks execution."""
    pass


class PipelineStageException(Exception):
    """Exception raised when a pipeline stage fails."""
    pass


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""
    success: bool
    blocking: bool
    blocking_reason: Optional[str] = None
    output: Optional[Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PipelineOrchestrator:
    """
    Central orchestrator for executing pipeline stages.
    
    Executes stages in the correct order with proper gate enforcement.
    """
    
    def __init__(self):
        """Initialize the pipeline orchestrator."""
        self.creativity_engine = CreativityEngine()
        self.account_economics_engine = AccountEconomicsEngine()
        self.customer_time_analyzer = CustomerTimeAnalyzer()
        self.deadline_analyzer = DeadlineAnalyzer()
        self.working_hours_analyzer = WorkingHoursAnalyzer()
        self.enigma_profile_manager = EnigmaProfileManager()
    
    def execute_pipeline(
        self,
        job_id: str,
        job_data: Dict[str, Any],
        stage_handlers: Optional[Dict[PipelineStage, Callable]] = None,
    ) -> tuple[PipelineContext, PipelineTrace]:
        """
        Execute the complete pipeline.
        
        Args:
            job_id: Job identifier
            job_data: Raw job data
            stage_handlers: Optional custom handlers for specific stages
            
        Returns:
            Tuple of (PipelineContext, PipelineTrace)
        """
        pipeline_id = str(uuid.uuid4())
        
        # Initialize context and trace
        context = PipelineContext(job_id=job_id, job_data=job_data)
        trace = PipelineTrace(pipeline_id=pipeline_id, job_id=job_id)
        
        try:
            # Execute stages in order
            self._execute_stage(
                PipelineStage.JOB_RECEIVED,
                context,
                trace,
                stage_handlers,
            )
            
            self._execute_stage(
                PipelineStage.CLASSIFICATION,
                context,
                trace,
                stage_handlers,
            )
            
            self._execute_stage(
                PipelineStage.WORK_SPECIFICATION,
                context,
                trace,
                stage_handlers,
            )
            
            self._execute_stage(
                PipelineStage.ECONOMICS_ASSESSMENT,
                context,
                trace,
                stage_handlers,
            )
            
            # Account state evaluation (TASK-048)
            if context.platform:
                self._evaluate_account_state(context, trace)
            
            # Time intelligence evaluation (TASK-049)
            self._evaluate_time_intelligence(context, trace)
            
            # Economics gate (updated with account state awareness)
            if not self._check_economics_gate(context, trace):
                context.status = PipelineStatus.BLOCKED
                context.blocking_stage = PipelineStage.ECONOMICS_ASSESSMENT
                trace.mark_completed()
                return context, trace
            
            self._execute_stage(
                PipelineStage.KNOWLEDGE_READINESS,
                context,
                trace,
                stage_handlers,
            )
            
            self._execute_stage(
                PipelineStage.EVIDENCE_READINESS,
                context,
                trace,
                stage_handlers,
            )
            
            # Knowledge/Evidence gate
            if not self._check_knowledge_evidence_gate(context, trace):
                context.status = PipelineStatus.BLOCKED
                context.blocking_stage = PipelineStage.KNOWLEDGE_READINESS
                trace.mark_completed()
                return context, trace
            
            self._execute_stage(
                PipelineStage.CREATIVITY_ENGINE,
                context,
                trace,
                stage_handlers,
            )
            
            self._execute_stage(
                PipelineStage.DECISION_EVALUATION,
                context,
                trace,
                stage_handlers,
            )
            
            # Decision gate
            if not self._check_decision_gate(context, trace):
                context.status = PipelineStatus.BLOCKED
                context.blocking_stage = PipelineStage.DECISION_EVALUATION
                trace.mark_completed()
                return context, trace
            
            self._execute_stage(
                PipelineStage.EXECUTION_READINESS,
                context,
                trace,
                stage_handlers,
            )
            
            # Execution gate
            if not self._check_execution_gate(context, trace):
                context.status = PipelineStatus.BLOCKED
                context.blocking_stage = PipelineStage.EXECUTION_READINESS
                trace.mark_completed()
                return context, trace
            
            self._execute_stage(
                PipelineStage.EXECUTION_PLANNING,
                context,
                trace,
                stage_handlers,
            )
            
            # Enigma Profile update (TASK-049)
            self._update_enigma_profile(context, trace)
            
            # Pipeline completed successfully
            context.status = PipelineStatus.COMPLETED
            context.current_stage = PipelineStage.COMPLETED
            trace.add_entry(
                PipelineStage.COMPLETED,
                TraceStatus.COMPLETED,
                output_reference="pipeline_completed",
            )
            trace.mark_completed()
            
        except PipelineGateException as e:
            context.status = PipelineStatus.BLOCKED
            context.blocking_reason = str(e)
            trace.add_entry(
                context.current_stage,
                TraceStatus.BLOCKED,
                blocking_reason=str(e),
            )
            trace.mark_completed()
            
        except PipelineStageException as e:
            context.status = PipelineStatus.FAILED
            context.blocking_reason = str(e)
            trace.add_entry(
                context.current_stage,
                TraceStatus.FAILED,
                blocking_reason=str(e),
            )
            trace.mark_completed()
        
        return context, trace
    
    def _execute_stage(
        self,
        stage: PipelineStage,
        context: PipelineContext,
        trace: PipelineTrace,
        stage_handlers: Optional[Dict[PipelineStage, Callable]],
    ) -> StageResult:
        """
        Execute a single pipeline stage.
        
        Args:
            stage: Stage to execute
            context: Pipeline context
            trace: Pipeline trace
            stage_handlers: Optional custom handlers
            
        Returns:
            StageResult
        """
        context.current_stage = stage
        context.status = PipelineStatus.IN_PROGRESS
        context.updated_at = datetime.utcnow().isoformat()
        
        trace.add_entry(stage, TraceStatus.STARTED)
        
        try:
            # Use custom handler if provided, otherwise use default
            if stage_handlers and stage in stage_handlers:
                result = stage_handlers[stage](context)
            else:
                result = self._default_stage_handler(stage, context)
            
            if result.blocking:
                raise PipelineGateException(result.blocking_reason)
            
            if not result.success:
                raise PipelineStageException("Stage execution failed")
            
            trace.add_entry(
                stage,
                TraceStatus.COMPLETED,
                output_reference=str(type(result.output).__name__) if result.output else None,
            )
            
            return result
            
        except Exception as e:
            trace.add_entry(
                stage,
                TraceStatus.FAILED,
                blocking_reason=str(e),
            )
            raise PipelineStageException(str(e))
    
    def _default_stage_handler(self, stage: PipelineStage, context: PipelineContext) -> StageResult:
        """
        Default handler for stages without custom implementations.
        
        Args:
            stage: Stage to handle
            context: Pipeline context
            
        Returns:
            StageResult
        """
        # Default implementations for key stages
        if stage == PipelineStage.JOB_RECEIVED:
            return StageResult(success=True, blocking=False, output=context.job_data)
        
        elif stage == PipelineStage.CREATIVITY_ENGINE:
            return self._handle_creativity_stage(context)
        
        return StageResult(success=True, blocking=False)
    
    def _handle_creativity_stage(self, context: PipelineContext) -> StageResult:
        """
        Handle creativity engine stage (updated with account state awareness).
        
        Args:
            context: Pipeline context
            
        Returns:
            StageResult
        """
        # Build creativity context from pipeline context
        # Include account state information for constraint detection
        creativity_context = CreativeOpportunityContext(
            work_specification=context.work_specification,
            profession=context.profession,
            expert_domain=context.expert_domain,
            required_capabilities=set(context.required_capabilities),
            required_tasks=set(context.required_tasks),
            knowledge_readiness=context.knowledge_readiness,
            execution_readiness=context.execution_readiness,
            evidence_readiness=context.evidence_readiness,
            risk_score=context.risk_score,
            portfolio_strength=context.portfolio_strength,
            review_strength=context.review_strength,
            experience_strength=context.experience_strength,
            knowledge_freshness=context.knowledge_freshness,
            platform_economics=context.economics_contract,
        )
        
        # Generate strategies
        creativity_result = self.creativity_engine.generate_strategies(creativity_context)
        
        # Update context
        context.creativity_context = creativity_context
        context.creativity_result = creativity_result
        context.creativity_constraints = creativity_result.constraints
        
        return StageResult(
            success=True,
            blocking=False,
            output=creativity_result,
        )
    
    def _evaluate_time_intelligence(self, context: PipelineContext, trace: PipelineTrace) -> None:
        """
        Evaluate time intelligence for customer timezone and deadlines (TASK-049).
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
        """
        # Infer customer timezone from job data
        explicit_timezone = context.job_data.get("timezone")
        location = context.job_data.get("location")
        platform = context.job_data.get("platform")
        country = context.job_data.get("country")
        
        customer_timezone = self.customer_time_analyzer.infer_timezone(
            explicit_timezone=explicit_timezone,
            location=location,
            platform=platform,
            country=country,
        )
        
        context.customer_timezone = customer_timezone
        
        # Create customer time context
        if customer_timezone.is_known():
            customer_time_context = self.customer_time_analyzer.create_customer_time_context(
                customer_timezone=customer_timezone,
            )
            context.customer_time_context = customer_time_context
            
            # Analyze deadline if present
            deadline = context.job_data.get("deadline")
            if deadline:
                deadline_analysis = self.deadline_analyzer.analyze_deadline(
                    deadline=deadline,
                    deadline_timezone=customer_timezone.timezone,
                )
                context.deadline_analysis = deadline_analysis
            
            # Analyze working hour overlap
            customer_working_hours = WorkingHours(
                start_hour=9,
                end_hour=18,
                timezone=customer_timezone.timezone,
            )
            working_hour_overlap = self.working_hours_analyzer.analyze_overlap(
                customer_working_hours=customer_working_hours,
            )
            context.working_hour_overlap = working_hour_overlap
        
        # Add trace entry
        trace.add_entry(
            PipelineStage.WORK_SPECIFICATION,
            TraceStatus.COMPLETED,
            output_reference="time_intelligence_evaluated",
            metadata={
                "timezone_known": customer_timezone.is_known(),
                "timezone_source": customer_timezone.source.value,
            },
        )
    
    def _evaluate_account_state(self, context: PipelineContext, trace: PipelineTrace) -> None:
        """
        Evaluate account state for economic safety (TASK-048).
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
        """
        if not context.platform:
            return
        
        # Evaluate account economics
        safety_result = self.account_economics_engine.evaluate_application_economics(
            platform=context.platform,
            job_data=context.job_data,
        )
        
        # Update context with account state information
        context.economic_safety_result = safety_result
        if safety_result.metrics:
            context.economic_metrics = safety_result.metrics
        
        # Get account state for context
        account_state = self.account_economics_engine.get_account_state(context.platform)
        if account_state:
            context.account_state = account_state
        
        # Add trace entry
        trace.add_entry(
            PipelineStage.ECONOMICS_ASSESSMENT,
            TraceStatus.COMPLETED,
            output_reference="account_state_evaluated",
            metadata={"safety_status": safety_result.status.value},
        )
    
    def _check_economics_gate(self, context: PipelineContext, trace: PipelineTrace) -> bool:
        """
        Check if economics gate passes (updated with account state awareness).
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
            
        Returns:
            True if gate passes, False otherwise
        """
        # Check account safety result first (TASK-048)
        if context.economic_safety_result:
            if context.economic_safety_result.status == EconomicSafetyStatus.BLOCK:
                context.economic_blocking_reason = context.economic_safety_result.blocking_reason
                trace.add_entry(
                    PipelineStage.ECONOMICS_ASSESSMENT,
                    TraceStatus.BLOCKED,
                    blocking_reason=context.economic_blocking_reason,
                )
                return False
            elif context.economic_safety_result.status == EconomicSafetyStatus.NEED_RESEARCH:
                context.economic_blocking_reason = context.economic_safety_result.blocking_reason
                trace.add_entry(
                    PipelineStage.ECONOMICS_ASSESSMENT,
                    TraceStatus.BLOCKED,
                    blocking_reason=context.economic_blocking_reason,
                )
                return False
        
        # Check for blocking economic decision (legacy)
        if context.economic_decision in [
            EconomicDecision.INSUFFICIENT_BALANCE,
            EconomicDecision.INSUFFICIENT_QUOTA,
            EconomicDecision.REQUIRES_MONEY,
            EconomicDecision.NOT_APPLICABLE,
        ]:
            context.economic_blocking_reason = f"Economic decision: {context.economic_decision.value}"
            trace.add_entry(
                PipelineStage.ECONOMICS_ASSESSMENT,
                TraceStatus.BLOCKED,
                blocking_reason=context.economic_blocking_reason,
            )
            return False
        
        # Check for explicit blocking reason
        if context.economic_blocking_reason:
            trace.add_entry(
                PipelineStage.ECONOMICS_ASSESSMENT,
                TraceStatus.BLOCKED,
                blocking_reason=context.economic_blocking_reason,
            )
            return False
        
        return True
    
    def _check_knowledge_evidence_gate(self, context: PipelineContext, trace: PipelineTrace) -> bool:
        """
        Check if knowledge/evidence gate passes.
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
            
        Returns:
            True if gate passes, False otherwise
        """
        # Check knowledge blocking
        if context.knowledge_blocking_reason:
            trace.add_entry(
                PipelineStage.KNOWLEDGE_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.knowledge_blocking_reason,
            )
            return False
        
        # Check evidence blocking
        if context.evidence_blocking_reason:
            trace.add_entry(
                PipelineStage.EVIDENCE_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.evidence_blocking_reason,
            )
            return False
        
        # Check for insufficient knowledge (requires research)
        if context.knowledge_readiness < 0.3:
            context.knowledge_blocking_reason = "Insufficient knowledge readiness"
            trace.add_entry(
                PipelineStage.KNOWLEDGE_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.knowledge_blocking_reason,
            )
            return False
        
        # Check for insufficient evidence
        if context.evidence_readiness < 0.3:
            context.evidence_blocking_reason = "Insufficient evidence readiness"
            trace.add_entry(
                PipelineStage.EVIDENCE_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.evidence_blocking_reason,
            )
            return False
        
        return True
    
    def _check_decision_gate(self, context: PipelineContext, trace: PipelineTrace) -> bool:
        """
        Check if decision gate passes.
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
            
        Returns:
            True if gate passes, False otherwise
        """
        # Decision must be ACCEPT or ACCEPT_WITH_CONDITIONS
        if context.decision not in ["ACCEPT", "ACCEPT_WITH_CONDITIONS"]:
            context.blocking_reason = f"Decision: {context.decision}"
            trace.add_entry(
                PipelineStage.DECISION_EVALUATION,
                TraceStatus.BLOCKED,
                blocking_reason=context.blocking_reason,
            )
            return False
        
        return True
    
    def _check_execution_gate(self, context: PipelineContext, trace: PipelineTrace) -> bool:
        """
        Check if execution gate passes.
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
            
        Returns:
            True if gate passes, False otherwise
        """
        # Check execution blocking reason
        if context.execution_blocking_reason:
            trace.add_entry(
                PipelineStage.EXECUTION_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.execution_blocking_reason,
            )
            return False
        
        # Check execution readiness
        if context.execution_readiness < 0.5:
            context.execution_blocking_reason = "Insufficient execution readiness"
            trace.add_entry(
                PipelineStage.EXECUTION_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.execution_blocking_reason,
            )
            return False
        
        # Check risk score
        if context.risk_score > 0.8:
            context.execution_blocking_reason = "Excessive risk score"
            trace.add_entry(
                PipelineStage.EXECUTION_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.execution_blocking_reason,
            )
            return False
        
        # Check scope clarity
        if context.scope_clarity < 0.5:
            context.execution_blocking_reason = "Insufficient scope clarity"
            trace.add_entry(
                PipelineStage.EXECUTION_READINESS,
                TraceStatus.BLOCKED,
                blocking_reason=context.execution_blocking_reason,
            )
            return False
        
        return True
    
    def _update_enigma_profile(self, context: PipelineContext, trace: PipelineTrace) -> None:
        """
        Update Enigma Profile with pipeline execution data (TASK-049).
        
        Args:
            context: Pipeline context
            trace: Pipeline trace
        """
        # Initialize profile if not exists
        if not self.enigma_profile_manager.profile.profile_id:
            self.enigma_profile_manager.initialize_default_profile()
        
        # Update profile with latest data
        profile = self.enigma_profile_manager.update_profile()
        
        # Update context with profile
        context.enigma_profile = profile
        
        # Add trace entry
        trace.add_entry(
            PipelineStage.COMPLETED,
            TraceStatus.COMPLETED,
            output_reference="enigma_profile_updated",
            metadata={
                "profile_id": profile.profile_id,
                "development_priorities": len(profile.development_priorities),
                "open_issues": len(profile.get_open_issues()),
            },
        )
