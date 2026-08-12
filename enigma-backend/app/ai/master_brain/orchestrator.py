from typing import Optional, Any, Dict

from app.ai.master_brain.events import BrainEvent, BrainEventBus, BrainEventType
from app.ai.master_brain.models import Planner, BrainDecision, BrainAction
from app.ai.master_brain.state import MasterBrainStateMachine
from app.core.logging_config import get_logger
from app.engine.decision_engine import DecisionEngine
from app.engine.capabilities import capability_registry
from app.engine.engine import engine
from app.engine.context_builder import build_context
from app.engine.contracts import WorkerResult
from app.intelligence import IntelligenceEngine
from app.intelligence.reasoning_session import ReasoningSession
from app.ai.client import AITimeoutError, AIConfigurationError, AIAuthenticationError, AIConnectionError, AIProviderError
from app.learning.observation import ExecutionObservation
from app.learning.mapper import EvidenceMapper
from app.learning.profile_updater import ProfileUpdater
from app.learning.context_loader import LearningContextLoader

logger = get_logger(__name__)


class MasterBrain:
    def __init__(
        self,
        planner: Optional[Planner] = None,
        intelligence_engine: Optional[IntelligenceEngine] = None,
    ) -> None:
        self.planner = planner
        self.intelligence_engine = intelligence_engine
        self.evidence_mapper = EvidenceMapper()
        self.profile_updater = ProfileUpdater()
        self.context_loader = LearningContextLoader()
        self._processed_executions = set()  # For idempotency
        self.state_machine = MasterBrainStateMachine()
        self.event_bus = self.state_machine.event_bus
        self.decision_engine: Optional[DecisionEngine] = None
        self.memory_engine = None

    async def decide(self, db, goal: str, context: Optional[Any] = None, constraints: Optional[list[str]] = None, session: Optional[ReasoningSession] = None) -> dict:
        reasoning_session = session
        if reasoning_session is None and isinstance(context, ReasoningSession):
            reasoning_session = context
        if reasoning_session is None and self.intelligence_engine is not None:
            if isinstance(context, dict):
                reasoning_session = self.intelligence_engine.build_reasoning_session(
                    goal=goal,
                    user=context.get("user"),
                    business=context.get("business"),
                    product=context.get("product"),
                    academy=context.get("academy"),
                    memory=context.get("memory"),
                    knowledge=context.get("knowledge"),
                    research=context.get("research"),
                    constraints=constraints,
                    preferences=context.get("preferences"),
                )
            else:
                reasoning_session = self.intelligence_engine.build_reasoning_session(goal=goal)

        if self.decision_engine is None:
            self.decision_engine = DecisionEngine(planner=self.planner)

        return await self.decision_engine.create_decision(db, goal=goal, context=reasoning_session, constraints=constraints)

    def reason(self, session: ReasoningSession) -> ReasoningSession:
        return session

    def build_execution_plan(self, session: ReasoningSession) -> dict:
        if self.planner is None:
            raise ValueError("Planner is not configured")
        plan = self.planner.build_execution_plan(session)
        self.state_machine.handle_event(BrainEventType.PLAN_CREATED, payload={"goal": getattr(session, "goal", None)})
        return plan

    def recall_memory(self, session: ReasoningSession) -> ReasoningSession:
        self.state_machine.handle_event(BrainEventType.MEMORY_RECALLED, payload={"goal": getattr(session, "goal", None)})
        return session

    def read_academy(self, topic: str) -> dict:
        self.state_machine.handle_event(BrainEventType.ACADEMY_READ, payload={"topic": topic})
        return {"topic": topic}

    def read_knowledge(self, session: ReasoningSession) -> ReasoningSession:
        self.state_machine.handle_event(BrainEventType.KNOWLEDGE_READ, payload={"goal": getattr(session, "goal", None)})
        return session

    def transition(self) -> None:
        self.state_machine.advance()

    async def chat(self, db, user_id: str, message: str) -> dict:
        """
        Chat with the master brain - generate AI response.
        
        Args:
            db: Database session
            user_id: User ID
            message: User message
            
        Returns:
            Dict with reply, intent, and knowledge_used
        """
        from app.ai.gateway import gateway
        
        # Generate AI response using the gateway
        messages = [
            {"role": "system", "content": "You are ENIGMA, an AI business brain assistant. Help users with business decisions, strategy, and growth."},
            {"role": "user", "content": message}
        ]
        
        try:
            response = await gateway.chat(messages, temperature=0.7, max_tokens=1000)
            
            # Extract the reply from OpenAI-compatible response
            reply = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Simple intent detection (can be enhanced)
            intent = "general"
            if "strategy" in message.lower() or "plan" in message.lower():
                intent = "strategic_planning"
            elif "market" in message.lower() or "competitor" in message.lower():
                intent = "market_analysis"
            elif "product" in message.lower():
                intent = "product_guidance"
            
            return {
                "reply": reply,
                "intent": intent,
                "knowledge_used": []
            }
        except (AITimeoutError, AIConfigurationError, AIAuthenticationError, AIConnectionError, AIProviderError):
            # Re-raise typed AI errors to allow router to map to appropriate HTTP status codes
            raise
        except Exception as e:
            # Log unexpected exceptions server-side (without exposing secrets)
            logger.error(f"Unexpected AI provider error in master_brain.chat: {type(e).__name__}", exc_info=True)
            
            # Re-raise as generic provider error for consistent handling
            raise AIProviderError(f"Unexpected AI provider error") from e

    def decide_capability(self, message: str, context: Optional[Dict[str, Any]] = None) -> BrainDecision:
        """
        Decide whether a capability execution is required based on message and context.
        
        This is a simplified Seller-focused decision boundary for TASK-013.
        Future versions will use AI-driven decision making.
        
        Args:
            message: User message
            context: Optional context (product_id, etc.)
            
        Returns:
            BrainDecision with action, capability, and execution details
        """
        message_lower = message.lower()
        
        # Check for Seller/product verification requests
        if "verify" in message_lower and "product" in message_lower:
            product_id = context.get("product_id") if context else None
            
            # Validate the capability exists
            resolution = capability_registry.resolve_capability("product_verification")
            if resolution is None:
                return BrainDecision(
                    action=BrainAction.ANSWER,
                    intent="product_guidance",
                    reasoning_summary="Product verification capability not available.",
                    execution_required=False,
                    confidence=0.0,
                )
            
            return BrainDecision(
                action=BrainAction.EXECUTE_CAPABILITY,
                intent="product_verification",
                capability="product_verification",
                target=product_id,
                reasoning_summary="Product verification is required to validate the product before recommending next actions.",
                execution_required=True,
                execution_input={"product_id": product_id} if product_id else {},
                confidence=0.9,
            )
        
        # Default to conversational response
        return BrainDecision(
            action=BrainAction.CHAT,
            intent="general",
            reasoning_summary="No capability execution required for this request.",
            execution_required=False,
            confidence=0.0,
        )

    async def execute_decision(
        self,
        decision: BrainDecision,
        db: Optional[Any] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a BrainDecision through the Engine.
        
        This implements the Brain → Engine handoff for TASK-013.
        
        Args:
            decision: BrainDecision with execution_required=True
            db: Database session for context building and persistence
            user_id: User ID for context building
            
        Returns:
            Dict with execution result and metadata
        """
        if not decision.execution_required:
            return {
                "status": "skipped",
                "reason": "Decision does not require execution",
                "decision": decision.to_dict(),
            }
        
        if not decision.capability:
            return {
                "status": "failed",
                "reason": "Decision missing capability",
                "decision": decision.to_dict(),
            }
        
        # Resolve capability to worker
        resolution = capability_registry.resolve_capability(decision.capability)
        if resolution is None:
            return {
                "status": "failed",
                "reason": f"Capability '{decision.capability}' not registered",
                "decision": decision.to_dict(),
            }
        
        worker_name = resolution["worker_name"]
        
        # Build authoritative context from server-side data
        # Server-side target takes precedence over client-provided execution_input
        product_id = decision.target or decision.execution_input.get("product_id")
        context = await build_context(
            db=db,
            user_id=user_id,
            product_id=product_id,
            extra_memory=decision.execution_input,
        )
        
        # Execute via Engine
        try:
            result: WorkerResult = await engine.execute(
                worker_name=worker_name,
                context=context,
                save=True,
                db=db,
                user_id=user_id,  # TASK-016: store ownership on execution record
            )
            
            return {
                "status": "completed",
                "execution_id": context.execution_id,
                "worker_name": worker_name,
                "capability": decision.capability,
                "result": result.to_dict(),
                "decision": decision.to_dict(),
            }
        except Exception as e:
            logger.error(f"Execution failed for worker {worker_name}: {type(e).__name__}", exc_info=True)
            return {
                "status": "failed",
                "reason": "Execution failed",  # Never expose raw exception text
                "worker_name": worker_name,
                "capability": decision.capability,
                "decision": decision.to_dict(),
            }

    def evaluate_execution_result(self, execution_result: Dict[str, Any], decision: BrainDecision) -> Dict[str, Any]:
        """
        Evaluate an execution result and produce a user-facing response.
        
        This implements the Result → Brain evaluation for TASK-013.
        
        Args:
            execution_result: Result from execute_decision
            decision: Original BrainDecision
            
        Returns:
            Dict with reply, intent, and execution metadata
        """
        if execution_result["status"] == "skipped":
            return {
                "reply": decision.reasoning_summary or "No execution was required for this request.",
                "intent": decision.intent,
                "execution": None,
            }
        
        if execution_result["status"] == "failed":
            error_reason = execution_result.get("reason", "Unknown error")
            return {
                "reply": f"Execution failed: {error_reason}. Please try again or contact support if the issue persists.",
                "intent": decision.intent,
                "execution": {
                    "status": "failed",
                    "capability": decision.capability,
                    "reason": error_reason,
                },
            }
        
        # Successful execution - evaluate result
        result_data = execution_result.get("result", {})
        worker_name = execution_result.get("worker_name")
        capability = execution_result.get("capability")
        
        # Build user-facing response based on capability
        if capability == "product_verification":
            verified_name = result_data.get("result", {}).get("verified_name", "Unknown")
            category = result_data.get("result", {}).get("category", "Unknown")
            confidence = result_data.get("confidence", 0.0)
            issues = result_data.get("result", {}).get("issues", [])
            
            if confidence >= 0.8:
                reply = f"Product verification completed successfully. Verified name: '{verified_name}', Category: '{category}' with {confidence:.0%} confidence."
                if issues:
                    reply += f" Issues found: {', '.join(issues)}."
            else:
                reply = f"Product verification completed with lower confidence ({confidence:.0%}). Verified name: '{verified_name}', Category: '{category}'. Manual review recommended."
                if issues:
                    reply += f" Issues: {', '.join(issues)}."
        else:
            reply = f"Execution completed for {capability}. Status: {result_data.get('status', 'unknown')}."
        
        return {
            "reply": reply,
            "intent": decision.intent,
            "execution": {
                "execution_id": execution_result.get("execution_id"),
                "capability": capability,
                "worker": worker_name,
                "status": execution_result["status"],
                "confidence": result_data.get("confidence", 0.0),
            },
            "result": result_data.get("result", {}),
        }

    async def execute_with_learning(
        self,
        decision: BrainDecision,
        db: Any,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute decision with learning loop integration.
        
        This is the full learning loop:
        1. Execute capability
        2. Create observation
        3. Persist evidence
        4. Update profile
        5. Reload context
        6. Re-evaluate with updated state
        
        Args:
            decision: BrainDecision
            db: Database session
            user_id: User ID
            
        Returns:
            Dict with execution result and learning metadata
        """
        # Step 1: Execute the decision
        execution_result = await self.execute_decision(decision, db, user_id)
        
        # Step 2: Create observation from WorkerResult
        execution_id = execution_result.get("execution_id")
        capability = decision.capability
        worker_name = execution_result.get("worker")
        
        # Check idempotency
        if execution_id in self._processed_executions:
            return {
                **execution_result,
                "learning": {
                    "persisted": False,
                    "reason": "already_processed",
                },
            }
        
        # Create observation
        observation = ExecutionObservation.from_worker_result(
            execution_id=execution_id,
            user_id=user_id,
            capability=capability,
            worker=worker_name,
            worker_result=execution_result,
            target_id=decision.target,
        )
        
        # Step 3: Persist evidence
        try:
            persistence_results = await self.evidence_mapper.persist_observation(observation, db)
        except Exception as e:
            logger.error(f"Evidence persistence failed: {e}")
            return {
                **execution_result,
                "learning": {
                    "persisted": False,
                    "reason": "persistence_failed",
                    "error": str(e),
                },
            }
        
        # Step 4: Update profile
        try:
            profile_updated = await self.profile_updater.update_capability_profile(observation, db)
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            profile_updated = False
        
        # Mark as processed
        self._processed_executions.add(execution_id)
        
        # Step 5: Reload context with learning data
        try:
            learning_context = await self.context_loader.load_learning_context(
                db=db,
                user_id=user_id,
                product_id=decision.target,
                capability=capability,
            )
        except Exception as e:
            logger.error(f"Context reload failed: {e}")
            learning_context = {}
        
        # Step 6: Re-evaluate with updated context
        re_evaluation = self._re_evaluate_after_execution(
            decision=decision,
            execution_result=execution_result,
            learning_context=learning_context,
        )
        
        return {
            **execution_result,
            "learning": {
                "persisted": True,
                "evidence_count": len(observation.evidence),
                "profile_updated": profile_updated,
                "persistence_results": persistence_results,
            },
            "re_evaluation": re_evaluation,
        }
    
    def _re_evaluate_after_execution(
        self,
        decision: BrainDecision,
        execution_result: Dict[str, Any],
        learning_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Re-evaluate after execution with updated learning context.
        
        For TASK-014, this is a simplified re-evaluation:
        - If execution succeeded with high confidence, return FINISH
        - If execution succeeded but suggests next steps, return RECOMMEND_NEXT_ACTION
        - If execution failed, return FINISH with explanation
        
        Args:
            decision: Original BrainDecision
            execution_result: Result from execution
            learning_context: Reloaded learning context
            
        Returns:
            Dict with re-evaluation decision
        """
        status = execution_result.get("status")
        confidence = execution_result.get("confidence", 0.0)
        capability = decision.capability
        
        # Simple re-evaluation logic for Seller flow
        if status == "failed":
            return {
                "action": BrainAction.FINISH.value,
                "reason": "Execution failed, cannot proceed",
                "next_action": None,
            }
        
        # Check capability confidence from learning context
        capability_history = learning_context.get("capability_history", {})
        capability_info = capability_history.get(capability, {})
        readiness = capability_info.get("readiness", 0.0)
        
        # For product_verification, if confidence is high, recommend market analysis
        if capability == "product_verification" and confidence >= 0.8:
            return {
                "action": BrainAction.RECOMMEND_NEXT_ACTION.value,
                "reason": "Product verification completed successfully",
                "next_action": "Research market demand",
                "next_action_reasoning": "Verified product data suggests market analysis would be valuable",
            }
        
        # Default: FINISH
        return {
            "action": BrainAction.FINISH.value,
            "reason": "Execution completed",
            "next_action": None,
        }


master_brain = MasterBrain()
