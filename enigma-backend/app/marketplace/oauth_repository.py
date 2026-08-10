"""
Database OAuth Token Repository

Secure, encrypted persistent storage for OAuth tokens.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime, timedelta
import json

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth import (
    OAuthToken as OAuthTokenModel,
    OAuthState as OAuthStateModel,
)
from app.marketplace.contracts import MarketplacePlatform
from app.marketplace.auth import Token, TokenType, OAuthState, AuthStatus
from app.core.encryption import TokenEncryption, EncryptionError, EncryptionKeyMissingError


class DatabaseTokenStore:
    """
    Database-backed token store with encryption.
    
    Replaces InMemoryTokenStore with persistent, encrypted storage.
    """
    
    def __init__(self, db: AsyncSession, encryption_key: Optional[str] = None):
        """
        Initialize database token store.
        
        Args:
            db: Async database session
            encryption_key: Optional encryption key (reads from env if None)
            
        Raises:
            EncryptionKeyMissingError: If encryption key is not available
        """
        self.db = db
        self._encryption = TokenEncryption(encryption_key)
    
    async def get_token(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        token_type: TokenType,
    ) -> Optional[Token]:
        """
        Get token for a profile and platform.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            token_type: Type of token (access_token, refresh_token)
            
        Returns:
            Token or None if not found
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        # Decrypt token
        if token_type == TokenType.ACCESS_TOKEN:
            encrypted_value = model.access_token_encrypted
        elif token_type == TokenType.REFRESH_TOKEN:
            encrypted_value = model.refresh_token_encrypted
        else:
            return None
        
        if not encrypted_value:
            return None
        
        try:
            decrypted_value = self._encryption.decrypt(encrypted_value)
        except EncryptionError:
            # Log error but don't expose details
            return None
        
        # Parse scopes
        scopes = json.loads(model.scopes) if model.scopes else []
        
        return Token(
            token_type=token_type,
            value=decrypted_value,
            expires_at=model.expires_at,
            scopes=scopes,
            metadata={"platform_user_id": model.platform_user_id},
        )
    
    async def save_token(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        token: Token,
    ) -> None:
        """
        Save token for a profile and platform.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            token: Token to save
            
        Raises:
            EncryptionError: If encryption fails
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        # Encrypt token value
        try:
            encrypted_value = self._encryption.encrypt(token.value)
        except EncryptionError as e:
            raise EncryptionError(f"Failed to encrypt token: {e}")
        
        if model:
            # Update existing
            if token.token_type == TokenType.ACCESS_TOKEN:
                model.access_token_encrypted = encrypted_value
            elif token.token_type == TokenType.REFRESH_TOKEN:
                model.refresh_token_encrypted = encrypted_value
            
            model.expires_at = token.expires_at
            model.scopes = json.dumps(token.scopes) if token.scopes else None
            model.auth_status = AuthStatus.AUTHENTICATED
            model.is_connected = True
            model.updated_at = datetime.utcnow()
            model.last_used_at = datetime.utcnow()
        else:
            # Create new
            model = OAuthTokenModel(
                profile_id=profile_id,
                platform=platform.value,
                access_token_encrypted=encrypted_value if token.token_type == TokenType.ACCESS_TOKEN else None,
                refresh_token_encrypted=encrypted_value if token.token_type == TokenType.REFRESH_TOKEN else None,
                token_type=token.token_type.value,
                scopes=json.dumps(token.scopes) if token.scopes else None,
                expires_at=token.expires_at,
                auth_status=AuthStatus.AUTHENTICATED,
                is_connected=True,
                last_used_at=datetime.utcnow(),
            )
            self.db.add(model)
        
        await self.db.commit()
    
    async def delete_token(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        token_type: TokenType,
    ) -> None:
        """
        Delete token for a profile and platform.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            token_type: Type of token to delete
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return
        
        if token_type == TokenType.ACCESS_TOKEN:
            model.access_token_encrypted = None
        elif token_type == TokenType.REFRESH_TOKEN:
            model.refresh_token_encrypted = None
        
        # If both tokens are deleted, mark as disconnected
        if not model.access_token_encrypted and not model.refresh_token_encrypted:
            model.auth_status = AuthStatus.NOT_AUTHENTICATED
            model.is_connected = False
        
        model.updated_at = datetime.utcnow()
        await self.db.commit()
    
    async def clear_platform_tokens(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> None:
        """
        Clear all tokens for a platform.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.db.delete(model)
            await self.db.commit()
    
    async def is_token_expired(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> bool:
        """
        Check if access token is expired.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            
        Returns:
            True if expired, False otherwise
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model or not model.expires_at:
            return True
        
        return datetime.utcnow() >= model.expires_at
    
    async def refresh_token(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        new_access_token: str,
        new_expires_at: datetime,
        new_refresh_token: Optional[str] = None,
    ) -> None:
        """
        Refresh tokens.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            new_access_token: New access token
            new_expires_at: New expiration time
            new_refresh_token: New refresh token (optional)
            
        Raises:
            EncryptionError: If encryption fails
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("No existing token found to refresh")
        
        # Encrypt new tokens
        try:
            encrypted_access = self._encryption.encrypt(new_access_token)
            encrypted_refresh = self._encryption.encrypt(new_refresh_token) if new_refresh_token else None
        except EncryptionError as e:
            raise EncryptionError(f"Failed to encrypt refreshed token: {e}")
        
        model.access_token_encrypted = encrypted_access
        if new_refresh_token:
            model.refresh_token_encrypted = encrypted_refresh
        model.expires_at = new_expires_at
        model.auth_status = AuthStatus.AUTHENTICATED
        model.last_refreshed_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def get_connection_status(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> AuthStatus:
        """
        Get connection status for a platform.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            
        Returns:
            Auth status
        """
        result = await self.db.execute(
            select(OAuthTokenModel).where(
                and_(
                    OAuthTokenModel.profile_id == profile_id,
                    OAuthTokenModel.platform == platform.value
                )
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return AuthStatus.NOT_AUTHENTICATED
        
        # Check if expired
        if model.expires_at and datetime.utcnow() >= model.expires_at:
            return AuthStatus.EXPIRED
        
        return AuthStatus(model.auth_status.value)
    
    async def revoke_connection(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
    ) -> None:
        """
        Revoke OAuth connection.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
        """
        await self.clear_platform_tokens(profile_id, platform)


class DatabaseOAuthStateManager:
    """
    Database-backed OAuth state manager.
    
    Replaces InMemoryOAuthStateManager with persistent storage.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize database OAuth state manager.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def create_state(
        self,
        profile_id: str,
        platform: MarketplacePlatform,
        redirect_uri: str,
        scopes: List[str],
        expires_in_minutes: int = 10,
    ) -> OAuthState:
        """
        Create OAuth state.
        
        Args:
            profile_id: Profile identifier for data isolation
            platform: Marketplace platform
            redirect_uri: OAuth redirect URI
            scopes: OAuth scopes
            expires_in_minutes: State expiration time in minutes
            
        Returns:
            OAuth state
        """
        import uuid
        
        state_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        model = OAuthStateModel(
            state_id=state_id,
            profile_id=profile_id,
            platform=platform.value,
            redirect_uri=redirect_uri,
            scopes=json.dumps(scopes),
            expires_at=expires_at,
        )
        self.db.add(model)
        await self.db.commit()
        
        return OAuthState(
            state_id=state_id,
            platform=platform.value,
            redirect_uri=redirect_uri,
            scopes=scopes,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )
    
    async def get_state(self, state_id: str) -> Optional[OAuthState]:
        """
        Get OAuth state.
        
        Args:
            state_id: State identifier
            
        Returns:
            OAuth state or None if not found or expired
        """
        result = await self.db.execute(
            select(OAuthStateModel).where(
                OAuthStateModel.state_id == state_id
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        # Check if expired
        if datetime.utcnow() >= model.expires_at:
            return None
        
        # Check if already consumed
        if model.is_consumed:
            return None
        
        scopes = json.loads(model.scopes) if model.scopes else []
        
        return OAuthState(
            state_id=model.state_id,
            platform=model.platform,
            redirect_uri=model.redirect_uri,
            scopes=scopes,
            created_at=model.created_at,
            expires_at=model.expires_at,
        )
    
    async def consume_state(self, state_id: str) -> bool:
        """
        Mark OAuth state as consumed.
        
        Args:
            state_id: State identifier
            
        Returns:
            True if state was found and consumed, False otherwise
        """
        result = await self.db.execute(
            select(OAuthStateModel).where(
                OAuthStateModel.state_id == state_id
            )
        )
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.is_consumed = True
        model.consumed_at = datetime.utcnow()
        await self.db.commit()
        
        return True
    
    async def delete_state(self, state_id: str) -> None:
        """
        Delete OAuth state.
        
        Args:
            state_id: State identifier
        """
        result = await self.db.execute(
            select(OAuthStateModel).where(
                OAuthStateModel.state_id == state_id
            )
        )
        model = result.scalar_one_or_none()
        
        if model:
            await self.db.delete(model)
            await self.db.commit()
    
    async def cleanup_expired_states(self) -> int:
        """
        Clean up expired OAuth states.
        
        Returns:
            Number of states cleaned up
        """
        result = await self.db.execute(
            select(OAuthStateModel).where(
                OAuthStateModel.expires_at < datetime.utcnow()
            )
        )
        models = result.scalars().all()
        
        count = 0
        for model in models:
            await self.db.delete(model)
            count += 1
        
        await self.db.commit()
        return count
