# Review: Validator Boundary Pilot 1 - Document Registry Validator

Date: 2026-07-01
Status: reviewed
Scope: checklist-driven hardening of `validate-document-registry.py`

## Review Result

Validator Boundary Pilot 1 is acceptable as the first application of
`VALIDATOR_BOUNDARY_REVIEW_CHECKLIST.md` to an existing validator.

```text
Validator: control-plane/registry/validate-document-registry.py
Fixture tests: cases=23 failures=0
Document registry: documents=24 pass=24 warn=0 fail=0
```

## Fixed

- CLI target preflight now happens before target resolution and YAML loading.
- Raw and resolved paths are both checked for protected path markers.
- Symlink paths are judged by their resolved destination.
- Symlink loops return structured findings instead of crashing.
- Function-level path validation and CLI entry behavior are both covered by
  fixtures.
- `test-document-registry-validator.py` is now registered as a local document
  object.

## Remaining Risks

- Governance Registry validator has not yet been run through the checklist.
- Document Registry validator still reads safe listed document files to check
  secret-like markers; this is expected behavior, but it must stay limited to
  listed paths.

## Recommendation

Run Validator Boundary Pilot 2 on `validate-governance-registry.py` next. It
has a smaller read surface, so it should mainly need target preflight, safe
resolve, CLI fixture, and evidence synchronization.
