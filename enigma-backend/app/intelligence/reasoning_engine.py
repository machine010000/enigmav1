from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ReasoningEngine(ABC):
    @abstractmethod
    def reason(self, context: Any) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def evaluate(self, context: Any) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def summarize(self, context: Any) -> str:
        raise NotImplementedError()

    @abstractmethod
    def explain(self, context: Any) -> str:
        raise NotImplementedError()
