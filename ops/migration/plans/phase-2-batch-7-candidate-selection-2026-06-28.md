# Phase 2 Batch 7 Candidate Selection - 2026-06-28

Status: candidate selection only; no migration performed.

Notice: This document selects the next Phase 2 batch candidate after Batch 6.
It is not migration authorization, not authorization to copy prompt files, not
authorization to activate prompts, not authorization to execute validation
scripts, and not authorization to create executable or remote workflows.

## Candidate Question

Choose the safer next Batch 7 direction:

1. Prompt catalogs, catalog-only.
2. Batch 6 follow-up validation execution authorization template.

## Current Context

| Item | Current state |
| --- | --- |
| Batch 5 ordinary runbooks | Completed and three-way reviewed. |
| Batch 6 validation scripts | Completed and three-way reviewed. |
| Validation script execution | Still not authorized; scripts are placed but not executable by default. |
| Prompt migration | Not started; Phase 1 says only README catalogs were observed. |
| Current repository state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Candidate A - Prompt Catalogs

| Item | Value |
| --- | --- |
| Candidate name | Prompt catalogs, catalog-only |
| Source directory | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts` |
| Planned target family | `/home/jenn/AGENTS_OS_Workspace/control-plane/prompts/` |
| Source files observed | `README.AGENTS_OS.md`, `agents\README.AGENTS_OS.md`, `codex\README.AGENTS_OS.md` |
| Target files likely needed | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, possibly `control-plane/prompts/reference/legacy-listed-prompts.md` |
| Handling limit | Catalog-only; no prompt activation, no missing prompt files created, no behavior authority. |
| Risk | Medium-low if kept catalog-only; high if treated as active prompts. |

### Prompt Source Evidence

| Source file | Size | SHA-256 | Observed role |
| --- | ---: | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md` | 819 bytes | `bf1cf95d12f54211fa9461a20454d66a5f7abf5145df647105f73fee095b8d55` | Root prompt catalog README. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\agents\README.AGENTS_OS.md` | 865 bytes | `7bed9fed366787d3d0c5c6cd37b033ecdc8bb5aace5a2280b2d75fedca796148` | Agent prompt catalog README. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md` | 951 bytes | `f830684fa454ae406cccf372f5954c3811b0666a72d1c4ab029cbe43107aea6e` | Codex prompt catalog README. |

### Prompt Risk Signals

| Signal | Source evidence | Required handling |
| --- | --- | --- |
| Missing prompt files listed by name | README files list `MEMORY_AGENT.md`, `REVIEW_AGENT.md`, `PROJECT_AGENT.md`, `METIS.md`, `AGENT_OS_OPERATOR.md`, `CODEX_MASTER_PROMPT.md`, `CODEX_REPO_AUDITOR.md`, `CODEX_EXTENSION_EXTRACTOR.md`, `CODEX_VCP_SYNC_AUDITOR.md`, and `CODEX_NO_SECRET_RULES.md`, but only README files were observed. | Do not create these missing files. Preserve as reference names only if useful. |
| Missing directories listed by name | Root README lists `review/` and `templates/`, but they were not observed in the source file listing. | Do not create these directories or imply they were migrated. |
| Prompt authority risk | Source says prompts are used by Codex, Agent rooms, Review Agent, Codex Desktop/Runtime/Harness. | State that catalogs are guidance only and do not override current instructions, AGENTS files, or governance boundaries. |
| Secret and execution risk | Source forbids real secret examples, bypassing approval, direct main modification, background execution, and unreviewed push. | Preserve non-authorization wording and hard-stop defaults. |
| Old validation path | Source references `../../ops/scripts/validate-no-secrets.sh` and `../../../ops/scripts/validate-no-secrets.sh`. | Replace with "validation script invocation is separately authorized"; do not provide copy-ready command examples. |

## Candidate B - Batch 6 Execution Authorization Template

