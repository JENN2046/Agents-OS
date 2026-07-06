# A2 Review: Policy Router External Write Guard

Review ID: `review-a2-policy-router-external-write-guard-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/policies/life-core/`

## Review Question

Does the router now prevent Notion external-write language from being mistaken
for local A2 router housekeeping?

## Findings

- The external-write rule now includes both `notion write` and `write notion`
  style phrases.
- `notion page`, `create notion`, and `update notion` are also treated as
  external-write signals.
- A fixture covers the observed false-positive.

## Risks

- The router remains phrase-based and may need more external-write variants over
  time.
- Conservative over-routing to `needs_activation` is acceptable for external
  systems.

## Decision

`review_passed_for_local_control_plane_use`
