# PR Gate Review Checklist

Use this checklist before opening a PR that touches readiness gates, runtime
provenance, package verification, endpoint/auth routing, redaction, or operator
status fields.

## Review Rule

Do not ask:

```text
Did the happy evidence match?
```

Ask:

```text
Is there any unproven state that can still make the gate report ready?
```

For equivalence claims:

```text
Prove A contains B, prove B contains A, then prove shared members match.
```

For fallbacks:

```text
Fallbacks are alternate proof paths with their own blockers, statuses, and regression tests.
```

## PR Body Proof Matrix

If `pr-risk-review.py` reports any risk surface, include this section in the PR
description:

```md
Risk surface:
- [ ] runtime provenance / package file set
- [ ] readiness gate
- [ ] public endpoint / OAuth / auth routing
- [ ] redaction / secret handling
- [ ] status enum / operator contract
- [ ] none

Invariant:

Evidence required:

Negative cases:

Status fields tested:
```

## Required Negative Matrix

For gate-like code, cover the relevant negative cases:

- missing expected artifact
- extra supplied or installed artifact
- content mismatch
- dirty trusted source
- unavailable evidence
- stale but superficially matching metadata
- equivalent but differently spelled self-reference
- non-public address classes, including multicast
- oversized candidate/resource exhaustion inputs
- proxy or environment interference where direct proof is required
- redaction before any early return

## Status Contract

If a gate has status fields, test both the behavior and the status. A status enum
is an operator contract, not debug output.