| Item | Value |
| --- | --- |
| Candidate name | Validation execution authorization template |
| Possible target family | `control-plane/templates/validation/` or `ops/validation/` |
| Purpose | A reusable checklist/template for separately authorizing validation-script execution after Batch 6. |
| Source file | No direct Windows source file selected in the current rules inventory. |
| Handling limit | New template, not migrated rules asset, not authorization to run scripts. |
| Risk | Low as documentation, but scope is adjacent to execution and could be misunderstood as permission to run scripts. |

### Template Risk Signals

| Signal | Impact |
| --- | --- |
| No direct source artifact | This would be a new local control artifact, not a migration of observed source. |
| Execution-adjacent wording | It must not become a standing permission slip for validation scripts. |
| Placement unresolved | Needs a separate placement decision: reusable template under `control-plane/templates/validation/` vs operational checklist under `ops/validation/`. |

## Comparison

| Criterion | Prompt catalogs | Execution authorization template |
| --- | --- | --- |
| Follows Phase 1 recommended order | Yes; prompts are the remaining rules-asset family after scripts. | Partly; it is a useful follow-up but not one of the originally inventoried source families. |
| Source evidence exists | Yes; three README catalog files were observed. | No direct source file selected. |
| Migration scope clarity | Clear if catalog-only. | Needs separate target-placement wording. |
| Risk if misunderstood | Prompt activation/authority risk. | Script execution authorization risk. |
| Low-risk path available | Yes: README-only catalog patch with explicit non-activation wording. | Yes: template-only patch, but it creates a new artifact rather than migrating observed source. |
| Best immediate next step | Strong candidate for Batch 7. | Good follow-up after prompt catalog planning or as Batch 8/Batch 6.x. |

## Selection

Selected Batch 7 candidate:

```text
Prompt catalogs, catalog-only
```

Reason:

Prompt catalogs are the remaining Phase 1 rules-asset family, and the observed
source is limited to three README catalog files. That gives a safe Batch 7 path
as long as the patch stays catalog-only and explicitly refuses prompt activation,
missing-file creation, private prompt migration, and authority escalation.

Deferred follow-up candidate:

```text
Validation execution authorization template
```

Reason:

The template is useful, but it is a new execution-adjacent artifact rather than
a directly observed migration source. It should receive its own small placement
decision before creation.

## Batch 7 Guardrails

- Do not activate, install, source, import, or apply any prompt.
- Do not create missing prompt files named only in source README catalogs.
- Do not create missing `review/` or `templates/` prompt directories from names
  alone.
- Do not copy private prompt material, private memory, AGENTS overrides, or
  state-private material.
- Do not let prompt wording override current system/developer/user
  instructions, checked-in `AGENTS.md`, `_ROOT_POLICY.md`, or
  `governance/SECURITY_BOUNDARIES.md`.
- Do not include copy-ready validation script commands.
- Do not authorize push, release, deploy, branch movement, remote writes,
  secret access, background execution, or permission self-expansion.

## Suggested Batch 7 Patch Plan Scope

Recommended next plan file:

```text
ops/migration/plans/phase-2-batch-7-prompt-catalogs-patch-plan-2026-06-28.md
```

Recommended planned targets:

```text
control-plane/prompts/README.md
control-plane/prompts/agents/README.md
control-plane/prompts/codex/README.md
control-plane/prompts/reference/legacy-listed-prompts.md
```

The `legacy-listed-prompts.md` file should be included only if the patch plan
decides that preserving listed-but-unobserved prompt names is useful. It must
remain reference-only.

## Preflight Needed Before Patch Plan

| Check | Reason |
| --- | --- |
| Reconfirm the three source README files exist and hashes match this selection. | Detect source drift before planning a patch. |
| Reconfirm target prompt files and directories are absent. | Avoid overwriting user-owned work. |
| Scan source README files for live-secret patterns. | Prompt files can accidentally contain secret examples. |
| Scan source README files for authority-risk phrases. | Ensure target rewrite removes or neutralizes activation/override wording. |
| Check current governance/security references. | Target catalogs must point to current authority surfaces. |

## Related Documents

- `../decisions/prompts-targets-2026-06-27.md`
- `../plans/phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/runbooks-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
