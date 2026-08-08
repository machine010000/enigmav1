import pytest
from app.ai.gateway import LLMGateway

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
