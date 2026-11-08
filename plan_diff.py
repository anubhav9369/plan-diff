"""Plan diff — show what changed between two InspectablePlan versions.

When a human refines a plan, they need to see exactly what moved:
which steps were added, removed, or reworded, which assumptions,
constraints, and risks changed, and whether the decision status moved.
``diff_plans`` returns the structured change set; ``render_diff`` turns
it into a short Markdown summary a reviewer can read in a minute.

The plan shape is the InspectablePlan schema from the
trustworthy-agentic-ai hub (Week 1, BRJP26100123). Steps are matched by
``id``; steps without an id are matched by position. No LLM call:
the diff is a deterministic comparison of what each plan declares.

Usage:
    python3 plan_diff.py old-plan.json new-plan.json
    python3 plan_diff.py old-plan.json new-plan.json --json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

STEP_FIELDS = ("action", "why", "needs_permission", "failure_points",
               "alternatives_considered")
LIST_FIELDS = ("assumptions", "constraints", "risks")


def _step_key(step: dict, index: int) -> str:
    return step.get("id") or f"#{index + 1}"


def _index_steps(steps: list) -> dict:
    return {_step_key(step, i): step for i, step in enumerate(steps or [])}


def diff_plans(old: dict, new: dict) -> dict:
    """Compare two InspectablePlan dicts and return the change set."""
    diff: dict = {
        "goal_changed": None,
        "decision_changed": None,
        "steps_added": [],
        "steps_removed": [],
        "steps_changed": [],
        "assumptions_added": [],
        "assumptions_removed": [],
        "constraints_added": [],
        "constraints_removed": [],
        "risks_added": [],
        "risks_removed": [],
    }

    if (old.get("goal") or "") != (new.get("goal") or ""):
        diff["goal_changed"] = {"old": old.get("goal"), "new": new.get("goal")}

    old_decision = old.get("human_decision") or {}
    new_decision = new.get("human_decision") or {}
    if old_decision.get("status") != new_decision.get("status"):
        diff["decision_changed"] = {
            "old": old_decision.get("status", "pending"),
            "new": new_decision.get("status", "pending"),
        }

    old_steps = _index_steps(old.get("steps"))
    new_steps = _index_steps(new.get("steps"))
    for key, step in new_steps.items():
        if key not in old_steps:
            diff["steps_added"].append(step)
    for key, step in old_steps.items():
        if key not in new_steps:
            diff["steps_removed"].append(step)
    for key in old_steps.keys() & new_steps.keys():
        changes = {}
        for field in STEP_FIELDS:
            if old_steps[key].get(field) != new_steps[key].get(field):
                changes[field] = {
                    "old": old_steps[key].get(field),
                    "new": new_steps[key].get(field),
                }
        if changes:
            diff["steps_changed"].append({"id": key, "changes": changes})

    for field in LIST_FIELDS:
        old_items = list(old.get(field) or [])
        new_items = list(new.get(field) or [])
        diff[f"{field}_added"] = [i for i in new_items if i not in old_items]
        diff[f"{field}_removed"] = [i for i in old_items if i not in new_items]

    return diff


def has_changes(diff: dict) -> bool:
    """True when the diff records any change at all."""
    return any(
        diff[key]
        for key in diff
        if key not in ("goal_changed", "decision_changed")
    ) or diff["goal_changed"] is not None or diff["decision_changed"] is not None


def render_diff(diff: dict) -> str:
    """Render a diff as a short Markdown summary for the reviewer."""
    if not has_changes(diff):
        return "No changes — the two plans are identical.\n"
    lines = ["# Plan changes\n"]
    if diff["goal_changed"]:
        lines.append("## Goal changed")
        lines.append(f"- Before: {diff['goal_changed']['old']}")
        lines.append(f"- After: {diff['goal_changed']['new']}")
        lines.append("")
    if diff["decision_changed"]:
        change = diff["decision_changed"]
        lines.append(f"Decision: **{change['old']}** → **{change['new']}**\n")
    for step in diff["steps_added"]:
        lines.append(f"## Step added: {_step_key(step, 0)}")
        lines.append(f"- {step.get('action') or '(no action stated)'}")
        if step.get("needs_permission"):
            lines.append("- 🔒 needs your permission")
        lines.append("")
    for step in diff["steps_removed"]:
        lines.append(f"## Step removed: {_step_key(step, 0)}")
        lines.append(f"- {step.get('action') or '(no action stated)'}")
        lines.append("")
    for entry in diff["steps_changed"]:
        lines.append(f"## Step changed: {entry['id']}")
        for field, change in entry["changes"].items():
            lines.append(f"- {field}: {change['old']!r} → {change['new']!r}")
        lines.append("")
    for field in LIST_FIELDS:
        for item in diff[f"{field}_added"]:
            lines.append(f"- {field[:-1].capitalize()} added: {item}")
        for item in diff[f"{field}_removed"]:
            lines.append(f"- {field[:-1].capitalize()} removed: {item}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] in ("-h", "--help"):
        print("usage: plan_diff.py <old-plan.json> <new-plan.json> [--json]")
        return 2
    old = json.loads(Path(argv[1]).read_text())
    new = json.loads(Path(argv[2]).read_text())
    diff = diff_plans(old, new)
    if "--json" in argv[3:]:
        print(json.dumps(diff, indent=2, default=str))
    else:
        print(render_diff(diff), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
