from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.ai.providers import LLMProvider
from app.ai.providers.nvidia import NVIDIAProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.gemini import GeminiProvider
from app.core.config import get_settings

settings = get_settings()

class LLMGateway:
    def __init__(self) -> None:
        provider_name = settings.AI_PROVIDER.lower()
        self._provider: LLMProvider
        if provider_name == "nvidia":
            self._provider = NVIDIAProvider()
        elif provider_name == "openai":
            self._provider = OpenAIProvider()
        elif provider_name == "ollama":
            self._provider = OllamaProvider()
        elif provider_name == "gemini":
            self._provider = GeminiProvider()
        else:
            self._provider = NVIDIAProvider()

    async def generate(self, system, user, *, temperature=0.7, max_tokens=1000, response_format=None):
        return await self._provider.generate(system=system, user=user, temperature=temperature, max_tokens=max_tokens, response_format=response_format)

    async def classify(self, system, user, *, temperature=0.1, max_tokens=256):
        return await self._provider.classify(system=system, user=user, temperature=temperature, max_tokens=max_tokens)

    async def extract(self, system, user, *, temperature=0.1, max_tokens=512):
        return await self._provider.extract(system=system, user=user, temperature=temperature, max_tokens=max_tokens)

    async def chat(self, messages, temperature=0.7, max_tokens=1000, response_format=None):
        return await self._provider.chat(messages, temperature, max_tokens, response_format)

gateway = LLMGateway()
