"""
Structured JSON logging configuration.

This module provides structured logging utilities that output JSON-formatted
logs to stdout, suitable for containerized deployments and log aggregation.

Features:
- JSON structured logging
- Correlation ID support
- Request/response logging
- Error tracking
- Performance metrics

Usage:
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("User created", user_id=123, email="user@example.com")
"""

import logging
import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

from app.core.config import settings

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation ID if available
        corr_id = correlation_id.get()
        if corr_id:
            log_data["correlation_id"] = corr_id
        
        # Add extra fields
        if hasattr(record, 'extra') and record.extra:
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Configure application logging."""
    # Create JSON formatter
    formatter = JSONFormatter()
    
    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def set_correlation_id(correlation_id_value: Optional[str] = None) -> str:
    """
    Set correlation ID for request tracking.
    
    Args:
        correlation_id_value: Optional correlation ID, generates one if not provided
        
    Returns:
        str: The correlation ID that was set
    """
    if correlation_id_value is None:
        correlation_id_value = str(uuid.uuid4())
    
    correlation_id.set(correlation_id_value)
    return correlation_id_value


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id.get()


def log_with_extra(logger: logging.Logger, level: int, message: str, **extra: Any) -> None:
    """
    Log a message with extra structured data.
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **extra: Additional structured data
    """
    logger.log(level, message, extra=extra)


def log_request(logger: logging.Logger, method: str, path: str, **extra: Any) -> None:
    """Log HTTP request."""
    log_with_extra(
        logger, 
        logging.INFO, 
        f"{method} {path}",
        event_type="request",
        method=method,
        path=path,
        **extra
    )


def log_response(logger: logging.Logger, method: str, path: str, status_code: int, 
                duration_ms: float, **extra: Any) -> None:
    """Log HTTP response."""
    log_with_extra(
        logger,
        logging.INFO,
        f"{method} {path} {status_code} ({duration_ms:.2f}ms)",
        event_type="response",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **extra
    )


def log_error(logger: logging.Logger, error: Exception, **extra: Any) -> None:
    """Log error with structured data."""
    log_with_extra(
        logger,
        logging.ERROR,
        str(error),
        event_type="error",
        error_type=type(error).__name__,
        **extra
    )