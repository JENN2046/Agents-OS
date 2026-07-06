# Life Core Policy Module: Standing Authorization

Policy ID: `life-core.standing-authorization.home-maintenance.v0.1`
Status: `review_passed_active_pilot_until_2026-07-07`
Source anchor: `agents-os-life-core-v0.1.local-mirror.md` section 6
Local scope: AGENTS OS home maintenance by authorized resident Agents

## Scope

Applies to Nobao, Project Agent, Memory Agent, and Review Agent for A2 and
limited A3a home maintenance while the pilot remains valid.

## Executable Rules

- Use this only for scoped AGENTS OS home maintenance.
- Keep actions small, reversible, reviewable, and locally evidenced.
- Leave receipts for A2 and any higher classified work.
- Re-check expiry and scope before relying on this module.

## Hard Denials

- No A3b broad autonomy.
- No A3c without full Activation.
- No A4 execution.
- No deletion, secrets, arbitrary shell, provider calls, external publication,
  money movement, self-escalation, or permission bypass.

## Current Local Use

The life-core module split is classified as A2 because it is local policy
housekeeping inside `control-plane/policies/life-core/`, with receipt and
reviewability.

## Receipt Rule

Receipts must state action scope, touched files, validation, denied boundaries,
and whether formal Memory registration was or was not performed.
