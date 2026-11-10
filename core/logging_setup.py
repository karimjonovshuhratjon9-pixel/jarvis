"""Rotating, secret-redacting application logging."""
from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re

_SECRET_PATTERNS = [
    re.compile(r"(?i)(GEMINI_API_KEY|GOOGLE_API_KEY|JARVIS_API_KEY|OPENAI_API_KEY)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
]

class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
            for pattern in _SECRET_PATTERNS:
                message = pattern.sub(r"\1=[REDACTED]" if "KEY" in pattern.pattern else "[REDACTED]", message)
            record.msg, record.args = message, ()
        except Exception:
            record.msg, record.args = "[log message redacted]", ()
        return True


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("jarvis")
    if getattr(logger, "_jarvis_configured", False):
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    log_dir = Path(os.environ.get("JARVIS_DATA_DIR", Path.home() / ".jarvis")) / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_dir / "jarvis.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        handler.addFilter(SecretRedactionFilter())
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    logger._jarvis_configured = True
    return logger
