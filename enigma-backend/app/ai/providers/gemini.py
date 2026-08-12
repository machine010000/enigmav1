from __future__ import annotations

import os
from typing import Any, Dict, Optional

from app.ai.providers import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"

    def _build_url(self):
        return f"{self.base_url}:generateContent?key={self.api_key}"

    def _build_payload(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[dict] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "system_instruction": {
                "parts": [{"text": system}] if system else [],
            },
            "contents": [
                {"role": "user", "parts": [{"text": user}]},
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if response_format and response_format.get("type") == "json_object":
            payload["generationConfig"]["responseMimeType"] = "application/json"
        return payload

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

        payload = self._build_payload(
            system, user, temperature=temperature,
            max_tokens=max_tokens, response_format=response_format,
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self._build_url(), json=payload)
            response.raise_for_status()
            data = response.json()
            content = ""
            for candidate in data.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    content += part.get("text", "")
            return {
                "choices": [
                    {"message": {"role": "model", "content": content}},
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


__all__ = ["GeminiProvider"]
