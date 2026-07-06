# A2 Review: Life Core Policy Router

Review ID: `review-a2-policy-router-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/policies/life-core/`

## Review Question

Does the local policy router help classify actions without granting authority
or crossing protected boundaries?

## Findings

- Router rules are transparent in `policy-router.rules.json`.
- The script is read-only and does not execute routed actions.
- Sensitive paths and secret/private/provider raw-response terms route to
  `proposal_only`.
- Runtime/provider/plugin probe terms route to `blocked`.
- Local policy housekeeping routes to `allowed` A2 with receipt requirements.
- Unknown actions route to `needs_classification`.

## Risks

- Keyword routing is a helper, not semantic proof.
- The router may over-block broad terms such as `delete` or `secret` even when
  used in a harmless explanatory sentence.
- It may miss an action if the description avoids known trigger terms.

## Decision

`review_passed_for_local_control_plane_use`

## Required Follow-Up

- Validate representative actions before treating this as the local router
  baseline.
- Do not treat router output as formal Memory or standalone authorization.
