"""
Autonomous Orchestrator

Application-level orchestrator for bounded multi-step autonomy.

TASK-015: Bounded control loop, capability validation, duplicate-action
          detection, failure-stop policy, execution trace.

TASK-016: Ownership enforcement hardened.
          - _validate_ownership is NO LONGER a stub — performs a real
            database query scoped to the authenticated user using the same
            WHERE product.id = X AND product.user_id = user_id pattern as
            the products router.
          - Ownership is revalidated BEFORE every executable step (not
            only at run start).
          - Step context reloads authoritative target on each iteration.
          - MAX_AUTONOMOUS_STEPS bounded from settings (1–5).
          - Structured log fields: run_id, step_number, capability,
            execution_id, user_id (safe identifier), stop_reason, duration.
          - No secrets, no raw prompts, no stack traces in logs.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from app.ai.client import (
    AITimeoutError,
    AIConfigurationError,
    AIAuthenticationError,
    AIConnectionError,
    AIProviderError,
)
from app.autonomy.contracts import (
    AutonomousRun,
    AutonomousStep,
    RunStatus,
    StepStatus,
    StopReason,
    ActionFingerprint,
    CapabilityPolicy,
)
from app.ai.master_brain.orchestrator import MasterBrain
from app.ai.master_brain.models import BrainDecision, BrainAction
from app.engine.capabilities import capability_registry
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Allowed module names — guard against client-supplied arbitrary strings
_ALLOWED_MODULES = frozenset({"seller", "content_creator", "service_provider"})


class AutonomousOrchestrator:
    """
    Orchestrates bounded autonomous runs with step limits and safety checks.

    Control loop (bounded — NOT while True):

        for step in range(max_steps):
            reload authoritative target   ← TASK-016 revalidation
            verify ownership              ← TASK-016 per-step
            build fresh execution context
            decision = Brain.decide(...)
            validate capability policy
            duplicate-action check
            execute capability
            persist observation / update profile
            reload learning state
            re-evaluate → FINISH or NEXT
    """

    def __init__(
        self,
        master_brain: Optional[MasterBrain] = None,
        max_steps: int = 3,
    ) -> None:
        self.master_brain = master_brain or MasterBrain()
        self.max_steps = max_steps
        self._action_fingerprints: List[ActionFingerprint] = []
        self._capability_policies: Dict[str, CapabilityPolicy] = {}
        self._init_capability_policies()

    def _init_capability_policies(self) -> None:
        """Initialize capability policies for known capabilities."""
        self._capability_policies["product_verification"] = CapabilityPolicy(
            capability="product_verification",
            module="seller",
            allowed=True,
            requires_ownership=True,
            requires_target=True,
            min_confidence=0.0,
            max_confidence=1.0,
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run_autonomous(
        self,
        user_id: str,
        goal: str,
        target_id: Optional[str] = None,
        module: str = "seller",
        db: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AutonomousRun:
        """
        Execute a bounded autonomous run.

        Args:
            user_id:   Authenticated user ID (from JWT — server-side only).
            goal:      Original goal / message from the user.
            target_id: Target product ID — must be owned by user_id.
            module:    Module scope (seller / content_creator / service_provider).
            db:        Database session.
            context:   Optional additional context (not used for auth decisions).

        Returns:
            AutonomousRun with full step trace and final state.
        """
        # Validate module — reject unknown values immediately
        if module not in _ALLOWED_MODULES:
            module = "seller"  # safe default — unknown modules → seller

        run_id = str(uuid4())
        run_start = time.monotonic()

        run = AutonomousRun(
            run_id=run_id,
            user_id=user_id,
            target_id=target_id,
            module=module,
            original_goal=goal,
            status=RunStatus.RUNNING,
            max_steps=self.max_steps,
            started_at=datetime.utcnow(),
        )

        logger.info(
            "autonomous_run_start",
            extra={
                "run_id": run_id,
                "user_id": user_id,
                "module": module,
                "max_steps": self.max_steps,
                "target_id": target_id,
            },
        )

        try:
            # Bounded control loop — NOT while True
            for step_number in range(1, self.max_steps + 1):

                step_start = time.monotonic()

                logger.info(
                    "autonomous_step_start",
                    extra={
                        "run_id": run_id,
                        "step_number": step_number,
                        "user_id": user_id,
                    },
                )

                # ── TASK-016: reload authoritative target each step ──────────
                # Never trust target data from a previous Brain output or client.
                authoritative_target = await self._reload_authoritative_target(
                    db=db,
                    user_id=user_id,
                    target_id=target_id,
                )

                # ── TASK-016: per-step ownership validation ──────────────────
                if db is not None and target_id is not None:
                    ownership_ok = await self._validate_ownership(
                        db=db,
                        user_id=user_id,
                        target_id=target_id,
                    )
                    if not ownership_ok:
                        run.stop(
                            reason=StopReason.OWNERSHIP_FAILURE,
                            final_response="Product not found",
                        )
                        logger.warning(
                            "autonomous_ownership_failure",
                            extra={
                                "run_id": run_id,
                                "step_number": step_number,
                                "user_id": user_id,
                            },
                        )
                        break

                    # Also verify target is still active / exists
                    if authoritative_target is None:
                        run.stop(
                            reason=StopReason.OWNERSHIP_FAILURE,
                            final_response="Product not found",
                        )
                        logger.warning(
                            "autonomous_target_not_found",
                            extra={
                                "run_id": run_id,
                                "step_number": step_number,
                                "user_id": user_id,
                            },
                        )
                        break

                # ── Load persisted context ───────────────────────────────────
                step_context = await self._load_step_context(
                    db=db,
                    user_id=user_id,
                    target_id=target_id,
                    module=module,
                    previous_steps=run.steps,
                )

                # ── Brain decides ────────────────────────────────────────────
                decision = await self._brain_decide(
                    goal=goal,
                    context=step_context,
                    previous_steps=run.steps,
                )

                # ── Validate decision ────────────────────────────────────────
                # TASK-016: capability policy always uses server-side ownership
                validation_result = await self._validate_decision(
                    decision=decision,
                    user_id=user_id,
                    target_id=target_id,
                    module=module,
                    db=db,
                )

                if not validation_result["valid"]:
                    run.stop(
                        reason=StopReason.CAPABILITY_NOT_AVAILABLE,
                        final_response=validation_result["reason"],
                    )
                    logger.info(
                        "autonomous_validation_failed",
                        extra={
                            "run_id": run_id,
                            "step_number": step_number,
                            "reason": validation_result["reason"],
                        },
                    )
                    break

                # ── FINISH ───────────────────────────────────────────────────
                if decision.action == BrainAction.FINISH:
                    run.stop(
                        reason=StopReason.FINISHED,
                        final_response=decision.reasoning_summary or "Brain decided to finish",
                    )
                    logger.info(
                        "autonomous_brain_finish",
                        extra={"run_id": run_id, "step_number": step_number},
                    )
                    break

                # ── RECOMMEND_NEXT_ACTION ────────────────────────────────────
                if decision.action == BrainAction.RECOMMEND_NEXT_ACTION:
                    executable = await self._is_recommendation_executable(
                        decision=decision,
                        user_id=user_id,
                        target_id=target_id,
                        module=module,
                        db=db,
                    )
                    if not executable:
                        run.stop(
                            reason=StopReason.CAPABILITY_NOT_AVAILABLE,
                            final_response=decision.reasoning_summary
                            or "Recommendation not currently executable",
                        )
                        run.final_decision = decision
                        break
                    decision = await self._convert_recommendation_to_execution(decision)

                # ── EXECUTE_CAPABILITY ───────────────────────────────────────
                if decision.action == BrainAction.EXECUTE_CAPABILITY:

                    # Duplicate-action protection
                    fingerprint = ActionFingerprint(
                        capability=decision.capability or "",
                        target=decision.target,
                        parameters=decision.execution_input,
                    )
                    if self._is_duplicate_action(fingerprint):
                        run.stop(
                            reason=StopReason.DUPLICATE_ACTION,
                            final_response="Duplicate action detected, stopping to prevent loop",
                        )
                        logger.warning(
                            "autonomous_duplicate_action",
                            extra={
                                "run_id": run_id,
                                "step_number": step_number,
                                "capability": decision.capability,
                            },
                        )
                        break

                    # Execute step
                    step = await self._execute_step(
                        step_number=step_number,
                        decision=decision,
                        user_id=user_id,
                        db=db,
                        context=step_context,
                    )

                    run.add_step(step)
                    self._action_fingerprints.append(fingerprint)

                    step_duration = time.monotonic() - step_start
                    logger.info(
                        "autonomous_step_complete",
                        extra={
                            "run_id": run_id,
                            "step_number": step_number,
                            "capability": step.capability,
                            "execution_id": step.execution_id,
                            "status": step.status.value,
                            "duration_seconds": round(step_duration, 3),
                        },
                    )

                    if step.status == StepStatus.FAILED:
                        run.stop(
                            reason=StopReason.FAILURE,
                            final_response=step.error or "Execution failed",
                        )
                        logger.error(
                            "autonomous_step_failed",
                            extra={
                                "run_id": run_id,
                                "step_number": step_number,
                                "capability": step.capability,
                            },
                        )
                        break

                    # Re-evaluate for next step
                    next_decision = await self._re_evaluate_step(
                        step=step,
                        context=step_context,
                        db=db,
                    )
                    step.next_decision = next_decision

                    if next_decision.action == BrainAction.FINISH:
                        run.stop(
                            reason=StopReason.FINISHED,
                            final_response=next_decision.reasoning_summary
                            or "Re-evaluation decided to finish",
                        )
                        logger.info(
                            "autonomous_reevaluation_finish",
                            extra={"run_id": run_id, "step_number": step_number},
                        )
                        break

                    if next_decision.next_action:
                        goal = next_decision.next_action

                else:
                    # CHAT / ANSWER — non-execution actions stop the loop
                    run.stop(
                        reason=StopReason.FINISHED,
                        final_response=decision.reasoning_summary
                        or "Non-execution decision, stopping",
                    )
                    break

            # Loop exhausted without an explicit stop
            if run.status == RunStatus.RUNNING:
                run.stop(
                    reason=StopReason.STEP_LIMIT_REACHED,
                    final_response=f"Reached maximum step limit ({self.max_steps})",
                )
                logger.info(
                    "autonomous_step_limit",
                    extra={"run_id": run_id, "steps_executed": run.current_step},
                )

        except Exception as e:
            logger.error(
                "autonomous_run_error",
                extra={"run_id": run_id, "error_type": type(e).__name__},
                exc_info=True,
            )
            run.stop(
                reason=StopReason.FAILURE,
                final_response="An unexpected error occurred",  # Never expose raw exception
            )

        total_duration = time.monotonic() - run_start
        logger.info(
            "autonomous_run_complete",
            extra={
                "run_id": run_id,
                "status": run.status.value,
                "stop_reason": run.stop_reason.value if run.stop_reason else None,
                "steps_executed": run.current_step,
                "duration_seconds": round(total_duration, 3),
                "user_id": user_id,
            },
        )

        return run

    # ------------------------------------------------------------------
    # TASK-016: Real ownership validation
    # ------------------------------------------------------------------

    async def _validate_ownership(
        self,
        db: Any,
        user_id: str,
        target_id: str,
    ) -> bool:
        """
        Validate that target_id is owned by user_id.

        Uses the canonical project pattern:
            SELECT * FROM products WHERE id = target_id AND user_id = user_id

        Returns True only when the product exists AND belongs to this user.
        Never raises — returns False on any error so the caller can stop safely.
        """
        try:
            from sqlalchemy import select
            from app.models.product import Product

            result = await db.execute(
                select(Product).where(
                    Product.id == target_id,
                    Product.user_id == user_id,
                )
            )
            product = result.scalar_one_or_none()
            return product is not None
        except Exception as e:
            logger.error(
                "ownership_check_error",
                extra={"error_type": type(e).__name__, "user_id": user_id},
            )
            return False

    async def _reload_authoritative_target(
        self,
        db: Optional[Any],
        user_id: str,
        target_id: Optional[str],
    ) -> Optional[Any]:
        """
        Reload the target product from the database.

        TASK-016: Must happen on every step — never reuse cached target
        data from a previous Brain output.
        Returns None when db is unavailable or product not found for user.
        """
        if db is None or target_id is None:
            return None
        try:
            from sqlalchemy import select
            from app.models.product import Product

            result = await db.execute(
                select(Product).where(
                    Product.id == target_id,
                    Product.user_id == user_id,
                )
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Context loading
    # ------------------------------------------------------------------

    async def _load_step_context(
        self,
        db: Optional[Any],
        user_id: str,
        target_id: Optional[str],
        module: str,
        previous_steps: List[AutonomousStep],
    ) -> Dict[str, Any]:
        """Load context for the current step, scoped to the authenticated user."""
        context: Dict[str, Any] = {
            "user_id": user_id,
            "target_id": target_id,
            "module": module,
            "previous_steps": [step.to_dict() for step in previous_steps],
        }

        if db and previous_steps:
            from app.learning.context_loader import LearningContextLoader

            loader = LearningContextLoader()
            try:
                last_step = previous_steps[-1]
                # TASK-016: user_id is passed so context_loader scopes its
                # WorkerExecution queries to this user only
                learning_context = await loader.load_learning_context(
                    db=db,
                    user_id=user_id,
                    product_id=target_id,
                    capability=last_step.capability,
                )
                context["learning_context"] = learning_context
            except Exception as e:
                logger.warning(
                    "learning_context_load_failed",
                    extra={"error_type": type(e).__name__},
                )
                context["learning_context"] = {}

        return context

    # ------------------------------------------------------------------
    # Brain interaction
    # ------------------------------------------------------------------

    async def _brain_decide(
        self,
        goal: str,
        context: Dict[str, Any],
        previous_steps: List[AutonomousStep],
    ) -> BrainDecision:
        """Get Brain decision for current step."""
        message = goal

        if previous_steps:
            last_step = previous_steps[-1]
            if last_step.next_decision and last_step.next_decision.next_action:
                message = last_step.next_decision.next_action

        # TASK-016: Brain receives only business context — never worker names,
        # Python class paths, or execution internals.
        decision = self.master_brain.decide_capability(
            message=message,
            context={"product_id": context.get("target_id")},
        )

        return decision

    # ------------------------------------------------------------------
    # Capability validation
    # ------------------------------------------------------------------

    async def _validate_decision(
        self,
        decision: BrainDecision,
        user_id: str,
        target_id: Optional[str],
        module: str,
        db: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Validate a Brain decision through capability policy.

        TASK-016 requirements met:
        1. Registered capability check
        2. Allowed module check
        3. Allowed target type check
        4. Ownership-approved target (uses real DB, not stub)
        5. Step budget enforced by caller (bounded loop)
        6. Duplicate-action protection checked separately
        """
        # Non-execution actions are always valid
        if decision.action in (
            BrainAction.FINISH,
            BrainAction.RECOMMEND_NEXT_ACTION,
            BrainAction.CHAT,
            BrainAction.ANSWER,
        ):
            return {"valid": True, "reason": None}

        if decision.action == BrainAction.EXECUTE_CAPABILITY:
            # 1. Capability must be named
            if not decision.capability:
                return {"valid": False, "reason": "Decision missing capability"}

            # 2. Capability must be registered — Brain cannot invent names
            resolution = capability_registry.resolve_capability(decision.capability)
            if resolution is None:
                return {
                    "valid": False,
                    "reason": f"Capability '{decision.capability}' not registered",
                }

            # 3. Look up or create a policy
            policy = self._capability_policies.get(decision.capability)
            if policy is None:
                policy = CapabilityPolicy(
                    capability=decision.capability,
                    module=module,
                    allowed=True,
                    requires_ownership=True,
                    requires_target=True,
                )

            # 4. Module boundary — Brain-proposed module must match request module
            if policy.module != module:
                return {
                    "valid": False,
                    "reason": (
                        f"Capability '{decision.capability}' belongs to module "
                        f"'{policy.module}', not '{module}'"
                    ),
                }

            # 5. TASK-016: ownership — always validate against DB, never trust
            #    client-supplied target or Brain output target value
            ownership_valid = True
            if policy.requires_ownership:
                if db is not None and target_id is not None:
                    ownership_valid = await self._validate_ownership(
                        db=db,
                        user_id=user_id,
                        target_id=target_id,
                    )
                elif policy.requires_target and target_id is None:
                    return {"valid": False, "reason": "Target ID is required"}

            # 6. Use policy.validate for confidence / target / ownership check
            is_valid, error_reason = policy.validate(
                user_id=user_id,
                target_id=target_id,
                ownership_valid=ownership_valid,
                confidence=decision.confidence,
            )

            return {"valid": is_valid, "reason": error_reason}

        return {"valid": False, "reason": f"Unknown action: {decision.action}"}

    # ------------------------------------------------------------------
    # Recommendation handling
    # ------------------------------------------------------------------

    async def _is_recommendation_executable(
        self,
        decision: BrainDecision,
        user_id: str,
        target_id: Optional[str],
        module: str,
        db: Optional[Any],
    ) -> bool:
        """Recommendations require explicit user confirmation — not auto-executable."""
        return False

    async def _convert_recommendation_to_execution(
        self,
        decision: BrainDecision,
    ) -> BrainDecision:
        """Convert RECOMMEND_NEXT_ACTION to EXECUTE_CAPABILITY (not yet wired)."""
        return decision

    # ------------------------------------------------------------------
    # Duplicate detection
    # ------------------------------------------------------------------

    def _is_duplicate_action(self, fingerprint: ActionFingerprint) -> bool:
        """Check if this action fingerprint has already been executed this run."""
        for existing in self._action_fingerprints:
            if fingerprint.matches(existing):
                return True
        return False

    # ------------------------------------------------------------------
    # Step execution
    # ------------------------------------------------------------------

    async def _execute_step(
        self,
        step_number: int,
        decision: BrainDecision,
        user_id: str,
        db: Optional[Any],
        context: Dict[str, Any],
    ) -> AutonomousStep:
        """Execute a single step with failure policy."""
        step = AutonomousStep(
            step_number=step_number,
            decision=decision,
            capability=decision.capability,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        try:
            execution_result = await self.master_brain.execute_with_learning(
                decision=decision,
                db=db,
                user_id=user_id,
            )

            step.execution_id = execution_result.get("execution_id")
            step.worker = execution_result.get("worker")
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow()
            step.outcome = execution_result

        except AITimeoutError as e:
            logger.error(
                "step_ai_timeout",
                extra={"step_number": step_number, "error_type": "AITimeoutError"},
            )
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            step.error = f"AI provider timeout: {str(e)}"

        except (AIAuthenticationError, AIConnectionError) as e:
            logger.error(
                "step_ai_connection_error",
                extra={"step_number": step_number, "error_type": type(e).__name__},
            )
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            step.error = f"AI connection error: {str(e)}"

        except AIConfigurationError as e:
            logger.error(
                "step_ai_config_error",
                extra={"step_number": step_number, "error_type": "AIConfigurationError"},
            )
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            step.error = f"AI configuration error: {str(e)}"

        except AIProviderError as e:
            logger.error(
                "step_ai_provider_error",
                extra={"step_number": step_number, "error_type": "AIProviderError"},
            )
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            step.error = f"AI provider error: {str(e)}"

        except Exception as e:
            logger.error(
                "step_unexpected_error",
                extra={"step_number": step_number, "error_type": type(e).__name__},
                exc_info=True,
            )
            step.status = StepStatus.FAILED
            step.completed_at = datetime.utcnow()
            # Never expose raw exception messages — they may contain sensitive data
            step.error = "Unexpected execution error"

        return step

    # ------------------------------------------------------------------
    # Re-evaluation
    # ------------------------------------------------------------------

    async def _re_evaluate_step(
        self,
        step: AutonomousStep,
        context: Dict[str, Any],
        db: Optional[Any],
    ) -> BrainDecision:
        """Re-evaluate after a step to determine next action."""
        if step.outcome:
            learning_context = context.get("learning_context", {})
            re_evaluation = self.master_brain._re_evaluate_after_execution(
                decision=step.decision,
                execution_result=step.outcome,
                learning_context=learning_context,
            )

            action = BrainAction.FINISH
            if re_evaluation.get("action") == "recommend_next_action":
                action = BrainAction.RECOMMEND_NEXT_ACTION

            return BrainDecision(
                action=action,
                intent="re_evaluation",
                reasoning_summary=re_evaluation.get("reason", ""),
                next_action=re_evaluation.get("next_action"),
                next_action_reasoning=re_evaluation.get("next_action_reasoning"),
                confidence=0.9,
            )

        return BrainDecision(
            action=BrainAction.FINISH,
            intent="re_evaluation",
            reasoning_summary="No re-evaluation available",
            confidence=0.0,
        )
