# Phase 1 Summary And Phase 2 Entry Criteria - 2026-06-27

Status: summary and entry criteria only，非迁移授权。

This document summarizes the Phase 1 rules-asset target decisions and defines
the minimum entry criteria for any later Phase 2 migration patch. It does not
authorize copying, moving, deleting, executing, activating prompts, changing
executable bits, pushing, syncing, merging, or changing source assets.

## Scope

| Item | Value |
| --- | --- |
| Phase summarized | Phase 1 rules-asset target decisions |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Assets covered | Registry/security docs, contracts, registry examples, runbooks, templates, ops scripts, prompts |
| Assets not covered | Runtime repositories, domain systems, memory systems, private state, project source migrations |
| Migration performed | No |
| Validation executed | No |

## Review Issues Closed

| Issue found in review | Closure |
| --- | --- |
| Some decisions used `Migrate as...`, which could be misread as authorization. | Reworded affected handling decisions to `Phase 2 migration candidate...` where needed. |
| `control-plane-assets-targets-2026-06-27.md` had no dedicated Phase 2 stop-conditions section. | Added a `Phase 2 Stop Conditions` section to that document. |
| Phase 0 labels and Phase 1 refined decisions could be misread as conflicting. | This document defines the precedence rule below. |

## Precedence Rule

Use this order during Phase 2 planning:

1. Current user instruction and safety rules.
2. WSL root policy and directory principles.
3. Phase 1 decision documents.
4. Phase 0 inventory labels.

Phase 0 labels are shallow inventory labels. A later Phase 1 decision may
refine them, but it does not authorize migration by itself.

Examples:

| Phase 0 label | Phase 1 refinement | Meaning |
| --- | --- | --- |
| Scripts were mostly `暂缓`. | `validate-no-secrets.sh` and `validate-extension-manifests.sh` became validation candidates. | They may enter a Phase 2 plan only after syntax, path, and output review. |
| Templates included a `.env` name hit. | The env template was placed under `control-plane/templates/env/`. | It remains example-only and must not become active config. |
| Prompts were `需审`. | Only README catalogs were observed. | They may become prompt-library indexes, not active prompts. |

## Phase 1 Target Summary

