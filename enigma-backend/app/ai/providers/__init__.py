from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[dict] = None,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def classify(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 256,
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def extract(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 512,
    ) -> Dict[str, Any]:
        ...

    async def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[dict] = None,
    ) -> Dict[str, Any]:
        system = ""
        user = ""
        for msg in messages:
            if msg.get("role") == "system":
                system = msg.get("content", "")
            elif msg.get("role") == "user":
                user = msg.get("content", "")
        return await self.generate(
            system, user,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )


def create_provider(name: str) -> LLMProvider:
    name = name.lower()
    if name == "nvidia":
        from app.ai.providers.nvidia import NVIDIAProvider
        return NVIDIAProvider()
    if name == "openai":
        from app.ai.providers.openai import OpenAIProvider
        return OpenAIProvider()
    if name == "ollama":
        from app.ai.providers.ollama import OllamaProvider
        return OllamaProvider()
    if name == "gemini":
        from app.ai.providers.gemini import GeminiProvider
        return GeminiProvider()
    raise ValueError(f"Unknown AI provider: {name}")


__all__ = ["LLMProvider", "create_provider"]
