"""
Creativity Models

Shared models and data structures for the creativity engine.
This module contains model definitions that are used across
multiple creativity components.
"""

from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from app.creativity.contracts import (
    ConstraintType,
    StrategyCategory,
    StrategyStatus,
)


class StrategyImpact(str, Enum):
    """Impact level of a strategy."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class StrategyComplexity(str, Enum):
    """Complexity level of implementing a strategy."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class StrategyRequirement:
    """
    A requirement for strategy implementation.
    """
    requirement_type: str
    description: str
    optional: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyEffect:
    """
    Expected effect of implementing a strategy.
    """
    effect_type: str
    magnitude: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyCompatibility:
    """
    Compatibility information for a strategy.
    """
    platform: Optional[str] = None
    domain: Optional[str] = None
    compatible: bool = True
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyMetadata:
    """
    Additional metadata for strategies.
    """
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    author: Optional[str] = None
    version: str = "1.0"
    tags: Set[str] = field(default_factory=set)
    references: Set[str] = field(default_factory=set)
