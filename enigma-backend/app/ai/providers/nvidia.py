from __future__ import annotations

from typing import Any, Dict, Optional

from app.ai.providers import LLMProvider
from app.ai.client import NVIDIAClient


class NVIDIAProvider(LLMProvider):
    def __init__(self) -> None:
        self._client = NVIDIAClient()

    async def generate(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[dict] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return await self._client.chat(
            messages, temperature, max_tokens, response_format, model
        )

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


__all__ = ["NVIDIAProvider"]
