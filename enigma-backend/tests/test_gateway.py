import pytest
from app.ai.gateway import LLMGateway
from app.ai.providers.nvidia import NVIDIAProvider

def test_gateway_instance():
    gateway = LLMGateway()
    assert gateway is not None

def test_gateway_has_generate():
    gateway = LLMGateway()
    assert hasattr(gateway, "generate")
    assert callable(gateway.generate)

def test_gateway_has_classify():
    gateway = LLMGateway()
    assert hasattr(gateway, "classify")
    assert callable(gateway.classify)

def test_gateway_has_extract():
    gateway = LLMGateway()
    assert hasattr(gateway, "extract")
    assert callable(gateway.extract)

import inspect
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_generate_is_coroutine():
    gateway = LLMGateway()
    assert inspect.iscoroutinefunction(gateway.generate)

@pytest.mark.asyncio
async def test_classify_is_coroutine():
    gateway = LLMGateway()
    assert inspect.iscoroutinefunction(gateway.classify)

@pytest.mark.asyncio
async def test_extract_is_coroutine():
    gateway = LLMGateway()
    assert inspect.iscoroutinefunction(gateway.extract)


@pytest.mark.asyncio
async def test_nvidia_model_override_is_forwarded():
    gateway = LLMGateway()
    gateway._provider.generate = AsyncMock(return_value={"choices": []})

    await gateway.generate(
        "system", "user", model="meta/llama-3.1-8b-instruct"
    )

    assert gateway._provider.generate.await_args.kwargs["model"] == (
        "meta/llama-3.1-8b-instruct"
    )


@pytest.mark.asyncio
async def test_nvidia_provider_forwards_model_to_client():
    provider = NVIDIAProvider()
    provider._client.chat = AsyncMock(return_value={"choices": []})

    await provider.generate(
        "system", "user", model="meta/llama-3.1-8b-instruct"
    )

    assert provider._client.chat.await_args.args[4] == (
        "meta/llama-3.1-8b-instruct"
    )
