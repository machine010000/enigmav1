"""
Authentication Abstraction for Marketplace Adapters

TASK-051: Secure credential handling with no hardcoded secrets.
No passwords, API secrets, OAuth tokens, or refresh tokens in source code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
import os
from pathlib import Path


class AuthStatus(str, Enum):
    """Authentication status."""
    AUTHENTICATED = "authenticated"
    NOT_AUTHENTICATED = "not_authenticated"
    EXPIRED = "expired"
    REFRESH_NEEDED = "refresh_needed"
    ERROR = "error"


class TokenType(str, Enum):
    """Token types."""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    API_KEY = "api_key"
    OAUTH_STATE = "oauth_state"


@dataclass
class Token:
    """Authentication token."""
    token_type: TokenType
    value: str
    expires_at: Optional[datetime] = None
    scopes: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def expires_in(self) -> Optional[timedelta]:
        """Get time until expiration."""
        if not self.expires_at:
            return None
        return self.expires_at - datetime.utcnow()


@dataclass
class OAuthState:
    """OAuth state for authorization flow."""
    state_id: str
    platform: str
    redirect_uri: str
    scopes: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if OAuth state is expired."""
        if not self.expires_at:
            # Default 10 minute expiry
            return datetime.utcnow() >= self.created_at + timedelta(minutes=10)
        return datetime.utcnow() >= self.expires_at


@dataclass
class Credential:
    """Platform credential."""
    platform: str
    credential_type: str  # "oauth", "api_key", "basic", etc.
    data: Dict[str, Any] = field(default_factory=dict)
    is_encrypted: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class CredentialProvider(ABC):
    """
    Abstract credential provider.
    
    TASK-051: No hardcoded credentials in source code.
    Credentials come from environment variables or secure storage.
    """
    
    @abstractmethod
    async def get_credential(self, platform: str) -> Optional[Credential]:
        """
        Get credential for a platform.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Credential or None if not found
        """
        pass
    
    @abstractmethod
    async def save_credential(self, credential: Credential) -> None:
        """
        Save credential for a platform.
        
        Args:
            credential: Credential to save
        """
        pass
    
    @abstractmethod
    async def delete_credential(self, platform: str) -> None:
        """
        Delete credential for a platform.
        
        Args:
            platform: Platform identifier
        """
        pass
    
    @abstractmethod
    async def has_credential(self, platform: str) -> bool:
        """
        Check if credential exists for platform.
        
        Args:
            platform: Platform identifier
            
        Returns:
            True if credential exists
        """
        pass


class TokenStore(ABC):
    """
    Abstract token store.
    
    TASK-051: No tokens in source code or localStorage.
    Tokens stored securely based on deployment architecture.
    """
    
    @abstractmethod
    async def get_token(self, platform: str, token_type: TokenType) -> Optional[Token]:
        """
        Get token for a platform.
        
        Args:
            platform: Platform identifier
            token_type: Type of token
            
        Returns:
            Token or None if not found
        """
        pass
    
    @abstractmethod
    async def save_token(self, platform: str, token: Token) -> None:
        """
        Save token for a platform.
        
        Args:
            platform: Platform identifier
            token: Token to save
        """
        pass
    
    @abstractmethod
    async def delete_token(self, platform: str, token_type: TokenType) -> None:
        """
        Delete token for a platform.
        
        Args:
            platform: Platform identifier
            token_type: Type of token
        """
        pass
    
    @abstractmethod
    async def clear_platform_tokens(self, platform: str) -> None:
        """
        Clear all tokens for a platform.
        
        Args:
            platform: Platform identifier
        """
        pass


