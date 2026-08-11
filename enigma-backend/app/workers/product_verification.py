"""
Product Verification Worker (Sprint 2)

Receives:
    A Product via the execution context, containing:
    - title / name
    - images
    - description
    - category

Returns:
    A WorkerResult whose result dict contains:
    - verified_name
    - category
    - attributes
    - confidence
    - issues

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


class ProductVerificationWorker(Worker):
    name = "product_verification"

    description = (
        "Verify and normalise a product's name, category, and attributes "
        "from its title, images, and description."
    )

    input_schema = [
        "title",
        "name",
        "images",
        "description",
        "category",
    ]

    output_schema = [
        "verified_name",
        "category",
        "attributes",
        "confidence",
        "issues",
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

    async def _classify_with_timeout(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        return await asyncio.wait_for(
            gateway.classify(
                system=system,
                user=user,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
            timeout=self.LLM_TIMEOUT_SECONDS,
        )

    async def _extract_with_timeout(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        return await asyncio.wait_for(
            gateway.extract(
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
        product: Dict[str, Any] = context.product or {}

        title = self._clean_string(
            product.get("name") or product.get("title")
        )

        description = self._clean_string(
            product.get("description")
        )

        images = (
            product.get("images")
            or product.get("image_urls")
            or []
        )

        if not isinstance(images, list):
            images = [images] if images else []

        reported_category = self._clean_string(
            product.get("category")
        )

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
                type="verification_started",
                message="Product verification started",
                data={
                    "title": title[:80],
                    "has_images": len(images) > 0,
                },
                execution_id=context.execution_id,
            )
        )

        # --------------------------------------------------------------
        # Required input validation
        # --------------------------------------------------------------

        if not title and not description:
            await _emit(
                WorkerEvent(
                    worker_name=self.name,
                    type="error",
                    message=(
                        "No title or description provided — "
                        "cannot verify"
                    ),
                    execution_id=context.execution_id,
                )
            )

            return WorkerResult(
                worker_name=self.name,
                status=WorkerStatus.FAILED,
                error="Product title and description are required",
                confidence=0.0,
                evidence=[],
            )

        evidence: List[Dict[str, Any]] = []
        llm_calls = 0
        issues: List[str] = []

        # --------------------------------------------------------------
        # 1. Title / name analysis
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Analysing product title/name…",
                execution_id=context.execution_id,
            )
        )

        verified_name = title
        name_confidence = 0.5

        if title:
            name_analysis = await self._verify_name(
                title,
                description,
            )

            llm_calls += name_analysis["llm_calls"]

            if name_analysis["verified_name"]:
                verified_name = name_analysis["verified_name"]

            name_confidence = name_analysis["confidence"]

            evidence.append(
                {
                    "worker": self.name,
                    "field": "verified_name",
                    "value": verified_name,
                    "source": "llm_name_analysis",
                    "confidence": name_confidence,
                    "timestamp": name_analysis.get(
                        "timestamp",
                        "",
                    ),
                }
            )

            if name_analysis.get("issues"):
                issues.extend(name_analysis["issues"])

        # --------------------------------------------------------------
        # 2. Category classification
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Classifying category…",
                execution_id=context.execution_id,
            )
        )

        (
            category,
            cat_confidence,
            cat_evidence,
        ) = await self._classify_category(
            title,
            description,
            reported_category,
        )

        llm_calls += cat_evidence.get("llm_calls", 0)

        evidence.extend(
            cat_evidence.get("items", [])
        )

        threshold = 0.7

        if isinstance(context.settings, dict):
            threshold = self._safe_confidence(
                context.settings.get(
                    "confidence_threshold",
                    0.7,
                ),
                0.7,
            )

        if cat_confidence < threshold:
            issues.append(
                f"Category confidence ({cat_confidence:.2f}) "
                "is below threshold"
            )

        # --------------------------------------------------------------
        # 3. Attribute extraction
        # --------------------------------------------------------------

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message="Extracting attributes…",
                execution_id=context.execution_id,
            )
        )

        (
            attributes,
            attr_confidence,
            attr_evidence,
        ) = await self._extract_attributes(
            title,
            description,
            category,
        )

        llm_calls += attr_evidence.get("llm_calls", 0)

        evidence.extend(
            attr_evidence.get("items", [])
        )

        if not attributes:
            issues.append(
                "No structured attributes could be extracted "
                "from the available text"
            )

        # --------------------------------------------------------------
        # 4. Image analysis status
        # --------------------------------------------------------------

        if images:
            await _emit(
                WorkerEvent(
                    worker_name=self.name,
                    type="progress",
                    message=(
                        f"Found {len(images)} image(s) — "
                        "noting visual-analysis gap"
                    ),
                    execution_id=context.execution_id,
                )
            )

            evidence.append(
                {
                    "worker": self.name,
                    "field": "images",
                    "value": f"{len(images)} image(s) provided",
                    "source": "context_input",
                    "confidence": 1.0,
                    "note": (
                        "Visual content analysis requires a "
                        "vision-capable model. Images were not analysed."
                    ),
                }
            )

            issues.append(
                "Images provided but text-only model cannot "
                "perform visual analysis"
            )

        else:
            issues.append(
                "No images provided — visual verification not possible"
            )

        # --------------------------------------------------------------
        # Aggregate confidence
        # --------------------------------------------------------------

        confidences = [
            name_confidence,
            cat_confidence,
            attr_confidence,
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

        result_data = {
            "verified_name": verified_name,
            "category": category,
            "attributes": attributes,
            "confidence": round(
                aggregate_confidence,
                4,
            ),
            "issues": issues,
        }

        await _emit(
            WorkerEvent(
                worker_name=self.name,
                type="progress",
                message=(
                    "Product verification complete — "
                    f"confidence {aggregate_confidence:.2f}"
                ),
                data={
                    "execution_id": context.execution_id,
                    "verified_name": verified_name,
                    "category": category,
                    "confidence": aggregate_confidence,
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

        # --------------------------------------------------------------
        # Memory / episode recording
        # --------------------------------------------------------------

        if context.execution_id:
            context.record_episode(
                worker_name=self.name,
                result=result,
                decision_id=(
                    context.memory.get("decision_id")
                    if isinstance(context.memory, dict)
                    else None
                ),
                product_id=(
                    context.product.get("id")
                    if isinstance(context.product, dict)
                    else None
                ),
                goal=(
                    context.product.get("name")
                    or "product verification"
                ),
            )

        return result

    # ------------------------------------------------------------------
    # LLM: Name
    # ------------------------------------------------------------------

    async def _verify_name(
        self,
        title: str,
        description: str,
    ) -> Dict[str, Any]:

        now = _iso_now()

        system = (
            "You are a meticulous product naming specialist.\n"
            "Normalise the product name to be clean, standardised, "
            "and free of typos.\n"
            "If the title looks like a placeholder or contains "
            "obvious noise, clean it.\n"
            "Do not invent product information.\n"
            "Return JSON only:\n"
            '{"verified_name":"...",'
            '"confidence":0.0,'
            '"issues":[]}'
        )

        user = (
            f"Title: {title}\n"
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
                verified_name = self._clean_string(
                    parsed.get("verified_name"),
                    title,
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
                    "verified_name": verified_name,
                    "confidence": confidence,
                    "issues": parsed_issues,
                    "llm_calls": 1,
                    "timestamp": now,
                }

            return {
                "verified_name": title,
                "confidence": 0.4,
                "issues": [
                    "LLM response could not be parsed — "
                    "using raw title"
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

        except asyncio.TimeoutError:
            return {
                "verified_name": title,
                "confidence": 0.3,
                "issues": [
                    "LLM name analysis timed out"
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

        except Exception as exc:
            return {
                "verified_name": title,
                "confidence": 0.3,
                "issues": [
                    f"LLM name analysis failed: {exc}"
                ],
                "llm_calls": 1,
                "timestamp": now,
            }

    # ------------------------------------------------------------------
    # LLM: Category
    # ------------------------------------------------------------------

    async def _classify_category(
        self,
        title: str,
        description: str,
        reported: str,
    ) -> tuple:

        now = _iso_now()

        system = (
            "You are a product categorisation expert.\n"
            "Given the product title, description, and any reported "
            "category, determine the single best category from:\n"
            "Fashion, Tech, Food, Beauty, Home, Sports, Books, "
            "Toys, Automotive, Industrial, Other.\n"
            "Do not invent facts.\n"
            "Return JSON only:\n"
            '{"category":"...",'
            '"confidence":0.0,'
            '"evidence":"..."}'
        )

        user = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Reported category: "
            f"{reported or 'unknown'}"
        )

        items: List[Dict[str, Any]] = []

        try:
            resp = await self._classify_with_timeout(
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
                category = self._clean_string(
                    parsed.get("category"),
                    reported or "Other",
                )

                confidence = self._safe_confidence(
                    parsed.get("confidence"),
                    0.5,
                )

                items.append(
                    {
                        "worker": self.name,
                        "field": "category",
                        "value": category,
                        "source": (
                            "llm_category_classification"
                        ),
                        "confidence": confidence,
                        "reasoning": parsed.get(
                            "evidence",
                            "",
                        ),
                        "timestamp": now,
                    }
                )

                return (
                    category,
                    confidence,
                    {
                        "items": items,
                        "llm_calls": 1,
                    },
                )

            items.append(
                {
                    "worker": self.name,
                    "field": "category",
                    "value": reported or "Other",
                    "source": "category_fallback",
                    "confidence": 0.2,
                    "reasoning": (
                        "LLM response could not be parsed"
                    ),
                    "timestamp": now,
                }
            )

            return (
                reported or "Other",
                0.2,
                {
                    "items": items,
                    "llm_calls": 1,
                },
            )

        except asyncio.TimeoutError:
            items.append(
                {
                    "worker": self.name,
                    "field": "category",
                    "value": reported or "Other",
                    "source": "category_fallback",
                    "confidence": 0.2,
                    "reasoning": "LLM category analysis timed out",
                    "timestamp": now,
                }
            )

            return (
                reported or "Other",
                0.2,
                {
                    "items": items,
                    "llm_calls": 1,
                },
            )

        except Exception as exc:
            items.append(
                {
                    "worker": self.name,
                    "field": "category",
                    "value": reported or "Other",
                    "source": "fallback_reported_category",
                    "confidence": 0.2,
                    "reasoning": f"LLM call failed: {exc}",
                    "timestamp": now,
                }
            )

            return (
                reported or "Other",
                0.2,
                {
                    "items": items,
                    "llm_calls": 1,
                },
            )

    # ------------------------------------------------------------------
    # LLM: Attributes
    # ------------------------------------------------------------------

    async def _extract_attributes(
        self,
        title: str,
        description: str,
        category: str,
    ) -> tuple:

        now = _iso_now()

        system = (
            "You are a product attribute extraction specialist.\n"
            "Extract structured attributes from the product title "
            "and description.\n"
            "Only extract information actually supported by the text.\n"
            "Do not invent specifications.\n"
            "Return JSON only:\n"
            '{"attributes":{},'
            '"confidence":0.0}'
        )

        user = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Category: {category}"
        )

        items: List[Dict[str, Any]] = []

        try:
            resp = await self._extract_with_timeout(
                system=system,
                user=user,
                temperature=0.1,
                max_tokens=512,
            )

            content = (
                resp.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            parsed = self._safe_json(content)

            if parsed:
                attrs = parsed.get(
                    "attributes",
                    {},
                )

                if not isinstance(attrs, dict):
                    attrs = {}

                confidence = self._safe_confidence(
                    parsed.get("confidence"),
                    0.5,
                )

                items.append(
                    {
                        "worker": self.name,
                        "field": "attributes",
                        "value": attrs,
                        "source": (
                            "llm_attribute_extraction"
                        ),
                        "confidence": confidence,
                        "timestamp": now,
                    }
                )

                return (
                    attrs,
                    confidence,
                    {
                        "items": items,
                        "llm_calls": 1,
                    },
                )

            items.append(
                {
                    "worker": self.name,
                    "field": "attributes",
                    "value": {},
                    "source": "llm_attribute_extraction",
                    "confidence": 0.0,
                    "reasoning": (
                        "LLM response could not be parsed"
                    ),
                    "timestamp": now,
                }
            )

            return (
                {},
                0.0,
                {
                    "items": items,
                    "llm_calls": 1,
                },
            )

        except asyncio.TimeoutError:
            items.append(
                {
                    "worker": self.name,
                    "field": "attributes",
                    "value": {},
                    "source": "llm_attribute_extraction",
                    "confidence": 0.0,
                    "reasoning": (
                        "LLM attribute extraction timed out"
                    ),
                    "timestamp": now,
                }
            )

            return (
                {},
                0.0,
                {
                    "items": items,
                    "llm_calls": 1,
                },
            )

        except Exception as exc:
            items.append(
                {
                    "worker": self.name,
                    "field": "attributes",
                    "value": {},
                    "source": "llm_attribute_extraction",
                    "confidence": 0.0,
                    "reasoning": f"LLM call failed: {exc}",
                    "timestamp": now,
                }
            )

            return (
                {},
                0.0,
                {
                    "items": items,
                    "llm_calls": 1,
                },
            )


def _iso_now() -> str:
    return datetime.utcnow().isoformat()


product_verification_worker = ProductVerificationWorker()