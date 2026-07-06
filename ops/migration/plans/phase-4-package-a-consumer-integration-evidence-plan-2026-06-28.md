# Phase 4 Package A Consumer Integration Evidence Plan - 2026-06-28

Status: plan only; no consumer integration evidence collection, validation,
scanning, parsing, script execution, or file modification has been performed.

Notice: This plan defines a possible read-only evidence package for consumer
integration. It is not authorization to inspect broader project trees, execute
validators, run new scans, parse files, source scripts, change executable bits,
edit consumers, edit registry data, create maintenance/sync helpers, or perform
remote, branch, release, deploy, secret, private-state, log, cache, runtime, or
project-repository actions.

## Authorization

User authorization:

```text
做 Phase 4 Package A consumer integration evidence plan，仍然只规划不执行。
```

Authorized scope:

- create this Package A plan
- do not create Package A evidence yet
- do not change any consumer file
- do not execute validators
- do not run active reference searches in this step
- do not parse additional files in this step

## Purpose

Plan a future read-only evidence package that can answer:

1. Which consumer areas are documented only?
2. Which consumer areas have static local references?
3. Which consumer areas appear implemented enough to be reviewed later?
4. Which consumer areas must remain explicitly unclaimed?

The future Package A evidence should classify consumers; it should not fix or
activate consumers.

## Planning Inputs

| Input | Path | Role |
| --- | --- | --- |
| Phase 4 scope plan | `ops/migration/plans/phase-4-scope-plan-2026-06-28.md` | Names Package A as the first Phase 4 package. |
| Phase 3 closeout review | `ops/migration/inventory/phase-3-closeout-review-2026-06-28.md` | Records that functional consumer integration was not exercised. |
| Phase 3 closeout receipt | `ops/migration/receipts/rules-assets-phase-3-closeout-receipt-2026-06-28.md` | Requires separate authorization for Phase 4 and integration validation. |
| Batch 11 consumer/readiness evidence | `ops/migration/inventory/registry-consumer-readiness-evidence-2026-06-28.md` | Prior read-only evidence: registry data was ready, but consumer readiness was partial. |

## Planned Consumer Areas

| Consumer area | Candidate surfaces for a later evidence package | Planned classification question |
| --- | --- | --- |
| Registry consumer/readiness | `ops/migration/inventory/registry-consumer-readiness-evidence-2026-06-28.md`, `control-plane/registry/README.md`, `control-plane/registry/WORKSPACE_REGISTRY.yaml`, `ops/validation/validate-workspace.sh`, `control-plane/runbooks/add-new-extension.md` | Are registry consumers documented only, static references, or implemented checks? |
| Prompt catalogs | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, `control-plane/prompts/reference/legacy-listed-prompts.md` | Do prompt catalogs remain reference/catalog only, or do they claim active authority? |
| Governance authority | `governance/SECURITY_BOUNDARIES.md`, `_ROOT_POLICY.md`, `_DIRECTORY_PRINCIPLES.md`, `_MIGRATION_MAP.md` | Do governance docs reference registry/control-plane authority without claiming runtime enforcement? |
| Validation execution authorization | `control-plane/templates/validation/validation-execution-authorization.template.md`, `ops/validation/README.md`, `ops/validation/validate-*.sh` | Do validation surfaces still require exact human authorization before execution? |

## Future Evidence Classification

If separately authorized, Package A evidence should classify each consumer surface
using these labels:

| Label | Meaning |
| --- | --- |
| `documented_only` | The consumer is named or described, but no local implementation/reference evidence is observed. |
| `static_reference` | The consumer references the authority path or policy text but is not executed. |
| `implemented_unexecuted` | The consumer has local implementation logic but is not run in this package. |
| `catalog_or_template_only` | The surface is intentionally reference/template material and not active behavior authority. |
| `stale_or_needs_review` | The surface contains wording that may be outdated after Phase 2/3 migration. |
| `out_of_scope` | The surface belongs to runtime, private state, project repositories, remote systems, or another migration track. |

Package A evidence should not use labels that imply runtime proof, such as
`integrated`, `verified_runtime`, or `production_ready`.

## Planned Preflight For Future Evidence

A later Package A evidence step should first confirm:

| Preflight item | Required result |
| --- | --- |
| This plan exists and hash is stable | Required before evidence collection. |
| Phase 4 scope plan exists and hash is stable | Required before evidence collection. |
| Phase 3 closeout review and receipt exist | Required before evidence collection. |
| Evidence target does not already exist | Avoid overwriting prior evidence. |
| Receipt target does not already exist | Avoid overwriting prior receipt. |
| Validation scripts remain non-executable | Expected mode `644`; no execution. |
| Deferred high-risk targets remain absent | `ops/maintenance/sync-upstream-vcp.sh`, root `WORKSPACE_REGISTRY.yaml`, and `governance/WORKSPACE_REGISTRY.yaml` should remain absent unless separately authorized. |

## Planned Evidence Collection Method

If separately authorized, Package A may perform only read-only local evidence
collection:

- read the candidate surfaces listed in this plan
- compare claims against prior Batch 11 evidence
- record observed references by file and line category
- distinguish documentation, static references, unexecuted implementation logic,
  and stale wording
- summarize counts and classifications
- avoid printing secrets or private-state content

Package A must not:

- execute validation scripts
- source validation scripts
- run broader project searches outside the listed surfaces unless separately
  authorized
- inspect runtime, memory, private-state, cache, log, or full project trees
- edit consumers, registry data, prompts, governance files, templates, or scripts
- create maintenance/sync helpers

## Planned Outputs For Future Evidence

If Package A evidence is later authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-4-consumer-integration-evidence-2026-06-28.md` | Record read-only consumer classification evidence. |
| `ops/migration/receipts/rules-assets-phase-4-package-a-consumer-integration-evidence-receipt-2026-06-28.md` | Record authorization, inputs, classifications, skipped actions, and remaining risks. |

This plan itself does not create those files.

## Open Decisions Before Evidence Authorization

| Decision | Default for safety |
| --- | --- |
| Whether to include `governance/codex-router/` | Exclude; it is a full project tree and was out of Phase 3 scope. |
| Whether to search all `runtime/`, `domains/`, `memory/`, or `archive/` | Exclude; separate migration tracks. |
| Whether to run `ops/validation/validate-workspace.sh` | No; execution requires a later exact-run authorization. |
| Whether to update stale wording found in Batch 11 | No; Package A evidence is read-only. |
| Whether to treat static references as integration proof | No; classify as `static_reference` only. |

## Stop Conditions

Stop and request separate authorization before:

- collecting evidence beyond the candidate surfaces listed here
- running any script or validator
- parsing additional structured files
- changing executable bits
- editing any consumer or registry file
- reading active env, credentials, private state, logs, caches, runtime output, or
  full project repositories
- performing sync, copy, move, delete, commit, push, release, deploy, or remote
  actions

## Package A Planning Result

```text
PHASE_4_PACKAGE_A_CONSUMER_INTEGRATION_EVIDENCE_PLAN_CREATED_NO_EXECUTION
```

The recommended next safe action is to authorize Package A evidence collection
only, if desired. That future step should remain read-only and should create the
planned evidence and receipt without changing consumers.
