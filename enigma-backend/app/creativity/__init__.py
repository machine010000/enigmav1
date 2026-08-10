"""
Creativity & Opportunity Strategy Engine

Domain-agnostic creativity engine for identifying alternative strategies
when Enigma encounters constraints during opportunity evaluation.

The Creativity Engine:
- Sits after economics and before decision
- Remains subordinate to governance and decision controls
- Generates strategy candidates, never final approvals
- Respects economics, knowledge freshness, and evidence governance
"""

from app.creativity.engine import CreativityEngine
from app.creativity.registry import CreativityRegistry

__all__ = [
    "CreativityEngine",
    "CreativityRegistry",
]
