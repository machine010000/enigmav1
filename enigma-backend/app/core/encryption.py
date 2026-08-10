"""
Encryption Utilities for OAuth Token Storage

Provides encryption/decryption for sensitive data like OAuth tokens.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib


class EncryptionError(Exception):
    """Encryption error."""
    pass


class EncryptionKeyMissingError(EncryptionError):
    """Encryption key is missing."""
    pass


class TokenEncryption:
    """
    Encryption utility for OAuth tokens.
    
    Uses Fernet symmetric encryption with PBKDF2 key derivation.
    Encryption key must be provided via environment variable.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize token encryption.
        
        Args:
            encryption_key: Base64-encoded encryption key. If None, reads from env.
            
        Raises:
            EncryptionKeyMissingError: If encryption key is not provided or found in env.
        """
        key = encryption_key or os.environ.get("ENIGMA_ENCRYPTION_KEY")
        
        if not key:
            raise EncryptionKeyMissingError(
                "ENIGMA_ENCRYPTION_KEY environment variable is required for token encryption. "
                "Set a secure random key in your environment."
            )
        
        # Ensure key is valid base64
        try:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
            
        Note:
            Store this key securely in environment variables, not in source code.
        """
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> str:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if None)
            
        Returns:
            Base64-encoded encryption key
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode()
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext.
        
        Args:
            plaintext: Text to encrypt
            
        Returns:
            Base64-encoded encrypted text
            
        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return ""
        
        try:
            encrypted = self._fernet.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext.
        
        Args:
            ciphertext: Base64-encoded encrypted text
            
        Returns:
            Decrypted plaintext
            
        Raises:
            EncryptionError: If decryption fails
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted = self._fernet.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        """
        Encrypt bytes.
        
        Args:
            data: Bytes to encrypt
            
        Returns:
            Encrypted bytes
        """
        return self._fernet.encrypt(data)
    
    def decrypt_bytes(self, data: bytes) -> bytes:
        """
        Decrypt bytes.
        
        Args:
            data: Bytes to decrypt
            
        Returns:
            Decrypted bytes
        """
        return self._fernet.decrypt(data)


class SafeTokenLogger:
    """
    Safe token logging that prevents token leakage.
    
    Redacts sensitive token information from logs.
    """
    
    SENSITIVE_KEYWORDS = [
        "access_token",
        "refresh_token",
        "client_secret",
        "authorization_code",
        "api_key",
        "api_secret",
        "password",
        "secret",
    ]
    
    @classmethod
    def redact(cls, data: dict) -> dict:
        """
        Redact sensitive keys from dictionary.
        
        Args:
            data: Dictionary to redact
            
        Returns:
            Dictionary with sensitive values redacted
        """
        redacted = data.copy()
        
        for key in redacted:
            key_lower = key.lower()
            for sensitive in cls.SENSITIVE_KEYWORDS:
                if sensitive in key_lower:
                    redacted[key] = "***REDACTED***"
                    break
        
        return redacted
    
    @classmethod
    def safe_log(cls, message: str, data: Optional[dict] = None) -> str:
        """
        Create safe log message with redacted data.
        
        Args:
            message: Log message
            data: Optional data to redact
            
        Returns:
            Safe log message
        """
        if data:
            redacted_data = cls.redact(data)
            return f"{message} | {redacted_data}"
        return message
    
    @classmethod
    def is_safe(cls, text: str) -> bool:
        """
        Check if text contains sensitive information.
        
        Args:
            text: Text to check
            
        Returns:
            True if text is safe (no sensitive keywords), False otherwise
        """
        text_lower = text.lower()
        for sensitive in cls.SENSITIVE_KEYWORDS:
            if sensitive in text_lower:
                return False
        return True
