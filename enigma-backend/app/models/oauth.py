"""
OAuth Token Database Models

Secure, encrypted storage for OAuth tokens.
"""

from sqlalchemy import Column, String, DateTime, Text, Index, Boolean
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base
from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.auth import AuthStatus


class AuthStatusEnum(str, enum.Enum):
    """Auth status enum for database."""
    AUTHENTICATED = "authenticated"
    NOT_AUTHENTICATED = "not_authenticated"
    EXPIRED = "expired"
    REFRESH_NEEDED = "refresh_needed"
    ERROR = "error"


class OAuthToken(Base):
    """
    Encrypted OAuth token storage.
    
    Stores OAuth access and refresh tokens with encryption at rest.
    Scoped by profile_id and platform for security isolation.
    """
    __tablename__ = "oauth_tokens"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier for data isolation
    platform = Column(String, nullable=False)  # MarketplacePlatform enum value
    
    # Encrypted tokens (NEVER store plaintext)
    access_token_encrypted = Column(Text, nullable=False)  # Encrypted access token
    refresh_token_encrypted = Column(Text, nullable=True)  # Encrypted refresh token (optional)
    
    # Token metadata
    token_type = Column(String, default="Bearer")  # e.g., "Bearer", "API Key"
    scopes = Column(Text, nullable=True)  # JSON array of scopes
    expires_at = Column(DateTime, nullable=True)  # Token expiration time
    
    # Connection status
    auth_status = Column(ENUM(AuthStatusEnum, name="auth_status_enum"), default=AuthStatusEnum.NOT_AUTHENTICATED)
    is_connected = Column(Boolean, default=False)
    
    # Platform-specific data (encrypted if sensitive)
    platform_user_id = Column(String, nullable=True)  # Platform-specific user ID
    platform_username = Column(String, nullable=True)  # Platform username
    additional_data = Column(Text, nullable=True)  # JSON for additional non-sensitive data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)  # Last time token was used
    last_refreshed_at = Column(DateTime, nullable=True)  # Last time token was refreshed

    # Indexes
    __table_args__ = (
        Index("ix_oauth_tokens_profile_platform", "profile_id", "platform", unique=True),
        Index("ix_oauth_tokens_expires_at", "expires_at"),
    )


class OAuthState(Base):
    """
    OAuth state for authorization flow.
    
    Stores OAuth state parameters during the authorization flow.
    """
    __tablename__ = "oauth_states"

    # Identity
    id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(String, nullable=False, unique=True)  # OAuth state parameter
    profile_id = Column(String, nullable=False, index=True)  # User/profile identifier
    platform = Column(String, nullable=False)  # MarketplacePlatform enum value
    
    # OAuth flow parameters
    redirect_uri = Column(Text, nullable=False)
    scopes = Column(Text, nullable=True)  # JSON array of scopes
    code_challenge = Column(Text, nullable=True)  # PKCE code challenge
    code_challenge_method = Column(String, nullable=True)  # e.g., "S256"
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    is_consumed = Column(Boolean, default=False)  # Whether this state has been used
    consumed_at = Column(DateTime, nullable=True)
    
    # Additional data
    metadata = Column(Text, nullable=True)  # JSON for additional data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_oauth_states_state_id", "state_id"),
        Index("ix_oauth_states_profile_platform", "profile_id", "platform"),
    )
