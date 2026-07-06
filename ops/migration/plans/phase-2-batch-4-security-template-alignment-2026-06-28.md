# Phase 2 Batch 4 Security Template Alignment - 2026-06-28

Status: alignment only; no migration performed.

Notice: This document aligns the planned security-template batch with the
governance security-boundary decision. It is not a patch plan, not migration
authorization, and not authorization to copy, move, delete, execute, push, or
create active security authority files.

## Decision

Select the security template as the next Phase 2 template-family candidate, but
do not create a patch plan until the governance security-boundary prerequisite
is handled explicitly.

Planned security-template source:

```text
A:\AGENTS_OS_Workspace\templates\SECURITY.template.md
```

Planned security-template target family:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md
```

The security template must remain a reusable project/repo template. It must
reference governance security boundaries and must not become the canonical
workspace safety boundary.

## Authority Alignment

| Item | Status | Notes |
| --- | --- | --- |
| Canonical security-boundary target | Planned as `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` | Set by `workspace-registry-security-boundaries-targets-2026-06-27.md`. |
| Current WSL target file | Not observed | `governance/SECURITY_BOUNDARIES.md` does not currently exist. |
| Source boundary evidence | Observed at `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | Used only as source evidence until the governance target file is migrated. |
| Template source | Observed at `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | It is a template, not authority. |

## Alignment Findings

| Topic | Source template | Boundary source evidence | Alignment decision |
| --- | --- | --- | --- |
| Authority role | Template says `# Security`. | Boundary file defines hard workspace rules. | Target template must state it is a project/repo template and defers to `governance/SECURITY_BOUNDARIES.md`. |
| Default mode | `read-only unless explicitly authorized`. | Boundary file blocks high-risk actions unless gated. | Keep conservative default wording. |
| Forbidden actions | Lists secret reading/printing, git push, release, deploy, arbitrary shell, destructive delete, self-expansion. | Boundary also blocks git tag, reset, clean, history rewrite, and defines runtime gates. | Preserve source list but broaden wording to defer to governance for complete hard stops. |
| Allowed config examples | `.env.example`, `config.env.example`, `*.template`, `*.example`. | Boundary source lists the same allowed template file patterns. | Keep as examples only; do not imply active config approval. |
| Forbidden config examples | `.env`, `.env.*`, `config.env`, tokens, API keys, private credentials. | Boundary source also protects `*.pem`, `*.key`, `*.p12`, `*.pfx`, SSH keys, `credentials.json`, and `token.json`. | Target template should either include the broader protected list or explicitly defer to governance for the full list. |
| Private state | Not mentioned. | Boundary file protects `state-private/`. | Target template should mention private state is governed by `governance/SECURITY_BOUNDARIES.md`. |
| High-risk paths | Not mentioned. | Boundary source lists runtime, state-private, domains, execution/governance paths. | Target template should not duplicate stale high-risk paths unless they are reconciled; prefer a pointer to governance. |

## Patch-Plan Prerequisite

Before creating a Batch 4 security-template patch plan, choose one of these
safe paths:

| Option | Meaning | Risk |
| --- | --- | --- |
| Preferred: migrate/reconcile `governance/SECURITY_BOUNDARIES.md` first | Establish the canonical boundary file before creating a template that references it. | Lowest drift risk. |
| Conditional: plan the template with an explicit missing-authority note | Security template can point to the planned governance path, but the patch plan must record that the target authority file is not present yet. | Acceptable only if the missing authority is visible in the plan and receipt. |

Default recommendation: create a separate security-boundary authority patch
plan before the security-template patch plan.

## Batch 4 Scope Boundary

Included for a later patch plan only after the prerequisite is handled:

| Source | Proposed target | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` | Rewrite/adapt as a reusable security document template that references, but does not replace, `governance/SECURITY_BOUNDARIES.md`. |

Excluded from Batch 4:

| Excluded asset | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | Canonical boundary file; should be handled by a separate authority patch plan. |
| `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` | Not created by this alignment document. |
| Env templates | Already handled by Batch 3. |
| Runbooks | Reserved for a later runbook batch. |
| Validator scripts | Scripts require separate syntax, path, output, and execution-safety review. |
| Active config, registry files, extension packages, private state, logs, cache, runtime artifacts | Outside security-template scope. |

## Required Checks Before A Security-Template Patch Plan

| Check | Purpose |
| --- | --- |
| Reconfirm `governance/SECURITY_BOUNDARIES.md` status. | Decide whether the patch plan can reference an existing target authority file or must record a missing-authority risk. |
| Reconfirm source template exists. | Avoid planning from stale source evidence. |
| Reconfirm target template file is absent. | Avoid overwriting user-owned work. |
| Compare allowed/forbidden config wording with boundary evidence. | Keep template examples aligned with governance. |
| Avoid duplicating stale high-risk path lists. | Prevent template drift from canonical boundaries. |
| State template non-authority explicitly. | Prevent a reusable template from becoming a hard gate by accident. |
| Scan for live-secret patterns. | Stop if a template contains real credentials or private values. |

## Stop Conditions

- Stop if a patch plan would present `SECURITY.template.md` as the canonical
  security boundary.
- Stop if the missing `governance/SECURITY_BOUNDARIES.md` target is hidden or
  not recorded.
- Stop if the template would create or modify active config, registry,
  private-state, runtime, or extension-package files.
- Stop if the template contains real secrets, tokens, credentials, private
  endpoints, or private account values.
- Stop before copying runbooks, scripts, active security authority files, or
  runtime artifacts.

## Next Safe Document

Recommended next document:

```text
ops/migration/plans/phase-2-batch-4-security-boundary-authority-patch-plan-2026-06-28.md
```

Alternative, if the missing target authority is accepted as an explicit risk:

```text
ops/migration/plans/phase-2-batch-4-security-template-patch-plan-2026-06-28.md
```
