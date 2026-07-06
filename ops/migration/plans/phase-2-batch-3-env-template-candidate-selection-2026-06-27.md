# Phase 2 Batch 3 Candidate Selection: Env Template - 2026-06-27

Status: selected candidate; no migration performed.

Notice: This document selects the Phase 2 Batch 3 candidate. It is not a patch
plan, not migration authorization, not authorization to copy files yet, and not
authorization to create or modify any active env/config file.

## Decision

Select the env example template as Phase 2 Batch 3.

Batch 3 should be limited to:

```text
A:\AGENTS_OS_Workspace\templates\config.env.example.template
```

Planned target family for a later Batch 3 patch plan:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example.template
```

## Why This Candidate Is Next

| Candidate | Selection | Reason |
| --- | --- | --- |
| Env example template | Selected | Already isolated by Phase 1; source uses `EXAMPLE_*` placeholder names and can be contained under `control-plane/templates/env/`. |
| Security template | Deferred | Needs alignment against `governance/SECURITY_BOUNDARIES.md` before copy. |
| Ordinary runbooks | Deferred | Procedure docs need stale-path and authorization wording cleanup before migration. |
| Upstream sync runbook | Not a Batch 3 candidate | Remote, branch, merge, and sync semantics require a restricted maintenance-reference plan. |
| Ops scripts | Not a Batch 3 candidate | Scripts require syntax, path, output, and execution-safety review. |

## Evidence Checked

| Evidence | Result |
| --- | --- |
| `templates-targets-2026-06-27.md` | Env example template target is `control-plane/templates/env/`; it must stay example-only and must not become active config. |
| Phase 1 summary | Env example template is an example-only candidate and never active config. |
| Batch 2 candidate selection | Env template was explicitly deferred for a later dedicated batch. |
| Batch 2 receipt | Env template target was explicitly skipped and not authorized by Batch 2. |
| Source file content | Source contains `EXAMPLE_API_BASE_URL`, `EXAMPLE_TOKEN`, and `EXAMPLE_MODE`; no real secret value was observed in this shallow check. |
| Target path status | `control-plane/templates/env/` and `control-plane/templates/env/config.env.example.template` are currently absent. |

## Batch 3 Scope Boundary

Included for the next patch plan:

| Source | Proposed target | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example.template` | Preserve as example-only env template after placeholder-only and live-secret pattern review. |

Excluded from Batch 3:

| Excluded asset | Reason |
| --- | --- |
| `.env` | Active env file; not a template migration target. |
| `.env.*` | May be active local config; excluded unless separately reviewed and authorized. |
| `.env.example` | Not the approved target filename for this batch. |
| `config.env` | Active config-style filename; excluded. |
| `config.env.example` | Not the approved target filename for this batch. |
| `SECURITY.template.md` | Reserved for a later security-template batch. |
| All runbooks | Reserved for a later runbook batch. |
| Any validator script | Scripts are outside this candidate selection. |
| Any active config, registry file, extension package, private state, logs, cache, or runtime artifact | Outside env-template scope and higher risk. |

## Required Checks Before A Batch 3 Patch

| Check | Purpose |
| --- | --- |
| Reconfirm source file exists. | Ensure the selected source did not move or change unexpectedly. |
| Reconfirm target file is absent. | Avoid overwriting user-owned work. |
| Reconfirm excluded active env/config targets are absent or untouched. | Prevent accidental promotion to active config. |
| Scan source content for live-secret patterns. | Stop if any real-looking token, key, credential, password, or private endpoint appears. |
| Confirm every assignment is example/placeholder-only. | `EXAMPLE_*` names and placeholder values must remain clearly non-active. |
| Preserve `.template` filename. | Do not rename to `.env`, `.env.example`, `config.env`, or `config.env.example`. |
| Add example-only comments if needed. | Make clear the file is not active local configuration. |

## Stop Conditions

- Stop if the source file is missing.
- Stop if the target file already exists.
- Stop if any active env/config filename would be created or modified.
- Stop if any real secret, token, key, credential, password, private endpoint,
  or private account value is found.
- Stop if placeholder status is ambiguous.
- Stop before copying security templates, runbooks, scripts, active config,
  registry files, extension packages, private state, logs, cache, or runtime
  artifacts.

## Next Document

If this candidate is accepted, the next safe document is:

```text
ops/migration/plans/phase-2-batch-3-env-template-patch-plan-2026-06-27.md
```
