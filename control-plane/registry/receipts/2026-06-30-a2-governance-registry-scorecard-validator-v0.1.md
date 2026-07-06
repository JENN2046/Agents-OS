# A2 Control-Plane Receipt: Governance Registry Scorecard Validator v0.1

Receipt ID: `a2-governance-registry-scorecard-validator-v0.1-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/registry/`

## Action

Created the first local scorecard validator for the AGENTS OS Governance
Registry draft.

## Why This Is A2

- The action is local to `control-plane/registry/`.
- The validator only reads local YAML and checks metadata fields.
- It does not execute registry objects.
- It does not grant authority.
- It does not write to external systems.
- It does not execute runtime/provider/plugin calls.
- It does not read secrets, private memory, or provider raw responses.
- It does not register formal Memory.

## Files Added

- `validate-governance-registry.py`
- `test-governance-registry-validator.py`
- `receipts/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.md`
- `reviews/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.review.md`

## Files Updated

- `README.md`
- `drafts/agents-os-governance-scorecard-v0.1-draft.md`
- `drafts/agents-os-governance-registry-v0.1-draft.md`
- `drafts/agents-os-governance-registry.v0.1.example.yaml`

## Validation Plan

- Run the scorecard validator on the draft Governance Registry YAML example.
- Run the scorecard validator fixture tests.
- Run task-envelope loop fixture tests.
- Run life-core policy-router fixture tests.
- Confirm no Python `__pycache__` files remain under `control-plane/`.

## Result

- Scorecard validator passed on the draft Governance Registry example:
  `objects=8 pass=8 warn=0 fail=0`.
- Scorecard validator fixture tests passed: `cases=3 failures=0`.
- Task-envelope loop fixture tests passed: `cases=3 failures=0`.
- Existing life-core policy-router fixture tests passed: `cases=17 failures=0`.
- Python syntax compilation passed for the new validator scripts.
- Python `__pycache__` files created during syntax compilation were removed
  after validation.
- One test expectation was corrected from `7` objects to `8` objects after the
  validator itself was registered in the draft registry.

## Continuation

`COMPLETED`
