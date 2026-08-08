import os

BASE = r"E:\app\enigma\enigma-backend"

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fixed: {path}")

# Fix master_brain.py - using single quotes and concatenation
mb_content = """import json
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.ai.client import nvidia_client
from app.models.knowledge import MasterKnowledge

class MasterBrain:
    SYSTEM_PROMPT = (
        "You are ENIGMA's Master Brain - the central intelligence hub.\n"
        "You have deep knowledge of business, marketing, and consumer psychology.\n"
        "You learn from every interaction and improve your guidance over time.\n"
        "When the user teaches you something, store it precisely.\n"
        "When asked for guidance, use your accumulated knowledge.\n"
        "Always think step-by-step and provide actionable insights."
    )

    async def chat(self, db, user_id, message):
        intent = await self._detect_intent(message)
        knowledge = await self._get_relevant_knowledge(db, message)
        context = self._build_context(knowledge)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT + "\n\n" + context},
            {"role": "user", "content": message}
        ]

        response = await nvidia_client.chat(messages, temperature=0.7)
        reply = response["choices"][0]["message"]["content"]

        if intent == "teach":
            extracted = await self._extract_knowledge(message, reply)
            if extracted:
                await self._store_knowledge(db, user_id, extracted)
                reply += "\n\n[✓] Learned: " + extracted["key"]

        return {"reply": reply, "intent": intent, "knowledge_used": len(knowledge)}

    async def _detect_intent(self, message):
        prompt = (
            'Analyze this message and classify intent:\n'
            'Message: "' + message + '"\n'
            'Choose one: teach, ask, command, feedback, chat\n'
            'Respond with just the intent word.'
        )
        response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=20)
        intent = response["choices"][0]["message"]["content"].strip().lower()
        return intent if intent in ["teach", "ask", "command", "feedback"] else "chat"

    async def _get_relevant_knowledge(self, db, query, limit=5):
        result = await db.execute(select(MasterKnowledge).limit(limit))
        return result.scalars().all()

    def _build_context(self, knowledge):
        if not knowledge:
            return ""
        context = "Relevant knowledge:\n"
        for k in knowledge:
            context += f"- [{k.category}] {k.key}: {k.value}\n"
        return context

    async def _extract_knowledge(self, message, reply):
        prompt = (
            'Extract structured knowledge from this teaching message.\n'
            'Message: "' + message + '"\n'
            'Respond in JSON format:\n'
            '{"category": "marketing|market|product|audience|other", '
            '"domain": "fashion|tech|food|general", '
            '"market": "egypt|saudi|global|unknown", '
            '"key": "short_key_name", '
            '"value": "detailed knowledge", '
            '"confidence": 0.8}'
        )
        try:
            response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=500)
            content = response["choices"][0]["message"]["content"]
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return None

    async def _store_knowledge(self, db, user_id, knowledge):
        mk = MasterKnowledge(
            category=knowledge.get("category", "general"),
            domain=knowledge.get("domain", "general"),
            market=knowledge.get("market", "global"),
            key=knowledge["key"],
            value=knowledge["value"],
            confidence=knowledge.get("confidence", 0.5),
            source="user_taught"
        )
        db.add(mk)
        await db.commit()

    async def guide_product_brain(self, db, product_category, product_market, task):
        result = await db.execute(select(MasterKnowledge).limit(10))
        knowledge = result.scalars().all()
        guidance = (
            "Guide product brain for:\n"
            "Category: " + product_category + "\n"
            "Market: " + product_market + "\n"
            "Task: " + task + "\n"
            "Accumulated wisdom:\n"
        )
        for k in knowledge:
            guidance += f"- {k.key}: {k.value} (confidence: {k.confidence})\n"
        response = await nvidia_client.chat([
            {"role": "system", "content": "You are guiding a product AI. Provide specific, actionable guidance."},
            {"role": "user", "content": guidance}
        ])
        return {"guidance": response["choices"][0]["message"]["content"], "knowledge_applied": len(knowledge)}

master_brain = MasterBrain()
"""

write_file(os.path.join(BASE, "app", "ai", "master_brain.py"), mb_content)

# Fix product_brain.py
pb_content = """import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.client import nvidia_client
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

        return {"basic_questions": basic_questions, "smart_questions": smart_questions, "master_tips": guidance["guidance"], "total_questions": len(basic_questions) + len(smart_questions)}

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
            response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
            content = response["choices"][0]["message"]["content"]
            json_match = __import__('re').search(r'\[.*\]', content, __import__('re').DOTALL)
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
            response = await nvidia_client.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            json_match = __import__('re').search(r'\{.*\}', content, __import__('re').DOTALL)
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
"""

write_file(os.path.join(BASE, "app", "ai", "product_brain.py"), pb_content)

print("All broken files fixed!")