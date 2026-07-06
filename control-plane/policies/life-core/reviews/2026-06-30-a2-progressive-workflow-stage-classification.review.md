# A2 Review: Progressive Workflow Stage Classification

Review ID: `review-a2-progressive-workflow-stage-classification-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/policies/life-core/`

## Review Question

Does the workflow now explain that the same topic changes color by stage, and
does the router reflect that distinction?

## Findings

- The workflow now distinguishes explanation, local draft, local rule change,
  external integration, execution, and red-line access.
- External tool integration planning now routes to yellow-zone draft rather than
  ordinary A0.
- Existing local tests now route to green/A2 when they do not touch runtime,
  providers, external systems, secrets, or private memory.
- Private memory raw-text language now routes to proposal-only/A4.

## Risks

- Stage detection is still phrase-based and should be expanded from real use.
- Yellow-zone draft is represented as `needs_classification` with a
  `yellow_zone_draft` permission label, not as a separate router decision.

## Decision

`review_passed_for_local_control_plane_use`
