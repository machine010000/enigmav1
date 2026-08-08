import asyncio

from app.ai.master_brain import master_brain
from app.intelligence import ReasoningSession
from app.memory.memory_engine import MemoryEngine
from app.memory.models import Episode
from app.workers.product_verification import ProductVerificationWorker
from app.engine.contracts import ExecutionContext, WorkerResult, WorkerStatus


def _serialize_episode(episode):
    if hasattr(episode, "to_dict"):
        return episode.to_dict()
    return {
        "id": getattr(episode, "id", None),
        "execution_id": getattr(episode, "execution_id", None),
        "decision_id": getattr(episode, "decision_id", None),
        "product_id": getattr(episode, "product_id", None),
        "worker": getattr(episode, "worker", None),
        "goal": getattr(episode, "goal", None),
        "inputs": getattr(episode, "inputs", {}),
        "outputs": getattr(episode, "outputs", {}),
        "evidence": getattr(episode, "evidence", []),
        "confidence": getattr(episode, "confidence", 0.0),
        "execution_time": getattr(episode, "execution_time", 0.0),
        "llm_calls": getattr(episode, "llm_calls", 0),
        "success": getattr(episode, "success", False),
    }


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None


class FakeGateway:
    async def chat(self, *args, **kwargs):
        return {"choices": [{"message": {"content": "chat"}}]}


async def _fake_worker_run(memory_engine: MemoryEngine):
    context = ExecutionContext(
        execution_id="exec-123",
        product={"id": "product-1", "name": "Nike Air Max 270"},
        memory={"decision_id": "decision-1"},
        memory_engine=memory_engine,
    )
    worker = ProductVerificationWorker()
    result = await worker.run(context)
    return result


def test_memory_flow_from_product_to_episode_and_decision_context():
    memory_engine = MemoryEngine()
    master_brain.memory_engine = memory_engine

    result = asyncio.run(_fake_worker_run(memory_engine))
    assert result.status == WorkerStatus.SUCCESS

    remembered = memory_engine.recall(goal="Nike Air Max 270")
    assert len(remembered) == 1

    session = ReasoningSession(
        goal="Verify Nike Air Max 270",
        product={"id": "product-1"},
        memory={
            "episodes": [_serialize_episode(episode) for episode in memory_engine.recall(goal="Nike Air Max 270")],
            "similar_episodes": [_serialize_episode(episode) for episode in memory_engine.find_similar_episodes("Verify Nike Air Max 270")],
        },
    )
    assert session.memory["similar_episodes"] or session.memory["episodes"]
