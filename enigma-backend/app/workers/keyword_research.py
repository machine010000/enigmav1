"""
Keyword Research Worker — TASK-018

First revenue-oriented capability: discovers and prioritises target keywords
for a topic, business, or niche.

Architecture:
- Follows the same Worker contract as market_analysis.py (app.engine.contracts.Worker)
- ONE bounded LLM call to minimise Railway/NVIDIA latency exposure
- Deterministic processing of LLM output (classification, scoring, deduplication)
- Evidence-First: every keyword carries provenance + source label
- Distinguishes clearly between AI-suggested hypotheses and validated outputs
  (TASK-018 Phase 9 requirement)

Input (from ExecutionContext.memory):
  topic          — business domain or target topic (required)
  seed_keywords  — optional list of starting keywords
  market         — geographic market / language context
  goal           — commercial | informational | mixed
  target         — product/service being researched

Output (WorkerResult.result):
  primary_keywords     — highest-priority keywords (list of KeywordEntry dicts)
  secondary_keywords   — supporting keywords
  intent_summary       — overview of intent distribution
  total_found          — count of all keywords
  confidence           — aggregate quality confidence
  issues               — any warnings about the analysis
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# NOTE: gateway is imported lazily inside _generate_keywords() to avoid
# the circular import cycle:
#   keyword_research → app.ai.gateway → app.ai.__init__ → master_brain
#   → app.engine.__init__ → registry → keyword_research
from app.engine.contracts import (
    ExecutionContext,
    EvidenceItem,
    Worker,
    WorkerEvent,
    WorkerResult,
    WorkerStatus,
)
from app.core.logging_config import get_logger


logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Bounded above the NVIDIA client's 120-second read timeout so the provider
# layer, rather than this wrapper, classifies connect/read failures.
LLM_TIMEOUT_SECONDS = 130

# Keyword intent categories
INTENT_COMMERCIAL = "commercial"
INTENT_INFORMATIONAL = "informational"
INTENT_NAVIGATIONAL = "navigational"
INTENT_TRANSACTIONAL = "transactional"
INTENT_UNKNOWN = "unknown"

_VALID_INTENTS = {
    INTENT_COMMERCIAL,
    INTENT_INFORMATIONAL,
    INTENT_NAVIGATIONAL,
    INTENT_TRANSACTIONAL,
    INTENT_UNKNOWN,
}

# Provenance labels (TASK-018 Phase 9: distinguish AI hypothesis vs validated)
SOURCE_AI_HYPOTHESIS = "ai_hypothesis"        # LLM generated, not verified
SOURCE_SEED_DERIVED = "seed_derived"          # Derived from seed keywords provided
SOURCE_CONTEXT_DERIVED = "context_derived"    # Derived from product/business context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return datetime.utcnow().isoformat()


def _safe_json(text: str) -> Optional[dict]:
    """Parse JSON from an LLM response robustly."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _safe_float(value: Any, fallback: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


def _safe_str(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value).strip() or fallback


def _normalise_intent(raw: Any) -> str:
    if not raw:
        return INTENT_UNKNOWN
    candidate = str(raw).strip().lower()
    for intent in _VALID_INTENTS:
        if intent in candidate:
            return intent
    return INTENT_UNKNOWN


def _priority_from_relevance(relevance: float) -> str:
    if relevance >= 0.75:
        return "high"
    if relevance >= 0.45:
        return "medium"
    return "low"


def _build_keyword_entry(
    keyword: str,
    intent: str,
    relevance: float,
    source: str,
    notes: str = "",
) -> Dict[str, Any]:
    """Build a canonical keyword entry dict."""
    return {
        "keyword": keyword,
        "intent": intent,
        "relevance": round(relevance, 4),
        "priority": _priority_from_relevance(relevance),
        "source": source,
        "notes": notes,
        "provenance": "ai_hypothesis" if source == SOURCE_AI_HYPOTHESIS else source,
    }


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

