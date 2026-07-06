# Phase 2 Batch 5 Ordinary Runbooks Patch Plan - 2026-06-28

Status: patch plan only; no migration performed.

Notice: This document plans the ordinary-runbooks patch. It is not migration
authorization, not authorization to copy files yet, not authorization to run any
runbook command, and not authorization for remote, sync, branch, push, release,
or deploy actions.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 5 |
| Batch name | Ordinary runbooks |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source directory | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks` |
| Target directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/` |
| Included asset type | Ordinary audit-first procedure runbooks |
| Excluded asset types | Upstream/sync maintenance runbooks, scripts, prompts, templates, active config, registry authority files, private state, logs, cache, runtime artifacts |
| Migration performed | No |
| Validation executed | Plan-only source and target checks |

## Source Evidence

| Source file | Size | SHA-256 | Batch handling |
| --- | ---: | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\README.AGENTS_OS.md` | 918 bytes | `a0bdb42e3533986cbd421cb3f84f0d7ac80d35da6e38a202ef35cda6f75d03c7` | Include as target-native runbook index. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\add-new-extension.md` | 511 bytes | `6260bdc6d2853d658ddd52f9636abc287c9331dce2280fbbda5f25530d34ae7d` | Include after stale registry/config wording is rewritten. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\onboard-new-agent.md` | 426 bytes | `7e23e163b49b5f5995622c65327eefcfe726dfd8dc4697b5970a6a4c2860b3eb` | Include after extension path wording is marked unverified or deferred. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\run-codex-task.md` | 362 bytes | `7cee543f9f89d447f661fc11be7f780bbbecef92adefc2a4a6c31fecca161bad` | Include after governance/Codex wording is aligned to current decisions. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\upstream-sync-vcptoolbox.md` | 904 bytes | `50144833eae8f94ce671af4cbb91d715abe0c3be3c8563bc6512c4daf7f799e8` | Exclude from ordinary batch; reserve for restricted maintenance reference. |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/` | Target home for ordinary audit-first procedure runbooks. |

Do not create `ops/maintenance/runbooks/` in this batch.

## Planned File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/README.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\README.AGENTS_OS.md` | Rewrite/adapt as the target-native ordinary runbooks index. List only observed ordinary runbooks as present. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/add-new-extension.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\add-new-extension.md` | Rewrite/adapt as ordinary guidance. Keep audit-first defaults and mark registry/config references safely. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/onboard-new-agent.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\onboard-new-agent.md` | Rewrite/adapt as ordinary guidance. Preserve private-state boundary and avoid asserting old extension paths as current. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/run-codex-task.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\run-codex-task.md` | Rewrite/adapt as audit-first Codex task guidance. Keep it procedural, not authorization. |

No existing target file is planned to be modified in this batch.

## Explicitly Skipped Files

