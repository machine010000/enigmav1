import json
import re
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import gateway
from app.ai.master_brain import master_brain
from app.models.product import Product


class ProductBrain:

    async def onboard(self, db, product_id):
        product = await db.get(Product, product_id)

        if not product:
            raise ValueError(f"Product {product_id} not found")

        basic_questions = [
            {
                "id": "product_exact",
                "question": "ما هو المنتج بالضبط؟ صفه بإيجاز.",
                "type": "text",
                "purpose": "understand_product"
            },
            {
                "id": "target_audience",
                "question": "من هو جمهورك المستهدف الرئيسي؟",
                "type": "text",
                "purpose": "identify_audience"
            },
            {
                "id": "price_range",
                "question": "ما هو السعر المتوقع أو الحالي؟",
                "type": "text",
                "purpose": "pricing"
            },
            {
                "id": "market_location",
                "question": "في أي سوق/بلد تبيع أو تخطط للبيع؟",
                "type": "text",
                "purpose": "market_location"
            }
        ]

        # AI-generated questions have a safe fallback.
        smart_questions = await self._generate_smart_questions(product)

        # Master Brain must NEVER make onboarding fail.
        default_guidance = [
            "حدد القيمة الأساسية للمنتج بوضوح.",
            "حدد العميل المستهدف والمشكلة التي يحلها المنتج.",
            "اجمع معلومات واضحة عن السعر والسوق والمنافسين."
        ]

        try:
            guidance_result = await master_brain.guide_product_brain(
                db,
                product.category,
                product.target_market or "global",
                "onboarding"
            )

            guidance = (
                guidance_result.get("guidance")
                if isinstance(guidance_result, dict)
                else None
            )

            if not guidance:
                guidance = default_guidance

        except Exception as e:
            print(f"Master Brain unavailable during onboarding: {e}")
            guidance = default_guidance

        return {
            "basic_questions": basic_questions,
            "smart_questions": smart_questions,
            "master_tips": guidance,
            "total_questions": len(basic_questions) + len(smart_questions)
        }

    async def _generate_smart_questions(self, product):
        prompt = (
            "Generate 5 specific onboarding questions for this product:\n"
            "Product: " + product.name + "\n"
            "Category: " + product.category + "\n"
            "Subcategory: " + (product.subcategory or "unknown") + "\n"
            "Market: " + (product.target_market or "global") + "\n"
            "Respond in JSON array format."
        )

        try:
            response = await gateway.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )

            content = response["choices"][0]["message"]["content"]

            json_match = re.search(r"\[.*\]", content, re.DOTALL)

            if json_match:
                questions = json.loads(json_match.group())

                if isinstance(questions, list) and questions:
                    return questions

        except Exception as e:
            print(f"Smart question generation unavailable: {e}")

        return [
            {
                "id": "usp",
                "question": "ما الذي يميز منتجك عن المنافسين؟",
                "type": "text",
                "purpose": "unique_selling_point"
            }
        ]

    async def process_onboarding_answers(self, db, product_id, answers):
        product = await db.get(Product, product_id)

        if not product:
            raise ValueError(f"Product {product_id} not found")

        product.onboarding_data = answers

        prompt = (
            "Analyze this product based on onboarding answers:\n"
            "Product: " + product.name + "\n"
            "Category: " + product.category + "\n"
            "Answers: " + json.dumps(answers, ensure_ascii=False) + "\n"
            "Provide structured understanding in JSON."
        )

        try:
            response = await gateway.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1500
            )

            content = response["choices"][0]["message"]["content"]

            json_match = re.search(r"\{.*\}", content, re.DOTALL)

            if json_match:
                understanding = json.loads(json_match.group())

                product.ai_understanding = understanding
                product.status = "researching"

                await db.commit()

                return {
                    "status": "success",
                    "understanding": understanding,
                    "next_step": "research"
                }

        except Exception as e:
            print(f"AI onboarding analysis unavailable: {e}")

        # AI unavailable: keep the answers and allow the workflow to continue.
        fallback_understanding = {
            "product_name": product.name,
            "category": product.category,
            "answers": answers,
            "analysis_status": "pending_ai_analysis"
        }

        product.ai_understanding = fallback_understanding
        product.status = "researching"

        await db.commit()

        return {
            "status": "success",
            "understanding": fallback_understanding,
            "next_step": "research",
            "ai_analysis": "pending"
        }


product_brain = ProductBrain()