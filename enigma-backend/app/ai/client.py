import httpx
import json
from app.core.config import get_settings


class AIConfigurationError(RuntimeError):
    """Raised when AI client configuration is missing or invalid."""
    pass


class AIAuthenticationError(RuntimeError):
    """Raised when AI provider authentication fails."""
    pass


class AIConnectionError(RuntimeError):
    """Raised when AI provider connection fails."""
    pass


class AITimeoutError(RuntimeError):
    """Raised when AI provider request times out."""
    pass


class AIProviderError(RuntimeError):
    """Raised when AI provider returns an error response."""
    pass

settings = get_settings()

# HTTP client timeouts (seconds) - must be shorter than worker timeout
HTTP_TIMEOUT = httpx.Timeout(
    connect=10.0,   # Connection establishment
    read=120.0,     # Server response reading (increased for LLM generation)
    write=10.0,     # Request writing
    pool=5.0,       # Connection pool acquisition
)

settings = get_settings()


class NVIDIAClient:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        # Use default NVIDIA base URL if not configured
        self.base_url = (settings.NVIDIA_BASE_URL or "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.model = settings.AI_MODEL

        if self.api_key:
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        else:
            self.headers = {}

    async def chat(
        self,
        messages,
        temperature=0.7,
        max_tokens=1000,
        response_format=None,
    ):
        # Validate configuration at request time
        missing = []
        if not self.api_key:
            missing.append("NVIDIA_API_KEY")
        if not self.base_url:
            missing.append("NVIDIA_BASE_URL")
        if not self.model:
            missing.append("AI_MODEL")
        
        if missing:
            raise AIConfigurationError(f"NVIDIA client configuration missing: {', '.join(missing)}")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )

                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            # Provide clearer error messages for common authentication issues
            if e.response.status_code == 401:
                raise AIAuthenticationError("NVIDIA API authentication failed: Invalid API key or credentials") from e
            elif e.response.status_code == 403:
                raise AIProviderError("NVIDIA API access denied: API key lacks required permissions or is invalid") from e
            elif e.response.status_code == 429:
                raise AIProviderError("NVIDIA API rate limit exceeded") from e
            else:
                raise AIProviderError(f"NVIDIA API request failed with status {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            raise AITimeoutError("NVIDIA API request timed out") from e
        except Exception as e:
            raise AIConnectionError(f"NVIDIA API request failed: {str(e)}") from e

    async def generate_json(
        self,
        system_prompt,
        user_prompt,
        temperature=0.5,
    ):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.chat(
                messages,
                temperature,
                2000,
                {"type": "json_object"},
            )

            content = response["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to parse NVIDIA API response as JSON: {str(e)}") from e


nvidia_client = NVIDIAClient()