"""Portable runtime configuration with safe defaults and optional local overrides."""
from __future__ import annotations
import json
import os
import platform
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "api_keys.json"

def get_config() -> dict:
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8")) if _CONFIG_PATH.exists() else {}
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}

def get_os() -> str:
    configured = str(get_config().get("os_system", "")).strip().lower()
    if configured in {"windows", "mac", "linux"}:
        return configured
    system = platform.system().lower()
    return "windows" if system == "windows" else "mac" if system == "darwin" else "linux"

def is_windows() -> bool: return get_os() == "windows"
def is_mac() -> bool: return get_os() == "mac"
def is_linux() -> bool: return get_os() == "linux"
