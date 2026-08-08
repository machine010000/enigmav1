from __future__ import annotations

import os
from typing import Any, Dict, Optional

from app.ai.providers import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self) -> None:
        from app.config import get_settings

        settings = get_settings()
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", settings.AI_MODEL)

    def _build_messages(self, system: str, user: str):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        return messages

    async def generate(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[dict] = None,
    ) -> Dict[str, Any]:
        import httpx

        messages = self._build_messages(system, user)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["num_predict"] = max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            return {
                "choices": [
                    {"message": {"role": "assistant", "content": content}},
                ],
            }

    async def classify(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        return await self.generate(system, user, temperature=temperature, max_tokens=max_tokens)

    async def extract(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        return await self.generate(system, user, temperature=temperature, max_tokens=max_tokens)


__all__ = ["OllamaProvider"]
