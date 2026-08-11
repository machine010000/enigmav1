"""
Context Builder — constructs an ExecutionContext from database models.

Part of TASK-003 (Execution Context) and TASK-004 (Execution Pipeline).
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.contracts import ExecutionContext
from app.models.user import User
from app.models.product import Product
from app.models.knowledge import MasterKnowledge


async def build_context(
    db: Optional[AsyncSession],
    user: Optional[User] = None,
    product: Optional[Product] = None,
    product_id: Optional[str] = None,
    user_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    extra_memory: Optional[Dict[str, Any]] = None,
) -> ExecutionContext:
    """
    Build a fully-populated ExecutionContext.

    Will fetch User and Product from the DB if only IDs are provided.
    Falls back gracefully to empty dicts when db / objects are unavailable.
    """
    memory: Dict[str, Any] = dict(extra_memory or {})

    # ---- user ----
    # TEMPORARY DIAGNOSTIC: bypass user DB query
    user_dict: Dict[str, Any] = {}
    if user is not None:
        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "plan": user.plan,
            "onboarding_data": user.__dict__.get("onboarding_data", {}),
        }
        memory["_user_id"] = user_dict["id"]

    # ---- product ----
    # TEMPORARY DIAGNOSTIC: bypass product DB query
    product_dict: Dict[str, Any] = {}
    if product is not None:
        product_dict = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "subcategory": product.subcategory,
            "domain": product.domain,
            "target_market": product.target_market,
            "status": product.status,
            "onboarding_data": product.onboarding_data or {},
            "ai_understanding": product.ai_understanding or {},
        }
        memory["_product_id"] = product_dict["id"]

    # ---- knowledge ----
    # TEMPORARY DIAGNOSTIC: bypass DB knowledge query
    knowledge_list: list = []

    settings_dict: Dict[str, Any] = {
        "confidence_threshold": 0.7,
        "max_llm_calls": 10,
    }

    return ExecutionContext(
        user=user_dict,
        product=product_dict,
        memory=memory,
        knowledge=knowledge_list,
        settings=settings_dict,
        history=[],
        execution_id=execution_id or str(uuid.uuid4()),
    )
