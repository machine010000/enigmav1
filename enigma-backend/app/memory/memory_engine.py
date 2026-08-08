from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple
import uuid

from app.memory.models import Episode, Pattern, Strategy

try:
    from app.knowledge_governance import CandidateKnowledge, Evidence, SourceType
    KNOWLEDGE_GOVERNANCE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_GOVERNANCE_AVAILABLE = False


class MemoryEngine:
    def __init__(self) -> None:
        self.episodes: List[Episode] = []
        self.strategies: List[Strategy] = []
        self.patterns: List[Pattern] = []
        self.recall_hits = 0
        self.recall_misses = 0
        self._recall_times: List[float] = []

    def store_episode(self, episode: Episode) -> Episode:
        self.episodes.append(episode)
        return episode

    def store_strategy(self, strategy: Strategy) -> Strategy:
        self.strategies.append(strategy)
        return strategy

    def store_pattern(self, pattern: Pattern) -> Pattern:
        self.patterns.append(pattern)
        return pattern

    def recall(self, goal: Optional[str] = None, worker: Optional[str] = None, product_id: Optional[str] = None) -> List[Episode]:
        started = datetime.now(timezone.utc)
        matches = [
            episode
            for episode in self.episodes
            if (goal is None or goal.lower() in episode.goal.lower())
            and (worker is None or episode.worker == worker)
            and (product_id is None or episode.product_id == product_id)
        ]
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        self._recall_times.append(elapsed)
        if matches:
            self.recall_hits += 1
        else:
            self.recall_misses += 1
        return matches

    def find_similar_episodes(self, goal: str, limit: int = 5) -> List[Episode]:
        normalized_goal = goal.lower()
        scored = []
        for episode in self.episodes:
            overlap = len(set(normalized_goal.split()) & set(episode.goal.lower().split()))
            if overlap > 0:
                scored.append((overlap, episode))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [episode for _, episode in scored[:limit]]

    def find_best_strategy(self, goal: Optional[str] = None) -> Optional[Strategy]:
        candidates = list(self.strategies)
        if goal is not None:
            lowered = goal.lower()
            candidates = [strategy for strategy in candidates if lowered in strategy.name.lower() or lowered in strategy.description.lower()]
        if not candidates:
            return None
        return max(candidates, key=lambda s: (s.success_rate, s.usage_count))

    def update_strategy_success(self, strategy_id: str, success: bool, increment_usage: bool = True) -> Optional[Strategy]:
        for strategy in self.strategies:
            if strategy.id == strategy_id:
                strategy.usage_count += 1 if increment_usage else 0
                strategy.success_rate = ((strategy.success_rate * max(strategy.usage_count - 1, 0)) + (1.0 if success else 0.0)) / max(strategy.usage_count, 1)
                strategy.updated_at = datetime.now(timezone.utc)
                return strategy
        return None

    def search_patterns(self, category: Optional[str] = None, trigger: Optional[str] = None) -> List[Pattern]:
        matches = []
        for pattern in self.patterns:
            if category is not None and pattern.category != category:
                continue
            if trigger is not None and trigger.lower() not in pattern.trigger.lower():
                continue
            matches.append(pattern)
        return matches

    def metrics(self) -> Dict[str, Any]:
        avg_confidence = sum(ep.confidence for ep in self.episodes) / len(self.episodes) if self.episodes else 0.0
        avg_llm_saved = sum(max(0, ep.llm_calls - 1) for ep in self.episodes) / len(self.episodes) if self.episodes else 0.0
        return {
            "episode_count": len(self.episodes),
            "recall_time": round(sum(self._recall_times) / len(self._recall_times), 6) if self._recall_times else 0.0,
            "hit_rate": round(self.recall_hits / (self.recall_hits + self.recall_misses), 4) if (self.recall_hits + self.recall_misses) else 0.0,
            "strategy_reuse_percent": round((sum(1 for s in self.strategies if s.usage_count > 1) / len(self.strategies)) * 100, 2) if self.strategies else 0.0,
            "pattern_count": len(self.patterns),
            "average_confidence": round(avg_confidence, 4),
            "average_llm_calls_saved": round(avg_llm_saved, 4),
            "memory_size": len(self.episodes) + len(self.strategies) + len(self.patterns),
        }

    def episode_to_candidate_knowledge(self, episode: Episode) -> Optional[Any]:
        """Convert Memory episode to CandidateKnowledge for governance."""
        if not KNOWLEDGE_GOVERNANCE_AVAILABLE:
            return None

        # Convert episode to Evidence with MEMORY source type
        result_text = str(episode.outputs) if episode.outputs else str(episode.evidence)
        evidence = Evidence(
            id=f"memory-{episode.id}",
            source="memory_engine",
            source_type=SourceType.MEMORY,
            claim=f"Goal: {episode.goal}, Result: {result_text}",
            retrieved_at=datetime.utcnow(),
            quality_score=episode.confidence * 0.6,  # Memory has lower default quality
            confidence=episode.confidence,
        )

        # Create CandidateKnowledge
        return CandidateKnowledge(
            id=f"memory-{episode.id}",
            name=f"Memory episode: {episode.goal[:50]}",
            definition=f"Experience from past execution: {episode.goal}",
            evidence=[evidence],
            source="memory",
            submitted_at=datetime.utcnow(),
        )
