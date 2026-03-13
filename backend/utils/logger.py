"""
Structured logging configuration with file rotation and console output.

Provides:
- Colored console output
- Rotating file handler
- Structured logging support
- Contextualized logging
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict, Any

from backend.config import settings


class ContextFilter(logging.Filter):
    """Add contextual information to log records."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record):
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class LoggerEngine:
    """
    Centralized logging configuration.

    Features:
    - Console and file output
    - Log rotation
    - Configurable levels
    - Context injection
    """

    _loggers: Dict[str, logging.Logger] = {}
    _context_filter: Optional[ContextFilter] = None

    @classmethod
    def configure(cls) -> None:
        """Configure logging system."""
        # Create log directory
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Format strings
        detailed_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(funcName)s:%(lineno)d | %(message)s"
        )
        simple_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        console_formatter = logging.Formatter(simple_format, datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(detailed_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)

        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.handlers.clear()  # Clear existing handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger instance."""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        return cls._loggers[name]

    @classmethod
    def set_context(cls, context: Dict[str, Any]) -> None:
        """Set context for all loggers."""
        cls._context_filter = ContextFilter(context)
        for logger in cls._loggers.values():
            # Remove old filter if exists
            logger.filters = [f for f in logger.filters if not isinstance(f, ContextFilter)]
            # Add new filter
            logger.addFilter(cls._context_filter)


# Initialize logging
LoggerEngine.configure()

# Convenience function
def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return LoggerEngine.get_logger(name)