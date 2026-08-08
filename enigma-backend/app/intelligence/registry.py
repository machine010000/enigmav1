from __future__ import annotations

from typing import Any, Dict, List, Optional


class IntelligenceRegistry:
    def __init__(self) -> None:
        self._engines: Dict[str, Any] = {}

    def register(self, name: str, engine: Any) -> None:
        self._engines[name.lower()] = engine

    def unregister(self, name: str) -> None:
        self._engines.pop(name.lower(), None)

    def list(self) -> List[str]:
        return list(self._engines.keys())

    def execute(self, name: str, context: Any, **kwargs: Any) -> Any:
        engine = self._engines.get(name.lower())
        if engine is None:
            raise KeyError(f"Engine '{name}' is not registered.")
        if hasattr(engine, "execute"):
            return engine.execute(context, **kwargs)
        raise AttributeError(f"Engine '{name}' does not support execute().")
