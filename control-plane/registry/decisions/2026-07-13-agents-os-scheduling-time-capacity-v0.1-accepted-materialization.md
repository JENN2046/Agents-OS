# Accepted Materialization: AGENTS OS Scheduling, Time, and Capacity v0.1

Status: `accepted`
Date: 2026-07-13
Owner: Jenn
Agent steward: Nobao
Acceptance unit: `R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE`
Materialization type: `derived acceptance projection`

## Authority

This materialization records the accepted view of the R1 bundle. It introduces
no new contract semantics and does not replace, rewrite, or modify the reviewed
subject bytes.

The immutable authority record is:

```text
Path: control-plane/registry/decisions/2026-07-13-agents-os-r1-scheduling-freeze-decision-v0.1.yaml
SHA-256: c09a68e3b35275156815acf5398ad7a80c499e2eb9f3c34ae934f63ebe094f8f
Decision: ACCEPTED_FROZEN
Accepted by: Jenn
Effective at: 2026-07-13T20:11:24+08:00
```

If this materialization conflicts with that immutable record or the exact
hash-bound subjects below, the immutable record and exact reviewed bytes win.

## Accepted Subjects

```yaml
acceptance_unit_id: R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE
atomic: true
partial_freeze_permitted: false
accepted_subjects:
  - path: control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md
    sha256: 4ef959a8dd5de2a6837d65debd19e00342168bc86542726c8f6b7635c991a5cf
    scope: Sections 3-9
  - path: control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
    sha256: 12e8984ad24f67d58d26ef9debf605317b0761a6e4f0181ade328567af52373e
    scope: Section 2.1 pending R1 amendment overlay
    effect: effective_as_part_of_this_atomic_freeze
```

The filenames and embedded pre-freeze lifecycle metadata of these subjects are
historical byte identity, not the current acceptance projection. Their accepted
status comes only from Jenn's immutable freeze decision.

## Excluded Subject

```yaml
path: control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md
sha256: a9f54a652018a131843a3563c021c016b32a3e96a953a952592841355ca4a64a
status: EXCLUDED_NOT_ACCEPTED_NOT_FROZEN
```

Resource-constrained Scheduling v0.2 remains a separate preserved design draft.

## Review Basis

```text
Path: control-plane/registry/reviews/2026-07-13-yellow-agents-os-scheduling-time-capacity-package-v0.1.review.yaml
SHA-256: d988d5a60c07892fa59de957fdda5ba232892d48e209e3b6190cf54c4585bb9d
Result: PASS_NO_BLOCKER_OR_MAJOR_READY_FOR_JENN_FREEZE_DECISION
Final round: 10
```

## Authority Not Granted

This acceptance freezes architecture semantics only. It does not authorize:

```text
implementation
Rust runtime construction
runtime activation
database creation or migration
service startup
provider, executor, or host calls
permission expansion
```

The remaining Resident implementation gates continue to be tracked separately.

## Change Rule

Do not edit the reviewed subjects to materialize acceptance. Any semantic change
requires a new revision, a new hash-bound review, and a new Jenn decision. Any
correction to the freeze decision requires a new superseding decision record.

## Integrity Check

```bash
sha256sum -- \
  control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md \
  control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md \
  control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md \
  control-plane/registry/reviews/2026-07-13-yellow-agents-os-scheduling-time-capacity-package-v0.1.review.yaml \
  control-plane/registry/decisions/2026-07-13-agents-os-r1-scheduling-freeze-decision-v0.1.yaml
```