| Skipped source or target | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\upstream-sync-vcptoolbox.md` | Contains remote, branch, fetch, pull, checkout, merge, validation, and push-authorization language; keep out of ordinary runbooks. |
| `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/runbooks/upstream-sync-vcptoolbox.md` | Restricted maintenance reference target; not created in this ordinary batch. |
| `approve-protected-action.md` | Named in source README but not observed as a source file; do not create a placeholder. |
| `handle-failed-action.md` | Named in source README but not observed as a source file; do not create a placeholder. |
| `ops/validation/validate-no-secrets.sh` | Validation script target is not migrated yet; do not create or run it in this batch. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Canonical registry target is decided but absent; do not create registry authority in this runbook batch. |
| Active config, private state, logs, cache, runtime output | Outside ordinary-runbook scope. |

## Required Rewrites And Alignment

| Topic | Target handling | Reason |
| --- | --- | --- |
| Source README filename | Rename/adapt `README.AGENTS_OS.md` to `README.md`. | Target directories use local `README.md` naming. |
| Source README file list | Remove or mark `approve-protected-action.md` and `handle-failed-action.md` as not present. | They were named in README but not observed in source inventory. |
| Upstream sync | Do not list `upstream-sync-vcptoolbox.md` as an ordinary runbook. | It is remote/sync-sensitive and reserved for a later restricted maintenance batch. |
| Validation script reference | Replace `../../ops/scripts/validate-no-secrets.sh` with a note that validation scripts are pending separate migration. | `ops/validation/validate-no-secrets.sh` is not present in WSL and scripts are out of scope. |
| Registry path | Rewrite source registration wording as: registry registration is pending the separately authorized migration of `control-plane/registry/WORKSPACE_REGISTRY.yaml`; `AGENTS_OS/registry/extensions.yaml` is historical source wording, and `control-plane/registry/examples/extensions.example.yaml` is example-only. | The old path is stale, the canonical registry file is decided but not migrated yet, and examples must not become active registry state. |
| Config examples | Point to example/template-only posture; do not authorize `config.env` or active `.env` files. | Matches Batch 3 env-template and governance boundaries. |
| Extension agent-pack path | Rewrite source placement wording as: agent-pack placement is pending a separate extension-assets migration decision; `extensions/Jenn-VCP-Extensions/agent-packs/` is historical source wording, and the observed WSL extension root `extensions/vcp-toolbox-jenn/` is not a final agent-pack target. | WSL currently has `extensions/vcp-toolbox-jenn/`, but exact extension package and agent-pack placement remains separate. |
| Private state | Preserve `state-private/` as the private-state boundary, with no copying or reading of private state. | Matches governance security boundaries. |
| Codex task flow | Keep audit-first wording and align with governance/Codex routing decisions without granting execution authority. | A runbook is guidance, not approval to act. |
| Forbidden defaults | Preserve no push, no release, no deploy, no secret reading, no destructive delete, and no main-branch modification by default. | Matches source runbooks and governance security boundaries. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source ordinary files exist | Check the four included source files under `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks`. | All four source files exist and sizes/hashes are recorded. |
| Reconfirm skipped sync file exists but remains skipped | Check `upstream-sync-vcptoolbox.md`. | File is observed but not included in ordinary target list. |
| Reconfirm target files are absent | Check the four planned files under `control-plane/runbooks/`. | None of the four target files exists before patch. |
| Reconfirm target directory state | Check `control-plane/runbooks/`. | Directory is absent or contains no conflicting target files before patch. |
| Reconfirm duplicate maintenance target absent | Check `ops/maintenance/runbooks/upstream-sync-vcptoolbox.md`. | Restricted maintenance file is not created by this batch. |
| Reconfirm authority surfaces | Check `governance/SECURITY_BOUNDARIES.md` and `control-plane/registry/WORKSPACE_REGISTRY.yaml`. | Security authority exists; registry authority absence is recorded and not papered over. |
| Stale path scan | Search target drafts for `AGENTS_OS/registry`, `Jenn-VCP-Extensions/agent-packs`, and old validation script paths. | Old paths are removed, marked historical, or explicitly not yet verified. |
| Remote/sync command scan | Search target drafts for `git fetch`, `git pull`, `git checkout`, `git merge`, `git push`, `release`, and `deploy`. | Ordinary runbooks do not contain remote/sync recipes; forbidden defaults may mention push/release/deploy only as blocked actions. |
| Live-secret pattern scan | Scan source and target drafts. | No real secret, token, credential, password, private endpoint, or private account value is present. |
| Private-state scan | Search target drafts for private-state copying or reading instructions. | Private state is referenced only as a boundary, never as content to copy/read. |

## Planned Content Rules

- Target files must live under `control-plane/runbooks/`.
- Target files must state or preserve that ordinary runbooks are audit-first
  guidance.
- Target files must not authorize push, pull, fetch, merge, release, deploy,
  branch movement, destructive delete, secret reading, or remote writes.
- Target files must not run or require running any script during migration.
- Target files must not make `control-plane/registry/WORKSPACE_REGISTRY.yaml`
  appear already migrated.
- Target files must not create placeholders for unobserved runbooks.
- Target files must not copy private state, logs, cache, runtime output, or
  extension package material.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file existence check | Confirm the four planned files exist under `control-plane/runbooks/`. | No extra runbooks should be created. |
| Excluded file absence check | Confirm `ops/maintenance/runbooks/upstream-sync-vcptoolbox.md` is still absent. | Maintenance/sync runbook remains deferred. |
| Unobserved placeholder absence check | Confirm `approve-protected-action.md` and `handle-failed-action.md` were not created. | README names alone are not source evidence. |
| Stale path check | Search `control-plane/runbooks/` for old source paths. | Stale paths must be removed or marked historical/unverified. |
| Remote/sync command check | Search ordinary target runbooks for remote or branch commands. | No remote/sync recipe should enter ordinary runbooks. |
| Governance alignment check | Confirm target runbooks reference governance/security boundaries without replacing them. | `governance/SECURITY_BOUNDARIES.md` remains authority. |
| Live-secret pattern scan | Scan target runbooks and receipt. | No live-secret pattern should be present. |
| Diff or content review | Inspect created files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated validator scripts in this batch.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-5-ordinary-runbooks-receipt-2026-06-28.md
```

The receipt should record:

- Exact authorization wording.
- Source files read.
- Source files skipped.
- Target directory created.
- Target files created.
- Path rewrites and deferred-path markings.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If the ordinary-runbooks patch is later applied and must be rolled back, remove
only the files created by that patch after confirming no later user work depends
on them:

```text
control-plane/runbooks/README.md
control-plane/runbooks/add-new-extension.md
control-plane/runbooks/onboard-new-agent.md
control-plane/runbooks/run-codex-task.md
ops/migration/receipts/rules-assets-batch-5-ordinary-runbooks-receipt-2026-06-28.md
```

Remove `control-plane/runbooks/` only if it is empty after those files are
removed. Do not remove `control-plane/`, `governance/`, `ops/maintenance/`, or
any source files under `A:\AGENTS_OS_Workspace`.

## Closed Wording Rules Before Authorization

| Item | Closed rule |
| --- | --- |
| Registry registration wording | Target runbooks must say: "Registry registration is pending the separately authorized migration of `control-plane/registry/WORKSPACE_REGISTRY.yaml`." They must not instruct users to write to `AGENTS_OS/registry/extensions.yaml`, must not say `control-plane/registry/WORKSPACE_REGISTRY.yaml` already exists, and may mention `control-plane/registry/examples/extensions.example.yaml` only as example-only reference material. |
| Agent-pack placement wording | Target runbooks must say: "Agent-pack placement is pending a separate extension-assets migration decision." They must not present `extensions/Jenn-VCP-Extensions/agent-packs/` as current WSL truth, and must not convert the observed `extensions/vcp-toolbox-jenn/` directory into a final agent-pack target in this batch. |
| Validation script wording | Target runbooks must say validation script migration is pending. They must not instruct users to run `../../ops/scripts/validate-no-secrets.sh` or `ops/validation/validate-no-secrets.sh` as an existing command in this batch. |

## Related Documents

- `../decisions/runbooks-targets-2026-06-27.md`
- `../plans/phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/source-path-reconciliation-2026-06-27.md`
