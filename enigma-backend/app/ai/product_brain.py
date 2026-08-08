import json
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
            {"id": "product_exact", "question": "ما هو المنتج بالضبط؟ صفه بإيجاز.", "type": "text", "purpose": "understand_product"},
            {"id": "target_audience", "question": "من هو جمهورك المستهدف الرئيسي؟", "type": "text", "purpose": "identify_audience"},
            {"id": "price_range", "question": "ما هو السعر المتوقع أو الحالي؟", "type": "text", "purpose": "pricing"},
            {"id": "market_location", "question": "في أي سوق/بلد تبيع أو تخطط للبيع؟", "type": "text", "purpose": "market_location"}
        ]

        smart_questions = await self._generate_smart_questions(product)
        guidance = await master_brain.guide_product_brain(db, product.category, product.target_market or "global", "onboarding")

        return {
            "basic_questions": basic_questions,
            "smart_questions": smart_questions,
            "master_tips": guidance["guidance"],
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
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
            content = response["choices"][0]["message"]["content"]
            json_match = __import__("re").search(r"\[.*\]", content, __import__("re").DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error: {e}")
        return [{"id": "usp", "question": "ما الذي يميز منتجك عن المنافسين؟", "type": "text", "purpose": "unique_selling_point"}]

    async def process_onboarding_answers(self, db, product_id, answers):
        product = await db.get(Product, product_id)
        product.onboarding_data = answers

        prompt = (
            "Analyze this product based on onboarding answers:\n"
            "Product: " + product.name + "\n"
            "Category: " + product.category + "\n"
            "Answers: " + json.dumps(answers, ensure_ascii=False) + "\n"
            "Provide structured understanding in JSON."
        )

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            json_match = __import__("re").search(r"\{.*\}", content, __import__("re").DOTALL)
            if json_match:
                understanding = json.loads(json_match.group())
                product.ai_understanding = understanding
                product.status = "researching"
                await db.commit()
                return {"status": "success", "understanding": understanding, "next_step": "research"}
        except Exception as e:
            print(f"Error: {e}")
        return {"status": "error", "message": "Could not process answers"}

product_brain = ProductBrain()