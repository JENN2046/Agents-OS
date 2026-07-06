# Receipt: Document Governance 9.5 Plan

Date: 2026-07-01
Status: completed
Scope: output the draft plan for improving AGENTS OS document governance from
the current 8/10 skeleton toward a 9.5/10 system.

## Progress

- Created the draft 9.5 plan document.
- Preserved the conclusion from the debate team: do not build score first;
  harden schema/lifecycle first.
- Kept the plan as draft, not active authority data.
- Did not modify `WORKSPACE_REGISTRY.yaml`.
- Did not add runtime/provider/external write behavior.

## Follow-up Progress

- Split the 9.5 target into a long-term vision target and a current
  implementation target.
- Aligned the lifecycle plan with the current registry statuses.
- Replaced `active template` with `doc_type=template` plus `status=active`.
- Added a migration rule so stricter fields do not break the clean baseline
  before backfill and review.
- Split warning treatment into `blocking_warn` and `advisory_warn`.
- Added rules for `ignored_by_rule` and `future_backlog` so they cannot become
  hiding places for ordinary backlog.
- Added a full implementation plan pack for Stage 0 through Stage 6, including
  purpose, inputs, steps, deliverables, validation, and done conditions.
- Kept `apply-fix` deferred and limited any future write-capable repair tool to
  a separately confirmed local write scope.

## Validation

```text
validate-document-registry PASS checked_documents=63 pass=63 warn=0 fail=0
validate-federated-document-registry PASS checked_registries=3 pass=3 warn=0 fail=0
test-federated-document-registry-validator PASS cases=21 failures=0
test-docctl-doctor PASS cases=8 failures=0
docctl doctor PASS registries=3 documents=105 scanned_files=152 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

The plan document, this receipt, and the paired review were registered in the
draft document registry so the baseline remains honest: no new unregistered
document backlog was introduced.

## Boundary

This work does not authorize external writes, runtime/provider calls, formal
Memory registration, protected-path reads, bulk moves/deletes, automatic
registry repair, or active authority changes.
