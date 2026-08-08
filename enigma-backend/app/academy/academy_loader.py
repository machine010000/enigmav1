from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.academy.academy_models import AcademyModule
from app.academy.academy_registry import AcademyRegistry
from app.academy.academy_validator import AcademyValidator, ValidationResult


class AcademyLoader:
    def __init__(self, registry: AcademyRegistry) -> None:
        self.registry = registry
        self.loaded_versions: Dict[str, str] = {}
        self.load_errors: Dict[str, str] = {}

    def load(self, providers: List[Any]) -> None:
        for provider in providers:
            try:
                module = provider.load()
                validation = AcademyValidator.validate_module(module)
                if validation.is_valid():
                    self.registry.register(module)
                    self.loaded_versions[module.name.lower()] = module.version
                else:
                    self.load_errors[module.name] = ", ".join(validation.errors)
            except Exception as exc:
                self.load_errors[provider.__class__.__name__] = str(exc)

    def get_load_errors(self) -> Dict[str, str]:
        return dict(self.load_errors)

    def get_loaded_versions(self) -> Dict[str, str]:
        return dict(self.loaded_versions)
