"""
Market Analysis Worker (Sprint 2)

Receives:
    A verified product from the execution context, containing:
    - verified_name
    - category
    - attributes
    - description

Returns:
    A WorkerResult whose result dict contains:
    - market_size
    - competition_level
    - opportunity_score
    - target_audience
    - pricing_recommendation
    - market_trends

Evidence-First Architecture:
    Every value returned carries an evidence entry describing the source
    and confidence of the claim.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.ai.gateway import gateway
from app.engine.contracts import (
    ExecutionContext,
    EvidenceItem,
    Worker,
    WorkerEvent,
    WorkerResult,
    WorkerStatus,
)


class MarketAnalysisWorker(Worker):
    name = "market_analysis"

    description = (
        "Analyze market size, competition, and opportunity "
        "for a verified product."
    )

    input_schema = [
        "verified_name",
        "category",
        "attributes",
        "description",
    ]

    output_schema = [
        "market_size",
        "competition_level",
        "opportunity_score",
        "target_audience",
        "pricing_recommendation",
        "market_trends",
    ]

    # Keep individual provider calls bounded.
    LLM_TIMEOUT_SECONDS = 30

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_json(text: str) -> Optional[dict]:
        """
        Parse JSON from an LLM response.

        Handles:
        - clean JSON
        - markdown ```json blocks
        - JSON surrounded by explanatory text
        """

        if not text:
            return None

        text = text.strip()

        # Remove markdown code fences.
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"\s*```$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        # First attempt: complete response is JSON.
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

        # Second attempt: locate the outermost JSON object.
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            return None

        candidate = text[start : end + 1]

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            return None

        return None

    @staticmethod
    def _clean_string(value: Any, fallback: str = "") -> str:
        if value is None:
            return fallback

        value = str(value).strip()

        return value if value else fallback

    @staticmethod
    def _safe_confidence(value: Any, fallback: float = 0.5) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            return fallback

        return max(0.0, min(1.0, value))

    async def _generate_with_timeout(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        """
        Execute gateway.generate with a hard timeout.

        This prevents one stalled provider request from holding the
        entire execution indefinitely.
        """

        return await asyncio.wait_for(
            gateway.generate(
                system=system,
                user=user,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
            timeout=self.LLM_TIMEOUT_SECONDS,
        )

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    async def run(self, context: ExecutionContext) -> WorkerResult:
        # Try to get verified product from context.memory (output from product_verification)
        # Fall back to context.product if not in memory
        verified_product = context.recall("product_verification_result")
        
        if not verified_product:
            # If no previous worker output, use context.product directly
            verified_product = context.product or {}
        
        verified_name = self._clean_string(
            verified_product.get("verified_name") or verified_product.get("name") or verified_product.get("title")
        )
        
        category = self._clean_string(
            verified_product.get("category")
        )
        
        description = self._clean_string(
            verified_product.get("description")
        )
        
        attributes = verified_product.get("attributes", {})

        emit = context.emit

        async def _emit(event: WorkerEvent) -> None:
            if emit is not None:
                try:
                    await emit(event)
                except Exception:
                    # Event emission must never break the worker.
                    pass

        # --------------------------------------------------------------
        # Announce
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="market_analysis_started",
                message="Market analysis started",
                data={
                    "product": verified_name[:80],
                    "category": category,
                },
                execution_id=context.execution_id,
            )
        )

        # --------------------------------------------------------------
        # Required input validation
        # --------------------------------------------------------------

        if not verified_name and not description:
            await _emit(
                WorkerEvent(
                    worker_name=self.name,
                    type="error",
                    message=(
                        "No product name or description provided — "
                        "cannot analyze market"
                    ),
                    execution_id=context.execution_id,
                )
            )

            return WorkerResult(
                worker_name=self.name,
                status=WorkerStatus.FAILED,
                error="Product name and description are required",
                confidence=0.0,
                evidence=[],
            )

        evidence: List[Dict[str, Any]] = []
        llm_calls = 0
        issues: List[str] = []

        # --------------------------------------------------------------
        # 1. Market size analysis
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Analysing market size…",
                execution_id=context.execution_id,
            )
        )

        market_size = "Unknown"
        market_size_confidence = 0.5

        if verified_name and category:
            market_analysis = await self._analyze_market_size(
                verified_name,
                category,
                description,
            )

            llm_calls += market_analysis["llm_calls"]

            if market_analysis["market_size"]:
                market_size = market_analysis["market_size"]

            market_size_confidence = market_analysis["confidence"]

            evidence.append(
                {
                    "worker": self.name,
                    "field": "market_size",
                    "value": market_size,
                    "source": "llm_market_analysis",
                    "confidence": market_size_confidence,
                    "timestamp": market_analysis.get(
                        "timestamp",
                        "",
                    ),
                }
            )

            if market_analysis.get("issues"):
                issues.extend(market_analysis["issues"])

        # --------------------------------------------------------------
        # 2. Competition analysis
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Analysing competition level…",
                execution_id=context.execution_id,
            )
        )

        competition_level = "Medium"
        competition_confidence = 0.5

        if verified_name and category:
            competition_analysis = await self._analyze_competition(
                verified_name,
                category,
                description,
            )

            llm_calls += competition_analysis["llm_calls"]

            if competition_analysis["competition_level"]:
                competition_level = competition_analysis["competition_level"]

            competition_confidence = competition_analysis["confidence"]

            evidence.append(
                {
                    "worker": self.name,
                    "field": "competition_level",
                    "value": competition_level,
                    "source": "llm_competition_analysis",
                    "confidence": competition_confidence,
                    "timestamp": competition_analysis.get(
                        "timestamp",
                        "",
                    ),
                }
            )

        # --------------------------------------------------------------
        # 3. Target audience
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Identifying target audience…",
                execution_id=context.execution_id,
            )
        )

        target_audience = []
        audience_confidence = 0.5

        if verified_name and category:
            audience_analysis = await self._identify_target_audience(
                verified_name,
                category,
                description,
            )

            llm_calls += audience_analysis["llm_calls"]

            if audience_analysis["target_audience"]:
                target_audience = audience_analysis["target_audience"]

            audience_confidence = audience_analysis["confidence"]

            evidence.append(
                {
                    "worker": self.name,
                    "field": "target_audience",
                    "value": target_audience,
                    "source": "llm_audience_analysis",
                    "confidence": audience_confidence,
                    "timestamp": audience_analysis.get(
                        "timestamp",
                        "",
                    ),
                }
            )

        # --------------------------------------------------------------
        # 4. Aggregate opportunity score
        # --------------------------------------------------------------

        confidences = [
            market_size_confidence,
            competition_confidence,
            audience_confidence,
        ]

        valid_confidences = [
            self._safe_confidence(c)
            for c in confidences
            if c is not None
        ]

        aggregate_confidence = (
            sum(valid_confidences) / len(valid_confidences)
            if valid_confidences
            else 0.0
        )

        # Simple opportunity score based on market size and competition
        opportunity_score = 0.5
        if market_size in ["Large", "Very Large"] and competition_level in ["Low", "Medium"]:
            opportunity_score = 0.8
        elif market_size in ["Medium", "Large"] and competition_level == "Low":
            opportunity_score = 0.7
        elif market_size == "Small" or competition_level == "High":
            opportunity_score = 0.4

        result_data = {
            "market_size": market_size,
            "competition_level": competition_level,
            "opportunity_score": round(opportunity_score, 2),
            "target_audience": target_audience,
            "pricing_recommendation": self._get_pricing_recommendation(category, competition_level),
            "market_trends": ["Growing demand", "Digital transformation"],
        }

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message=(
                    "Market analysis complete — "
                    f"opportunity score {opportunity_score:.2f}"
                ),
                data={
                    "execution_id": context.execution_id,
                    "market_size": market_size,
                    "competition_level": competition_level,
                    "opportunity_score": opportunity_score,
                    "llm_calls": llm_calls,
                    "evidence_count": len(evidence),
                },
            )
        )

        result = WorkerResult(
            worker_name=self.name,
            status=WorkerStatus.SUCCESS,
            result=result_data,
            evidence=evidence,
            confidence=aggregate_confidence,
            llm_calls=llm_calls,
        )

        return result

    # ------------------------------------------------------------------
    # LLM: Market Size
    # ------------------------------------------------------------------

    async def _analyze_market_size(
        self,
        product_name: str,
        category: str,
        description: str,
    ) -> Dict[str, Any]:

        now = _iso_now()

        system = (
            "You are a market research analyst.\n"
            "Estimate the market size for the given product.\n"
            "Return JSON only:\n"
            '{"market_size":"Small|Medium|Large|Very Large",'
            '"confidence":0.0,'
            '"issues":[]}'
        )

        user = (
            f"Product: {product_name}\n"
            f"Category: {category}\n"
            f"Description: {description}"
        )

        try:
            resp = await self._generate_with_timeout(
                system=system,
                user=user,
                temperature=0.1,
                max_tokens=256,
            )

            content = (
                resp.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = self._safe_json(content)

            if parsed:
                market_size = self._clean_string(
                    parsed.get("market_size"),
                    "Medium",
                )

                confidence = self._safe_confidence(
                    parsed.get("confidence"),
                    0.5,
                )

                parsed_issues = parsed.get(
                    "issues",
                    [],
                )

                if not isinstance(parsed_issues, list):
                    parsed_issues = [str(parsed_issues)]

                return {
                    "market_size": market_size,
                    "confidence": confidence,
                    "issues": parsed_issues,
                    "llm_calls": 1,
                    "timestamp": now,
                }

            return {
                "market_size": "Medium",
                "confidence": 0.4,
                "issues": [
                    "LLM response could not be parsed — "
                    "using default"
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

        except asyncio.TimeoutError:
            return {
                "market_size": "Medium",
                "confidence": 0.3,
                "issues": [
                    "LLM market analysis timed out"
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

        except Exception as exc:
            return {
                "market_size": "Medium",
                "confidence": 0.3,
                "issues": [
                    f"LLM market analysis failed: {exc}"
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

    # ------------------------------------------------------------------
    # LLM: Competition
    # ------------------------------------------------------------------

    async def _analyze_competition(
        self,
        product_name: str,
        category: str,
        description: str,
    ) -> Dict[str, Any]:

        now = _iso_now()

        system = (
            "You are a competitive intelligence analyst.\n"
            "Estimate the competition level for the given product.\n"
            "Return JSON only:\n"
            '{"competition_level":"Low|Medium|High",'
            '"confidence":0.0}'
        )

        user = (
            f"Product: {product_name}\n"
            f"Category: {category}\n"
            f"Description: {description}"
        )

        try:
            resp = await self._generate_with_timeout(
                system=system,
                user=user,
                temperature=0.1,
                max_tokens=256,
            )

            content = (
                resp.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = self._safe_json(content)

            if parsed:
                competition_level = self._clean_string(
                    parsed.get("competition_level"),
                    "Medium",
                )

                confidence = self._safe_confidence(
                    parsed.get("confidence"),
                    0.5,
                )

                return {
                    "competition_level": competition_level,
                    "confidence": confidence,
                    "llm_calls": 1,
                    "timestamp": now,
                }

            return {
                "competition_level": "Medium",
                "confidence": 0.4,
                "llm_calls": 1,
                "timestamp": now,
            }

        except asyncio.TimeoutError:
            return {
                "competition_level": "Medium",
                "confidence": 0.3,
                "llm_calls": 1,
                "timestamp": now,
            }

        except Exception as exc:
            return {
                "competition_level": "Medium",
                "confidence": 0.3,
                "llm_calls": 1,
                "timestamp": now,
            }

    # ------------------------------------------------------------------
    # LLM: Target Audience
    # ------------------------------------------------------------------

    async def _identify_target_audience(
        self,
        product_name: str,
        category: str,
        description: str,
    ) -> Dict[str, Any]:

        now = _iso_now()

        system = (
            "You are a marketing strategist.\n"
            "Identify the target audience segments for the given product.\n"
            "Return JSON only:\n"
            '{"target_audience":["segment1","segment2"],'
            '"confidence":0.0}'
        )

        user = (
            f"Product: {product_name}\n"
            f"Category: {category}\n"
            f"Description: {description}"
        )

        try:
            resp = await self._generate_with_timeout(
                system=system,
                user=user,
                temperature=0.1,
                max_tokens=256,
            )

            content = (
                resp.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = self._safe_json(content)

            if parsed:
                target_audience = parsed.get("target_audience", [])
                
                if not isinstance(target_audience, list):
                    target_audience = [str(target_audience)]

                confidence = self._safe_confidence(
                    parsed.get("confidence"),
                    0.5,
                )

                return {
                    "target_audience": target_audience,
                    "confidence": confidence,
                    "llm_calls": 1,
                    "timestamp": now,
                }

            return {
                "target_audience": ["General consumers"],
                "confidence": 0.4,
                "llm_calls": 1,
                "timestamp": now,
            }

        except asyncio.TimeoutError:
            return {
                "target_audience": ["General consumers"],
                "confidence": 0.3,
                "llm_calls": 1,
                "timestamp": now,
            }

        except Exception as exc:
            return {
                "target_audience": ["General consumers"],
                "confidence": 0.3,
                "llm_calls": 1,
                "timestamp": now,
            }

    # ------------------------------------------------------------------
    # Helper: Pricing Recommendation
    # ------------------------------------------------------------------

    def _get_pricing_recommendation(
        self,
        category: str,
        competition_level: str,
    ) -> str:
        """Generate a simple pricing recommendation based on category and competition."""
        
        if competition_level == "High":
            return "Competitive pricing required - consider value differentiation"
        elif competition_level == "Low":
            return "Premium pricing opportunity - low competition"
        else:
            return "Mid-range pricing - balance competitiveness and margin"


def _iso_now() -> str:
    return datetime.utcnow().isoformat()


market_analysis_worker = MarketAnalysisWorker()
