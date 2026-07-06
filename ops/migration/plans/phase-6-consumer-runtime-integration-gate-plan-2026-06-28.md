# Phase 6 Consumer Runtime Integration Gate Plan - 2026-06-28

Status: gate plan only; no consumer/runtime integration evidence collection,
runtime inspection, consumer rewrite, validator execution, loader execution,
YAML parsing, secret scan, file repair, maintenance/sync helper creation, or
remote action has been performed.

Notice: This plan defines the first concrete Phase 6 gate after the Phase 6
scope plan. It names the future read-only evidence boundary for
consumer/runtime integration, but it does not authorize evidence collection,
runtime tree inspection, script execution, consumer edits, registry edits,
runtime edits, or any remote, branch, release, deploy, sync, commit, push, copy,
move, or delete action.

Terminology note: "consumer", "runtime", and "integration" are local planning
words for this migration track. They do not create fixed permanent architecture
labels.

## Authorization

User authorization:

```text
做 phase-6-consumer-runtime-integration-gate-plan-2026-06-28.md，仍然只规划，不收集 evidence。
```

Authorized scope:

- create this consumer/runtime integration gate plan
- define future read-only evidence boundaries
- define future preflight checks, output targets, stop conditions, and
  acceptance limits
- do not collect evidence in this step
- do not read runtime internals or broader project trees
- do not execute validators, loaders, tests, scripts, or runtime code
- do not edit consumers, runtime files, registry data, governance files,
  prompts, runbooks, templates, or validator scripts
- do not create receipts for evidence collection in this step
- do not perform remote, branch, release, deploy, sync, commit, push, copy,
  move, delete, or destructive actions

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-6-scope-plan-2026-06-28.md` | `664aaa73d978b4d342833447eac7cc13d17f1ebd11aedbd346a6dc3c64001c4b` | `644` | Phase 6 scope authority. |
| `ops/migration/receipts/rules-assets-phase-5-closeout-receipt-2026-06-28.md` | `c44d05cd9b6cf6ca3337a372166a247dcd580b78db94afdd6f3fee120556ef36` | `644` | Carries consumer/runtime integration into Phase 6. |
| `ops/migration/inventory/phase-4-consumer-integration-evidence-2026-06-28.md` | `6f95fa0bb3aba567585f2c6fb8d76e12c06e3d2317f57ceb03f37a53fd10d9a4` | `644` | Prior static consumer evidence baseline. |
| `ops/migration/receipts/rules-assets-phase-4-consumer-rewrite-review-closeout-receipt-2026-06-28.md` | `c040cb4a33480ec7ebb0f5583485032f7c5977ce50f5eb9bbbc1be836fcf89bd` | `644` | Prior consumer README/runbook rewrite closeout. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Current validation consumer boundary. |
| `control-plane/runbooks/README.md` | `acc0049db6e621a63498a99d0b102385f07ec3dd9128e4b75d53aaa1ddab787d` | `644` | Current runbook consumer boundary. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Static registry authority data. |
| `ops/validation/validate-workspace.sh` | `b924ebaa5bf5396ae9b8bb5136cdd4265bfacfe9c11143d45e1fd18a81000ff5` | `644` | Existing local validator; no execution here. |
| `ops/validation/validate-extension-manifests.sh` | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4` | `644` | Existing local validator; no execution here. |
| `ops/validation/validate-no-secrets.sh` | `7bd0222675d7167e3c56f94b0734dcc683a0d4107f398b76c090c7bfcc8e23e6` | `644` | Existing local validator; no execution here. |
| This gate plan target | n/a | n/a | Target was absent before creation. |
| Future evidence target | n/a | n/a | `ops/migration/inventory/phase-6-consumer-runtime-integration-evidence-2026-06-28.md` was absent. |
| Future evidence receipt target | n/a | n/a | `ops/migration/receipts/rules-assets-phase-6-consumer-runtime-integration-evidence-receipt-2026-06-28.md` was absent. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

Top-level runtime-adjacent roots were observed by name only for boundary
planning: `archive/`, `control-plane/`, `domains/`, `execution/`,
`extensions/`, `governance/`, `labs/`, `memory/`, `ops/`, `runtime/`, and
`state-private/`. Their contents were not inspected by this gate plan.

## Gate Purpose

This gate is meant to answer, in a later separately authorized evidence step:

1. Which control-plane, governance, prompt, runbook, registry, and validation
   surfaces claim or imply consumer behavior?
2. Which claims are documentation-only versus locally implemented but
   unexecuted?
3. Which runtime-adjacent roots are merely present versus proven integrated?
4. Which items must stay deferred because proving them requires execution,
   runtime inspection, private-state reads, or remote/operational action?

This gate must not turn static documentation into runtime proof.

## Future Evidence Boundary

If separately authorized, the next evidence package may read only the Tier 1
surfaces below unless a later plan extends the allowlist.

### Tier 1 - Static Control Surfaces

