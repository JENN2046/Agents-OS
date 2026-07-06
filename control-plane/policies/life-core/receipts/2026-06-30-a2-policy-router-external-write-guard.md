# A2 Control-Plane Receipt: Policy Router External Write Guard

Receipt ID: `a2-policy-router-external-write-guard-2026-06-30`
Date: 2026-06-30
Executor: Nobao
Classification: `A2_home_maintenance`
Scope: `control-plane/policies/life-core/`

## Action

Added explicit Notion external-write phrases to the policy router and locked the
observed false-positive into fixtures.

## Trigger

During hands-on router use, `write Notion page with router result` incorrectly
routed to `allowed` / `A2` because it matched local router housekeeping terms
before matching any external-write phrase.

## Files Updated

- `policy-router.py`
- `policy-router.rules.json`
- `policy-router.fixtures.json`
- `policy-router.md`

## Boundaries Preserved

- No Notion write.
- No external write.
- No runtime execution.
- No provider call.
- No secret or private-memory read.
- No formal Memory registration.

## Validation Plan

- Run `test-policy-router.py`.
- Confirm `write Notion page with router result` routes to
  `needs_activation` / `A3c_or_P3a`.

## Result

Validated locally after creation:

- `test-policy-router.py` passed: 10 cases, 0 failures.
- `write Notion page with router result` now routes to `needs_activation` /
  `A3c_or_P3a`.
- The strict Notion-write route requires `preflight_report`,
  `activation_package`, and `receipt`.
- Lower-priority A2 matches remain visible in `matched_rules`, but no longer
  dilute strict required modules, evidence, denied boundaries, or next steps.
- `read .env and state-private secrets` still routes to `proposal_only` / `A4`
  with only proposal-log evidence.

## Continuation

`COMPLETED`
