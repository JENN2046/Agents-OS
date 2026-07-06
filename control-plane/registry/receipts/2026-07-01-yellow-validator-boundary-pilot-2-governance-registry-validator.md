# Receipt: Validator Boundary Pilot 2 - Governance Registry Validator

Date: 2026-07-01
Status: completed
Scope: checklist-driven hardening of `validate-governance-registry.py`
Zone: yellow

## What Changed

- Applied `VALIDATOR_BOUNDARY_REVIEW_CHECKLIST.md` to the Governance Registry
  validator.
- Added safe target resolution so symlink loops become structured `SC-TARGET`
  findings instead of tracebacks.
- Added raw and resolved target protected-path checks.
- Stopped resolving CLI target before preflight.
- Added invalid-target structured output with `target_read_performed: false`.
- Expanded governance validator fixtures from 3 to 11 cases.
- Added fixtures for malformed root, protected target, outside target,
  symlink to outside workspace, symlink to protected path, symlink loop, CLI
  outside target, and CLI symlink loop target.
- Registered `test-governance-registry-validator.py` as a local document object.
- Updated Governance Registry evidence for `governance-registry-scorecard-validator`.

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
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
cases=11 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py control-plane/registry/drafts/agents-os-governance-registry.v0.1.example.yaml
Status: PASS
Summary: objects=18 pass=18 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py /etc/hosts --json
Status: expected failure
SC-TARGET: target points outside workspace
target_read_performed: false
```

## Result

The Governance Registry validator now follows the same target-read boundary
model as the Document Registry and Federated Document Registry validators.
