from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.routers.auth import get_current_user
from app.ai.product_brain import product_brain

router = APIRouter(prefix="/products", tags=["products"])

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    domain: Optional[str] = None
    target_market: Optional[str] = "global"

class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    status: str
    created_at: Optional[str] = None
    
    @classmethod
    def from_product(cls, product: Product) -> "ProductResponse":
        return cls(
            id=str(product.id),
            name=product.name,
            category=product.category,
            status=product.status,
            created_at=product.created_at.isoformat() if product.created_at else None
        )

class OnboardingAnswers(BaseModel):
    answers: dict

@router.post("", response_model=ProductResponse)
async def create_product(data: ProductCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    product = Product(user_id=current_user.id, name=data.name, description=data.description, category=data.category, subcategory=data.subcategory, domain=data.domain, target_market=data.target_market, status="onboarding")
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return ProductResponse.from_product(product)

@router.get("", response_model=List[ProductResponse])
async def list_products(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.user_id == current_user.id).order_by(desc(Product.created_at)))
    products = result.scalars().all()
    return [ProductResponse.from_product(p) for p in products]

@router.get("/{product_id}")
async def get_product(product_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.from_product(product)

@router.get("/{product_id}/onboarding")
async def get_onboarding_questions(product_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    questions = await product_brain.onboard(db, product_id)
    return questions

@router.post("/{product_id}/onboarding")
async def submit_onboarding_answers(product_id: str, data: OnboardingAnswers, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.user_id == current_user.id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    result = await product_brain.process_onboarding_answers(db, product_id, data.answers)
    return result
