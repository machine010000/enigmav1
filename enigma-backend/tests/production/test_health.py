"""
Startup/Health Tests

Tests for startup health checks and configuration validation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.core.health import HealthCheck, perform_startup_health_check, get_health_status
from app.core.config import settings


class TestHealthCheck:
    """Test HealthCheck class."""
    
    def test_initialization(self):
        """Test health check initialization."""
        health = HealthCheck()
        assert health.checks == []
        assert health.errors == []
        assert health.warnings == []
    
    def test_check_configuration_valid(self):
        """Test configuration check with valid configuration."""
        health = HealthCheck()
        result = health.check_configuration()
        assert result is True
        assert len(health.errors) == 0
    
    def test_check_configuration_invalid_environment(self):
        """Test configuration check with invalid environment."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "invalid"
            result = health.check_configuration()
            assert result is False
            assert len(health.errors) > 0
    
    def test_check_essential_secrets_missing_in_production(self):
        """Test essential secrets check fails in production."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_settings.SECRET_KEY = ""
            mock_settings.DATABASE_URL = ""
            mock_settings.NVIDIA_API_KEY = ""
            
            result = health.check_essential_secrets()
            assert result is False
            assert len(health.errors) > 0
    
    def test_check_essential_secrets_missing_in_development(self):
        """Test essential secrets check warns in development."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            mock_settings.SECRET_KEY = ""
            mock_settings.DATABASE_URL = ""
            mock_settings.NVIDIA_API_KEY = ""
            
            result = health.check_essential_secrets()
            assert result is True  # Should pass in development
            assert len(health.warnings) > 0
    
    def test_check_no_localhost_leakage_production(self):
        """Test localhost leakage check in production."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_settings.REDIS_URL = "redis://localhost:6379/0"
            
            result = health.check_no_localhost_leakage()
            assert result is False
            assert len(health.errors) > 0
    
    def test_check_no_localhost_leakage_development(self):
        """Test localhost leakage check in development."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            mock_settings.REDIS_URL = "redis://localhost:6379/0"
            
            result = health.check_no_localhost_leakage()
            assert result is True  # Should pass in development
    
    def test_check_timeout_configuration_valid(self):
        """Test timeout configuration check with valid values."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.API_TIMEOUT_SECONDS = 30
            mock_settings.DATABASE_TIMEOUT_SECONDS = 10
            mock_settings.REDIS_TIMEOUT_SECONDS = 5
            
            result = health.check_timeout_configuration()
            assert result is True
    
    def test_check_timeout_configuration_invalid(self):
        """Test timeout configuration check with invalid values."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.API_TIMEOUT_SECONDS = -1
            mock_settings.DATABASE_TIMEOUT_SECONDS = 10
            mock_settings.REDIS_TIMEOUT_SECONDS = 5
            
            result = health.check_timeout_configuration()
            assert result is False
            assert len(health.errors) > 0
    
    def test_check_retry_configuration_valid(self):
        """Test retry configuration check with valid values."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.MAX_RETRIES = 3
            mock_settings.RETRY_DELAY_SECONDS = 1
            
            result = health.check_retry_configuration()
            assert result is True
    
    def test_check_retry_configuration_invalid(self):
        """Test retry configuration check with invalid values."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.MAX_RETRIES = -1
            mock_settings.RETRY_DELAY_SECONDS = 1
            
            result = health.check_retry_configuration()
            assert result is False
            assert len(health.errors) > 0


class TestHealthCheckAsync:
    """Test async health check methods."""
    
    @pytest.mark.asyncio
    async def test_check_database_connection_no_url(self):
        """Test database connection check with no URL."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.DATABASE_URL = ""
            
            result = await health.check_database_connection()
            assert result is True  # Should skip gracefully
            assert len(health.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_check_redis_connection_no_url(self):
        """Test Redis connection check with no URL."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.REDIS_URL = ""
            
            result = await health.check_redis_connection()
            assert result is True  # Should skip gracefully
            assert len(health.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_check_ai_provider_connection_no_key(self):
        """Test AI provider connection check with no key."""
        health = HealthCheck()
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.NVIDIA_API_KEY = ""
            
            result = await health.check_ai_provider_connection()
            assert result is True  # Should skip gracefully
            assert len(health.warnings) > 0


class TestRunAllChecks:
    """Test run_all_checks method."""
    
    @pytest.mark.asyncio
    async def test_run_all_checks_healthy(self):
        """Test run_all_checks with healthy configuration."""
        health = HealthCheck()
        
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            mock_settings.SECRET_KEY = "test-secret"
            mock_settings.DATABASE_URL = ""
            mock_settings.NVIDIA_API_KEY = ""
            mock_settings.REDIS_URL = ""
            
            result = await health.run_all_checks()
            
            assert result["status"] == "healthy"
            assert result["environment"] == "development"
            assert result["checks_performed"] > 0
            assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_run_all_checks_unhealthy(self):
        """Test run_all_checks with unhealthy configuration."""
        health = HealthCheck()
        
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "production"
            mock_settings.SECRET_KEY = ""  # Missing in production
            
            result = await health.run_all_checks()
            
            assert result["status"] == "unhealthy"
            assert len(result["errors"]) > 0


class TestPerformStartupHealthCheck:
    """Test perform_startup_health_check function."""
    
    @pytest.mark.asyncio
    async def test_perform_startup_health_check(self):
        """Test perform_startup_health_check function."""
        with patch('app.core.health.settings') as mock_settings:
            mock_settings.ENVIRONMENT = "development"
            mock_settings.SECRET_KEY = "test"
            
            result = await perform_startup_health_check()
            
            assert "status" in result
            assert "timestamp" in result
            assert "environment" in result
            assert "checks_performed" in result


class TestGetHealthStatus:
    """Test get_health_status function."""
    
    def test_get_health_status(self):
        """Test get_health_status function."""
        status = get_health_status()
        
        assert status["status"] == "ok"
        assert "timestamp" in status
        assert "environment" in status
        assert "is_production" in status
