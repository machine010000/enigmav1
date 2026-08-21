"""Focused CORS parsing and browser preflight tests for TASK-069A."""

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.config import (
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    Settings,
    parse_cors_origins,
)


def _cors_app(origins: list[str]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    @app.post("/chat")
    async def chat() -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://example.vercel.app", ["https://example.vercel.app"]),
        (
            "https://example.vercel.app,https://app.example.com",
            ["https://example.vercel.app", "https://app.example.com"],
        ),
        (
            "  http://localhost:3000, , HTTPS://APP.EXAMPLE.COM/  ",
            ["http://localhost:3000", "https://app.example.com"],
        ),
        ("", []),
        (", ,", []),
    ],
)
def test_exact_origin_parsing(raw: str, expected: list[str]) -> None:
    assert parse_cors_origins(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "*",
        "https://good.example,*",
        "example.vercel.app",
        "ftp://example.com",
        "https://example.com/api",
        "https://example.com?preview=1",
        "https://user:password@example.com",
        "https://example.com:invalid",
        "https://example .com",
    ],
)
def test_unsafe_or_malformed_origins_are_rejected(raw: str) -> None:
    with pytest.raises(ValueError, match="CORS"):
        parse_cors_origins(raw)


def test_settings_rejects_wildcard_with_credentialed_cors(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "test-only-secret")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    with pytest.raises(ValidationError, match="credentialed CORS"):
        Settings(_env_file=None)


@pytest.mark.asyncio
async def test_allowed_origin_preflight_and_response_headers() -> None:
    origin = "https://example.vercel.app"
    app = _cors_app([origin])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        preflight = await client.options(
            "/chat",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        response = await client.post(
            "/chat",
            headers={"Origin": origin, "Authorization": "Bearer test"},
        )

    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == origin
    assert preflight.headers["access-control-allow-credentials"] == "true"
    assert "POST" in preflight.headers["access-control-allow-methods"]
    allowed_headers = preflight.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed_headers
    assert "content-type" in allowed_headers
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.asyncio
async def test_disallowed_origin_gets_no_cors_permission() -> None:
    app = _cors_app(["https://allowed.vercel.app"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        preflight = await client.options(
            "/chat",
            headers={
                "Origin": "https://disallowed.vercel.app",
                "Access-Control-Request-Method": "POST",
            },
        )
        response = await client.post(
            "/chat", headers={"Origin": "https://disallowed.vercel.app"}
        )

    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers
    assert "access-control-allow-origin" not in response.headers
