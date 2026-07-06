# Review: Document Governance Baseline v0.1

Date: 2026-07-01
Status: reviewed
Scope: baseline review for the local AGENTS OS document-governance control
plane.

## Baseline Snapshot

Target:

```text
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Expected healthy state:

```text
registries=3
documents=102
scanned_files=149
known_external_scope=1
archived=50
unregistered=0
warn=0
fail=0
```

Registry split:

```text
registry-document-registry: documents=60, archived=25, known_external_scope=1
task-envelope-document-registry: documents=12, archived=9
life-core-document-registry: documents=30, archived=16
```

The baseline count includes this baseline receipt and review because evidence
files are also governed local documents.

## Intake Rule

Every new or changed document-governance file should end in one of four states:

```text
current effective document -> registered in its directory Document Registry
draft/template/example -> registered with explicit non-active authority wording
known externally governed file -> known_external_scope
historical material -> archive note
```

The closeout check is:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

The clean target is:

```text
unregistered=0
warn=0
fail=0
```

## Boundary

This baseline does not make draft/example registry files active authority. It
does not authorize external writes, runtime/provider calls, formal Memory
registration, protected-path reads, bulk moves/deletes, or changes to
`WORKSPACE_REGISTRY.yaml`.

## Review Result

No blocking issue found.

Validation result:

```text
registry document registry: PASS documents=60 pass=60 warn=0 fail=0
federated document registry: PASS registries=3 pass=3 warn=0 fail=0
federated validator fixtures: PASS cases=21 failures=0
docctl doctor tests: PASS cases=8 failures=0
docctl doctor: PASS registries=3 documents=102 scanned_files=149 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```
