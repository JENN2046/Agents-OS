# Receipt: docctl known_external_scope

Date: 2026-07-01
Status: completed
Scope: add a small `known_external_scope` capability to `docctl doctor` and
mark `control-plane/registry/WORKSPACE_REGISTRY.yaml` as handled outside the
draft Document Registry.

## Progress

- Added `known_external_scope` handling to `docctl doctor`.
- Marked `control-plane/registry/WORKSPACE_REGISTRY.yaml` as known external
  scope in the federated document registry example.
- Added fixture coverage for normal known scope and protected known scope.
- Kept `WORKSPACE_REGISTRY.yaml` unchanged.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
PASS cases=6 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PASS documents=55 pass=55 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PASS registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
PASS cases=21 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PASS registries=3 documents=97 scanned_files=144 known_external_scope=1 unregistered=50 warn=50 fail=0
```

`control-plane/registry/WORKSPACE_REGISTRY.yaml` is now reported as known
external scope instead of unregistered backlog. The remaining 50 warnings are
the historical archive/evidence backlog already classified for grouped archive
handling.

## Boundary

This work does not authorize external writes, runtime/provider calls, formal
Memory registration, protected-path reads, or active authority changes.
