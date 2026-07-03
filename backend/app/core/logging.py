"""Structured logging configuration.

Emits either human-readable lines (development) or single-line JSON (production,
suitable for log aggregation) based on :attr:`Settings.log_json`.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from app.core.config import get_settings

_CONFIGURED = False


class _JsonFormatter(logging.Formatter):
    """Render log records as compact JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include any structured extras attached via ``logger.info(..., extra={...})``.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


# Attributes present on every LogRecord that must not be treated as extras.
_RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def configure_logging() -> None:
    """Configure the root logger once, idempotently."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for ``name``."""

    configure_logging()
    return logging.getLogger(name)