| Asset group | Phase 1 target decision | Phase 2 posture |
| --- | --- | --- |
| `WORKSPACE_REGISTRY.yaml` | `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Candidate after path normalization and source-path verification. |
| `SECURITY_BOUNDARIES.md` | `governance/SECURITY_BOUNDARIES.md` | Candidate after high-risk path reconciliation. |
| Contract schema | `control-plane/contracts/jenn-extension.manifest.schema.json` | Candidate after JSON parse and secret-name scan. |
| Contract README | `control-plane/contracts/README.md` | Candidate as rewritten target-native README. |
| Registry examples | `control-plane/registry/examples/` | Candidate as example-only files; not active registry state. |
| Registry README | `control-plane/registry/README.md` | Candidate as rewritten target-native README. |
| Ordinary runbooks | `control-plane/runbooks/` | Candidate after stale path and governance wording review. |
| Upstream sync runbook | `ops/maintenance/runbooks/upstream-sync-vcptoolbox.md` | Restricted reference only; no command execution. |
| Ordinary templates | `control-plane/templates/common/` and `control-plane/templates/extensions/` | Candidate after placeholder, path, and schema review. |
| Env example template | `control-plane/templates/env/` | Example-only candidate; never active config. |
| Security template | `control-plane/templates/security/` | Template candidate; must reference, not replace, governance security boundaries. |
| Validation script candidates | `ops/validation/` | Candidate only after syntax, path, and output review; no executable bit by default. |
| Maintenance/sync script | `ops/maintenance/sync-upstream-vcp.sh` | Restricted helper/reference only; no remote action authorization. |
| Draft/deferred scripts | `ops/validation/drafts/` or no active target | Preserve only as drafts or rewrite later. |
| Agent prompt catalogs | `control-plane/prompts/agents/` | Candidate as README/catalog only; no identity activation. |
| Codex prompt catalogs | `control-plane/prompts/codex/` | Candidate as README/catalog only; no behavior authority. |
| Legacy prompt names | `control-plane/prompts/reference/` | Reference only; do not create missing prompt files. |

## Global Phase 2 Entry Criteria

No Phase 2 patch should start unless all items below are true:

| Criterion | Required state |
| --- | --- |
| Scope | A specific batch is named, with source files and target files listed. |
| Authorization | User has authorized that specific local migration patch. |
| Source status | Windows source remains read-only; no source files are changed. |
| Target status | Target directories and files are created only by the scoped patch. |
| Private state | `state-private/`, private memory, private prompts, and local audit state are excluded. |
| Secrets | Real `.env`, tokens, keys, credentials, private auth files, logs, caches, and runtime DBs are excluded. |
| Old paths | Old `AGENTS_OS/`, root registry/security, and Windows path assumptions are normalized or clearly marked as historical. |
| Examples | `.example`, `.template`, and example registry files are marked example-only. |
| Scripts | No source or migrated script is executed during migration. |
| Executable bits | No script is made executable by default. |
| Prompts | No prompt is activated, installed, or allowed to override current instructions. |
| Remote actions | No fetch, pull, push, merge, release, deploy, PR, tag, or remote write occurs. |
| Validation | Validation is defined before migration and run only where safe and local. |
| Receipt | A migration receipt path is declared before the patch starts. |
| Rollback | Rollback is possible by removing the newly added target files/directories from the patch. |

## Batch-Specific Entry Criteria

| Batch | Minimum checks before patch |
| --- | --- |
| Registry/security | Normalize `WORKSPACE_REGISTRY.yaml`; reconcile `SECURITY_BOUNDARIES.md`; confirm no root duplicate authority. |
| Contracts/registry examples | Parse JSON/YAML; mark examples; keep registry examples below `control-plane/registry/examples/`. |
| Runbooks | Rewrite stale paths; preserve audit-first wording; isolate upstream sync as restricted reference. |
| Templates | Confirm placeholder-only content; isolate env example; align security template with governance boundary. |
| Ops scripts | Run syntax-only review only when explicitly in scope; review output policy; do not execute scripts. |
| Prompts | Treat observed files as README/catalogs; do not create missing prompt files; keep non-authorization wording. |

## Recommended Phase 2 Order

| Order | Batch | Reason |
| ---: | --- | --- |
| 1 | Contracts and registry examples | Lowest risk; mostly schema/example/docs material. |
| 2 | Registry/security docs | Important authority surfaces; needs careful path normalization. |
| 3 | Templates | Useful reusable assets; env/security template risks are contained by placement. |
| 4 | Ordinary runbooks | Procedural guidance needs stale-path cleanup. |
| 5 | Ops scripts | Executable-code risk; requires stricter validation and no executable bit. |
| 6 | Prompts | Behavior-authority risk; should be last and catalog-only unless separately approved. |

## Phase 2 Stop Conditions

Stop before or during Phase 2 if:

- A candidate contains a real secret, credential, token, private memory, or
  private prompt.
- A target file would create duplicate authority with root policy, registry, or
  security boundaries.
- A script requires execution, executable-bit changes, remote actions, or
  non-obvious path rewrites.
- A prompt would override current instructions, grant authority, or activate an
  identity/behavior change.
- A runbook or script implies push, release, deploy, merge, branch movement, or
  remote write without separate explicit approval.
- A file named in a README was not observed in inventory.

## Required Phase 2 Receipt

Any actual migration patch must create a receipt under:

```text
ops/migration/receipts/rules-assets-migration-receipt-YYYY-MM-DD.md
```

The receipt must include:

- User authorization scope.
- Source files read.
- Target files created or modified.
- Files intentionally skipped.
- Secret/private-state checks.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Related Documents

- `rules-assets-migration-plan-2026-06-27.md`
- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/control-plane-assets-targets-2026-06-27.md`
- `../decisions/runbooks-targets-2026-06-27.md`
- `../decisions/templates-targets-2026-06-27.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/prompts-targets-2026-06-27.md`
