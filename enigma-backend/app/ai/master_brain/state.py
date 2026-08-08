from enum import Enum, auto

from app.ai.master_brain.events import BrainEvent, BrainEventBus, BrainEventType


class State(Enum):
    RECEIVE_GOAL = auto()
    UNDERSTAND_USER = auto()
    IDENTIFY_SCENARIO = auto()
    GENERATE_JOURNEY = auto()
    RECALL_MEMORY = auto()
    READ_ACADEMY = auto()
    READ_KNOWLEDGE = auto()
    GENERATE_HYPOTHESES = auto()
    GAP_ANALYSIS = auto()
    PLAN_EXECUTION = auto()
    WAIT_FOR_RESULTS = auto()
    UPDATE_DECISION = auto()
    FINISHED = auto()
    FAILED = auto()


class MasterBrainStateMachine:
    def __init__(self) -> None:
        self.current_state = State.RECEIVE_GOAL
        self.event_bus = BrainEventBus()
        self._event_state_order = [
            BrainEventType.GOAL_RECEIVED,
            BrainEventType.USER_UNDERSTOOD,
            BrainEventType.SCENARIO_IDENTIFIED,
            BrainEventType.MEMORY_RECALLED,
            BrainEventType.ACADEMY_READ,
            BrainEventType.KNOWLEDGE_READ,
            BrainEventType.HYPOTHESIS_CREATED,
            BrainEventType.GAPS_FOUND,
            BrainEventType.PLAN_CREATED,
            BrainEventType.WAITING_RESULTS,
            BrainEventType.DECISION_UPDATED,
            BrainEventType.FINISHED,
        ]

    def handle_event(self, event_type: BrainEventType, payload: dict | None = None) -> None:
        if self.current_state == State.FINISHED:
            return

        target_state = self._next_state(event_type)
        current_index = list(State).index(self.current_state)
        target_index = list(State).index(target_state)

        if target_index <= current_index:
            raise ValueError(f"Invalid transition: {self.current_state} -> {event_type}")

        event = BrainEvent(event_type=event_type, payload=payload or {})
        self.event_bus.publish(event)
        self.current_state = target_state

    def advance(self) -> None:
        next_event = self._next_event_for_state(self.current_state)
        if next_event is not None:
            self.handle_event(next_event)

    def _next_event_for_state(self, state: State) -> BrainEventType | None:
        mapping = {
            State.RECEIVE_GOAL: BrainEventType.GOAL_RECEIVED,
            State.UNDERSTAND_USER: BrainEventType.USER_UNDERSTOOD,
            State.IDENTIFY_SCENARIO: BrainEventType.SCENARIO_IDENTIFIED,
            State.GENERATE_JOURNEY: BrainEventType.MEMORY_RECALLED,
            State.RECALL_MEMORY: BrainEventType.ACADEMY_READ,
            State.READ_ACADEMY: BrainEventType.KNOWLEDGE_READ,
            State.READ_KNOWLEDGE: BrainEventType.HYPOTHESIS_CREATED,
            State.GENERATE_HYPOTHESES: BrainEventType.GAPS_FOUND,
            State.GAP_ANALYSIS: BrainEventType.PLAN_CREATED,
            State.PLAN_EXECUTION: BrainEventType.WAITING_RESULTS,
            State.WAIT_FOR_RESULTS: BrainEventType.DECISION_UPDATED,
            State.UPDATE_DECISION: BrainEventType.FINISHED,
        }
        return mapping.get(state)

    def _next_state(self, event_type: BrainEventType) -> State:
        mapping = {
            BrainEventType.GOAL_RECEIVED: State.UNDERSTAND_USER,
            BrainEventType.USER_UNDERSTOOD: State.IDENTIFY_SCENARIO,
            BrainEventType.SCENARIO_IDENTIFIED: State.GENERATE_JOURNEY,
            BrainEventType.MEMORY_RECALLED: State.RECALL_MEMORY,
            BrainEventType.ACADEMY_READ: State.READ_ACADEMY,
            BrainEventType.KNOWLEDGE_READ: State.READ_KNOWLEDGE,
            BrainEventType.HYPOTHESIS_CREATED: State.GENERATE_HYPOTHESES,
            BrainEventType.GAPS_FOUND: State.GAP_ANALYSIS,
            BrainEventType.PLAN_CREATED: State.PLAN_EXECUTION,
            BrainEventType.WAITING_RESULTS: State.WAIT_FOR_RESULTS,
            BrainEventType.DECISION_UPDATED: State.UPDATE_DECISION,
            BrainEventType.FINISHED: State.FINISHED,
        }
        return mapping[event_type]
