# Receipt: Grouped Archive Note

Date: 2026-07-01
Status: completed
Scope: create one grouped archive note for the 50 historical document-governance
files reported by `docctl doctor`.

## Progress

- Created a grouped archive note for historical governance drafts, receipts, and
  reviews.
- Added `archive_notes` support to `docctl doctor`.
- Linked the grouped archive note from each federated document registry entry.
- Did not move, delete, rewrite, or promote historical files.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
PASS cases=8 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PASS documents=58 pass=58 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PASS registries=3 pass=3 warn=0 fail=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
PASS cases=21 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PASS registries=3 documents=100 scanned_files=147 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

The 50 historical files are now covered by the grouped archive note:

- registry directory: 25
- task-envelope directory: 9
- life-core directory: 16

## Boundary

This work does not authorize external writes, runtime/provider calls, formal
Memory registration, protected-path reads, bulk moves/deletes, or active
authority changes.
