"""
User Brain - The orchestrator for each user
Detects user type, manages journeys, and delegates to workers
"""
import json
from typing import Dict, Any, List, Optional
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.ai.gateway import gateway
from app.ai.master_brain import master_brain
from app.models.user import User

class UserType(Enum):
    SELLER = "seller"
    SERVICE_PROVIDER = "service_provider"
    CONTENT_CREATOR = "content_creator"
    INVESTOR = "investor"
    UNKNOWN = "unknown"

class UserBrain:
    """
    Each user has their own User Brain that:
    1. Detects user type from behavior/conversation
    2. Manages User Journey / Product Journey / Production Journey
    3. Develops custom research systems
    4. Orchestrates Worker Brains via APIs
    5. Learns and evolves systems over time
    """

    async def detect_user_type(self, db: AsyncSession, user_id: str, conversation: str = "") -> Dict[str, Any]:
        """
        Detect user type from conversation or onboarding answers
        """
        user = await db.get(User, user_id)

        prompt = f"""Analyze this user and determine their type:
User Name: {user.name}
Conversation/Context: {conversation}

Choose ONE type and explain why:
- seller: sells physical products
- service_provider: offers services
- content_creator: creates content for monetization
- investor: invests in businesses/products
- unknown: not enough information

Respond in JSON:
{{
    "user_type": "seller|service_provider|content_creator|investor|unknown",
    "confidence": 0.0-1.0,
    "reasoning": "why this type",
    "recommended_workers": ["worker1", "worker2"],
    "suggested_journeys": ["journey1", "journey2"]
}}"""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=800)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Store in user profile
                user.onboarding_data = user.onboarding_data or {}
                user.onboarding_data["user_type"] = result
                await db.commit()
                return result
        except Exception as e:
            print(f"Error detecting user type: {e}")

        return {
            "user_type": "unknown",
            "confidence": 0.0,
            "reasoning": "Could not determine",
            "recommended_workers": [],
            "suggested_journeys": []
        }

    async def create_user_journey(self, db: AsyncSession, user_id: str, user_type: str) -> Dict[str, Any]:
        """
        Create User Journey based on user type
        """
        prompt = f"""Create a detailed User Journey for a {user_type}.

Include these phases:
1. Discovery - how they find ENIGMA
2. Onboarding - first experience
3. Daily Usage - regular workflow
4. Growth - scaling their business
5. Mastery - advanced features

For each phase include:
- actions
- emotions
- pain points
- ENIGMA features that help

Respond in JSON format."""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                journey = json.loads(json_match.group())
                # Store journey
                user = await db.get(User, user_id)
                user.onboarding_data = user.onboarding_data or {}
                user.onboarding_data["user_journey"] = journey
                await db.commit()
                return journey
        except Exception as e:
            print(f"Error creating journey: {e}")

        return {"phases": []}

    async def create_product_journey(self, db: AsyncSession, user_id: str, product_id: str) -> Dict[str, Any]:
        """
        Create Product Journey - from idea to market success
        """
        from app.models.product import Product
        product = await db.get(Product, product_id)

        prompt = f"""Create a Product Journey for:
Product: {product.name}
Category: {product.category}
Market: {product.target_market or "global"}

Phases:
1. Research & Validation
2. Development & Testing
3. Launch & Marketing
4. Growth & Scaling
5. Optimization & Learning

For each phase include:
- key activities
- success metrics
- ENIGMA automation
- timeline

Respond in JSON."""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                journey = json.loads(json_match.group())
                product.ai_understanding = product.ai_understanding or {}
                product.ai_understanding["product_journey"] = journey
                await db.commit()
                return journey
        except Exception as e:
            print(f"Error: {e}")

        return {"phases": []}

    async def create_production_journey(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Create Production Journey - how user creates/delivers value
        """
        user = await db.get(User, user_id)
        user_type = user.onboarding_data.get("user_type", {}).get("user_type", "unknown") if user.onboarding_data else "unknown"

        prompt = f"""Create a Production Journey for a {user_type}.

This covers HOW they create/deliver their product/service:
1. Content Creation Process (for creators)
2. Service Delivery Process (for service providers)
3. Product Sourcing/Manufacturing (for sellers)
4. Investment Analysis Process (for investors)

Include:
- workflow steps
- tools needed
- automation opportunities
- quality checkpoints

Respond in JSON."""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                journey = json.loads(json_match.group())
                user.onboarding_data = user.onboarding_data or {}
                user.onboarding_data["production_journey"] = journey
                await db.commit()
                return journey
        except Exception as e:
            print(f"Error: {e}")

        return {"phases": []}

    async def develop_research_system(self, db: AsyncSession, user_id: str, product_category: str) -> Dict[str, Any]:
        """
        User Brain develops custom research system for a category
        Learns from previous research and improves
        """
        user = await db.get(User, user_id)

        # Check if we have previous research systems
        existing_systems = user.onboarding_data.get("research_systems", {}) if user.onboarding_data else {}

        prompt = f"""Develop a research system for: {product_category}

Existing systems: {json.dumps(existing_systems, ensure_ascii=False)}

Create a comprehensive research framework:
{{
    "sources": [
        {{"name": "source_name", "priority": 1-5, "query_template": "how to search", "data_to_extract": ["field1", "field2"], "automation_level": "manual|semi|full"}}
    ],
    "analysis_framework": {{
        "metrics": ["metric1", "metric2"],
        "comparison_criteria": ["criteria1", "criteria2"],
        "scoring_system": "description"
    }},
    "learning_rules": [
        "rule1: what to remember",
        "rule2: what to improve next time"
    ],
    "output_format": {{
        "report_structure": ["section1", "section2"],
        "confidence_threshold": 0.8
    }}
}}

This system should EVOLVE - each product researched improves the system."""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.4, max_tokens=2000)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                system = json.loads(json_match.group())
                user.onboarding_data = user.onboarding_data or {}
                user.onboarding_data["research_systems"] = user.onboarding_data.get("research_systems", {})
                user.onboarding_data["research_systems"][product_category] = system
                await db.commit()
                return system
        except Exception as e:
            print(f"Error: {e}")

        return {"sources": [], "analysis_framework": {}}

    async def orchestrate_workers(self, db: AsyncSession, user_id: str, task: str, context: Dict) -> Dict[str, Any]:
        """
        User Brain decides which workers to call and what to ask them
        """
        user = await db.get(User, user_id)
        user_type = user.onboarding_data.get("user_type", {}).get("user_type", "unknown") if user.onboarding_data else "unknown"

        prompt = f"""As User Brain, orchestrate this task:

User Type: {user_type}
Task: {task}
Context: {json.dumps(context, ensure_ascii=False)}

Available Workers:
1. seller_worker - for e-commerce, products, listings
2. content_worker - for content creation, social media
3. service_worker - for service delivery, client management
4. investor_worker - for market analysis, investments
5. research_worker - for data gathering, analysis

Decide:
- Which workers to call?
- What to ask each worker?
- In what order?
- How to combine results?

Respond in JSON:
{{
    "plan": [
        {{
            "step": 1,
            "worker": "worker_name",
            "task": "what to do",
            "input": {{}},
            "expected_output": ""
        }}
    ],
    "fallback": "what if workers fail"
}}"""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.4, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error: {e}")

        return {"plan": [], "fallback": "manual execution"}

    async def evolve_system(self, db: AsyncSession, user_id: str, feedback: str) -> Dict[str, Any]:
        """
        User Brain evolves its systems based on feedback
        """
        user = await db.get(User, user_id)
        current_systems = user.onboarding_data or {}

        prompt = f"""Evolve the user's systems based on feedback:

Current Systems: {json.dumps(current_systems, ensure_ascii=False)}
Feedback: {feedback}

What should change?
- Which systems need improvement?
- What new systems needed?
- What to remove?

Respond with evolution plan in JSON."""

        try:
            response = await gateway.chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=1500)
            content = response["choices"][0]["message"]["content"]
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                evolution = json.loads(json_match.group())
                # Apply evolution
                user.onboarding_data = user.onboarding_data or {}
                user.onboarding_data["system_evolution"] = evolution
                await db.commit()
                return evolution
        except Exception as e:
            print(f"Error: {e}")

        return {"changes": [], "reason": "Could not evolve"}

user_brain = UserBrain()