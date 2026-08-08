from __future__ import annotations

from typing import Dict, List, Optional

from app.academy.academy_models import AcademyModule


class AcademyRegistry:
    def __init__(self) -> None:
        self._modules: Dict[str, AcademyModule] = {}

    def register(self, module: AcademyModule) -> None:
        self._modules[module.name.lower()] = module

    def unregister(self, module_name: str) -> None:
        self._modules.pop(module_name.lower(), None)

    def get(self, module_name: str) -> Optional[AcademyModule]:
        return self._modules.get(module_name.lower())

    def list_modules(self) -> List[AcademyModule]:
        return list(self._modules.values())

    def search_topics(self, topic: str) -> List[AcademyModule]:
        term = topic.lower()
        return [
            module
            for module in self._modules.values()
            if any(term in t.lower() for t in module.topics)
            or any(term in keyword.lower() for article in module.articles for keyword in article.keywords)
        ]
