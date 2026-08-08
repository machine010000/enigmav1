"""
Product Verification Worker (Sprint 2)

Receives
-------
A Product via the execution context, containing:
    - title / name
    - images   (list of URLs — may be empty)
    - description

Returns
-------
A WorkerResult whose ``result`` dict contains:
    - verified_name   : the canonical, normalised product name
    - category         : the most-likely product category
    - attributes       : extracted product attributes (material, color, etc.)
    - confidence       : aggregate 0–1 confidence
    - issues           : list of data-quality or ambiguity issues found

Evidence-First Architecture
---------------------------
Every value returned carries an ``evidence`` entry: which sub-worker
produced it, the source of truth, and a per-claim confidence.  This lets the
Brain trace, review, and re-evaluate any decision when new information
arrives — without hallucinating.
"""
from __future__ import annotations

import json
import re
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
    description = "Verify and normalise a product's name, category, and attributes from its title, images, and description."
    input_schema = ["title", "name", "images", "description", "category"]
    output_schema = ["verified_name", "category", "attributes", "confidence", "issues"]

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _safe_json(text: str) -> Optional[dict]:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
        return None

    # ------------------------------------------------------------------ run
    async def run(self, context: ExecutionContext) -> WorkerResult:
        product: Dict[str, Any] = context.product or {}
        title: str = (product.get("name") or product.get("title") or "").strip()
        description: str = (product.get("description") or "").strip()
        images: List[str] = product.get("images") or product.get("image_urls") or []
        reported_category: str = (product.get("category") or "").strip()

        emit = context.emit

        async def _emit(event: WorkerEvent) -> None:
            if emit is not None:
                await emit(event)

        # ---- announce ----
        await _emit(WorkerEvent(
            worker_name=self.name,
            type="verification_started",
            message="Product verification started",
            data={"title": title[:80], "has_images": len(images) > 0},
            execution_id=context.execution_id,
        ))

        if not title and not description:
            await _emit(WorkerEvent(
                worker_name=self.name, type="error",
                message="No title or description provided — cannot verify",
                execution_id=context.execution_id,
            ))
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

        # ---- 1. Title / name analysis ----
        await _emit(WorkerEvent(
            worker_name=self.name, type="progress",
            message="Analysing product title/name…",
            execution_id=context.execution_id,
        ))
        verified_name = title
        name_confidence = 0.5
        if title:
            name_analysis = await self._verify_name(title, description)
            llm_calls += name_analysis["llm_calls"]
            if name_analysis["verified_name"]:
                verified_name = name_analysis["verified_name"]
                name_confidence = name_analysis["confidence"]
            evidence.append({
                "worker": self.name,
                "field": "verified_name",
                "value": verified_name,
                "source": "llm_name_analysis",
                "confidence": name_confidence,
                "timestamp": name_analysis.get("timestamp", ""),
            })
            if name_analysis.get("issues"):
                issues.extend(name_analysis["issues"])

        # ---- 2. Category classification ----
        await _emit(WorkerEvent(
            worker_name=self.name, type="progress",
            message="Classifying category…",
            execution_id=context.execution_id,
        ))
        category, cat_confidence, cat_evidence = await self._classify_category(
            title, description, reported_category
        )
        llm_calls += cat_evidence.get("llm_calls", 0)
        evidence.extend(cat_evidence["items"])
        if not cat_evidence.get("confidence", 0) >= context.settings.get("confidence_threshold", 0.7):
            issues.append(f"Category confidence ({cat_confidence:.2f}) is below threshold")

        # ---- 3. Attribute extraction ----
        await _emit(WorkerEvent(
            worker_name=self.name, type="progress",
            message="Extracting attributes…",
            execution_id=context.execution_id,
        ))
        attributes, attr_confidence, attr_evidence = await self._extract_attributes(
            title, description, category
        )
        llm_calls += attr_evidence.get("llm_calls", 0)
        evidence.extend(attr_evidence["items"])
        if not attributes:
            issues.append("No structured attributes could be extracted from the available text")

        # ---- 4. Issue detection ----
        if images:
            await _emit(WorkerEvent(
                worker_name=self.name, type="progress",
                message=f"Found {len(images)} image(s) — noting visual-analysis gap",
                execution_id=context.execution_id,
            ))
            evidence.append({
                "worker": self.name,
                "field": "images",
                "value": f"{len(images)} image(s) provided",
                "source": "context_input",
                "confidence": 1.0,
                "note": "Visual content analysis requires a vision-capable model (current model is text-only). "
                        "Images were not analysed.",
            })
            issues.append("Images provided but text-only model cannot perform visual analysis")
        else:
            issues.append("No images provided — visual verification not possible")

        # ---- aggregate confidence ----
        confidences = [name_confidence, cat_confidence, attr_confidence]
        valid_confidences = [c for c in confidences if c is not None]
        aggregate_confidence = sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0

        result_data = {
            "verified_name": verified_name,
            "category": category,
            "attributes": attributes,
            "confidence": round(aggregate_confidence, 4),
            "issues": issues,
        }

        await _emit(WorkerEvent(
            worker_name=self.name,
            type="progress",
            message=f"Product verification complete — confidence {aggregate_confidence:.2f}",
            data={
                "execution_id": context.execution_id,
                "verified_name": verified_name,
                "category": category,
                "confidence": aggregate_confidence,
                "llm_calls": llm_calls,
                "evidence_count": len(evidence),
            },
        ))

        result = WorkerResult(
            worker_name=self.name,
            status=WorkerStatus.SUCCESS,
            result=result_data,
            evidence=evidence,
            confidence=aggregate_confidence,
            llm_calls=llm_calls,
        )
        if context.execution_id:
            context.record_episode(
                worker_name=self.name,
                result=result,
                decision_id=context.memory.get("decision_id") if isinstance(context.memory, dict) else None,
                product_id=context.product.get("id") if isinstance(context.product, dict) else None,
                goal=context.product.get("name") or "product verification",
            )
        return result

    # ------------------------------------------------------------------ LLM calls
    async def _verify_name(self, title: str, description: str) -> Dict[str, Any]:
        now = _iso_now()
        system = (
            "You are a meticulous product naming specialist.\n"
            "Normalise the product name to be clean, standardised, and free of typos.\n"
            "If the title looks like a placeholder or contains obvious noise, clean it.\n"
            "Return JSON only: {\"verified_name\": \"...\", \"confidence\": 0.0-1.0, \"issues\": [\"...\"]}"
        )
        user = f"Title: {title}\nDescription: {description}"
        try:
            resp = await gateway.generate(
                system=system, user=user,
                temperature=0.1, max_tokens=256,
            )
            content = resp["choices"][0]["message"]["content"]
            parsed = self._safe_json(content)
            if parsed:
                return {
                    "verified_name": parsed.get("verified_name", title),
                    "confidence": float(parsed.get("confidence", 0.5)),
                    "issues": parsed.get("issues", []),
                    "llm_calls": 1,
                    "timestamp": now,
                }
        except Exception as exc:
            return {
                "verified_name": title,
                "confidence": 0.3,
                "issues": [f"LLM name analysis failed: {exc}"],
                "llm_calls": 1,
                "timestamp": now,
            }
        return {
            "verified_name": title,
            "confidence": 0.4,
            "issues": ["LLM response could not be parsed — using raw title"],
            "llm_calls": 1,
            "timestamp": now,
        }

    async def _classify_category(
        self, title: str, description: str, reported: str
    ) -> tuple:
        now = _iso_now()
        system = (
            "You are a product categorisation expert.\n"
            "Given the product title, description, and any reported category,\n"
            "determine the single best category from the ENIGMA category tree:\n"
            "Fashion, Tech, Food, Beauty, Home, Sports, Books, Toys, Automotive, Industrial, Other.\n"
            "Return JSON: {\"category\": \"...\", \"confidence\": 0.0-1.0, \"evidence\": \"...\"}"
        )
        user = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Reported category: {reported or 'unknown'}"
        )
        items: List[Dict[str, Any]] = []
        try:
            resp = await gateway.classify(
                system=system, user=user,
                temperature=0.1, max_tokens=256,
            )
            content = resp["choices"][0]["message"]["content"]
            parsed = self._safe_json(content)
            if parsed:
                cat = parsed.get("category", reported or "Other")
                conf = float(parsed.get("confidence", 0.5))
                items.append({
                    "worker": self.name,
                    "field": "category",
                    "value": cat,
                    "source": "llm_category_classification",
                    "confidence": conf,
                    "reasoning": parsed.get("evidence", ""),
                    "timestamp": now,
                })
                return cat, conf, {"items": items, "llm_calls": 1}
        except Exception as exc:
            items.append({
                "worker": self.name,
                "field": "category",
                "value": reported or "Other",
                "source": "fallback_reported_category",
                "confidence": 0.2,
                "reasoning": f"LLM call failed: {exc}",
                "timestamp": now,
            })
            return reported or "Other", 0.2, {"items": items, "llm_calls": 1}

        return reported or "Other", 0.2, {"items": items, "llm_calls": 1}

    async def _extract_attributes(
        self, title: str, description: str, category: str
    ) -> tuple:
        now = _iso_now()
        system = (
            "You are a product attribute extraction specialist.\n"
            "Extract structured attributes (material, color, size, style, key features, etc.)\n"
            "from the product title and description.\n"
            "Return JSON: {\"attributes\": {...}, \"confidence\": 0.0-1.0}"
        )
        user = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Category: {category}"
        )
        items: List[Dict[str, Any]] = []
        try:
            resp = await gateway.extract(
                system=system, user=user,
                temperature=0.1, max_tokens=512,
            )
            content = resp["choices"][0]["message"]["content"]
            parsed = self._safe_json(content)
            if parsed:
                attrs = parsed.get("attributes", {})
                conf = float(parsed.get("confidence", 0.5))
                items.append({
                    "worker": self.name,
                    "field": "attributes",
                    "value": attrs,
                    "source": "llm_attribute_extraction",
                    "confidence": conf,
                    "timestamp": now,
                })
                return attrs, conf, {"items": items, "llm_calls": 1}
        except Exception as exc:
            items.append({
                "worker": self.name,
                "field": "attributes",
                "value": {},
                "source": "llm_attribute_extraction",
                "confidence": 0.0,
                "reasoning": f"LLM call failed: {exc}",
                "timestamp": now,
            })
            return {}, 0.0, {"items": items, "llm_calls": 1}

        return {}, 0.0, {"items": items, "llm_calls": 1}


def _iso_now() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat()


product_verification_worker = ProductVerificationWorker()
