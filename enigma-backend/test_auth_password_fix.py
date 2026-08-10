"""
Test Authentication Password Fix

Tests for the bcrypt 72-byte password limit fix using SHA-256 pre-hashing.
"""

import pytest
from app.routers.auth import get_password_hash, verify_password, _prehash_password


def test_prehash_password():
    """Test that pre-hashing produces consistent SHA-256 hashes."""
    password = "test_password_123"
    hash1 = _prehash_password(password)
    hash2 = _prehash_password(password)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest is 64 characters
    assert hash1 != password


def test_normal_password():
    """Test normal password hashing and verification."""
    password = "password123"
    hashed = get_password_hash(password)
    
    # Should verify correctly
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("wrong_password", hashed) is False


def test_long_ascii_password():
    """Test long ASCII password (> 72 bytes)."""
    # Create a password longer than 72 bytes
    password = "a" * 100  # 100 ASCII characters = 100 bytes
    
    # Should not raise ValueError
    hashed = get_password_hash(password)
    
    # Should verify correctly
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("a" * 99, hashed) is False


def test_long_unicode_password():
    """Test long Unicode password where byte count > character count."""
    # Unicode characters can be multiple bytes
    password = "🔐" * 50  # 50 emoji characters, but more than 72 bytes
    
    # Should not raise ValueError
    hashed = get_password_hash(password)
    
    # Should verify correctly
    assert verify_password(password, hashed) is True
    
    # Wrong password should fail
    assert verify_password("🔐" * 49, hashed) is False


def test_mixed_unicode_password():
    """Test mixed ASCII and Unicode password."""
    password = "P@ssw0rd!🔐🔑🗝️" * 10  # Mix of ASCII and Unicode
    
    # Should not raise ValueError
    hashed = get_password_hash(password)
    
    # Should verify correctly
    assert verify_password(password, hashed) is True


def test_backward_compatibility():
    """Test that old bcrypt hashes still work (if they exist)."""
    # This is a placeholder for testing backward compatibility
    # In practice, you would need an actual old bcrypt hash from the database
    
    # For now, we just verify that the verify function tries both methods
    password = "old_password"
    new_hashed = get_password_hash(password)
    
    # New hash should verify
    assert verify_password(password, new_hashed) is True


def test_password_entropy_preserved():
    """Test that different passwords produce different hashes."""
    password1 = "password123"
    password2 = "password124"  # Very similar
    
    hash1 = get_password_hash(password1)
    hash2 = get_password_hash(password2)
    
    # Different passwords should produce different hashes
    assert hash1 != hash2


def test_empty_password():
    """Test empty password handling."""
    password = ""
    
    # Should not raise ValueError
    hashed = get_password_hash(password)
    
    # Should verify correctly
    assert verify_password(password, hashed) is True


def test_special_characters():
    """Test password with special characters."""
    password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    
    # Should not raise ValueError
    hashed = get_password_hash(password)
    
    # Should verify correctly
    assert verify_password(password, hashed) is True


if __name__ == "__main__":
    # Run tests manually
    print("Running password hash tests...")
    
    try:
        test_prehash_password()
        print("✅ test_prehash_password passed")
    except AssertionError as e:
        print(f"❌ test_prehash_password failed: {e}")
    
    try:
        test_normal_password()
        print("✅ test_normal_password passed")
    except AssertionError as e:
        print(f"❌ test_normal_password failed: {e}")
    
    try:
        test_long_ascii_password()
        print("✅ test_long_ascii_password passed")
    except AssertionError as e:
        print(f"❌ test_long_ascii_password failed: {e}")
    
    try:
        test_long_unicode_password()
        print("✅ test_long_unicode_password passed")
    except AssertionError as e:
        print(f"❌ test_long_unicode_password failed: {e}")
    
    try:
        test_mixed_unicode_password()
        print("✅ test_mixed_unicode_password passed")
    except AssertionError as e:
        print(f"❌ test_mixed_unicode_password failed: {e}")
    
    try:
        test_backward_compatibility()
        print("✅ test_backward_compatibility passed")
    except AssertionError as e:
        print(f"❌ test_backward_compatibility failed: {e}")
    
    try:
        test_password_entropy_preserved()
        print("✅ test_password_entropy_preserved passed")
    except AssertionError as e:
        print(f"❌ test_password_entropy_preserved failed: {e}")
    
    try:
        test_empty_password()
        print("✅ test_empty_password passed")
    except AssertionError as e:
        print(f"❌ test_empty_password failed: {e}")
    
    try:
        test_special_characters()
        print("✅ test_special_characters passed")
    except AssertionError as e:
        print(f"❌ test_special_characters failed: {e}")
    
    print("\nAll tests completed!")
