# A2 Control-Plane Receipt: Life Core Policy Router

Receipt ID: `a2-policy-router-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/policies/life-core/`

## Action

Added a small read-only policy router for local life-core action
classification.

## Why This Is A2

- The action is local to the control-plane policy directory.
- The router is read-only and does not execute routed actions.
- It organizes existing life-core policy modules into a routing helper.
- It does not access secrets, private memory, runtime, providers, external
  accounts, browser login state, Notion writes, Git, production, release, or
  formal Memory.

## Files Added

- `policy-router.py`
- `policy-router.rules.json`
- `policy-router.md`
- `receipts/2026-06-30-a2-policy-router.md`
- `reviews/2026-06-30-a2-policy-router.review.md`

## Files Updated

- `README.md`
- `policy-index.json`

## Boundaries Preserved

- No Notion write.
- No external write.
- No Git action.
- No runtime execution.
- No provider call.
- No secret or private-memory read.
- No formal Memory registration.
- No permission escalation.

## Validation Plan

- Confirm `policy-index.json` parses as JSON.
- Confirm `policy-router.rules.json` parses as JSON.
- Run router against representative A2, runtime-blocked, proposal-only, and
  unknown actions.
- Confirm outputs are conservative and include required modules and evidence.

## Result

Validated locally after creation:

- `policy-index.json` parsed successfully.
- `policy-router.rules.json` parsed successfully.
- WSL `python3` is available as Python 3.12.3.
- Windows-side `python` command is not available, so docs use `python3`.
- A2 sample routed to `allowed` / `A2`.
- VCPToolBox runtime/provider sample routed to `blocked`.
- `state-private` + secrets sample routed to `proposal_only` / `A4`, even
  though it also matched a read-only term.
- Unknown sample routed to `needs_classification`.

## Continuation

`COMPLETED`
