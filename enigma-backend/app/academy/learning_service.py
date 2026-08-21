"""AI-backed Academy learning material using ENIGMA's shared gateway/governance."""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.academy.academy_manager import AcademyManager
from app.academy.academy_models import AcademyModule, KnowledgeArticle
from app.ai.gateway import gateway as default_gateway
from app.knowledge_governance import knowledge_governance_service


@dataclass(frozen=True)
class AcademyLearningMaterial:
    topic: str
    capability_gap: Optional[str]
    knowledge_summary: str
    execution_checklist: List[str] = field(default_factory=list)
    risks_common_mistakes: List[str] = field(default_factory=list)
    recommended_skills_tools: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    knowledge_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


class AcademyLearningService:
    def __init__(self, ai_gateway: Optional[Any] = None, governance: Optional[Any] = None) -> None:
        self.gateway = ai_gateway or default_gateway
        self.governance = governance or knowledge_governance_service
        self.manager = AcademyManager()

    async def learn(self, *, topic: str, task: str = "", capability_gap: Optional[str] = None,
                    store: bool = True) -> AcademyLearningMaterial:
        if not topic or not topic.strip():
            raise ValueError("topic is required")
        response = await self.gateway.generate(
            system=(
                "Create concise, operational training material. Do not invent sources. Return JSON: "
                "knowledge_summary, execution_checklist, risks_common_mistakes, "
                "recommended_skills_tools, sources, confidence."
            ),
            user=json.dumps({"topic": topic, "task": task, "capability_gap": capability_gap}),
            temperature=0.2,
            max_tokens=1400,
            response_format={"type": "json_object"},
        )
        data = self._parse(response)
        material = AcademyLearningMaterial(
            topic=topic.strip(), capability_gap=capability_gap,
            knowledge_summary=str(data.get("knowledge_summary") or "").strip(),
            execution_checklist=self._strings(data.get("execution_checklist")),
            risks_common_mistakes=self._strings(data.get("risks_common_mistakes")),
            recommended_skills_tools=self._strings(data.get("recommended_skills_tools")),
            sources=self._strings(data.get("sources")), confidence=self._confidence(data.get("confidence")),
        )
        if not material.knowledge_summary:
            raise ValueError("Academy response omitted knowledge_summary")
        if store:
            governed = self.governance.submit_candidate(self._candidate(material), actor="academy_learning_service")
            material = AcademyLearningMaterial(**{**material.to_dict(), "knowledge_id": governed.concept.id})
        return material

    def _candidate(self, material: AcademyLearningMaterial):
        article = KnowledgeArticle(
            id=str(uuid.uuid4()), module="academy_generated", title=material.topic,
            content=material.knowledge_summary + "\n" + "\n".join(material.execution_checklist),
            summary=material.knowledge_summary, keywords=[material.topic] + ([material.capability_gap] if material.capability_gap else []),
            references=material.sources, evidence=material.sources, confidence=material.confidence,
        )
        module = AcademyModule(
            id=str(uuid.uuid4()), name=f"Academy: {material.topic}", version="1.0",
            description=material.knowledge_summary, topics=[material.topic],
            capabilities=[material.capability_gap] if material.capability_gap else [], confidence=material.confidence,
            articles=[article], source_count=1,
        )
        return self.manager.module_to_candidate_knowledge(module)

    @staticmethod
    def _parse(response: Any) -> Dict[str, Any]:
        if isinstance(response, dict) and "knowledge_summary" in response:
            return response
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "") if isinstance(response, dict) else ""
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(content).strip(), flags=re.I)
        try:
            parsed = json.loads(content)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Academy AI response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Academy AI response must be a JSON object")
        return parsed

    @staticmethod
    def _strings(value: Any) -> List[str]:
        return [str(item).strip() for item in value] if isinstance(value, list) else []

    @staticmethod
    def _confidence(value: Any) -> float:
        try: return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError): return 0.0
