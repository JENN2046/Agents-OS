# Life Core Policy Module: Evidence Levels

Policy ID: `life-core.evidence-levels.v0.1`
Status: `review_passed_active_reference`
Source anchor: `agents-os-life-core-v0.1.local-mirror.md` section 7
Local scope: logs, receipts, reviews, memory registration, activation evidence

## Levels

- Small action: log.
- Important action: receipt.
- Boundary action: Review.
- Community-inheritable action: Memory.
- High-impact real-world action: full Activation.
- A4 raw capability: proposal log only.

## Executable Rules

- Pick the evidence level before or during the action, not only after success.
- A2 actions need at least a receipt when they modify local control-plane state.
- Boundary decisions need reviewability and may require a Review artifact.
- Formal memory must not be implied by a receipt.

## Hard Denials

- Do not fake validation, review, receipt, or Memory registration.
- Do not expose secrets or private raw memory in evidence artifacts.

## Receipt Rule

Receipts should include scope, classification, files touched, validation,
result, denied boundaries, remaining risk, and continuation status.
