"""Pure canonical identity helpers shared by runtime and data migrations."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_source_url(value: Optional[str]) -> Optional[str]:
    """Return the authoritative canonical marketplace URL representation."""
    if not value:
        return None
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError("source_url must be an absolute HTTP(S) URL")
    host = parts.hostname.lower() if parts.hostname else ""
    port = (
        f":{parts.port}"
        if parts.port
        and not (parts.scheme.lower() == "http" and parts.port == 80)
        and not (parts.scheme.lower() == "https" and parts.port == 443)
        else ""
    )
    path = parts.path.rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, item)
            for key, item in parse_qsl(parts.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
        )
    )
    return urlunsplit((parts.scheme.lower(), host + port, path, query, ""))


def fallback_fingerprint(platform: str, title: str, client_info: dict[str, Any]) -> str:
    stable = {
        "platform": platform.strip().lower(),
        "title": " ".join(title.lower().split()),
        "client": client_info.get("name") or client_info.get("username") or client_info.get("id") or "",
    }
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def normalize_external_id(value: Optional[str]) -> Optional[str]:
    normalized = (value or "").strip().lower()
    return normalized or None


def canonical_dedupe_key(
    platform: str,
    external_project_id: Optional[str],
    source_url: Optional[str],
    title: str,
    client_info: dict[str, Any],
) -> str:
    normalized_url = normalize_source_url(source_url)
    identity = (
        normalized_url
        or normalize_external_id(external_project_id)
        or fallback_fingerprint(platform, title, client_info)
    )
    return hashlib.md5(
        f"{platform.strip().lower()}|{identity}".encode(),
        usedforsecurity=False,
    ).hexdigest()
