# A2 Review: Task Envelope v0.1

Review ID: `review-a2-task-envelope-v0.1-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/task-envelope/`

## Review Question

Does the first task envelope template connect the progressive workflow to an
actual usable doing-form?

## Findings

- The template asks what the task is, which stage it is in, and whether it is
  green, yellow, or red.
- It includes policy-router precheck fields.
- It asks whether the work can be automatic, draft-only, review-gated,
  Jenn-gated, or proposal-only.
- It includes allowed scope, denied scope, steps, stop conditions, evidence,
  validation, risk, and final status.
- The wording is written for human use in Chinese plain language.

## Risks

- This is a local template, not a schema-enforced form yet.
- Later work should add a small filled example and possibly a machine-readable
  companion format.

## Decision

`review_passed_for_local_control_plane_use`
