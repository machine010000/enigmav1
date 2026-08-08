import httpx
import json
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()

class NVIDIAClient:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model = settings.AI_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat(self, messages, temperature=0.7, max_tokens=1000, response_format=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def generate_json(self, system_prompt, user_prompt, temperature=0.5):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = await self.chat(messages, temperature, 2000, {"type": "json_object"})
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)

nvidia_client = NVIDIAClient()
