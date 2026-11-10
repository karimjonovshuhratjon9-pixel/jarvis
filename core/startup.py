"""Windows per-user startup registration. No shell commands are executed."""
from __future__ import annotations
import os
import sys
from pathlib import Path

APP_NAME = "JARVIS OS V2"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{Path(sys.executable).resolve()}"'
    root = Path(__file__).resolve().parent.parent
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    interpreter = pythonw if pythonw.exists() else Path(sys.executable)
    return f'"{interpreter}" "{root / "main.py"}"'


def set_auto_start(enabled: bool) -> tuple[bool, str]:
    if os.name != "nt":
        return False, "Automatic login startup is currently supported on Windows only."
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())
                return True, "JARVIS will start when this Windows account signs in."
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            return True, "JARVIS automatic startup is disabled."
    except Exception as exc:
        return False, f"Could not update Windows startup: {exc}"


def auto_start_status() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run") as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except Exception:
        return False
