# Phase 2 Batch 7 Prompt Catalogs Patch Plan - 2026-06-28

Status: patch plan only; no migration performed.

Notice: This document plans the prompt-catalogs patch. It is not migration
authorization, not authorization to copy files yet, not authorization to
activate, install, source, import, or apply any prompt, and not authorization to
change agent, Codex, reviewer, operator, memory, or execution behavior.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 7 |
| Batch name | Prompt catalogs |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source directory | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts` |
| Target directory family | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/` |
| Included asset type | Prompt catalog README files and reference-only listed-name index |
| Excluded asset types | Active prompts, private prompts, private memory, AGENTS overrides, runtime prompts, scripts, templates, runbooks, state-private material, logs, cache, runtime artifacts |
| Migration performed | No |
| Prompt activation performed | No |

## Legacy Reference Decision

Decision:

```text
Include control-plane/prompts/reference/legacy-listed-prompts.md as reference-only.
```

Reason:

The source README catalogs list prompt filenames and prompt subdirectories that
were not observed as source files during inventory. A reference-only target file
preserves this evidence in one place and reduces the chance that a later patch
silently invents, activates, or treats missing prompt names as migrated assets.

Handling rule:

`legacy-listed-prompts.md` must state that every listed item is historical or
listed-only evidence, not an active prompt, not a migrated prompt file, not a
behavior authority, and not authorization to create the missing file later.

Rejected alternative:

Do not omit the legacy-listed names entirely. Omitting them would make the old
README lists harder to audit and could cause future confusion about whether the
missing files were forgotten or intentionally excluded.

## Source Evidence

