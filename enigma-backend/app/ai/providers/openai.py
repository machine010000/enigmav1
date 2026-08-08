from __future__ import annotations

import os
from typing import Any, Dict, Optional

from app.ai.providers import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        from app.config import get_settings

        settings = get_settings()
        self.api_key = os.getenv("OPENAI_API_KEY", settings.NVIDIA_API_KEY)
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, system: str, user: str):
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

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
            "max_tokens": max_tokens,
            "stream": False,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

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


__all__ = ["OpenAIProvider"]