class KeywordResearchWorker(Worker):
    """
    Keyword Research Worker.

    Discovers and prioritises target keywords for a topic, business, or niche.
    Uses a single bounded LLM call for keyword generation, with deterministic
    post-processing for classification, deduplication, and scoring.

    Evidence-First: every keyword records its source and provenance so the
    Brain can distinguish AI hypotheses from seed-derived or validated data.
    """

    name = "keyword_research"

    description = (
        "Discover and prioritise target keywords for a topic or business. "
        "Returns primary and secondary keywords with intent classification, "
        "relevance scores, and evidence provenance."
    )

    input_schema = [
        "topic",
        "seed_keywords",
        "market",
        "goal",
        "target",
    ]

    output_schema = [
        "primary_keywords",
        "secondary_keywords",
        "intent_summary",
        "total_found",
        "confidence",
        "issues",
    ]

    capabilities = ["keyword_research"]

    # ------------------------------------------------------------------
    # run
    # ------------------------------------------------------------------

    async def run(self, context: ExecutionContext) -> WorkerResult:
        started_at = datetime.utcnow()

        # ---- Read inputs from context ----
        topic = _safe_str(
            context.recall("topic")
            or context.recall("business")
            or context.recall("target")
            or context.product.get("name")
            or context.product.get("description", "")[:120],
            fallback="",
        )
        seed_keywords: List[str] = context.recall("seed_keywords") or []
        market = _safe_str(context.recall("market") or "global")
        goal = _safe_str(context.recall("goal") or "mixed")

        async def _emit(msg: str, data: Optional[Dict] = None) -> None:
            if context.emit:
                try:
                    await context.emit(
                        WorkerEvent(
                            worker_name=self.name,
                            type="progress",
                            message=msg,
                            data=data or {},
                            execution_id=context.execution_id,
                        )
                    )
                except Exception:
                    pass

        # ---- Validate required input ----
        if not topic:
            await _emit("keyword_research_failed: no topic provided")
            return WorkerResult(
                worker_name=self.name,
                status=WorkerStatus.FAILED,
                error="topic is required — provide via context memory key 'topic'",
                result={"issues": ["topic is required"]},
                confidence=0.0,
                evidence=[],
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        await _emit(
            f"keyword_research_started: topic='{topic[:60]}' market={market}",
            {"topic": topic[:60], "market": market, "goal": goal},
        )

        # ---- Single bounded LLM call ----
        llm_result = await self._generate_keywords(
            topic=topic,
            seed_keywords=seed_keywords,
            market=market,
            goal=goal,
            execution_id=context.execution_id,
        )

        llm_calls = llm_result["llm_calls"]
        raw_keywords = llm_result["keywords"]
        parse_issues = llm_result["issues"]
        llm_confidence = llm_result["confidence"]

        # TASK-018 Phase 17: if LLM returned no keywords due to timeout/error → FAILED immediately
        # Never write positive evidence on timeout or LLM failure
        if not raw_keywords and any(
            "timed out" in i.lower() or "failed" in i.lower()
            for i in parse_issues
        ):
            await _emit("keyword_research_failed: LLM timeout or error — no evidence written")
            return WorkerResult(
                worker_name=self.name,
                status=WorkerStatus.FAILED,
                result={"issues": parse_issues, "primary_keywords": [], "secondary_keywords": []},
                error=parse_issues[0] if parse_issues else "No keywords generated",
                confidence=0.0,
                llm_calls=llm_calls,
                evidence=[],
                started_at=started_at,
                completed_at=datetime.utcnow(),
            )

        await _emit(
            f"keywords_generated: {len(raw_keywords)} raw keywords from LLM",
            {"count": len(raw_keywords), "llm_calls": llm_calls},
        )

        # ---- Deterministic post-processing ----
        # 1. Incorporate seed keywords with higher confidence (seed_derived)
        seed_set = {s.strip().lower() for s in seed_keywords if s.strip()}
        processed: Dict[str, Dict[str, Any]] = {}

        for entry in raw_keywords:
            kw = _safe_str(entry.get("keyword", "")).lower()
            if not kw or len(kw) < 3:
                continue
            intent = _normalise_intent(entry.get("intent"))
            relevance = _safe_float(entry.get("relevance", 0.5))
            # Seed-derived keywords get a small relevance boost + cleaner provenance
            source = SOURCE_SEED_DERIVED if kw in seed_set else SOURCE_AI_HYPOTHESIS
            if source == SOURCE_SEED_DERIVED:
                relevance = min(1.0, relevance + 0.10)
            processed[kw] = _build_keyword_entry(
                keyword=kw,
                intent=intent,
                relevance=relevance,
                source=source,
                notes=_safe_str(entry.get("notes", "")),
            )

        # 2. Add any seed keywords that LLM missed entirely
        for seed in seed_keywords:
            s = seed.strip().lower()
            if s and s not in processed:
                processed[s] = _build_keyword_entry(
                    keyword=s,
                    intent=INTENT_UNKNOWN,
                    relevance=0.55,
                    source=SOURCE_SEED_DERIVED,
                    notes="Provided as seed keyword — not yet classified",
                )

        # 3. Sort by relevance descending
        sorted_keywords = sorted(
            processed.values(),
            key=lambda x: x["relevance"],
            reverse=True,
        )

        # 4. Split primary (high priority) vs secondary
        primary = [k for k in sorted_keywords if k["priority"] == "high"]
        secondary = [k for k in sorted_keywords if k["priority"] != "high"]

        # Intent distribution summary
        intent_counts: Dict[str, int] = {}
        for kw in sorted_keywords:
            i = kw["intent"]
            intent_counts[i] = intent_counts.get(i, 0) + 1

        total = len(sorted_keywords)
        intent_summary = {
            i: {"count": c, "pct": round(c / total * 100, 1) if total else 0}
            for i, c in intent_counts.items()
        }

        # 5. Aggregate confidence
        if sorted_keywords:
            rel_scores = [k["relevance"] for k in sorted_keywords]
            aggregate_confidence = round(
                (sum(rel_scores) / len(rel_scores)) * llm_confidence, 4
            )
        else:
            aggregate_confidence = 0.0

        # ---- Build evidence list ----
        evidence: List[Dict[str, Any]] = [
            {
                "worker": self.name,
                "field": "primary_keywords",
                "value": [k["keyword"] for k in primary[:5]],
                "source": SOURCE_AI_HYPOTHESIS,
                "confidence": aggregate_confidence,
                "timestamp": _iso_now(),
                "note": (
                    "TASK-018 Phase 9: these keywords are AI-generated hypotheses. "
                    "They have not been validated against live search-volume data."
                ),
            },
            {
                "worker": self.name,
                "field": "total_found",
                "value": total,
                "source": "deterministic_processing",
                "confidence": 1.0,
                "timestamp": _iso_now(),
            },
        ]
        if seed_keywords:
            evidence.append(
                {
                    "worker": self.name,
                    "field": "seed_keywords",
                    "value": seed_keywords,
                    "source": SOURCE_SEED_DERIVED,
                    "confidence": 0.9,
                    "timestamp": _iso_now(),
                    "note": "User-provided seed keywords — higher provenance confidence",
                }
            )

        issues = list(parse_issues)
        if not primary:
            issues.append("No high-priority keywords found — all scored below 0.75")
        if total == 0:
            issues.append("No keywords were generated — check topic input")

        completed_at = datetime.utcnow()
        execution_time = (completed_at - started_at).total_seconds()

        await _emit(
            f"keyword_research_complete: {len(primary)} primary, "
            f"{len(secondary)} secondary keywords",
            {
                "primary_count": len(primary),
                "secondary_count": len(secondary),
                "total": total,
                "confidence": aggregate_confidence,
            },
        )

        result_data: Dict[str, Any] = {
            "primary_keywords": primary[:20],
            "secondary_keywords": secondary[:30],
            "intent_summary": intent_summary,
            "total_found": total,
            "confidence": aggregate_confidence,
            "issues": issues,
            "topic": topic,
            "market": market,
            "goal": goal,
        }

        return WorkerResult(
            worker_name=self.name,
            status=WorkerStatus.SUCCESS,
            result=result_data,
            evidence=evidence,
            confidence=aggregate_confidence,
            llm_calls=llm_calls,
            started_at=started_at,
            completed_at=completed_at,
            execution_time=execution_time,
        )

    # ------------------------------------------------------------------
    # Single bounded LLM call (TASK-018 Phase 10)
    # ------------------------------------------------------------------

    async def _generate_keywords(
        self,
        topic: str,
        seed_keywords: List[str],
        market: str,
        goal: str,
        execution_id: str = "",
    ) -> Dict[str, Any]:
        """
        One structured LLM call to generate keyword candidates.

        Hard timeout: LLM_TIMEOUT_SECONDS (130s).
        On timeout or error: returns safe empty result with issue flag.
        Never creates false positive evidence on failure.
        """
        # Lazy import to avoid circular dependency via app.engine.__init__
        from app.ai.gateway import gateway  # noqa: PLC0415

        now = _iso_now()

        seed_clause = ""
        if seed_keywords:
            seeds = ", ".join(f'"{s}"' for s in seed_keywords[:10])
            seed_clause = f"\nSeed keywords to include: {seeds}"

        system = (
            "You are an expert keyword research analyst specialising in SEO and "
            "digital marketing. Analyse the given topic and produce a structured "
            "keyword research output.\n\n"
            "Return ONLY a valid JSON object with this exact structure:\n"
            "{\n"
            '  "keywords": [\n'
            '    {\n'
            '      "keyword": "string (2-6 words, lowercase)",\n'
            '      "intent": "commercial|informational|transactional|navigational",\n'
            '      "relevance": 0.0,\n'
            '      "notes": "brief rationale"\n'
            "    }\n"
            "  ],\n"
            '  "confidence": 0.0,\n'
            '  "analysis_notes": "string"\n'
            "}\n\n"
            "Rules:\n"
            "- Return 15-25 keywords covering a range of intents\n"
            "- relevance 0.0-1.0 (how well the keyword matches the topic/goal)\n"
            "- Be honest about confidence — lower is better than overclaiming\n"
            "- Focus on actionable, realistic search phrases people actually use\n"
            "- Do NOT include brand names, competitor names, or trademarks"
        )

        user = (
            f"Topic: {topic}\n"
            f"Market / location: {market}\n"
            f"Goal: {goal} (commercial = buyer-intent, informational = awareness)"
            f"{seed_clause}"
        )

        request_started = time.monotonic()
        try:
            resp = await asyncio.wait_for(
                gateway.generate(
                    system=system,
                    user=user,
                    temperature=0.2,
                    max_tokens=1200,
                ),
                timeout=LLM_TIMEOUT_SECONDS,
            )

            content = (
                resp.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = _safe_json(content)

            if parsed and isinstance(parsed.get("keywords"), list):
                raw_keywords = [
                    k for k in parsed["keywords"]
                    if isinstance(k, dict) and k.get("keyword")
                ]
                confidence = _safe_float(parsed.get("confidence", 0.65))
                return {
                    "keywords": raw_keywords,
                    "confidence": confidence,
                    "issues": [],
                    "llm_calls": 1,
                    "timestamp": now,
                }

            # Parsed but wrong shape
            return {
                "keywords": [],
                "confidence": 0.0,
                "issues": ["LLM response had unexpected shape — no keywords extracted"],
                "llm_calls": 1,
                "timestamp": now,
            }

        except asyncio.TimeoutError:
            # TASK-018 Phase 17: timeout must never create false positive evidence
            from app.core.config import get_settings  # noqa: PLC0415
            settings = get_settings()
            logger.error(
                "keyword_research_provider_timeout execution_id=%s capability=%s "
                "provider=%s model=%s failure_stage=worker_gateway_deadline "
                "exception_type=TimeoutError elapsed_ms=%s worker_timeout_seconds=%s "
                "provider_read_timeout_seconds=120.0",
                execution_id,
                self.capabilities[0],
                settings.AI_PROVIDER,
                settings.AI_MODEL,
                round((time.monotonic() - request_started) * 1000),
                LLM_TIMEOUT_SECONDS,
            )
            return {
                "keywords": [],
                "confidence": 0.0,
                "issues": [
                    "LLM call timed out — no keywords generated. "
                    "No evidence written. Re-run to retry."
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

        except Exception as exc:
            from app.core.config import get_settings  # noqa: PLC0415
            settings = get_settings()
            logger.error(
                "keyword_research_provider_failure execution_id=%s capability=%s "
                "provider=%s model=%s failure_stage=provider_gateway "
                "exception_type=%s elapsed_ms=%s worker_timeout_seconds=%s "
                "provider_read_timeout_seconds=120.0",
                execution_id,
                self.capabilities[0],
                settings.AI_PROVIDER,
                settings.AI_MODEL,
                type(exc).__name__,
                round((time.monotonic() - request_started) * 1000),
                LLM_TIMEOUT_SECONDS,
            )
            return {
                "keywords": [],
                "confidence": 0.0,
                "issues": [f"LLM call failed: {type(exc).__name__}"],
                "llm_calls": 1,
                "timestamp": now,
            }


# Module-level singleton — imported by registry
keyword_research_worker = KeywordResearchWorker()
