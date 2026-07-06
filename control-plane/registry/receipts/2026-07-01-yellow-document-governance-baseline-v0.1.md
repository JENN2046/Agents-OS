# Receipt: Document Governance Baseline v0.1

Date: 2026-07-01
Status: completed
Scope: establish the first clean document-governance baseline after registry,
known external-scope, and grouped archive cleanup.

## Progress

- Recorded the current clean `docctl doctor` state as Document Governance
  Baseline v0.1.
- Updated the registry README with the baseline and document intake routing.
- Added Golden Path route 7 for document-governance closeout.
- Registered this receipt and the paired baseline review.
- Did not modify `WORKSPACE_REGISTRY.yaml`.
- Did not move, delete, rewrite, or promote archived historical files.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PASS documents=60 pass=60 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PASS registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
PASS cases=21 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
PASS cases=8 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PASS registries=3 documents=102 scanned_files=149 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

This count includes the baseline receipt and review themselves, which are
registered to keep `unregistered=0`.

## Boundary

This work does not authorize external writes, runtime/provider calls, formal
Memory registration, protected-path reads, bulk moves/deletes, or active
authority changes.
