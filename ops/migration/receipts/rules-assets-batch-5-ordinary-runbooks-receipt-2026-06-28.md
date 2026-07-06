# Batch 5 Receipt: Ordinary Runbooks

Status: completed local ordinary-runbooks patch.

Execution date: 2026-06-28.

Notice: This receipt records an authorized Batch 5 local runbook patch. It is
not a general migration authorization, not authorization to run any runbook
command, not authorization for upstream sync, not authorization to create
registry authority files, not authorization to activate agents or extensions,
and not authorization for remote, branch, push, release, deploy, secret,
private-state, log, cache, or runtime actions.

## Authorization Wording

User requested:

```text
授权执行 Batch 5 补丁：创建 4 个 ordinary runbooks 目标文件，并补 Batch 5 receipt。
```

## Source Files Read

| Source file | SHA-256 | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\README.AGENTS_OS.md` | `a0bdb42e3533986cbd421cb3f84f0d7ac80d35da6e38a202ef35cda6f75d03c7` | Adapted as target-native ordinary runbook index. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\add-new-extension.md` | `6260bdc6d2853d658ddd52f9636abc287c9331dce2280fbbda5f25530d34ae7d` | Adapted as ordinary extension drafting guidance. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\onboard-new-agent.md` | `7e23e163b49b5f5995622c65327eefcfe726dfd8dc4697b5970a6a4c2860b3eb` | Adapted as ordinary agent onboarding planning guidance. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\run-codex-task.md` | `7cee543f9f89d447f661fc11be7f780bbbecef92adefc2a4a6c31fecca161bad` | Adapted as audit-first Codex task guidance. |

All four included source hashes matched the Batch 5 patch plan immediately
before target creation.

## Source Files Skipped

| Skipped source or named file | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\upstream-sync-vcptoolbox.md` | Remote/sync-sensitive; reserved for a separate restricted maintenance-reference batch. |
| `approve-protected-action.md` | Named in source README but not observed as a source file; no placeholder created. |
| `handle-failed-action.md` | Named in source README but not observed as a source file; no placeholder created. |

## Target Directory Created

| Target directory | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/` | Created for ordinary audit-first runbooks. |

## Target Files Created

| Target file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/README.md` | Created as ordinary runbook index; excludes upstream sync and unobserved placeholder runbooks. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/add-new-extension.md` | Created as extension drafting guidance; registry registration deferred. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/onboard-new-agent.md` | Created as agent onboarding planning guidance; agent-pack placement deferred. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/run-codex-task.md` | Created as audit-first Codex task guidance; keeps risky actions forbidden by default. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-5-ordinary-runbooks-receipt-2026-06-28.md` | Created as receipt for this local patch. |

## Path Rewrites And Deferred Markings

| Topic | Result |
| --- | --- |
| Registry registration | Target says registry registration is pending the separately authorized migration of `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| Historical registry path | Target says not to write to `AGENTS_OS/registry/extensions.yaml`. |
| Registry examples | Target says `control-plane/registry/examples/extensions.example.yaml` is example-only and not active registry state. |
| Agent-pack placement | Target says agent-pack placement is pending a separate extension-assets migration decision. |
| Historical agent-pack path | Target says `extensions/Jenn-VCP-Extensions/agent-packs/` is not current WSL truth. |
| Observed WSL extension root | Target says `extensions/vcp-toolbox-jenn/` is not a final agent-pack target in this batch. |
| Validation scripts | Target says validation script migration is pending and does not instruct users to run old or absent validator paths as existing commands. |
| Private state | Target mentions `state-private/` only as a boundary and does not authorize copying or reading private state. |

## Validation Run

| Check | Result |
| --- | --- |
| Pre-existing target check | Four ordinary target files and this receipt were absent before creation. |
| Source hash check | Four included ordinary runbook source hashes matched the Batch 5 patch plan. |
| Target file list check | `control-plane/runbooks/` contains exactly `README.md`, `add-new-extension.md`, `onboard-new-agent.md`, and `run-codex-task.md`. |
| Excluded maintenance target check | `ops/maintenance/runbooks/upstream-sync-vcptoolbox.md` was not created. |
| Unobserved placeholder check | `control-plane/runbooks/approve-protected-action.md` and `control-plane/runbooks/handle-failed-action.md` were not created. |
| Live-secret pattern scan | No live-secret patterns were found in the four target runbooks. |
| Remote/sync command scan | No executable remote/sync command lines were found in the four target runbooks. |
| Closed wording rules check | Registry, agent-pack, and validation-script wording follows the closed Batch 5 rules. |
| Non-authorization wording check | All four target runbooks explicitly state they are guidance, not authorization to execute or activate risky work. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Source or migrated validator scripts | Batch 5 plan says not to run scripts in this batch. |
| Runbook execution | Runbooks are guidance documents; this migration does not authorize executing procedures. |
| Registry migration or validation | `control-plane/registry/WORKSPACE_REGISTRY.yaml` is outside this batch and remains separately pending. |
| Extension-assets placement validation | Agent-pack and extension package placement is outside this batch and remains separately pending. |
| Repository-level `git diff` or `git status` validation | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Registry registration remains pending. | Target runbook explicitly defers registry registration until `control-plane/registry/WORKSPACE_REGISTRY.yaml` is separately migrated and authorized. |
| Agent-pack target remains pending. | Target runbook explicitly defers placement to a separate extension-assets migration decision. |
| Validation scripts remain pending. | Target README and extension runbook state script migration is pending and do not present absent scripts as runnable. |
| Future readers could confuse guidance with authorization. | Target runbooks and this receipt state that risky actions require separate explicit authorization and receipt. |
| Workspace root has no Git diff surface. | Validation relied on file existence checks, source hashes, direct content checks, and pattern scans. |

## Rollback Path

If this Batch 5 ordinary-runbooks patch must be rolled back, remove only the
files created by this receipt after confirming no later user work depends on
them:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/add-new-extension.md
/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/onboard-new-agent.md
/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/run-codex-task.md
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-5-ordinary-runbooks-receipt-2026-06-28.md
```

Remove `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/` only if it is
empty after those files are removed.

Do not remove `control-plane/`, `governance/`, `ops/maintenance/`,
`control-plane/registry/`, existing templates, existing registry examples, or
any source files under `A:\AGENTS_OS_Workspace`.
