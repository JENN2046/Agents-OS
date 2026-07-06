# Receipt: Document Governance 9.5 Stage 5 docctl score

Date: 2026-07-02
Status: completed
Scope: execute Stage 5 of the Document Governance 9.5 plan: add a versioned
read-only document-governance score after schema, lifecycle, intake, exception,
and impact rules are stable.

## Progress

- Added `docctl.py score` as a read-only score view over `docctl doctor`.
- Added JSON output for score.
- Added hard gates for `unregistered_files > 0`, doctor failures, and blocking
  warnings.
- Separated `blocking_warn` and `advisory_warn`.
- Added explainable deductions.
- Added fixtures for current clean score, unregistered hard gate, count mismatch
  hard gate, protected target failure, and score CLI JSON output.
- Documented score usage and hard gates in `SCORECARD.md` and the registry
  README.

## Boundary

This work did not write score results to registry files, hide hard gate
failures, start ColaMeta service, run executor workflows, call providers, modify
auth/token/cookie/session state, modify provider/runtime configuration, modify
`.colameta/memory.md`, modify `WORKSPACE_REGISTRY.yaml`, read `state-private/`,
write formal AGENTS OS Memory content, perform external writes, commit, push,
tag, deploy, release, publish, or perform bulk move/delete/rename.

## Validation

```text
test-docctl-score PASS cases=5 failures=0
docctl score PASS score=100 eligible_95=True blocking_warn=0 advisory_warn=0 hard_gates=0
validate-document-registry PASS checked_documents=96 pass=96 warn=0 fail=0
validate-federated-document-registry PASS checked_registries=3 pass=3 warn=0 fail=0
test-docctl-impact PASS cases=7 failures=0
test-docctl-intake PASS cases=10 failures=0
test-docctl-doctor PASS cases=8 failures=0
docctl doctor PASS registries=3 documents=138 scanned_files=185 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
ColaMeta PlanLoader/Linter PASS loader_valid=True versions=7 lint_status=passed blocking=0 warnings=0
.colameta/memory.md bytes=0
```
