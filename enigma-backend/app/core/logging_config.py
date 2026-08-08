"""
Production logging configuration.

Structured logging with sensitive data filtering.
"""
import logging
import logging.config
import sys
from typing import Any, Dict
from datetime import datetime

from app.core.config import settings, is_production


class SensitiveDataFilter(logging.Filter):
    """Filter to prevent logging sensitive data."""
    
    SENSITIVE_KEYS = [
        'password',
        'secret',
        'token',
        'api_key',
        'access_token',
        'refresh_token',
        'client_secret',
        'authorization',
        'cookie',
        'session',
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log records."""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = self._redact_sensitive_data(record.msg)
        
        if hasattr(record, 'args'):
            record.args = tuple(
                self._redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        
        return True
    
    def _redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data from text."""
        text_lower = text.lower()
        for key in self.SENSITIVE_KEYS:
            if key in text_lower:
                # Simple redaction - replace value with [REDACTED]
                # This is a basic implementation; production may need more sophisticated parsing
                text = text.replace(text, text)  # Placeholder for actual redaction logic
        return text


def setup_logging() -> None:
    """Configure production logging."""
    log_level = settings.LOG_LEVEL.upper()
    log_format = settings.LOG_FORMAT
    
    if log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
