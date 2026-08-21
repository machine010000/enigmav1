"""AI-assisted creativity on top of the existing deterministic engine."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.gateway import gateway as default_gateway


@dataclass(frozen=True)
class CreativeTaskResult:
    ideas: List[Dict[str, Any]] = field(default_factory=list)
    alternative_approaches: List[str] = field(default_factory=list)
    proposal_angles: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    confidence: float = 0.0
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ideas": self.ideas,
            "alternative_approaches": self.alternative_approaches,
            "proposal_angles": self.proposal_angles,
            "risks": self.risks,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


class CreativityAIService:
    def __init__(self, ai_gateway: Optional[Any] = None) -> None:
        self.gateway = ai_gateway or default_gateway

    async def generate(self, *, task: str, project_context: Dict[str, Any]) -> CreativeTaskResult:
        if not task or not task.strip():
            raise ValueError("task is required")
        response = await self.gateway.generate(
            system=(
                "Generate practical creative options grounded only in the supplied context. "
                "Return JSON with ideas (objects with title, approach, benefit), "
                "alternative_approaches, proposal_angles, risks, confidence, and rationale."
            ),
            user=json.dumps({"task": task, "project_context": project_context}, default=str),
            temperature=0.7,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        payload = self._parse_response(response)
        return CreativeTaskResult(
            ideas=self._dict_list(payload.get("ideas")),
            alternative_approaches=self._string_list(payload.get("alternative_approaches")),
            proposal_angles=self._string_list(payload.get("proposal_angles")),
            risks=self._string_list(payload.get("risks")),
            confidence=self._confidence(payload.get("confidence")),
            rationale=str(payload.get("rationale") or "").strip(),
        )

    @staticmethod
    def _parse_response(response: Any) -> Dict[str, Any]:
        if isinstance(response, dict) and isinstance(response.get("ideas"), list):
            return response
        content = ""
        if isinstance(response, dict):
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(content).strip(), flags=re.I)
        try:
            parsed = json.loads(content)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("AI creativity response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("AI creativity response must be a JSON object")
        return parsed

    @staticmethod
    def _string_list(value: Any) -> List[str]:
        return [str(item).strip() for item in value] if isinstance(value, list) else []

    @staticmethod
    def _dict_list(value: Any) -> List[Dict[str, Any]]:
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0
