# Receipt: docctl doctor Should-Register Backlog

Date: 2026-07-01
Status: completed
Scope: register the 15 current `should_register` files from the `docctl doctor`
backlog classification and keep this cleanup evidence registered.

## Progress

- Registered 14 current source/template/example files in the registry directory
  document registry.
- Registered 1 task-envelope document registry example in the task-envelope
  document registry.
- Registered this receipt and its paired review so the cleanup does not create
  fresh unregistered evidence files.
- Updated the federated expected document counts for the changed registries.
- Did not modify `WORKSPACE_REGISTRY.yaml`.
- Did not move, delete, or reclassify historical archive files.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PASS documents=53 pass=53 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/task-envelope/drafts/document-registry.v0.1.example.yaml
PASS documents=12 pass=12 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PASS registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
PASS cases=21 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PASS registries=3 documents=95 scanned_files=142 unregistered=51 warn=51 fail=0
```

The remaining 51 unregistered files match the known backlog shape: one active
authority registry file intentionally left out of this cleanup and 50 historical
archive/evidence files awaiting grouped archive handling.

## Boundary

This work does not authorize external writes, runtime/provider calls, formal
Memory registration, protected-path reads, or active authority changes.
