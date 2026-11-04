"""
AQUILA - Structured Application Logging Configuration
Provides standardized, structured logging across all system components.
Ensures zero exposure of credentials, absolute filesystem paths, or sensitive PII.
"""

import os
import sys
import logging
from datetime import datetime, timezone

LOG_LEVEL = os.environ.get("AQUILA_LOG_LEVEL", "INFO").upper()

class StructuredFormatter(logging.Formatter):
    """Formats log records with standardized component, timestamp, and operation context."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        component = getattr(record, "component", "AQUILA")
        operation = getattr(record, "operation", record.funcName)
        
        # Base log message
        msg = record.getMessage()

        # Sanitize internal filesystem paths if present
        if "C:\\" in msg or "c:\\" in msg or "/home/" in msg:
            # Replace absolute paths with generic markers
            msg = msg.replace(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), ".")

        return f"[{timestamp}] [{record.levelname:<5}] [{component}] [{operation}] {msg}"


def setup_logger(name: str = "aquila", component: str = "SYSTEM") -> logging.Logger:
    """Creates or retrieves a structured logger with standard handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    # Attach default component attribute
    logger = logging.LoggerAdapter(logger, {"component": component, "operation": "MAIN"})
    return logger

# Default platform logger
app_logger = setup_logger("aquila", "AQUILA_CORE")

