"""Tests for the plan diff (stdlib unittest, no third-party deps)."""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plan_diff import diff_plans, has_changes, render_diff

DAY39 = Path(__file__).resolve().parent.parent
V1 = json.loads((DAY39 / "examples" / "plan-v1.json").read_text())
V2 = json.loads((DAY39 / "examples" / "plan-v2.json").read_text())


class TestDiffPlans(unittest.TestCase):
    def test_identical_plans_have_no_changes(self):
        self.assertFalse(has_changes(diff_plans(V1, copy.deepcopy(V1))))

    def test_goal_change_reports_old_and_new(self):
        diff = diff_plans(V1, V2)
        self.assertEqual(diff["goal_changed"]["old"], V1["goal"])
        self.assertEqual(diff["goal_changed"]["new"], V2["goal"])

    def test_added_step_detected_by_id(self):
        diff = diff_plans(V1, V2)
        added = [s["id"] for s in diff["steps_added"]]
        self.assertEqual(added, ["step-6"])

    def test_removed_step_detected_by_id(self):
        old = copy.deepcopy(V1)
        new = copy.deepcopy(V1)
        del new["steps"][0]
        removed = [s["id"] for s in diff_plans(old, new)["steps_removed"]]
        self.assertEqual(removed, ["step-1"])

    def test_changed_step_reports_each_field(self):
        diff = diff_plans(V1, V2)
        changed = {c["id"]: c["changes"] for c in diff["steps_changed"]}
        self.assertIn("step-2", changed)
        self.assertIn("action", changed["step-2"])
        self.assertIn("failure_points", changed["step-2"])
        self.assertIn("Summary exceeds the word cap",
                      changed["step-2"]["failure_points"]["new"])

    def test_permission_flag_flip_is_a_change(self):
        old = copy.deepcopy(V1)
        new = copy.deepcopy(V1)
        new["steps"][0]["needs_permission"] = True
        diff = diff_plans(old, new)
        self.assertEqual(len(diff["steps_changed"]), 1)
        self.assertTrue(
            diff["steps_changed"][0]["changes"]["needs_permission"]["new"])

    def test_assumption_removed_and_risk_added(self):
        diff = diff_plans(V1, V2)
        self.assertIn("The material to summarise is supplied or already "
                      "retrieved.", diff["assumptions_removed"])
        self.assertIn("Summary arrives after the 6 PM deadline.",
                      diff["risks_added"])
        self.assertIn("Summary must be under 300 words.",
                      diff["constraints_added"])

    def test_decision_status_change_detected(self):
        diff = diff_plans(V1, V2)
        self.assertEqual(diff["decision_changed"],
                         {"old": "pending", "new": "refine"})

    def test_cli_renders_example_diff_and_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, str(DAY39 / "plan_diff.py"),
             str(DAY39 / "examples" / "plan-v1.json"),
             str(DAY39 / "examples" / "plan-v2.json")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("step-6", proc.stdout)
        self.assertIn("pending", proc.stdout)
        self.assertIn("refine", proc.stdout)
        self.assertIn("Summary arrives after the 6 PM deadline.",
                      proc.stdout)


if __name__ == "__main__":
    unittest.main()