class OAuthStateManager(ABC):
    """
    Abstract OAuth state manager.
    
    TASK-051: OAuth state stored securely, not in localStorage.
    """
    
    @abstractmethod
    async def create_state(self, platform: str, redirect_uri: str, scopes: list[str]) -> OAuthState:
        """
        Create OAuth state.
        
        Args:
            platform: Platform identifier
            redirect_uri: OAuth redirect URI
            scopes: OAuth scopes
            
        Returns:
            OAuth state
        """
        pass
    
    @abstractmethod
    async def get_state(self, state_id: str) -> Optional[OAuthState]:
        """
        Get OAuth state.
        
        Args:
            state_id: State identifier
            
        Returns:
            OAuth state or None if not found
        """
        pass
    
    @abstractmethod
    async def delete_state(self, state_id: str) -> None:
        """
        Delete OAuth state.
        
        Args:
            state_id: State identifier
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_states(self) -> int:
        """
        Clean up expired OAuth states.
        
        Returns:
            Number of states cleaned up
        """
        pass


class EnvironmentCredentialProvider(CredentialProvider):
    """
    Credential provider using environment variables.
    
    TASK-051: Credentials from environment, not hardcoded.
    """
    
    def __init__(self):
        """Initialize environment credential provider."""
        self._cache: Dict[str, Credential] = {}
    
    async def get_credential(self, platform: str) -> Optional[Credential]:
        """Get credential from environment variables."""
        if platform in self._cache:
            return self._cache[platform]
        
        # Try to load from environment
        env_prefix = f"{platform.upper()}_"
        credential_data = {}
        
        # Common credential keys
        for key in ["CLIENT_ID", "CLIENT_SECRET", "API_KEY", "ACCESS_TOKEN"]:
            env_key = f"{env_prefix}{key}"
            if env_key in os.environ:
                credential_data[key.lower()] = os.environ[env_key]
        
        if credential_data:
            credential = Credential(
                platform=platform,
                credential_type="environment",
                data=credential_data,
                is_encrypted=False,  # Environment variables should be encrypted at system level
            )
            self._cache[platform] = credential
            return credential
        
        return None
    
    async def save_credential(self, credential: Credential) -> None:
        """
        Save credential (not supported for environment provider).
        
        Environment provider is read-only.
        """
        raise NotImplementedError("Environment credential provider is read-only")
    
    async def delete_credential(self, platform: str) -> None:
        """Delete credential from cache."""
        if platform in self._cache:
            del self._cache[platform]
    
    async def has_credential(self, platform: str) -> bool:
        """Check if credential exists."""
        return await self.get_credential(platform) is not None


class InMemoryTokenStore(TokenStore):
    """
    In-memory token store for development/testing.
    
    TASK-051: For development only. Production should use secure storage.
    """
    
    def __init__(self):
        """Initialize in-memory token store."""
        self._tokens: Dict[str, Dict[TokenType, Token]] = {}
    
    async def get_token(self, platform: str, token_type: TokenType) -> Optional[Token]:
        """Get token from memory."""
        if platform not in self._tokens:
            return None
        return self._tokens[platform].get(token_type)
    
    async def save_token(self, platform: str, token: Token) -> None:
        """Save token to memory."""
        if platform not in self._tokens:
            self._tokens[platform] = {}
        self._tokens[platform][token.token_type] = token
    
    async def delete_token(self, platform: str, token_type: TokenType) -> None:
        """Delete token from memory."""
        if platform in self._tokens and token_type in self._tokens[platform]:
            del self._tokens[platform][token_type]
    
    async def clear_platform_tokens(self, platform: str) -> None:
        """Clear all tokens for platform."""
        if platform in self._tokens:
            del self._tokens[platform]


class InMemoryOAuthStateManager(OAuthStateManager):
    """
    In-memory OAuth state manager for development/testing.
    
    TASK-051: For development only. Production should use secure storage.
    """
    
    def __init__(self):
        """Initialize in-memory OAuth state manager."""
        self._states: Dict[str, OAuthState] = {}
    
    async def create_state(self, platform: str, redirect_uri: str, scopes: list[str]) -> OAuthState:
        """Create OAuth state."""
        import uuid
        state_id = str(uuid.uuid4())
        
        state = OAuthState(
            state_id=state_id,
            platform=platform,
            redirect_uri=redirect_uri,
            scopes=scopes,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        
        self._states[state_id] = state
        return state
    
    async def get_state(self, state_id: str) -> Optional[OAuthState]:
        """Get OAuth state."""
        return self._states.get(state_id)
    
    async def delete_state(self, state_id: str) -> None:
        """Delete OAuth state."""
        if state_id in self._states:
            del self._states[state_id]
    
    async def cleanup_expired_states(self) -> int:
        """Clean up expired OAuth states."""
        expired = [sid for sid, state in self._states.items() if state.is_expired()]
        for sid in expired:
            del self._states[sid]
        return len(expired)


class ConnectionStatus:
    """Connection status for marketplace adapters."""
    
    def __init__(self):
        """Initialize connection status."""
        self._status: Dict[str, AuthStatus] = {}
        self._last_connected: Dict[str, datetime] = {}
        self._last_error: Dict[str, str] = {}
    
    def set_status(self, platform: str, status: AuthStatus, error: Optional[str] = None) -> None:
        """Set connection status."""
        self._status[platform] = status
        if status == AuthStatus.AUTHENTICATED:
            self._last_connected[platform] = datetime.utcnow()
        if error:
            self._last_error[platform] = error
    
    def get_status(self, platform: str) -> AuthStatus:
        """Get connection status."""
        return self._status.get(platform, AuthStatus.NOT_AUTHENTICATED)
    
    def is_connected(self, platform: str) -> bool:
        """Check if platform is connected."""
        return self.get_status(platform) == AuthStatus.AUTHENTICATED
    
    def get_last_connected(self, platform: str) -> Optional[datetime]:
        """Get last connected time."""
        return self._last_connected.get(platform)
    
    def get_last_error(self, platform: str) -> Optional[str]:
        """Get last error."""
        return self._last_error.get(platform)
    
    def get_all_statuses(self) -> Dict[str, AuthStatus]:
        """Get all connection statuses."""
        return self._status.copy()


# Global instances (for development)
credential_provider = EnvironmentCredentialProvider()
token_store = InMemoryTokenStore()
oauth_state_manager = InMemoryOAuthStateManager()
connection_status = ConnectionStatus()
