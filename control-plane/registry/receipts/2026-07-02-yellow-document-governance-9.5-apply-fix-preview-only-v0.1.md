# Receipt: Document Governance 9.5 apply-fix preview-only v0.1

Date: 2026-07-02
Status: completed
Scope: implement the confirmed read-only `docctl apply-fix --preview` mode for
Document Governance 9.5.

## Progress

- Added `docctl.py apply-fix --preview <proposal-id>` as a read-only preview
  over existing `plan-fix` proposals.
- Added JSON output for `apply-fix --preview`.
- Added a text formatter for quick local inspection.
- Kept preview output explicitly bounded with `write_performed=false`,
  `patch_created=false`, `snapshot_write_performed=false`, and
  `execution_authorized=false`.
- Added fixture tests for current proposal preview, missing proposal id,
  protected target blocking, CLI JSON output, and CLI text output.
- Documented preview-only usage in the registry README and 9.5 plan.

## Boundary

This work did not execute repair writes, create repair patches, write snapshots,
start ColaMeta service, run executor workflows, call providers, modify
auth/token/cookie/session state, modify provider/runtime configuration, modify
`.colameta/plan.json`, modify `.colameta/state.json`, write
`.colameta/memory.md` content, modify `WORKSPACE_REGISTRY.yaml`, read
`state-private/`, read raw logs, write formal AGENTS OS Memory content, perform
external writes, commit, push, tag, deploy, release, publish, or perform bulk
move/delete/rename.

## Validation

```text
test-docctl-apply-fix-preview PASS cases=5 failures=0
validate-document-registry PASS checked_documents=133 pass=133 warn=0 fail=0
validate-federated-document-registry PASS checked_registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=175 scanned_files=222 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl apply-fix --preview PF-0001 PASS preview_status=no_action_needed write_performed=False patch_created=False snapshot_write_performed=False execution_authorized=False registry_write_performed=False
docctl apply-fix --preview PF-0001 --json PASS preview_only=True write_performed=False patch_created=False snapshot_write_performed=False execution_authorized=False provider_call_performed=False
docctl plan-fix PASS plan_status=no_action_needed write_performed=False patch_created=False snapshot_write_performed=False
docctl status PASS score=100 eligible_95=True trend_status=ready snapshots_found=1 plan_status=no_action_needed write_performed=False snapshot_write_performed=False registry_write_performed=False
docctl score PASS score=100 eligible_95=True blocking_warn=0 advisory_warn=0 hard_gates=0
docctl trend PASS trend_status=ready snapshots_found=1 no_regression_from_latest=True unregistered=0 warn=0 fail=0
.colameta/memory.md bytes=0
tmp_docctl_dirs=0
git_status=not_a_git_repository
```
