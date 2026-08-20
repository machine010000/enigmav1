from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from argon2 import PasswordHasher
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.core.config import get_settings
from app.models.user import User
import os
from sqlalchemy import insert

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)
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
    
    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            plan=user.plan
        )

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash using Argon2.
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """
    Hash password using Argon2.
    
    Argon2 is a modern, secure password hashing algorithm that handles
    passwords of any length without pre-hashing requirements.
    """
    return ph.hash(password)

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


async def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated bootstrap-admin identity."""
    admin_email = settings.ADMIN_USER_EMAIL.strip().lower()
    if (
        not admin_email
        or current_user.email.strip().lower() != admin_email
        or current_user.plan != "admin"
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

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


@router.post("/admin-login", response_model=Token)
async def admin_login(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Temporary bootstrap admin login.

    Accepts JSON body: {"username": "...", "password": "..."}
    Validates against environment variables `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
    On success, ensures a local admin User exists and returns an access token for that user.

    NOTE: Development-only convenience. In production set ADMIN_USERNAME/ADMIN_PASSWORD
    via environment and avoid using defaults.
    """
    username = payload.get("username")
    password = payload.get("password")

    # Development-safe defaults allowed only when not running in production
    env = os.getenv("ENVIRONMENT", "development").lower()
    env_admin_user = os.getenv("ADMIN_USERNAME")
    env_admin_pass = os.getenv("ADMIN_PASSWORD")

    # If not provided via env and running production, reject
    if env == "production" and (not env_admin_user or not env_admin_pass):
        raise HTTPException(status_code=500, detail="Admin credentials not configured")

    admin_user = env_admin_user or "Enigma001"
    admin_pass = env_admin_pass or "Enigma123"

    if not username or not password or username != admin_user or password != admin_pass:
        raise HTTPException(status_code=400, detail="Incorrect admin credentials")

    # Upsert a local admin user record to associate with the token
    admin_email = settings.ADMIN_USER_EMAIL

    result = await db.execute(select(User).where(User.email == admin_email))
    user = result.scalar_one_or_none()
    if not user:
        # Create a minimal user row for admin access
        user = User(email=admin_email, name="Enigma Admin", hashed_password=get_password_hash("admin-temp"), plan="admin")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.plan != "admin":
        user.plan = "admin"
        await db.commit()

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_user(current_user)
