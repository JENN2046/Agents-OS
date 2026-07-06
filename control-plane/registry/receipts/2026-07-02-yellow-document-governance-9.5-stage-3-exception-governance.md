# Receipt: Document Governance 9.5 Stage 3 Exception Governance

Date: 2026-07-02
Status: completed
Scope: execute Stage 3 of the Document Governance 9.5 plan: make
`known_external_scope` and `archive_note` entries reviewable so they cannot hide
ordinary backlog.

## Progress

- Added required metadata validation for `known_external_scope` entries:
  `reason` and `review_trigger`.
- Added required metadata validation for `archive_notes` entries: `safe_use`,
  `review_trigger`, and either `replacement` or `no_replacement_reason`.
- Added protected path validation for exception entries.
- Added a guard preventing already registered document paths from being hidden
  as `known_external_scope`.
- Backfilled metadata in the federated document registry example.
- Added review-trigger language to the grouped historical archive note.
- Expanded federated validator fixtures from 21 to 27 cases.

## Boundary

This work did not expand `known_external_scope` automatically, promote archived
files to active documents, bulk move historical material, start ColaMeta service,
run executor workflows, call providers, modify auth/token/cookie/session state,
modify provider/runtime configuration, modify `.colameta/memory.md`, modify
`WORKSPACE_REGISTRY.yaml`, read `state-private/`, write formal AGENTS OS Memory
content, perform external writes, commit, push, tag, deploy, release, publish,
or perform bulk move/delete/rename.

## Validation

```text
validate-federated-document-registry PASS checked_registries=3 pass=3 warn=0 fail=0
test-federated-document-registry-validator PASS cases=27 failures=0
validate-document-registry PASS checked_documents=90 pass=90 warn=0 fail=0
test-document-registry-validator PASS cases=29 failures=0
test-docctl-doctor PASS cases=8 failures=0
docctl doctor PASS registries=3 documents=132 scanned_files=179 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
ColaMeta PlanLoader/Linter PASS loader_valid=True versions=7 lint_status=passed blocking=0 warnings=0
.colameta/memory.md bytes=0
```
