"""
Simple Password Hash Test (No app dependencies)

Tests the password hashing logic without requiring full app imports.
"""

import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _prehash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle bcrypt's 72-byte limit.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash with backward compatibility.
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
    """
    prehashed = _prehash_password(password)
    return pwd_context.hash(prehashed)


def test_normal_password():
    """Test normal password hashing and verification."""
    password = "password123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    print("✅ test_normal_password passed")

def test_long_ascii_password():
    """Test long ASCII password (> 72 bytes)."""
    password = "a" * 100  # 100 bytes
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("a" * 99, hashed) is False
    print("✅ test_long_ascii_password passed")

def test_long_unicode_password():
    """Test long Unicode password."""
    password = "🔐" * 50
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    assert verify_password("🔐" * 49, hashed) is False
    print("✅ test_long_unicode_password passed")

def test_special_characters():
    """Test password with special characters."""
    password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True
    print("✅ test_special_characters passed")

if __name__ == "__main__":
    print("Running password hash tests...")
    test_normal_password()
    test_long_ascii_password()
    test_long_unicode_password()
    test_special_characters()
    print("\n✅ All tests passed!")
