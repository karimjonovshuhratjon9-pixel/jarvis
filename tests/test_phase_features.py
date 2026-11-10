import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.plan_validation import validate_plan
from core.permissions import authorize_tool, PermissionDecision
from core.health_check import run_health_check
from memory.semantic_index import SemanticMemoryIndex
from core.logging_setup import SecretRedactionFilter
from core import startup
from actions import code_helper
import logging
import config


class PermissionTests(unittest.TestCase):
    def test_generated_code_and_unknown_tools_fail_closed(self):
        self.assertFalse(authorize_tool("generated_code", {"description": "do anything"}).allowed)
        self.assertFalse(authorize_tool("invented_tool", {}).allowed)

    def test_send_message_requires_explicit_approval(self):
        self.assertFalse(authorize_tool("send_message", {"receiver": "A"}).allowed)
        self.assertTrue(authorize_tool("send_message", {"user_approved": True}).allowed)

    def test_read_only_search_is_allowed(self):
        self.assertTrue(authorize_tool("web_search", {"query": "weather"}).allowed)


class PlanValidationTests(unittest.TestCase):
    def test_valid_plan_is_normalized(self):
        result = validate_plan({"goal": "search", "steps": [{"tool": "web_search", "description": "search", "parameters": {"query": "x"}}]})
        self.assertEqual(result["steps"][0]["step"], 1)

    def test_unknown_tool_rejected(self):
        with self.assertRaises(ValueError):
            validate_plan({"steps": [{"tool": "generated_code", "parameters": {}}]})

    def test_too_many_steps_rejected(self):
        with self.assertRaises(ValueError):
            validate_plan({"steps": [{"tool": "web_search", "parameters": {}} for _ in range(9)]})


class MemoryIndexTests(unittest.TestCase):
    def test_index_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = SemanticMemoryIndex(Path(tmp) / "memory.sqlite3")
            index.upsert("projects", "jarvis", "Uzbek voice assistant with Windows automation")
            results = index.search("Uzbek voice assistant")
            self.assertTrue(results)
            self.assertEqual(results[0]["key"], "jarvis")
            self.assertTrue(index.delete("projects", "jarvis"))
            self.assertEqual(index.search("Uzbek voice assistant"), [])


class HealthCheckTests(unittest.TestCase):
    def test_health_check_reports_project_and_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text("GEMINI_API_KEY=\n", encoding="utf-8")
            result = run_health_check(root)
            self.assertTrue(result["checks"]["project_root"]["ok"])
            self.assertTrue(result["checks"]["env_file"]["ok"])


class FoundationHardeningTests(unittest.TestCase):
    def test_secret_redaction_filter_masks_api_keys(self):
        record = logging.LogRecord("test", logging.INFO, "", 0, "GEMINI_API_KEY=%s", ("AIza" + "x" * 30,), None)
        SecretRedactionFilter().filter(record)
        self.assertNotIn("AIza", record.getMessage())
        self.assertIn("REDACTED", record.getMessage())

    def test_os_config_works_without_private_api_json(self):
        self.assertIn(config.get_os(), {"windows", "mac", "linux"})

    def test_auto_start_is_windows_only(self):
        with patch.object(startup.os, "name", "posix"):
            ok, message = startup.set_auto_start(True)
        self.assertFalse(ok)
        self.assertIn("Windows", message)

    def test_code_execution_is_disabled_by_default(self):
        with patch.dict("os.environ", {"JARVIS_ENABLE_CODE_EXECUTION": "0"}, clear=False):
            result = code_helper._run_file(Path("/tmp/does-not-run.py"), [], 5)
        self.assertIn("disabled", result.lower())


if __name__ == "__main__":
    unittest.main()
