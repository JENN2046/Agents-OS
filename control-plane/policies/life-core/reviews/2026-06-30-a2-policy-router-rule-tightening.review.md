# A2 Review: Policy Router Rule Tightening

Review ID: `review-a2-policy-router-rule-tightening-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/policies/life-core/`

## Review Question

Does the router now distinguish read-only explanation from A2 policy
housekeeping more reliably?

## Findings

- A2 policy housekeeping now requires a scope signal and a modification intent
  signal.
- Pure explain/review actions that mention `life-core`, `policy`, or `modules`
  should stay A0 when they also match read-only terms.
- High-priority hard boundaries still outrank lower allowed routes.
- Fixture tests make the known false-positive a regression case.

## Risks

- The router is still keyword-based and may need more fixture cases as new
  action language appears.
- Some legitimate A2 actions may route to `needs_classification` if described
  without a known modification verb.

## Decision

`review_passed_for_local_control_plane_use`

## Required Follow-Up

- Run the fixture tests and update the receipt.
- Keep adding fixtures before widening router authority.
