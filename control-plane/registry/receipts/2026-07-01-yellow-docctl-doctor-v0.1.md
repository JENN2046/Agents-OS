# Receipt: docctl doctor v0.1

Date: 2026-07-01
Status: completed
Scope: read-only local doctor for document governance

## Completed

- Added `control-plane/registry/docctl.py`.
- Added `control-plane/registry/test-docctl-doctor.py`.
- Implemented `docctl doctor` as a read-only scan over explicitly listed
  Federated Document Registry entries.
- Covered unregistered source warnings, count mismatch failure, missing
  review-reference failure, and protected-path failure with local fixtures.

## Boundary

`docctl doctor` does not:

- modify registry files
- create databases, search indexes, or vector indexes
- scan the full workspace
- read protected paths
- execute arbitrary registry `validation.commands`
- write external systems
- call providers
- register formal Memory

It does run the existing local document registry validators as read-only
subprocesses.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
cases=4 failures=0

PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
Status: PASS
Summary: registries=3 documents=77 scanned_files=139 unregistered=66 warn=66 fail=0
```

The `warn=66` result is existing backlog surfaced by the doctor, not a hard
validator failure.
