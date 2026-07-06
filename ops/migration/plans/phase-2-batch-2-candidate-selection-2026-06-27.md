# Phase 2 Batch 2 Candidate Selection - 2026-06-27

Status: selected candidate; no migration performed.

Notice: This document selects the safest next Batch 2 candidate. It is not a
patch plan, not migration authorization, and not authorization to copy, move,
delete, execute, sync, push, or normalize files.

## Decision

Select ordinary templates as Phase 2 Batch 2.

Batch 2 should be limited to the ordinary template subset:

```text
A:\AGENTS_OS_Workspace\templates\README.AGENTS_OS.md
A:\AGENTS_OS_Workspace\templates\README.template.md
A:\AGENTS_OS_Workspace\templates\jenn-extension.manifest.example.json
```

Planned target family for a later Batch 2 patch plan:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/README.template.md
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/jenn-extension.manifest.example.json
```

## Why This Candidate Is Lowest Risk

| Candidate | Selection | Reason |
| --- | --- | --- |
| Ordinary templates | Selected | Small reusable documentation/schema-adjacent assets; no remote commands; target directories are currently clear. |
| Env example template | Deferred | Contains env/token-like placeholder names and must remain isolated example-only material. |
| Security template | Deferred | Must be aligned against `governance/SECURITY_BOUNDARIES.md` before copy. |
| Ordinary runbooks | Deferred | Procedure docs need stale-path and governance wording cleanup before migration. |
| Upstream sync runbook | Not a Batch 2 candidate | Remote, branch, merge, and sync semantics require a restricted maintenance-reference plan. |

## Evidence Checked

| Evidence | Result |
| --- | --- |
| Phase 1 recommended order | Templates are listed before ordinary runbooks because risks are contained by placement. |
| `templates-targets-2026-06-27.md` | Ordinary templates are candidates after placeholder, path, and schema review. |
| `runbooks-targets-2026-06-27.md` | Runbooks need path normalization; upstream sync is remote/branch-sensitive. |
| Source template files | Five template files observed under `A:\AGENTS_OS_Workspace\templates`. |
| Source runbook files | Five runbook files observed under `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks`. |
| Target ordinary template files | Planned ordinary template targets are currently absent. |
| Source manifest example JSON | Parsed successfully. |

## Batch 2 Scope Boundary

Included for the next patch plan:

| Source | Proposed target | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\templates\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md` | Rewrite as target-native template-library index. |
| `A:\AGENTS_OS_Workspace\templates\README.template.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/README.template.md` | Preserve template shape; update stale `AGENTS_OS` layer wording to current WSL layout wording. |
| `A:\AGENTS_OS_Workspace\templates\jenn-extension.manifest.example.json` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/jenn-extension.manifest.example.json` | Copy only after JSON parse and basic schema-required-field check. |

Excluded from Batch 2:

| Excluded asset | Reason |
| --- | --- |
| `config.env.example.template` | Keep for a later env-template batch after placeholder-only review. |
| `SECURITY.template.md` | Keep for a later security-template batch after governance boundary alignment. |
| All runbooks | Keep for a later runbook batch after stale-path and authorization wording review. |
| Any validator script | Scripts are outside this candidate selection. |
| Any active config, env file, registry file, or extension package | Outside ordinary template scope. |

## Required Checks Before A Batch 2 Patch

| Check | Purpose |
| --- | --- |
| Reconfirm target files are absent. | Avoid overwriting user-owned work. |
| Parse `jenn-extension.manifest.example.json` as JSON. | Ensure the example remains machine-readable. |
| Check required manifest fields against `jenn-extension.manifest.schema.json`. | Keep the example aligned with the Batch 1 schema. |
| Scan selected template content for real secret-like values. | Confirm only placeholders/examples are present. |
| Review stale layer/path wording in `README.template.md`. | Avoid carrying old `AGENTS_OS` wording as current target truth. |
| Keep validation references non-executable unless scripts are migrated. | Avoid implying unavailable commands. |

## Stop Conditions

- Do not copy env templates in Batch 2.
- Do not copy security templates in Batch 2.
- Do not copy or execute runbooks in Batch 2.
- Do not create active config files.
- Do not create active registry files.
- Do not run source or migrated validator scripts.
- Stop if selected templates contain real secrets, credentials, or private data.

## Next Document

If this candidate is accepted, the next safe document is:

```text
ops/migration/plans/phase-2-batch-2-ordinary-templates-patch-plan-2026-06-27.md
```
