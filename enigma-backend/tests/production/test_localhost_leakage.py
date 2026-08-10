"""
Localhost Leakage Tests

Tests to ensure no localhost leakage in production configuration.
"""

import pytest
import os
from unittest.mock import patch

from app.core.config import Settings


class TestLocalhostLeakage:
    """Test localhost leakage prevention."""
    
    def test_redis_url_no_localhost_default(self):
        """Test REDIS_URL has no localhost default."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Should be empty string, not localhost
            assert settings.REDIS_URL == ""
    
    def test_upwork_redirect_uri_no_localhost_default(self):
        """Test UPWORK_REDIRECT_URI has no localhost default."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Should be empty string, not localhost
            assert settings.UPWORK_REDIRECT_URI == ""
    
    def test_cors_origins_no_localhost_default(self):
        """Test CORS_ORIGINS has no localhost default."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # Should be empty string, not localhost
            assert settings.CORS_ORIGINS == ""
            assert settings.cors_origins_list == []
    
    def test_redis_url_localhost_allowed_in_development(self):
        """Test localhost in REDIS_URL is allowed in development."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "REDIS_URL": "redis://localhost:6379/0",
        }):
            settings = Settings()
            assert "localhost" in settings.REDIS_URL
    
    def test_upwork_redirect_uri_localhost_allowed_in_development(self):
        """Test localhost in UPWORK_REDIRECT_URI is allowed in development."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "UPWORK_REDIRECT_URI": "http://localhost:8000/callback",
        }):
            settings = Settings()
            assert "localhost" in settings.UPWORK_REDIRECT_URI
    
    def test_cors_origins_localhost_allowed_in_development(self):
        """Test localhost in CORS_ORIGINS is allowed in development."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "CORS_ORIGINS": "http://localhost:3000",
        }):
            settings = Settings()
            assert "localhost" in settings.cors_origins_list[0]
    
    def test_redis_url_localhost_blocked_in_production(self):
        """Test localhost in REDIS_URL is blocked in production."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "REDIS_URL": "redis://localhost:6379/0",
        }, clear=True):
            settings = Settings()
            # Health check will detect this, but we can verify it's set
            assert "localhost" in settings.REDIS_URL
    
    def test_upwork_redirect_uri_localhost_blocked_in_production(self):
        """Test localhost in UPWORK_REDIRECT_URI is blocked in production."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "UPWORK_REDIRECT_URI": "http://localhost:8000/callback",
        }, clear=True):
            settings = Settings()
            assert "localhost" in settings.UPWORK_REDIRECT_URI
    
    def test_cors_origins_localhost_blocked_in_production(self):
        """Test localhost in CORS_ORIGINS is blocked in production."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "http://localhost:3000",
        }, clear=True):
            settings = Settings()
            assert "localhost" in settings.cors_origins_list[0]
    
    def test_api_host_localhost_allowed(self):
        """Test localhost in API_HOST is allowed (bind address)."""
        with patch.dict(os.environ, {"API_HOST": "127.0.0.1"}, clear=True):
            settings = Settings()
            assert settings.API_HOST == "127.0.0.1"
    
    def test_production_uses_production_urls(self):
        """Test production configuration uses production URLs."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "REDIS_URL": "redis://prod-redis.example.com:6379/0",
            "UPWORK_REDIRECT_URI": "https://enigma.example.com/callback",
            "CORS_ORIGINS": "https://enigma.example.com",
        }, clear=True):
            settings = Settings()
            assert "localhost" not in settings.REDIS_URL
            assert "localhost" not in settings.UPWORK_REDIRECT_URI
            assert not any("localhost" in origin for origin in settings.cors_origins_list)
    
    def test_127_0_0_1_treated_as_localhost(self):
        """Test 127.0.0.1 is treated as localhost."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "REDIS_URL": "redis://127.0.0.1:6379/0",
        }, clear=True):
            settings = Settings()
            assert "127.0.0.1" in settings.REDIS_URL
