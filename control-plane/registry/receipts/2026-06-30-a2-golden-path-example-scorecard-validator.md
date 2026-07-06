# A2 Control-Plane Receipt: Golden Path Example - Scorecard Validator

Receipt ID: `a2-golden-path-example-scorecard-validator-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/registry/`

## Action

Created the first real Golden Path example by replaying
`路线 1：新增治理部件` against the existing Governance Registry Scorecard
Validator.

## Why This Is A2

- The action is local to `control-plane/registry/`.
- It creates an example and evidence only.
- It does not modify `WORKSPACE_REGISTRY.yaml`.
- It does not mark any draft as active.
- It does not write to external systems.
- It does not execute runtime/provider/plugin calls.
- It does not read secrets, private memory, or provider raw responses.
- It does not register formal Memory.

## Files Added

- `examples/2026-06-30-golden-path-new-governance-object-scorecard-validator.md`
- `receipts/2026-06-30-a2-golden-path-example-scorecard-validator.md`
- `reviews/2026-06-30-a2-golden-path-example-scorecard-validator.review.md`

## Files Updated

- `README.md`
- `drafts/agents-os-golden-paths-v0.1-draft.md`

## Validation Plan

- Run Governance Registry scorecard validator.
- Run scorecard validator fixture tests.
- Run task-envelope loop fixture tests.
- Run life-core policy-router fixture tests.
- Confirm no Python `__pycache__` files remain under `control-plane/`.

## Result

- Golden Path example file exists and references `路线 1：新增治理部件`.
- The example checks the real `governance-registry-scorecard-validator`
  object against all ten route-1 steps.
- Governance Registry scorecard passed:
  `objects=9 pass=9 warn=0 fail=0`.
- Scorecard validator fixture tests passed: `cases=3 failures=0`.
- Task-envelope loop fixture tests passed: `cases=3 failures=0`.
- Existing life-core policy-router fixture tests passed: `cases=17 failures=0`.
- No Python `__pycache__` files remain under `control-plane/`.

## Continuation

`COMPLETED`
