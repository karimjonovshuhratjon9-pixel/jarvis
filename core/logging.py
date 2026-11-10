"""Centralized logging for JARVIS OS V2.

Provides:
- Structured logging via the standard `logging` module.
- Automatic secret redaction (API keys, tokens, passwords).
- Log rotation (size-based, with backups).
- UTF-8 encoding.
- Integration with the existing UI log sink (write_log).

Usage:
    from core.logging import get_logger
    logger = get_logger("module_name")
    logger.info("Something happened")
    logger.error("Failed", exc_info=True)
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import re
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------

# Patterns that indicate a secret value follows.
_SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|token|password|secret|authorization|auth|bearer)\s*[=:]\s*"
    r"([^\s,;'\"]+)"
)

# Long high-entropy-looking strings that are likely keys.
_LONG_KEY_RE = re.compile(r"\b[A-Za-z0-9_\-\.]{20,}\b")


def redact_line(line: str) -> str:
    """Return a copy of `line` with secret values replaced by [REDACTED]."""
    if not line:
        return ""
    s = str(line)

    # Redact key=value patterns.
    s = _SECRET_KEY_RE.sub(r"\1=[REDACTED]", s)

    # Redact long alphanumeric strings that look like keys.
    # Only redact if the line already contained a secret keyword.
    if _SECRET_KEY_RE.search(s):
        s = _LONG_KEY_RE.sub("[REDACTED]", s)

    return s


class RedactingFormatter(logging.Formatter):
    """Formatter that applies redact_line to the message."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return redact_line(message)


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "jarvis.log"

_MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
_BACKUP_COUNT = 5

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_handler: Optional[logging.handlers.RotatingFileHandler] = None
_root_logger: Optional[logging.Logger] = None


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Initialize the centralized logger. Safe to call multiple times."""
    global _handler, _root_logger

    if _root_logger is not None:
        return _root_logger

    root = logging.getLogger("jarvis")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # File handler with rotation.
    handler = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(RedactingFormatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(handler)

    # Console handler (stderr) for CLI visibility.
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(RedactingFormatter(_FORMAT, datefmt=_DATEFMT))
    root.addHandler(console)

    _handler = handler
    _root_logger = root
    return root


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the centralized 'jarvis' logger.

    If setup_logging() has not been called, sets up with defaults.
    """
    if _root_logger is None:
        setup_logging()
    return logging.getLogger(f"jarvis.{name}")


def rotate_now() -> None:
    """Force log rotation."""
    if _handler is not None:
        _handler.doRollover()


def get_log_dir() -> Path:
    return _LOG_DIR


def get_log_file() -> Path:
    return _LOG_FILE


# ---------------------------------------------------------------------------
# UI integration
# ---------------------------------------------------------------------------

_ui_sink = None


def set_ui_sink(sink) -> None:
    """Register a callable that receives log lines (e.g. JarvisUI.write_log)."""
    global _ui_sink
    _ui_sink = sink


class _UIHandler(logging.Handler):
    """Logging handler that forwards records to the UI sink."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if _ui_sink is None:
                return
            msg = self.format(record)
            msg = redact_line(msg)
            _ui_sink(msg)
        except Exception:
            pass


def install_ui_handler() -> None:
    """Attach a UI handler to the root logger."""
    if _root_logger is None:
        setup_logging()
    handler = _UIHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(RedactingFormatter(_FORMAT, datefmt=_DATEFMT))
    _root_logger.addHandler(handler)