"""Regression tests for JARVIS Phase 1 security hardening."""
from __future__ import annotations

import importlib
import os
import sys
import tarfile
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

# file_processor imports the Google GenAI SDK at module import time. Keep these
# security tests runnable in minimal CI environments where that optional SDK is
# not installed; the tests below never make network/API calls.
try:
    from google import genai  # noqa: F401
except ImportError:
    google_module = sys.modules.setdefault("google", types.ModuleType("google"))
    genai_module = types.ModuleType("google.genai")
    setattr(google_module, "genai", genai_module)
    sys.modules["google.genai"] = genai_module

# PyAutoGUI attempts to connect to an X11 display at import time on Linux.
# The security tests do not exercise GUI input, so provide a harmless stub.
sys.modules.setdefault("pyautogui", types.ModuleType("pyautogui"))

from actions import open_app, desktop, file_processor
from api import server


class OpenAppSecurityTests(unittest.TestCase):
    def test_windows_launcher_never_uses_shell(self):
        with patch.object(open_app.shutil, "which", return_value="C:/Apps/notepad.exe"), \
             patch.object(open_app.subprocess, "Popen") as popen:
            self.assertTrue(open_app._launch_windows("notepad.exe"))
        args, kwargs = popen.call_args
        self.assertEqual(args[0], ["C:/Apps/notepad.exe"])
        self.assertIs(kwargs.get("shell"), False)

    def test_windows_launcher_rejects_control_characters(self):
        with patch.object(open_app.shutil, "which") as which:
            self.assertFalse(open_app._launch_windows("notepad\ncalc"))
        which.assert_not_called()

    def test_windows_launcher_rejects_shell_metacharacter_payload(self):
        with patch.object(open_app.shutil, "which", return_value=None), \
             patch("pyautogui.press", create=True) as press, \
             patch("pyautogui.write", create=True) as write:
            self.assertFalse(open_app._launch_windows("notepad & calc"))
        press.assert_not_called()
        write.assert_not_called()

    def test_windows_settings_uri_uses_startfile_not_shell(self):
        with patch("os.startfile", create=True) as startfile, \
             patch.object(open_app.subprocess, "Popen") as popen:
            self.assertTrue(open_app._launch_windows("ms-settings:"))
        startfile.assert_called_once_with("ms-settings:")
        popen.assert_not_called()


class DesktopExecutionSecurityTests(unittest.TestCase):
    def test_generated_python_is_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "should_not_exist.txt"
            code = f"Path({str(marker)!r}).write_text('executed')"
            result = desktop._execute_generated_code(code)
            self.assertIn("disabled for security", result)
            self.assertFalse(marker.exists())

    def test_empty_or_unsafe_response_is_rejected(self):
        self.assertIn("cannot be performed safely", desktop._execute_generated_code("UNSAFE"))
        self.assertIn("cannot be performed safely", desktop._execute_generated_code(""))


class ArchiveExtractionSecurityTests(unittest.TestCase):
    def test_zip_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.zip"
            dest = root / "out"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("../escaped.txt", "owned")
            with self.assertRaises(ValueError):
                file_processor._extract_archive_safely(archive, dest)
            self.assertFalse((root / "escaped.txt").exists())

    def test_zip_absolute_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "absolute.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("/tmp/jarvis-escape.txt", "owned")
            with self.assertRaises(ValueError):
                file_processor._extract_archive_safely(archive, root / "out")

    def test_zip_regular_file_extracts_inside_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "ok.zip"
            dest = root / "out"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("docs/readme.txt", "safe")
            count = file_processor._extract_archive_safely(archive, dest)
            self.assertEqual(count, 1)
            self.assertEqual((dest / "docs" / "readme.txt").read_text(), "safe")

    def test_zip_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "link.zip"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr(info, "../../outside")
            with self.assertRaises(ValueError):
                file_processor._extract_archive_safely(archive, root / "out")

    def test_tar_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "link.tar"
            with tarfile.open(archive, "w") as tf:
                info = tarfile.TarInfo("link")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../outside"
                tf.addfile(info)
            with self.assertRaises(ValueError):
                file_processor._extract_archive_safely(archive, root / "out")

    def test_archive_size_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "large.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("large.bin", b"x" * 32)
            with patch.object(file_processor, "_ARCHIVE_MAX_BYTES", 16):
                with self.assertRaises(ValueError):
                    file_processor._extract_archive_safely(archive, root / "out")


class CorsSecurityTests(unittest.TestCase):
    def test_cors_does_not_use_wildcard_with_credentials(self):
        middleware = next(
            item for item in server.app.user_middleware
            if item.cls.__name__ == "CORSMiddleware"
        )
        self.assertNotIn("*", middleware.kwargs["allow_origins"])
        self.assertFalse(middleware.kwargs["allow_credentials"])
        self.assertTrue(middleware.kwargs["allow_origins"])


if __name__ == "__main__":
    unittest.main()
