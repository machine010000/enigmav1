from __future__ import annotations

from typing import Dict, Optional

from app.academy.academy_manager import AcademyManager


class AcademyEngine:
    def __init__(self, manager: Optional[AcademyManager] = None) -> None:
        self.manager = manager or AcademyManager()

    def load_providers(self, providers: list[object]) -> None:
        self.manager.load_providers(providers)

    def get_module_context(self, topic: str, subtopic: Optional[str] = None) -> Dict[str, object]:
        return self.manager.get_context(topic, subtopic)

    def list_modules(self) -> list[object]:
        return self.manager.list_modules()

    def get_module(self, module_name: str) -> Optional[object]:
        return self.manager.get_module(module_name)
