"""Execution worker exposing Academy learning to the Brain/Engine."""
from __future__ import annotations

from app.academy.learning_service import AcademyLearningService
from app.engine.contracts import ExecutionContext, Worker, WorkerResult, WorkerStatus


class AcademyLearningWorker(Worker):
    name = "academy_learning"
    description = "Build governed learning material for a task or capability gap."
    input_schema = ["topic", "task", "capability_gap", "store"]
    output_schema = ["knowledge_summary", "execution_checklist", "risks_common_mistakes",
                     "recommended_skills_tools", "sources", "confidence", "knowledge_id"]
    capabilities = ["academy_learning"]

    def __init__(self, service=None) -> None:
        self.service = service

    async def run(self, context: ExecutionContext) -> WorkerResult:
        service = self.service or AcademyLearningService()
        topic = context.recall("topic") or context.recall("capability_gap") or ""
        material = await service.learn(
            topic=str(topic), task=str(context.recall("task", "")),
            capability_gap=context.recall("capability_gap"),
            store=bool(context.recall("store", True)),
        )
        result = material.to_dict()
        context.remember("academy_learning_result", result)
        return WorkerResult(
            worker_name=self.name, status=WorkerStatus.SUCCESS, result=result,
            confidence=material.confidence,
            evidence=[{"worker": self.name, "field": "knowledge_summary", "value": material.knowledge_summary,
                       "source": "ai_gateway_then_knowledge_governance", "confidence": material.confidence}],
            llm_calls=1,
        )


academy_learning_worker = AcademyLearningWorker()
