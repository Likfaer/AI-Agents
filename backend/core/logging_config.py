"""
Structured logging with JSON output and file rotation.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone

from backend.core.config import settings


class UTCFormatter(logging.Formatter):
    """JSON-structured log formatter with UTC timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "agent_id"):
            log_obj["agent_id"] = record.agent_id
        if hasattr(record, "task_id"):
            log_obj["task_id"] = record.task_id
        if hasattr(record, "tool"):
            log_obj["tool"] = record.tool

        import json
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging() -> None:
    """Configure application-wide logging."""
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Console handler — human-readable
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root_logger.addHandler(console_handler)

    # File handler — JSON structured
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(UTCFormatter())
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    for noisy in ("httpx", "httpcore", "openai", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
