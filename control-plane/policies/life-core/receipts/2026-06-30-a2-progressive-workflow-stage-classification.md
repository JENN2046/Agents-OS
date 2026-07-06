# A2 Control-Plane Receipt: Progressive Workflow Stage Classification

Receipt ID: `a2-progressive-workflow-stage-classification-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/policies/life-core/`

## Action

Added stage-based classification to the progressive workflow and aligned the
policy router with the new distinction.

## Why This Is A2

- The action is local to the life-core policy directory.
- It clarifies an existing local policy document and router behavior.
- It adds tests for previously unclear cases.
- It does not write to external systems, execute runtime/provider calls, read
  secrets, read private memory, or register formal Memory.

## Files Updated

- `progressive-workflow.md`
- `policy-router.py`
- `policy-router.md`
- `policy-router.rules.json`
- `policy-router.fixtures.json`
- `README.md`
- `policy-index.json`
- `receipts/2026-06-30-a2-progressive-workflow-stage-classification.md`
- `reviews/2026-06-30-a2-progressive-workflow-stage-classification.review.md`

## Validation Plan

- Parse router rules and fixtures.
- Run `test-policy-router.py`.
- Confirm private memory raw text routes to `proposal_only`.
- Confirm local tests route to green/A2.
- Confirm external tool integration plan routes to yellow-zone draft.

## Result

Validated locally after creation:

- `policy-index.json`, `policy-router.rules.json`, and
  `policy-router.fixtures.json` parsed successfully.
- `test-policy-router.py` passed: 17 cases, 0 failures.
- `read private memory raw text` routes to `proposal_only` / `A4`.
- `run local tests` routes to `allowed` / `A2`.
- `prepare external tool integration plan` routes to `needs_classification` /
  `yellow_zone_draft`.
- `identity change for Agent boundary` routes to `needs_activation` /
  `review_memory_gate`.
- `call provider from external tool integration plan` routes to `blocked` /
  `not_authorized_by_life_core`.
- `needs_classification` now outranks plain `allowed`, so yellow-zone draft
  evidence is not diluted by A0 output.

## Continuation

`COMPLETED`
