"""Non-invasive startup diagnostics; optional integrations never block core startup."""
from __future__ import annotations
import importlib.util
import os
import platform
import shutil
import sys
from pathlib import Path

REQUIRED = ("google", "PyQt6", "sounddevice", "numpy")
OPTIONAL = ("mss", "cv2", "playwright", "docx", "openpyxl", "pptx", "keyring")


def run_health_check(base_dir: str | Path | None = None) -> dict:
    root = Path(base_dir or Path(__file__).resolve().parent.parent)
    checks = {
        "python_version": {"ok": sys.version_info >= (3, 11), "value": platform.python_version()},
        "project_root": {"ok": root.exists(), "value": str(root)},
        "env_file": {"ok": (root / ".env").exists(), "value": ".env present" if (root / ".env").exists() else ".env missing"},
        "gemini_key_configured": {"ok": bool(os.environ.get("GEMINI_API_KEY", "").strip()), "value": "configured" if os.environ.get("GEMINI_API_KEY", "").strip() else "not configured yet"},
        "git": {"ok": shutil.which("git") is not None, "value": shutil.which("git") or "not found"},
    }
    for module in REQUIRED:
        checks[f"dependency:{module}"] = {"ok": importlib.util.find_spec(module) is not None, "value": "installed" if importlib.util.find_spec(module) else "missing"}
    for module in OPTIONAL:
        found = importlib.util.find_spec(module) is not None
        checks[f"optional:{module}"] = {"ok": True, "value": "available" if found else "not installed (feature may be unavailable)"}
    return {"ok": all(v["ok"] for k, v in checks.items() if k.startswith("dependency:") or k in {"python_version", "project_root"}), "checks": checks}
