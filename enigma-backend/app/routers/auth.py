from datetime import datetime, timedelta
from typing import Optional
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    plan: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

def _prehash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle bcrypt's 72-byte limit.
    
    This preserves full password entropy while staying within bcrypt's constraints.
    SHA-256 produces a 32-byte (64 hex character) hash, well within bcrypt's limit.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Supports both:
    1. New method: SHA-256 pre-hash + bcrypt (for passwords > 72 bytes)
    2. Old method: Direct bcrypt (for backward compatibility with existing users)
    """
    # Try new method first (SHA-256 pre-hash)
    prehashed = _prehash_password(plain_password)
    if pwd_context.verify(prehashed, hashed_password):
        return True
    
    # Try old method (direct bcrypt) for backward compatibility
    if pwd_context.verify(plain_password, hashed_password):
        return True
    
    return False

def get_password_hash(password: str) -> str:
    """
    Hash password using SHA-256 pre-hash + bcrypt.
    
    This method handles passwords of any length by first pre-hashing with SHA-256,
    then applying bcrypt. The SHA-256 hash is always 32 bytes (64 hex chars),
    well within bcrypt's 72-byte limit.
    """
    prehashed = _prehash_password(password)
    return pwd_context.hash(prehashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_data.email, name=user_data.name, hashed_password=get_password_hash(user_data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
