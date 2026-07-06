# Review: Validator Boundary Pilot 2 - Governance Registry Validator

Date: 2026-07-01
Status: reviewed
Scope: checklist-driven hardening of `validate-governance-registry.py`

## Review Result

Validator Boundary Pilot 2 is acceptable as the checklist application for the
Governance Registry validator.

```text
Validator: control-plane/registry/validate-governance-registry.py
Fixture tests: cases=11 failures=0
Governance registry: objects=18 pass=18 warn=0 fail=0
```

## Fixed

- CLI target preflight now happens before target resolution and YAML loading.
- Raw and resolved target paths are both checked for protected path markers.
- Symlink targets are judged by their resolved destination.
- Symlink loops return structured findings instead of crashing.
- Function-level target validation and CLI entry behavior are both covered by
  fixtures.
- `test-governance-registry-validator.py` is now registered as a local document
  object.

## Remaining Risks

- Governance Registry object `path` fields are still treated as metadata, not as
  files to open. This is intentional for this validator.
- The three registry validators now share the same boundary pattern, but the
  helper code is still duplicated.

## Recommendation

Next step should be a small refactor proposal for a shared local path-boundary
helper, only after one more review confirms the duplicated behavior is stable.
