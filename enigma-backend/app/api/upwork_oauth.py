"""
Upwork OAuth flow endpoints.

Handles OAuth 2.0 authentication with Upwork.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any
import secrets

from app.marketplace.upwork_adapter import UpworkAdapter, UpworkCredentials
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Store OAuth state temporarily (in production, use Redis)
_oauth_states: Dict[str, Dict[str, Any]] = {}


@router.get("/upwork/auth")
async def initiate_upwork_auth() -> Dict[str, str]:
    """
    Initiate Upwork OAuth 2.0 authorization flow.
    
    Returns the authorization URL for the user to visit.
    """
    if not settings.UPWORK_CLIENT_ID or not settings.UPWORK_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Upwork credentials not configured"
        )
    
    # Generate state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL
    auth_url = (
        f"https://www.upwork.com/ab/account-security/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={settings.UPWORK_CLIENT_ID}"
        f"&redirect_uri={settings.UPWORK_REDIRECT_URI}"
        f"&state={state}"
    )
    
    # Store state temporarily
    _oauth_states[state] = {
        "created_at": "now",  # In production, use actual timestamp
    }
    
    logger.info(f"Initiated Upwork OAuth flow with state: {state}")
    
    return {
        "authorization_url": auth_url,
        "state": state,
    }


@router.get("/upwork/callback")
async def upwork_callback(
    code: str,
    state: str,
) -> Dict[str, Any]:
    """
    Handle Upwork OAuth callback.
    
    Exchange authorization code for access token.
    """
    # Verify state
    if state not in _oauth_states:
        logger.warning(f"Invalid OAuth state: {state}")
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Clean up state
    del _oauth_states[state]
    
    # Exchange code for token
    adapter = UpworkAdapter()
    
    try:
        account = await adapter.authenticate({"authorization_code": code})
        
        logger.info(f"Successfully authenticated Upwork account: {account.account_id}")
        
        return {
            "status": "success",
            "account_id": account.account_id,
            "username": account.username,
            "account_status": account.status.value,
            "connects_available": account.limits.credits_available,
            "connects_total": account.limits.credits_total,
        }
    except Exception as e:
        logger.error(f"Upwork authentication failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upwork/account/status")
async def get_upwork_account_status() -> Dict[str, Any]:
    """
    Get current Upwork account status.
    
    Returns account information including connects and limits.
    """
    # In production, this would retrieve stored credentials from database
    # For now, we'll return a placeholder response
    
    return {
        "status": "not_authenticated",
        "message": "Please authenticate with Upwork first",
    }


@router.post("/upwork/auth/refresh")
async def refresh_upwork_token() -> Dict[str, str]:
    """
    Refresh Upwork access token.
    
    In production, this would use the stored refresh token.
    """
    return {
        "status": "not_implemented",
        "message": "Token refresh not yet implemented",
    }
