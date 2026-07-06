# Receipt: Validator Boundary Pilot 1 - Document Registry Validator

Date: 2026-07-01
Status: completed
Scope: checklist-driven hardening of `validate-document-registry.py`
Zone: yellow

## What Changed

- Applied `VALIDATOR_BOUNDARY_REVIEW_CHECKLIST.md` to the Document Registry
  validator.
- Added safe path resolution so symlink loops become structured `DOC-*`
  findings instead of tracebacks.
- Added resolved-path protected checks for `canonical_path`, `source_of_truth`,
  `related`, and CLI targets.
- Stopped resolving CLI target before preflight.
- Expanded document validator fixtures from 14 to 23 cases.
- Added fixtures for symlink to outside workspace, symlink to protected path,
  symlink loop, CLI outside target, CLI symlink loop target, and malformed
  registry root.
- Registered `test-document-registry-validator.py` as a local document object.

## Boundaries Held

- Did not modify `control-plane/registry/WORKSPACE_REGISTRY.yaml`.
- Did not read `state-private/`.
- Did not scan the full workspace.
- Did not create a database, search index, vector index, or full-workspace
  document map.
- Did not write external systems.
- Did not touch runtime, provider config, or formal Memory.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
cases=23 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
Status: PASS
Summary: documents=24 pass=24 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py /etc/hosts --json
Status: expected failure
DOC-TARGET: target points outside workspace
target_read_performed: false
```

## Result

The Document Registry validator now follows the same core boundary model as the
Federated Document Registry validator:

```text
raw path check
safe resolve
resolved path protected check
workspace boundary check
structured failure before read
CLI fixture coverage
```
