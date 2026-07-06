# Yellow-Zone Review: Governance Registry Draft v0.1

Review ID: `review-yellow-governance-registry-draft-v0.1-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/registry/`

## Review Question

Does this draft define a useful local governance registry without accidentally
turning the registry into an authorization system?

## Findings

- The draft clearly marks itself as `draft_not_active`.
- It keeps active workspace registry data separate from governance registry
  drafts.
- It defines object types, minimum fields, status values, color-zone fields,
  evidence links, and validation expectations.
- It includes first candidate objects for `life-core`, `policy-router`,
  `task-envelope-system`, and `workspace-registry`.
- It repeats that registry data cannot authorize external writes, runtime
  execution, provider calls, secret access, or formal Memory registration.

## Risks

- The YAML shape is only an example and should not become active without Jenn's
  review.
- The first object list is incomplete.
- Active status for listed existing systems describes their current local use,
  but the Governance Registry itself remains draft.
- Future validator work will be needed before this can become a reliable
  machine-checked registry.

## Decision

`review_passed_as_local_draft`

This is acceptable as a first yellow-zone draft. It should not be treated as
active authority data until Jenn explicitly approves a promotion path.
