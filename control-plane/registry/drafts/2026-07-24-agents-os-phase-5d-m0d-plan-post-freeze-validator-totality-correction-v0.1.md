# Phase 5D M0-D Plan Post-Freeze Validator Totality Correction v0.1

Status: authorized narrow correction for PR #32

## Purpose

The immutable R2 offline validator correctly rejects an altered Plan boundary
in ordinary cases, but an unexpected key in `current_boundary` reaches an
unchecked dictionary lookup and raises `KeyError`. This correction does not
rewrite the immutable validator. It adds a successor that verifies the frozen
validator digest, parses only the Plan header, and rejects malformed boundary
shapes before it can delegate.

## Successor contract

The successor must emit one JSON object with:

```yaml
result: PASS | BLOCK
terminal_outcome: NOT_EXECUTED
delegated_historical_validator: true | false
errors: []
```

Before delegation, `current_boundary` must be a mapping whose key set exactly
matches the immutable R2 boundary inventory. The following inputs must return
`result: BLOCK`, `delegated_historical_validator: false`, and never expose an
uncaught exception:

1. an unknown boundary key;
2. a missing boundary key or missing boundary mapping;
3. a non-mapping boundary value; and
4. a duplicate YAML boundary key.

When the frozen R2 Plan, profile, and synthetic fixture are supplied, the
successor must verify the historical validator SHA-256, delegate exactly once,
and preserve its favorable offline result. The successor is an input-totality
guard only; it does not recalculate Plan semantics or create Host, plugin,
runtime, database, provider, Memory, sensing, or effect authority.

## Current operational entrypoint

The immutable R2 manifest remains an historical package-reproduction record.
For every current validation invocation, including an altered or future Plan
header, callers must use the successor rather than invoke the frozen validator
directly:

```text
python3 control-plane/registry/validate-phase-5d-m0d-plan-post-freeze-validator-totality.py \
  [FIXTURE_PATH] [--plan PLAN_PATH] [--profile PROFILE_PATH]
```

The no-argument form validates the frozen R2 inputs. The successor preserves
the frozen validator's favorable result for those inputs and returns one JSON
`BLOCK` object for malformed input without delegating. `--self-test` runs the
fixed totality regression suite; `--correction-fixture PATH` is available only
to select that suite's synthetic fixture.

## Frozen boundary

The R1/R2 subjects, manifests, reviews, decisions, receipts, and original
validator remain immutable. A later correction must add a new successor or
decision record; it must not edit a frozen R2 byte to silence this review
finding.
