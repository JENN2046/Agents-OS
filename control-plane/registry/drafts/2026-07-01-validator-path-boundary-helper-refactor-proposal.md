# Validator Path Boundary Helper Refactor Proposal v0.1

Date: 2026-07-01
Status: draft_proposal
Scope: local AGENTS OS registry validators

This proposal is not active authority. It does not change validator behavior,
grant permission, read protected paths, write external systems, run providers,
or register formal Memory.

## Purpose

The three registry validators now repeat the same path-boundary pattern:

- `safe_resolve`
- `is_protected_path`
- `is_under_workspace`
- `preflight_target`

This proposal defines a small future refactor that may move only that shared
path-boundary logic into one local helper.

## Proposed Helper Boundary

Possible file:

```text
control-plane/registry/path_boundary.py
```

Allowed helper responsibilities:

- resolve a path without crashing on symlink loops
- detect raw protected path text such as `state-private/`, `.env`, `secrets/`,
  `credentials/`, `tokens/`, and `cookies/`
- detect resolved protected destinations
- check whether a resolved path stays under the AGENTS OS workspace root
- preflight a CLI target before any validator reads YAML
- return plain structured findings using the rule id provided by the caller

The helper may accept caller-owned inputs such as:

```text
target: Path
workspace_root: Path
rule_id: str
protected_parts: set[str]
```

## Must Stay Local To Each Validator

The helper must not own domain behavior.

These stay inside each validator:

- result schema and output shape
- `invalid_target_result`
- summary counters
- YAML loading
- document / registry / governance object rules
- domain rule ids beyond the caller-provided target rule id
- field-level path rules such as `DOC-017` or `FDR-003`
- secret-like metadata scanning
- child validator behavior
- CLI text formatting

## Implementation Order

If Jenn confirms implementation later:

1. Add `path_boundary.py` with copied behavior only.
2. Move one validator to the helper first, preferably Governance Registry
   because its path read surface is smallest.
3. Run that validator's fixture tests.
4. Move Document Registry and Federated Document Registry one at a time.
5. Run all three validator test suites after each move.
6. Update the baseline review or write a new review recording behavior parity.

## Required Validation

The refactor is acceptable only if all current cases still pass:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
```

Expected baseline at proposal time:

```text
document registry tests: cases=24 failures=0
federated registry tests: cases=21 failures=0
governance registry tests: cases=12 failures=0
```

## Risk Control

Main risk:

- a helper bug could affect all three validators at once

Mitigation:

- keep the helper small
- do not move domain logic into the helper
- migrate one validator at a time
- keep protected target, outside target, protected symlink, outside symlink, and
  symlink-loop fixtures in the validator test files
- do not delete old local logic until behavior parity is proven by tests

## Draft Decision

Recommended next action:

```text
Do not implement yet by default.
Keep this as a small refactor proposal.
Implement only after Jenn confirms this specific helper boundary.
```
