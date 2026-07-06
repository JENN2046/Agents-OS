# Review: AGENTS OS Machine Skeleton Hardening v0.1

Status: accepted
Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao

## Review Result

Pass.

The hardening fixes close the queue path boundary issue, improve P3/external
write signal detection, make blocked previews unambiguously non-actionable, and
connect the schema descriptor's `required_false` field to real validation.

## Findings

- PASS: Protected queue paths are blocked before read.
- PASS: Outside-workspace queue paths are blocked before read.
- PASS: Denied signal fixtures cover provider/service, external write, and
  database write.
- PASS: Blocked previews remain `execution_authorized=false` and
  `actionable=false`.
- PASS: Current unblocked `NOW` preview remains `execution_authorized=false`,
  `requires_nobao_review=true`, and `actionable=true`.
- PASS: Machine tests pass with `cases=12 failures=0`.

## Residual Risk

Pattern-based denied-signal detection is not semantic authorization. It should
remain a conservative preview-layer guard, not an executor permission model.
