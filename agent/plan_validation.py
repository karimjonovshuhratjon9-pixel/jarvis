"""Validate model-generated plans before any tool is called."""
from __future__ import annotations
from core.permissions import KNOWN_TOOLS

MAX_STEPS = 8
MAX_TEXT = 4000


def validate_plan(plan: dict) -> dict:
    if not isinstance(plan, dict):
        raise ValueError("Planner response must be a JSON object.")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Planner returned no executable steps.")
    if len(steps) > MAX_STEPS:
        raise ValueError(f"Plan exceeds the {MAX_STEPS}-step safety limit.")
    clean = []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            raise ValueError(f"Plan step {index} is not an object.")
        tool = str(step.get("tool", "")).strip()
        if tool not in KNOWN_TOOLS:
            raise ValueError(f"Plan step {index} uses unsupported tool '{tool}'.")
        params = step.get("parameters", {})
        if not isinstance(params, dict):
            raise ValueError(f"Plan step {index} parameters must be an object.")
        clean.append({**step, "step": index, "tool": tool, "parameters": params,
                      "description": str(step.get("description", ""))[:MAX_TEXT]})
    return {**plan, "steps": clean}
