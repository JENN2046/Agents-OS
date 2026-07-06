# Review: Validator Path Boundary Helper Refactor

Date: 2026-07-01
Status: reviewed
Scope: implementation review for shared path-boundary helper

## Result

Accepted for the local registry validators.

The helper is small and stays inside the proposed boundary. It owns only:

- `safe_resolve`
- `is_protected_path`
- `is_under_workspace`
- `preflight_target`

Each validator still owns its own:

- result schema
- domain rule ids
- YAML loading
- `invalid_target_result`
- object/document/registry validation rules
- CLI text formatting

## Migration Order

The migration followed the proposal order:

1. `validate-governance-registry.py`
2. `validate-document-registry.py`
3. `validate-federated-document-registry.py`

This kept the smallest read surface first and validated each step before moving
to the next validator.

The validators also keep a small local import guard so `path_boundary.py` can be
resolved when a validator is loaded through `importlib` from a different working
directory.

## Evidence

```text
governance validator tests: cases=12 failures=0
document validator tests: cases=24 failures=0
federated validator tests: cases=21 failures=0

governance registry example: objects=18 pass=18 warn=0 fail=0
document registry example: documents=32 pass=32 warn=0 fail=0
federated registry example: registries=3 pass=3 warn=0 fail=0
```

## Remaining Risk

- A future helper bug could affect all three validators. Keep path-boundary
  fixtures in the individual validator test files.
- Do not move domain validation or result formatting into the helper.
- Any future helper expansion should get a separate review.