| Area | Future read allowlist | Planned handling |
| --- | --- | --- |
| Prior evidence and closeouts | `ops/migration/inventory/phase-4-consumer-integration-evidence-2026-06-28.md`, `ops/migration/receipts/rules-assets-phase-4-consumer-rewrite-review-closeout-receipt-2026-06-28.md`, `ops/migration/receipts/rules-assets-phase-5-closeout-receipt-2026-06-28.md` | Read-only baseline comparison. |
| Registry authority | `control-plane/registry/README.md`, `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Text and path evidence only; no YAML parsing unless separately authorized. |
| Registry/runbook bridge | `control-plane/runbooks/README.md`, `control-plane/runbooks/add-new-extension.md` | Confirm whether guidance names registry or validation consumers. |
| Validation surfaces | `ops/validation/README.md`, `ops/validation/validate-workspace.sh`, `ops/validation/validate-extension-manifests.sh`, `ops/validation/validate-no-secrets.sh` | Read-only script/reference review; no execution, sourcing, tracing, or chmod. |
| Validation authorization template | `control-plane/templates/validation/validation-execution-authorization.template.md` | Confirm execution remains exact-authorization gated. |
| Prompt catalogs | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, `control-plane/prompts/reference/legacy-listed-prompts.md` | Confirm catalog/reference role only; no prompt activation. |
| Governance authority | `governance/SECURITY_BOUNDARIES.md`, `_ROOT_POLICY.md`, `_DIRECTORY_PRINCIPLES.md`, `_MIGRATION_MAP.md` | Confirm policy/reference role only; no runtime enforcement claim. |

### Tier 2 - Runtime-Adjacent Root Boundary

The next evidence package may record only top-level presence/absence for these
roots unless separately authorized to inspect specific files inside them:

```text
runtime/
execution/
extensions/
domains/
memory/
state-private/
archive/
labs/
governance/codex-router/
```

Tier 2 does not authorize recursive listing, file content reads, scripts,
loaders, private-state reads, log/cache reads, active env reads, or project
repository inspection.

## Future Classification Labels

The future evidence package should use limited labels:

| Label | Meaning |
| --- | --- |
| `documented_only` | Wording names a consumer or behavior, but no implementation evidence is read. |
| `static_reference` | A file references an authority path or policy but is not executed. |
| `implemented_unexecuted` | Local logic exists, but no runtime behavior is executed in this gate. |
| `catalog_or_template_only` | A surface is guidance, catalog, or template material only. |
| `top_level_presence_only` | A root exists by name, but internals were not inspected. |
| `deferred_requires_exact_run` | Proving behavior requires a separately authorized exact run. |
| `deferred_requires_narrow_read_allowlist` | Proving integration requires a later file-specific read allowlist. |
| `out_of_scope` | The item belongs to private state, runtime behavior, remote systems, or another migration track. |

Do not use labels such as `runtime_verified`, `fully_integrated`,
`production_ready`, or `accepted` during evidence collection.

## Future Preflight Requirements

Before collecting any Phase 6 integration evidence, a future preflight should
confirm:

| Preflight item | Required result |
| --- | --- |
| Phase 6 scope plan hash stable | `664aaa73d978b4d342833447eac7cc13d17f1ebd11aedbd346a6dc3c64001c4b` unless intentionally superseded. |
| This gate plan hash stable | Required before evidence collection. |
| Phase 5 closeout receipt hash stable | Required because it carried this gate forward. |
| Phase 4 consumer evidence hash stable | Required baseline. |
| Phase 4 consumer rewrite closeout hash stable | Required baseline. |
| Future evidence target absent | `ops/migration/inventory/phase-6-consumer-runtime-integration-evidence-2026-06-28.md`. |
| Future receipt target absent | `ops/migration/receipts/rules-assets-phase-6-consumer-runtime-integration-evidence-receipt-2026-06-28.md`. |
| Validator scripts remain mode `644` | No executable-bit changes. |
| Runtime/private roots remain closed except top-level presence | No recursive reads unless separately authorized. |
| Output policy confirmed | No raw secret values, active env values, private-state contents, logs, caches, or full runtime output. |

## Planned Future Outputs

If separately authorized after preflight, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-6-consumer-runtime-integration-evidence-2026-06-28.md` | Record read-only integration evidence using the limited labels above. |
| `ops/migration/receipts/rules-assets-phase-6-consumer-runtime-integration-evidence-receipt-2026-06-28.md` | Record authorization, stable inputs, evidence boundaries, skipped actions, and remaining risks. |

Those outputs must not grant runtime acceptance. They may only support a later
review deciding whether static/local integration readiness is enough to proceed
to a narrower consumer patch or exact-run behavior gate.

## Acceptance Limits For This Gate

This gate can at most prepare for a future static/local evidence review. It
cannot grant:

| Acceptance type | Status |
| --- | --- |
| Runtime behavior acceptance | Not authorized. |
| Extension loader acceptance | Not authorized. |
| Governance runtime enforcement acceptance | Not authorized. |
| Full consumer integration acceptance | Not authorized. |
| Full manifest/schema/content acceptance | Not authorized. |
| Full credential audit acceptance | Not authorized. |
| Maintenance/sync helper acceptance | Not authorized. |
| Remote/operational acceptance | Not authorized. |

## Stop Conditions

Stop and request separate authorization before:

- collecting the future evidence package
- creating the future evidence receipt
- reading beyond the Tier 1 allowlist
- recursively listing or reading runtime-adjacent roots
- opening active env files, credentials, private-state files, logs, caches, or
  broad project trees
- executing validators, loaders, tests, scripts, shell commands for behavior, or
  runtime code
- parsing YAML, JSON, schemas, manifests, or registry data beyond plain text
  review
- editing consumers, registry data, prompts, governance files, runbooks,
  templates, validator scripts, or runtime files
- changing executable bits
- creating maintenance/sync helpers
- copying, moving, deleting, committing, pushing, syncing, releasing,
  deploying, branching, or taking remote/external action

## Planning Result

```text
PHASE_6_CONSUMER_RUNTIME_INTEGRATION_GATE_PLAN_CREATED_NO_EVIDENCE_COLLECTION
```

The Phase 6 consumer/runtime integration gate is planned only. The next safe
step, if separately authorized, is a formal preflight for the future read-only
evidence package. No evidence was collected by this plan.
