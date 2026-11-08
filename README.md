# plan-diff

Show what changed between two versions of an InspectablePlan — so a
human refining a plan can see exactly what moved before approving it.

Part of Week 1 (Inspectable Plans) of the trustworthy-agentic-ai
prototype for **BRJP26100123 — Building Trustworthy AI Systems through
Explainability and Human-in-the-Loop Control**. Companion repos:
[trustworthy-agentic-ai](https://github.com/anubhav9369/trustworthy-agentic-ai)
(the InspectablePlan schema) and
[plan-explainer](https://github.com/anubhav9369/plan-explainer)
(plain-language rendering + review checklist).

## What it does

`diff_plans` compares two plan JSON files and reports:

- goal reworded (old → new)
- decision status moved (e.g. `pending` → `refine`)
- steps added, removed, or changed — matched by `id`, with per-field
  old → new values (`action`, `why`, `needs_permission`,
  `failure_points`, `alternatives_considered`)
- assumptions, constraints, and risks added or removed

No LLM call: the diff is a deterministic comparison of what each plan
declares. Stdlib only, no third-party dependencies.

## Usage

```bash
python3 plan_diff.py old-plan.json new-plan.json
python3 plan_diff.py old-plan.json new-plan.json --json
```

Example — the two plans in `examples/` differ in the goal (a 6 PM
deadline was added), one step reworded, one step added (delivery
check), one assumption dropped, one constraint and one risk added,
and the decision moved from `pending` to `refine`:

```bash
python3 plan_diff.py examples/plan-v1.json examples/plan-v2.json
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

9 tests, all passing.
