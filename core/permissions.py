"""Central, fail-closed permission checks for JARVIS tool execution."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re

KNOWN_TOOLS = {
    "open_app", "web_search", "deep_research", "game_updater", "browser_control",
    "file_controller", "media_control", "code_helper", "dev_agent", "screen_process",
    "send_message", "email_control", "reminder", "youtube_video", "weather_report",
    "computer_settings", "desktop_control", "computer_control", "flight_finder",
    "create_presentation", "agent_task", "check_messages", "prepare_message_reply",
    "task_status", "file_processor", "jarvis_ui_control", "search_memory", "save_memory",
}

# Actions that can publish, delete, spend, or materially change system state.
HIGH_RISK = {
    ("file_controller", "delete"), ("file_controller", "move"),
    ("send_message", "*"), ("email_control", "approve"),
    ("prepare_message_reply", "approve"),
    ("computer_settings", "shutdown"), ("computer_settings", "restart"),
    ("computer_settings", "power_off"), ("computer_settings", "turn_off"),
    ("computer_settings", "hibernate"), ("computer_settings", "sleep"),
    ("game_updater", "install"), ("game_updater", "update"),
    ("desktop_control", "clean"),
}

@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    risk: str
    reason: str


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "approved", "approve"}


def classify_action(tool: str, parameters: dict[str, Any] | None = None) -> str:
    params = parameters or {}
    action = str(params.get("action", "*")).strip().lower()
    if (tool, action) in HIGH_RISK or (tool, "*") in HIGH_RISK:
        return "high"
    if tool in {"computer_control", "computer_settings", "desktop_control", "email_control", "game_updater"}:
        return "medium"
    return "low"


def authorize_tool(tool: str, parameters: dict[str, Any] | None = None) -> PermissionDecision:
    params = parameters or {}
    if tool in {"generated_code", "python", "shell", "terminal", "exec"}:
        return PermissionDecision(False, "blocked", "Arbitrary AI-generated code or shell execution is disabled.")
    if tool not in KNOWN_TOOLS:
        return PermissionDecision(False, "blocked", f"Unknown tool '{tool}' is blocked; no fallback execution is permitted.")
    risk = classify_action(tool, params)
    if risk == "high" and not _truthy(params.get("user_approved")):
        return PermissionDecision(False, risk, "This action requires explicit user approval before execution.")
    action = str(params.get("action", "")).lower()
    if tool in {"code_helper", "file_processor"} and action in {"run", "execute", "build"}:
        if not _truthy(os.environ.get("JARVIS_ENABLE_CODE_EXECUTION")):
            return PermissionDecision(False, "high", "Code execution is disabled. Review the code and explicitly enable it in local settings first.")
    return PermissionDecision(True, risk, "Allowed by the local JARVIS permission policy.")


def write_audit_event(tool: str, parameters: dict[str, Any] | None, decision: PermissionDecision) -> None:
    """Append a privacy-conscious event; never persist message bodies or secrets."""
    root = Path(os.environ.get("JARVIS_DATA_DIR", Path.home() / ".jarvis"))
    try:
        root.mkdir(parents=True, exist_ok=True)
        action = str((parameters or {}).get("action", ""))[:40]
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool[:60], "action": action,
            "allowed": decision.allowed, "risk": decision.risk,
            "reason": decision.reason[:180],
        }
        path = root / "audit.jsonl"
        if path.exists() and path.stat().st_size > 1_000_000:
            backup = path.with_suffix(".jsonl.1")
            if backup.exists(): backup.unlink()
            path.replace(backup)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        # Audit failure must not crash the UI; high-risk authorization still fails closed.
        pass
