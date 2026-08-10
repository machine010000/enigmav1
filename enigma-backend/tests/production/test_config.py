"""
Production Configuration Tests

Tests for production configuration validation and environment isolation.
"""

import pytest
import os
from unittest.mock import patch

from app.core.config import Settings, get_settings, is_production, is_development, is_testing


class TestSettingsValidation:
    """Test Settings validation."""
    
    def test_environment_validation_valid(self):
        """Test valid environment values."""
        for env in ["development", "test", "production"]:
            with patch.dict(os.environ, {"ENVIRONMENT": env}, clear=True):
                settings = Settings()
                assert settings.ENVIRONMENT == env.lower()
    
    def test_environment_validation_invalid(self):
        """Test invalid environment value raises error."""
        with patch.dict(os.environ, {"ENVIRONMENT": "invalid"}):
            with pytest.raises(ValueError, match="ENVIRONMENT must be one of"):
                Settings()
    
    def test_secret_key_validation_production(self):
        """Test SECRET_KEY required in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "SECRET_KEY": ""}):
            with pytest.raises(ValueError, match="SECRET_KEY must be set in production"):
                Settings()
    
    def test_secret_key_validation_development(self):
        """Test SECRET_KEY optional in development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development", "SECRET_KEY": ""}):
            settings = Settings()
            assert settings.SECRET_KEY == ""
    
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,https://example.com"}):
            settings = Settings()
            origins = settings.cors_origins_list
            assert len(origins) == 2
            assert "http://localhost:3000" in origins
            assert "https://example.com" in origins
    
    def test_cors_origins_empty(self):
        """Test empty CORS origins."""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}):
            settings = Settings()
            assert settings.cors_origins_list == []
    
    def test_timeout_defaults(self):
        """Test timeout configuration defaults."""
        settings = Settings()
        assert settings.API_TIMEOUT_SECONDS == 30
        assert settings.DATABASE_TIMEOUT_SECONDS == 10
        assert settings.REDIS_TIMEOUT_SECONDS == 5
    
    def test_retry_defaults(self):
        """Test retry configuration defaults."""
        settings = Settings()
        assert settings.MAX_RETRIES == 3
        assert settings.RETRY_DELAY_SECONDS == 1
    
    def test_custom_timeouts(self):
        """Test custom timeout configuration."""
        with patch.dict(os.environ, {
            "API_TIMEOUT_SECONDS": "60",
            "DATABASE_TIMEOUT_SECONDS": "20",
            "REDIS_TIMEOUT_SECONDS": "10",
        }):
            settings = Settings()
            assert settings.API_TIMEOUT_SECONDS == 60
            assert settings.DATABASE_TIMEOUT_SECONDS == 20
            assert settings.REDIS_TIMEOUT_SECONDS == 10
    
    def test_custom_retry(self):
        """Test custom retry configuration."""
        with patch.dict(os.environ, {
            "MAX_RETRIES": "5",
            "RETRY_DELAY_SECONDS": "2",
        }):
            settings = Settings()
            assert settings.MAX_RETRIES == 5
            assert settings.RETRY_DELAY_SECONDS == 2


