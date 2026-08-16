"""Small capability-to-curriculum-runner registry.

Runner modules are imported lazily so curriculum and revalidation modules remain
free to share contracts without introducing import cycles.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol

from app.learning.curriculum import TrainingMode


class CurriculumRunner(Protocol):
    capability: str
    mode: TrainingMode

    async def load_attempt_history(self, db: Any, user_id: str) -> List[Dict[str, Any]]: ...
    async def run_next(self, db: Any, user_id: str,
                       mode: Optional[TrainingMode] = None) -> Any: ...
    async def run(self, db: Any, user_id: str, max_attempts: int = 3,
                  mode: Optional[TrainingMode] = None) -> List[Any]: ...


RunnerFactory = Callable[..., CurriculumRunner]


class RunnerNotRegisteredError(LookupError):
    pass


class CapabilityRunnerRegistry:
    def __init__(self) -> None:
        self._factories: Dict[str, RunnerFactory] = {}

    def register(self, capability_id: str, factory: RunnerFactory) -> None:
        capability_id = capability_id.strip()
        if not capability_id:
            raise ValueError("capability_id is required")
        self._factories[capability_id] = factory

    def resolve(self, capability_id: str, *, mode: TrainingMode = TrainingMode.QUALIFICATION,
                **kwargs: Any) -> CurriculumRunner:
        factory = self._factories.get(capability_id)
        if factory is None:
            raise RunnerNotRegisteredError(capability_id)
        runner = factory(mode=TrainingMode(mode), **kwargs)
        if runner.capability != capability_id:
            raise ValueError(
                f"runner factory for {capability_id!r} produced {runner.capability!r}"
            )
        return runner

    def registered_capabilities(self) -> List[str]:
        return list(self._factories)


def _keyword_runner_factory(**kwargs: Any) -> CurriculumRunner:
    from app.learning.curriculum import KeywordResearchTrainingRunner
    return KeywordResearchTrainingRunner(**kwargs)


def _competitor_runner_factory(**kwargs: Any) -> CurriculumRunner:
    from app.learning.competitor_curriculum import CompetitorResearchTrainingRunner
    return CompetitorResearchTrainingRunner(**kwargs)


def _product_verification_runner_factory(**kwargs: Any) -> CurriculumRunner:
    from app.learning.product_verification_curriculum import ProductVerificationTrainingRunner
    return ProductVerificationTrainingRunner(**kwargs)


capability_runner_registry = CapabilityRunnerRegistry()
capability_runner_registry.register("keyword_research", _keyword_runner_factory)
capability_runner_registry.register("competitor_research", _competitor_runner_factory)
capability_runner_registry.register("product_verification", _product_verification_runner_factory)
