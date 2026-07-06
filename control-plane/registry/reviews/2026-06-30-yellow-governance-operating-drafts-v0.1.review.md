# Yellow-Zone Review: Governance Operating Drafts v0.1

Review ID: `review-yellow-governance-operating-drafts-v0.1-2026-06-30`
Date: 2026-06-30
Reviewer: Nobao local self-review
Scope: `control-plane/registry/`

## Review Question

Do the Golden Paths, Decision Record Template, and Governance Scorecard drafts
make AGENTS OS governance easier to run without making drafts look like active
authority?

## Findings

- All three files are marked `draft_not_active`.
- Golden Paths focuses on repeatable local routes and includes stop conditions.
- Decision Record Template separates "why this changed" from task envelopes,
  receipts, and reviews.
- Governance Scorecard defines basic health checks without claiming final
  authority.
- The drafts repeatedly preserve Jenn authority, P3 hard stop, secret
  boundaries, private memory boundaries, provider raw response boundaries,
  external-write gates, runtime gates, and formal Memory gates.

## Risks

- The drafts are not yet machine-enforced.
- Scorecard rules are text-only and need a later validator if Jenn wants them
  enforced.
- Golden Paths are useful only if future work actually follows them.
- Decision Records can create paperwork if used for tiny changes, so the draft
  limits them to governance-impacting decisions.

## Decision

`review_passed_as_local_draft`

These drafts are acceptable as local yellow-zone operating guidance. They do
not become active authority until Jenn approves a promotion path.