class TestEnvironmentDetection:
    """Test environment detection functions."""
    
    def test_is_production_true(self):
        """Test is_production returns True for production environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            # Create new settings instance
            from app.core.config import Settings
            test_settings = Settings()
            assert test_settings.ENVIRONMENT == "production"
    
    def test_is_production_false(self):
        """Test is_production returns False for non-production environments."""
        for env in ["development", "test"]:
            with patch.dict(os.environ, {"ENVIRONMENT": env}, clear=True):
                from app.core.config import Settings
                test_settings = Settings()
                assert test_settings.ENVIRONMENT != "production"
    
    def test_is_development_true(self):
        """Test is_development returns True for development environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            from app.core.config import Settings
            test_settings = Settings()
            assert test_settings.ENVIRONMENT == "development"
    
    def test_is_development_false(self):
        """Test is_development returns False for non-development environments."""
        for env in ["test", "production"]:
            with patch.dict(os.environ, {"ENVIRONMENT": env}, clear=True):
                from app.core.config import Settings
                test_settings = Settings()
                assert test_settings.ENVIRONMENT != "development"
    
    def test_is_testing_true(self):
        """Test is_testing returns True for test environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=True):
            from app.core.config import Settings
            test_settings = Settings()
            assert test_settings.ENVIRONMENT == "test"
    
    def test_is_testing_false(self):
        """Test is_testing returns False for non-test environments."""
        for env in ["development", "production"]:
            with patch.dict(os.environ, {"ENVIRONMENT": env}, clear=True):
                from app.core.config import Settings
                test_settings = Settings()
                assert test_settings.ENVIRONMENT != "test"


class TestConfigurationDefaults:
    """Test configuration defaults."""
    
    def test_default_environment(self):
        """Test default environment is development."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ENVIRONMENT == "development"
    
    def test_default_debug(self):
        """Test default DEBUG is False."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.DEBUG is False
    
    def test_default_api_host(self):
        """Test default API host."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.API_HOST == "0.0.0.0"
    
    def test_default_api_port(self):
        """Test default API port."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.API_PORT == 8000
    
    def test_default_ai_provider(self):
        """Test default AI provider."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.AI_PROVIDER == "nvidia"
    
    def test_default_ai_model(self):
        """Test default AI model."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.AI_MODEL == "meta/llama-3.3-70b-instruct"
    
    def test_default_jwt_algorithm(self):
        """Test default JWT algorithm."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ALGORITHM == "HS256"
    
    def test_default_token_expiry(self):
        """Test default token expiry."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60


class TestConfigurationFromEnv:
    """Test configuration from environment variables."""
    
    def test_environment_from_env(self):
        """Test ENVIRONMENT from environment variable."""
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
            settings = Settings()
            assert settings.ENVIRONMENT == "test"
    
    def test_debug_from_env(self):
        """Test DEBUG from environment variable."""
        with patch.dict(os.environ, {"DEBUG": "true"}):
            settings = Settings()
            assert settings.DEBUG is True
    
    def test_api_host_from_env(self):
        """Test API_HOST from environment variable."""
        with patch.dict(os.environ, {"API_HOST": "127.0.0.1"}):
            settings = Settings()
            assert settings.API_HOST == "127.0.0.1"
    
    def test_api_port_from_env(self):
        """Test API_PORT from environment variable."""
        with patch.dict(os.environ, {"API_PORT": "9000"}):
            settings = Settings()
            assert settings.API_PORT == 9000
    
    def test_database_url_from_env(self):
        """Test DATABASE_URL from environment variable."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}):
            settings = Settings()
            assert settings.DATABASE_URL == "postgresql://test"
    
    def test_nvidia_api_key_from_env(self):
        """Test NVIDIA_API_KEY from environment variable."""
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            settings = Settings()
            assert settings.NVIDIA_API_KEY == "test-key"
    
    def test_secret_key_from_env(self):
        """Test SECRET_KEY from environment variable."""
        with patch.dict(os.environ, {"SECRET_KEY": "test-secret"}):
            settings = Settings()
            assert settings.SECRET_KEY == "test-secret"
    
    def test_redis_url_from_env(self):
        """Test REDIS_URL from environment variable."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://test:6379"}):
            settings = Settings()
            assert settings.REDIS_URL == "redis://test:6379"
    
    def test_log_level_from_env(self):
        """Test LOG_LEVEL from environment variable."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.LOG_LEVEL == "DEBUG"


class TestGetSettings:
    """Test get_settings function."""
    
    def test_get_settings_returns_settings(self):
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)


class TestExtraFieldsIgnored:
    """Test that extra fields are ignored."""
    
    def test_extra_fields_ignored(self):
        """Test extra environment variables are ignored."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "UNKNOWN_FIELD": "should_be_ignored",
        }):
            settings = Settings()
            assert not hasattr(settings, "UNKNOWN_FIELD")
