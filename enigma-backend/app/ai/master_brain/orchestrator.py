from typing import Optional, Any

from app.ai.master_brain.events import BrainEvent, BrainEventBus, BrainEventType
from app.ai.master_brain.models import Planner
from app.ai.master_brain.state import MasterBrainStateMachine
from app.core.logging_config import get_logger
from app.engine.decision_engine import DecisionEngine
from app.intelligence import IntelligenceEngine
from app.intelligence.reasoning_session import ReasoningSession
from app.ai.client import AITimeoutError, AIConfigurationError, AIAuthenticationError, AIConnectionError, AIProviderError

logger = get_logger(__name__)


class MasterBrain:
    def __init__(
        self,
        planner: Optional[Planner] = None,
        intelligence_engine: Optional[IntelligenceEngine] = None,
    ) -> None:
        self.state_machine = MasterBrainStateMachine()
        self.event_bus = self.state_machine.event_bus
        self.planner = planner
        self.intelligence_engine = intelligence_engine
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


master_brain = MasterBrain()