| Source file | Size | SHA-256 | Batch handling |
| --- | ---: | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md` | 819 bytes | `bf1cf95d12f54211fa9461a20454d66a5f7abf5145df647105f73fee095b8d55` | Rewrite as target-native root prompt catalog README. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\agents\README.AGENTS_OS.md` | 865 bytes | `7bed9fed366787d3d0c5c6cd37b033ecdc8bb5aace5a2280b2d75fedca796148` | Rewrite as agent prompt catalog README. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md` | 951 bytes | `f830684fa454ae406cccf372f5954c3811b0666a72d1c4ab029cbe43107aea6e` | Rewrite as Codex prompt catalog README. |

## Plan-Level Checks Already Performed

| Check | Result |
| --- | --- |
| Source file listing | Only three source README files were observed under `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts`. |
| Source hash check | The three source README hashes matched the Batch 7 candidate-selection evidence. |
| Target directory check | `control-plane/prompts/`, `control-plane/prompts/agents/`, `control-plane/prompts/codex/`, and `control-plane/prompts/reference/` were absent during planning. |
| Target file check | The four planned target files were absent during planning. |
| Live-secret scan | No live-secret patterns were found in the three source README files. |
| Authority-risk scan | Source READMEs mention prompt authority, identity, memory, execution, push/release/deploy, direct main modification, and old validation script paths. These must be rewritten as catalog-only and non-authorization language. |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/` | Target home for reusable prompt catalog guidance. |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/agents/` | Target home for agent prompt catalog guidance. |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/codex/` | Target home for Codex prompt catalog guidance. |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/reference/` | Target home for reference-only listed prompt names. |

Do not create `control-plane/prompts/review/` or
`control-plane/prompts/templates/` in this batch.

## Planned File Changes

| Action | Target file | Source evidence | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/README.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md` | Rewrite as catalog-only prompt library index with explicit non-authorization language. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/agents/README.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\agents\README.AGENTS_OS.md` | Rewrite as agent prompt catalog index; do not activate identity, memory, room, or agent-pack behavior. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/codex/README.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md` | Rewrite as Codex prompt catalog index; do not treat as active Codex operating authority. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/reference/legacy-listed-prompts.md` | Listed names from the three source README files | Create as reference-only evidence of listed-but-unobserved prompt names and directories. |

No existing target file is planned to be modified in this batch.

## Listed-Only Items To Preserve As Reference

| Listed-only item | Source catalog | Handling |
| --- | --- | --- |
| `review/` | Root prompt README | Reference-only; do not create directory. |
| `templates/` | Root prompt README | Reference-only; do not create directory. |
| `MEMORY_AGENT.md` | Agent prompt README | Reference-only; do not create prompt file. |
| `REVIEW_AGENT.md` | Agent prompt README | Reference-only; do not create prompt file. |
| `PROJECT_AGENT.md` | Agent prompt README | Reference-only; do not create prompt file. |
| `METIS.md` | Agent prompt README | Reference-only; do not create prompt file. |
| `AGENT_OS_OPERATOR.md` | Agent prompt README | Reference-only; do not create prompt file. |
| `CODEX_MASTER_PROMPT.md` | Codex prompt README | Reference-only; do not create prompt file. |
| `CODEX_REPO_AUDITOR.md` | Codex prompt README | Reference-only; do not create prompt file. |
| `CODEX_EXTENSION_EXTRACTOR.md` | Codex prompt README | Reference-only; do not create prompt file. |
| `CODEX_VCP_SYNC_AUDITOR.md` | Codex prompt README | Reference-only; do not create prompt file. |
| `CODEX_NO_SECRET_RULES.md` | Codex prompt README | Reference-only; do not create prompt file. |

## Explicitly Skipped Assets

| Skipped asset | Reason |
| --- | --- |
| Active prompt files named in source READMEs | They were listed but not observed as source files. |
| `control-plane/prompts/review/` | Listed by source README but not observed as a source directory. |
| `control-plane/prompts/templates/` | Listed by source README but not observed as a source directory. |
| Private prompts and private memory | Not inventoried or authorized; excluded by prompt target decision. |
| `AGENTS.override.md` or active AGENTS prompt material | Active behavior override material is outside this batch. |
| Runtime prompts and extension-specific prompt assets | No concrete source files were observed for this batch. |
| Validation scripts | Already handled by Batch 6; no script invocation is authorized here. |

## Required Rewrites And Alignment

| Topic | Target handling | Reason |
| --- | --- | --- |
| Source README filenames | Rewrite `README.AGENTS_OS.md` files as target-native `README.md` files. | WSL target directories use local README naming. |
| Catalog-only posture | Every target file must say it is guidance/catalog material only, not active prompt authority. | Prevent prompt activation by migration. |
| Authority order | State that prompt catalogs do not override current system/developer/user instructions, checked-in `AGENTS.md`, `_ROOT_POLICY.md`, or `governance/SECURITY_BOUNDARIES.md`. | Matches Phase 1 prompt authority rule. |
| Missing prompt files | Move listed-but-unobserved prompt names to `legacy-listed-prompts.md` as reference-only. | Prevent invented prompt files. |
| Missing directories | Do not create `review/` or `templates/`; record them as listed-only. | Directory names alone are not source evidence. |
| Validation references | Replace old `../../ops/scripts/validate-no-secrets.sh` and `../../../ops/scripts/validate-no-secrets.sh` with "validation script invocation requires separate explicit approval." | Batch 6 files exist but script execution is not authorized. |
| Agent identity and memory wording | Keep identity, memory, room, and permission language as catalog guidance only; no activation or self-expansion. | Avoid agent behavior changes. |
| Codex behavior wording | Keep audit-first and stop-for-risk language, but do not let catalog text become active Codex operating authority. | Current active instructions and governance outrank prompt catalogs. |
| Risky actions | Preserve bans on secret access, push, release, deploy, direct main modification, background execution, bypassing approval, and unreviewed push. | Keep source safety posture. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source README files exist | Check the three source README files. | All three source files exist and hashes match this plan. |
| Reconfirm target files are absent | Check the four planned target files. | None of the four target files exists before patch. |
| Reconfirm target directories are absent or non-conflicting | Check `control-plane/prompts/` family. | Directories are absent or contain no conflicting target files. |
| Reconfirm skipped prompt files are absent | Check the listed-only prompt filenames under planned target directories. | Missing prompt names are not accidentally created. |
| Live-secret pattern scan | Scan source READMEs and target drafts. | No real secret, token, credential, password, private endpoint, or private account value is present. |
| Authority-risk scan | Search target drafts for activation, override, direct main modification, background execution, push/release/deploy, and bypass language. | Such phrases appear only as forbidden or non-authorization wording. |
| Validation-command scan | Search target drafts for copy-ready validation script commands. | Target catalogs do not include runnable validation commands. |
| Private-state scan | Search target drafts for private prompt, private memory, and state-private handling. | Private material is referenced only as excluded or forbidden. |

## Planned Content Rules

- Target files must live under `control-plane/prompts/`.
- Target files must be catalog-only and non-authorization.
- Target files must not activate, install, source, import, or apply prompts.
- Target files must not create behavior authority for Codex, agents, reviewers,
  operators, memory systems, rooms, or harnesses.
- Target files must not create missing prompt files from README-listed names.
- Target files must not copy private prompt text, private memory, AGENTS
  overrides, or state-private material.
- Target files must not include copy-ready validation script commands.
- Target files must not authorize secret access, push, release, deploy, branch
  movement, direct main modification, background execution, remote writes, or
  permission self-expansion.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file existence check | Confirm the four planned files exist under `control-plane/prompts/`. | No extra prompt files should be created. |
| Listed-only file absence check | Confirm listed-only prompt names were not created as prompt files. | They should appear only inside `legacy-listed-prompts.md`. |
| Missing directory absence check | Confirm `control-plane/prompts/review/` and `control-plane/prompts/templates/` were not created. | Source directories were not observed. |
| Live-secret pattern scan | Scan target files and receipt. | No live-secret pattern should be present. |
| Prompt activation scan | Search target files for activation/override wording. | Any such wording must be framed as forbidden or non-authorization. |
| Validation-command scan | Search target files for `validate-no-secrets.sh` command examples. | No copy-ready validation command should appear. |
| Diff or content review | Inspect created files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run validation scripts, prompt tooling, activation commands, or runtime
commands in this batch.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-7-prompt-catalogs-receipt-2026-06-28.md
```

The receipt should record:

- Exact authorization wording.
- Source files read.
- Listed-only prompt names and directories.
- Target directories created.
- Target files created.
- Files and directories explicitly skipped.
- Non-activation and non-authorization checks.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If the prompt-catalogs patch is later applied and must be rolled back, remove
only the files created by that patch after confirming no later user work depends
on them:

```text
control-plane/prompts/README.md
control-plane/prompts/agents/README.md
control-plane/prompts/codex/README.md
control-plane/prompts/reference/legacy-listed-prompts.md
ops/migration/receipts/rules-assets-batch-7-prompt-catalogs-receipt-2026-06-28.md
```

Remove prompt directories only if they are empty after those files are removed.
Do not remove `control-plane/`, existing migration documents, receipts, or any
source files under `A:\AGENTS_OS_Workspace`.

## Related Documents

- `phase-2-batch-7-candidate-selection-2026-06-28.md`
- `../decisions/prompts-targets-2026-06-27.md`
- `../plans/phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/runbooks-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
