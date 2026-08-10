"""
Secret Leakage Tests

Tests to ensure no hardcoded secrets in codebase.
"""

import pytest
import os
import re
from pathlib import Path


class TestSecretLeakage:
    """Test secret leakage prevention."""
    
    def test_no_hardcoded_api_keys_in_python(self):
        """Test no hardcoded API keys in Python files."""
        app_dir = Path("e:/app/enigma/enigma-backend/app")
        
        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            r'api_key\s*=\s*["\'][^"\']{20,}["\']',  # Long strings assigned to api_key
            r'secret\s*=\s*["\'][^"\']{20,}["\']',  # Long strings assigned to secret
            r'password\s*=\s*["\'][^"\']{8,}["\']',  # Passwords
            r'token\s*=\s*["\'][^"\']{20,}["\']',  # Tokens
        ]
        
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            
            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                # Filter out test files and comments
                if matches and "test" not in str(py_file):
                    # Check if it's in a comment or docstring
                    for match in matches:
                        if not match.strip().startswith("#"):
                            pytest.fail(f"Potential hardcoded secret in {py_file}: {match}")
    
    def test_no_hardcoded_urls_in_python(self):
        """Test no hardcoded production URLs in Python files."""
        app_dir = Path("e:/app/enigma/enigma-backend/app")
        
        # Patterns that might indicate hardcoded URLs
        url_patterns = [
            r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # HTTP/HTTPS URLs
        ]
        
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            
            for pattern in url_patterns:
                matches = re.findall(pattern, content)
                # Filter out localhost, example.com, and test URLs
                for match in matches:
                    if not any(skip in match for skip in ["localhost", "127.0.0.1", "example.com", "test"]):
                        # Check if it's in a comment or docstring
                        if not match.strip().startswith("#"):
                            # Allow certain patterns (like NVIDIA API base URL)
                            if "nvidia" not in match.lower() and "api" not in match.lower():
                                pytest.fail(f"Potential hardcoded URL in {py_file}: {match}")
    
    def test_no_secrets_in_config_file(self):
        """Test no actual secrets in .env.example."""
        env_example = Path("e:/app/enigma/enigma-backend/.env.example")
        
        if env_example.exists():
            content = env_example.read_text()
            
            # Check for actual secrets (not placeholders)
            secret_indicators = ["nvapi-", "sk-", "pk_", "secret_key="]
            
            for line in content.splitlines():
                if line.strip() and not line.strip().startswith("#"):
                    for indicator in secret_indicators:
                        if indicator in line.lower() and "=" in line:
                            value = line.split("=", 1)[1].strip()
                            # Check if it looks like a real secret (not placeholder)
                            if value and not any(placeholder in value.lower() for placeholder in ["your-", "example", "placeholder", "change"]):
                                pytest.fail(f"Potential real secret in .env.example: {line}")
    
    def test_no_secrets_in_gitignore(self):
        """Test .env is in .gitignore."""
        gitignore = Path("e:/app/enigma/.gitignore")
        
        if gitignore.exists():
            content = gitignore.read_text()
            assert ".env" in content, ".env not in .gitignore"
    
    def test_no_database_credentials_in_code(self):
        """Test no database credentials hardcoded in code."""
        app_dir = Path("e:/app/enigma/enigma-backend/app")
        
        # Pattern for database connection strings with credentials
        db_patterns = [
            r'postgresql://[^:]+:[^@]+@',  # postgresql://user:pass@host
            r'mysql://[^:]+:[^@]+@',  # mysql://user:pass@host
            r'mongodb://[^:]+:[^@]+@',  # mongodb://user:pass@host
        ]
        
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            
            for pattern in db_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Check if it's in a comment
                    if not match.strip().startswith("#"):
                        pytest.fail(f"Potential hardcoded database credentials in {py_file}: {match}")
    
    def test_environment_variables_only_source_of_truth(self):
        """Test that configuration only uses environment variables."""
        from app.core.config import Settings
        
        # Check that Settings doesn't have hardcoded secrets
        settings = Settings()
        
        # These should be empty unless set via environment
        assert settings.SECRET_KEY == "" or len(settings.SECRET_KEY) < 10, "SECRET_KEY appears hardcoded"
        assert settings.NVIDIA_API_KEY == "" or len(settings.NVIDIA_API_KEY) < 10, "NVIDIA_API_KEY appears hardcoded"
        assert settings.UPWORK_CLIENT_ID == "" or len(settings.UPWORK_CLIENT_ID) < 10, "UPWORK_CLIENT_ID appears hardcoded"
        assert settings.UPWORK_CLIENT_SECRET == "" or len(settings.UPWORK_CLIENT_SECRET) < 10, "UPWORK_CLIENT_SECRET appears hardcoded"
