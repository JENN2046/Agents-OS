# Prompts Target Decision - 2026-06-27

Status: target-placement decision only，非迁移授权。

This decision record separates agent-common prompt material, Codex prompt
material, and legacy/reference-only prompt names from the Windows reference
root. It does not authorize copying, moving, deleting, activating prompts,
changing agent behavior, executing tasks, pushing, syncing, or changing source
assets.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Prompt target placement and authority handling |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source area reviewed | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts` |
| Assets observed | `README.AGENTS_OS.md`, `agents\README.AGENTS_OS.md`, `codex\README.AGENTS_OS.md` |
| Assets named but not observed | `MEMORY_AGENT.md`, `REVIEW_AGENT.md`, `PROJECT_AGENT.md`, `METIS.md`, `AGENT_OS_OPERATOR.md`, `CODEX_MASTER_PROMPT.md`, `CODEX_REPO_AUDITOR.md`, `CODEX_EXTENSION_EXTRACTOR.md`, `CODEX_VCP_SYNC_AUDITOR.md`, `CODEX_NO_SECRET_RULES.md`, `review/`, `templates/` |
| Assets excluded | Private prompts, private memory, active AGENTS overrides, runtime prompts, scripts |
| Evidence used | Source file content read, keyword scan for authority/risk terms, WSL target directory check, `_DIRECTORY_PRINCIPLES.md`, Phase 0 inventory, script/runbook target decisions |
| Migration performed | No |
| Prompt activation performed | No |

## Grouping Decision

| Group | Planning target | Handling rule |
| --- | --- | --- |
| Agent common prompt material | `control-plane/prompts/agents/` | Keep as public/common prompt guidance only after identity, memory, and permission wording is reviewed. |
| Codex prompt material | `control-plane/prompts/codex/` | Keep as Codex prompt guidance only after alignment with current AGENTS rules, governance gates, and security boundaries. |
| Legacy/reference-only prompt names | `control-plane/prompts/reference/` | Record as historical or planned names only; do not create active prompt files from names listed in README. |

This is a planning split for the current migration, not a permanent category
system. Future prompt assets should be placed by actual role, privacy level, and
authority risk.

## File Decisions

| Source file | Target for planning | Handling decision | Reason |
| --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/README.md` | Rewrite or adapt as a prompt library index with explicit non-authorization language. | The file describes reusable prompts for Codex, Agent, Reviewer, and Operator. It also says prompts are not universal authorization and must not bypass approval. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\agents\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/agents/README.md` | Keep as agent-common prompt catalog/index only; do not activate identity or memory behavior from it. | The file describes role prompts and operating instructions, but only the README was observed. Listed prompt files were not present in the inventory. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/codex/README.md` | Keep as Codex prompt catalog/index only; do not treat as active Codex operating authority. | The file describes Codex audit, extraction, sync, validation, and execution prompts, but only the README was observed. Its content must be reconciled with current Codex rules before use. |
| Prompt names listed but not observed | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/reference/legacy-listed-prompts.md` | Reference only if a Phase 2 migration needs to preserve the old catalog. | Names listed in README are not files observed in the source scope. They should not be invented, activated, or treated as migrated assets. |

## Prompt Authority Rule

Prompt files do not outrank:

- Current system, developer, and user instructions.
- Checked-in `AGENTS.md` files.
- `_ROOT_POLICY.md`.
- `_DIRECTORY_PRINCIPLES.md`.
- `governance/SECURITY_BOUNDARIES.md` once migrated.
- Governance gates, approval policy, and explicit task authorization.

Prompt files must not authorize:

- Reading, printing, or summarizing real secrets.
- Push, release, deploy, remote writes, or branch-sensitive actions.
- Background execution or hidden network activity.
- Direct main modification.
- Permission self-expansion.
- Bypassing review, approval, or receipt requirements.

## Directory Decisions

| Target directory | Decision | Notes |
| --- | --- | --- |
| `control-plane/prompts/` | Create only during a later approved Phase 2 migration patch. | Owns reusable prompt guidance that is safe to keep public/common. |
| `control-plane/prompts/agents/` | Use for common agent prompt guidance and catalogs. | Private identity, private memory, and personal prompt material do not belong here. |
| `control-plane/prompts/codex/` | Use for Codex prompt guidance and catalogs. | Current Codex behavior still comes from active instructions, AGENTS files, and governance boundaries. |
| `control-plane/prompts/reference/` | Use for historical prompt names and reference-only catalogs. | This is for preserving evidence, not for activation. |
| `governance/prompts/` | Not used for this batch. | Prompts may reference governance, but governance authority should live in governance docs/code, not prompt text. |
| `extensions/prompts/` | Not used for this batch. | Extension-specific prompts should live with their extension only under a separate scoped decision. |
| `state-private/` | Reserved for private prompt or private memory material if later discovered. | Not inventoried or migrated in this phase. |

## Required Review Before Phase 2 Copy

| Asset | Required review |
| --- | --- |
| Root prompt README | Convert to `README.md`; keep "prompt is not authorization" wording; remove references to missing directories or mark them reference-only. |
| Agent prompt README | Convert to `README.md`; review identity, memory, and permission language; do not imply self-expanding agent authority. |
| Codex prompt README | Convert to `README.md`; align with current AGENTS instructions, governance gates, runbook decisions, and script decisions. |
| Legacy prompt names | Preserve only as reference if useful; do not create files for names that were not observed. |

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Put prompts under `governance/` | Rejected for this batch | The observed files are prompt catalogs, not hard-gate policy or approval logic. |
| Put agent prompts under `extensions/` | Rejected for this batch | No concrete agent pack files were observed, only a catalog README. |
| Treat `CODEX_MASTER_PROMPT.md` as migrated | Rejected | The file name was listed but no such file was observed in source scope. |
| Treat prompt README files as active behavior authority | Rejected | Prompt catalogs cannot override current AGENTS rules, governance boundaries, or user authorization. |
| Create missing prompt files from names in README | Rejected | That would invent assets not supported by the inventory. |
| Migrate private prompt material | Rejected for this phase | No private prompt review was authorized, and `state-private/` remains denied by default. |

## Phase 2 Stop Conditions

- Do not activate or install any prompt during migration.
- Do not copy private prompt text, private memory, `AGENTS.override.md`, or
  state-private material.
- Do not create prompt files for names that were only listed but not observed.
- Do not let prompt wording authorize push, release, deploy, secret access,
  background execution, or bypassing approval.
- Do not create target directories or copy files until Phase 2.

## Related Documents

- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `runbooks-targets-2026-06-27.md`
- `ops-scripts-targets-2026-06-27.md`
- `templates-targets-2026-06-27.md`
- `workspace-registry-security-boundaries-targets-2026-06-27.md`
