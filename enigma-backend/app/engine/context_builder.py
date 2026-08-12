"""
Context Builder — constructs an ExecutionContext from database models.

TASK-016: Product ownership is now validated before context is built.
If the requesting user does not own the product, a PermissionError is
raised so the caller (orchestrator / router) can return 404 per the
project convention (hiding resource existence for unauthorised users).

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


class ProductOwnershipError(Exception):
    """Raised when a user attempts to access a product they do not own."""


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

    TASK-016: Ownership enforcement
    --------------------------------
    When both user_id and product_id are provided with a DB session this
    function verifies that the product belongs to the authenticated user
    using the canonical WHERE product.id = X AND product.user_id = user_id
    query.  If the product does not exist *for that user* a
    ProductOwnershipError is raised — the caller should translate this to
    HTTP 404 (hiding whether the product exists for another user).
    """
    memory: Dict[str, Any] = dict(extra_memory or {})

    # ---- user ----
    user_dict: Dict[str, Any] = {}
    if user is None and user_id and db is not None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
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

    # ---- product — ownership enforced ----
    product_dict: Dict[str, Any] = {}
    if product is None and product_id and db is not None:
        if user_id:
            # TASK-016: canonical ownership check — same pattern as products router
            result = await db.execute(
                select(Product).where(
                    Product.id == product_id,
                    Product.user_id == user_id,
                )
            )
            product = result.scalar_one_or_none()
            if product is None:
                # Follow project convention: 404 — do not reveal existence
                raise ProductOwnershipError(
                    f"Product '{product_id}' not found for the current user"
                )
        else:
            # No user_id provided — fall back to unowned lookup (internal use only)
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one_or_none()

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
    knowledge_list: list = []
    if db is not None:
        result = await db.execute(
            select(MasterKnowledge).order_by(MasterKnowledge.created_at.desc()).limit(50)
        )
        knowledge_list = [
            {
                "id": str(k.id),
                "category": k.category,
                "domain": k.domain,
                "market": k.market,
                "key": k.key,
                "value": k.value,
                "confidence": k.confidence,
                "source": k.source,
            }
            for k in result.scalars().all()
        ]

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
