# Phase 4 Scope Plan - 2026-06-28

Status: scope plan only; no Phase 4 execution, validation, scanning, parsing, or
validator run has been performed.

Notice: This plan defines possible Phase 4 work after Phase 3 closed the
rules-asset validation gate. It is not authorization to execute validators, run
new scans, parse files, source scripts, change executable bits, create
maintenance/sync helpers, perform integration changes, or take remote, branch,
release, deploy, secret, private-state, log, cache, runtime, or
project-repository actions.

## Goal

Define a narrow, staged Phase 4 scope for work that Phase 3 explicitly did not
claim:

1. validator runtime behavior
2. JSON Schema semantic validation
3. registry business-rule validation
4. consumer integration evidence
5. maintenance/sync helper planning
6. runtime/domain/memory/project migration boundaries

Phase 4 should stay local, reversible, package-based, and evidence-driven.

## Evidence Used

| Evidence | Path | Observed fact |
| --- | --- | --- |
| Phase 3 validation scope plan | `ops/migration/plans/phase-3-validation-scope-plan-2026-06-28.md` | Defines completed Packages A-E and excluded areas. |
| Phase 3 validation evidence | `ops/migration/inventory/phase-3-validation-evidence-2026-06-28.md` | Records A-E results and remaining non-validated areas. |
| Phase 3 validation receipt | `ops/migration/receipts/rules-assets-phase-3-validation-receipt-2026-06-28.md` | Confirms A-E completed without validator runtime execution. |
| Phase 3 closeout review | `ops/migration/inventory/phase-3-closeout-review-2026-06-28.md` | States Phase 3 can close for the rules-asset validation track. |
| Phase 3 closeout receipt | `ops/migration/receipts/rules-assets-phase-3-closeout-receipt-2026-06-28.md` | States Phase 4, validator execution, integration validation, maintenance/sync planning, or remote-adjacent work require separate authorization. |

## Phase 4 Scope Boundary

Phase 4 should not be treated as a single execution pass. It should be split into
small, separately authorized packages.

In scope for planning:

- identify candidate packages
- define required preflight checks
- define evidence and receipt outputs
- define stop conditions
- define what remains forbidden without later authorization

Out of scope for this plan:

- running any validator
- running new scans
- parsing additional files
- changing executable bits
- creating maintenance/sync helpers
- changing registry data or consumers
- moving runtime, domain, memory, private-state, or project repositories
- touching remote branches, releases, deployments, sync targets, or external
  services

## Candidate Phase 4 Packages

### Package A - Consumer Integration Evidence Plan

Risk: low to medium.

Purpose:

- map declared consumers to current local evidence
- distinguish documented consumers from implemented consumers
- avoid changing consumers

Candidate evidence:

| Consumer area | Candidate files or surfaces | Planned handling |
| --- | --- | --- |
| Registry consumer/readiness | `ops/migration/inventory/registry-consumer-readiness-evidence-2026-06-28.md`, `control-plane/registry/README.md`, `ops/validation/validate-workspace.sh` | Read-only evidence comparison. |
| Prompt catalogs | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, `control-plane/prompts/reference/legacy-listed-prompts.md` | Confirm catalog/reference role only. |
| Governance authority | `governance/SECURITY_BOUNDARIES.md`, `_ROOT_POLICY.md`, `_DIRECTORY_PRINCIPLES.md` | Confirm authority references, not runtime enforcement. |
| Validation execution authorization | `control-plane/templates/validation/validation-execution-authorization.template.md`, `ops/validation/README.md` | Confirm execution still requires exact authorization. |

Allowed output:

- evidence table only
- no consumer edits
- no validator execution

### Package B - Registry Semantic Rules Plan

Risk: medium.

Purpose:

- define semantic checks for `control-plane/registry/WORKSPACE_REGISTRY.yaml`
- decide which checks are warnings versus hard failures
- keep this as a plan until explicitly authorized

Candidate semantic checks:

| Rule family | Example check | Execution status in this plan |
| --- | --- | --- |
| Required top-level keys | Expected registry sections exist. | Planned only. |
| Path policy | Root and governance registry copies remain absent unless explicitly approved. | Planned only. |
| Permission defaults | Forbidden capabilities remain default-denied. | Planned only. |
| Consumer declarations | Declared consumers are classified as documented, static, or implemented. | Planned only. |
| Example boundaries | Example registry files stay example-only. | Planned only. |

Allowed output:

- future semantic-rule checklist
- no registry edits
- no validator execution

### Package C - JSON Schema Semantic Validation Plan

Risk: medium.

Purpose:

- decide whether schema validation should be performed locally
- identify which instance files may be validated against which schema
- avoid fetching external schemas or dependencies

Candidate pair:

| Schema | Candidate instance | Status |
| --- | --- | --- |
| `control-plane/contracts/jenn-extension.manifest.schema.json` | `control-plane/templates/extensions/jenn-extension.manifest.example.json` | Candidate only; not validated in this plan. |

Open planning questions:

- whether local Python has an already available JSON Schema validator
- whether missing validator dependency should block or remain deferred
- whether schema validation should be warning-only or hard-fail

Allowed output:

- future validation plan
- no dependency install
- no schema validation during this scope-plan step

### Package D - Validator Execution Authorization Plan

Risk: high.

Purpose:

- define the gate before any `ops/validation/*.sh` script can be executed
- require exact working directory, exact script path, exact scope, expected
  output handling, and receipt location

Candidate scripts:

```text
ops/validation/validate-extension-manifests.sh
ops/validation/validate-no-secrets.sh
ops/validation/validate-workspace.sh
```

Required before any execution:

| Required item | Reason |
| --- | --- |
| Exact script path | Prevent accidental wider execution. |
| Exact working directory | Prevent scanning outside intended scope. |
| Exact input scope | Prevent private/runtime/project traversal. |
| Output redaction policy | Prevent secret or private-state disclosure. |
| Failure handling policy | Decide whether warnings block later work. |
| Receipt target | Preserve evidence and rollback path. |

Default decision:

- do not execute validators in Phase 4 unless a separate exact-run authorization
  names the script and scope

### Package E - Maintenance/Sync Helper Planning

Risk: high.

Purpose:

- plan, but not create or run, any maintenance/sync helper
- keep remote, copy, move, mirror, and sync behavior outside default scope

Current deferred target:

```text
ops/maintenance/sync-upstream-vcp.sh
```

Planning rules:

- helper remains absent by default
- no sync command examples should be made copy-ready
- no remote target, branch, release, or deployment behavior should be implied
- any future helper must have dry-run, path allowlist, secret exclusion, and
  receipt behavior before implementation

### Package F - Runtime/Project Migration Boundary Plan

Risk: high.

Purpose:

- define what is not part of the rules-asset track
- prepare separate migration plans for runtime, domains, memory, private state,
  archives, or full project repositories only if explicitly requested

Excluded by default:

```text
runtime/
domains/
memory/
state-private/
archive/
governance/codex-router/
node_modules/
active .env or credential files
```

Allowed output:

- boundary plan only
- no file moves
- no repository migration
- no private-state reads

## Suggested Phase 4 Order

| Order | Package | Reason |
| ---: | --- | --- |
| 1 | Package A - Consumer Integration Evidence Plan | Lowest execution risk; clarifies what is documented versus implemented. |
| 2 | Package B - Registry Semantic Rules Plan | Defines rules before any semantic check is run. |
| 3 | Package C - JSON Schema Semantic Validation Plan | Prepares schema validation without installing dependencies or running it. |
| 4 | Package D - Validator Execution Authorization Plan | High-risk gate before any functional validator run. |
| 5 | Package E - Maintenance/Sync Helper Planning | High-risk and remote-adjacent; keep late. |
| 6 | Package F - Runtime/Project Migration Boundary Plan | Broadest surface; keep separate from rules-asset track. |

## Planned Phase 4 Outputs

If later authorized package-by-package, Phase 4 may create:

| Output | Purpose |
| --- | --- |
| `ops/migration/plans/phase-4-package-a-consumer-integration-evidence-plan-2026-06-28.md` | Plan read-only consumer evidence checks. |
| `ops/migration/inventory/phase-4-consumer-integration-evidence-2026-06-28.md` | Record evidence only if Package A is separately authorized. |
| `ops/migration/plans/phase-4-package-b-registry-semantic-rules-plan-2026-06-28.md` | Define registry semantic rules before running checks. |
| `ops/migration/plans/phase-4-package-c-json-schema-semantic-validation-plan-2026-06-28.md` | Define schema validation constraints. |
| `ops/migration/plans/phase-4-package-d-validator-execution-authorization-plan-2026-06-28.md` | Define exact-run authorization gates. |
| `ops/migration/plans/phase-4-package-e-maintenance-sync-helper-plan-2026-06-28.md` | Plan maintenance/sync safely without creating helper scripts. |
| `ops/migration/plans/phase-4-package-f-runtime-project-boundary-plan-2026-06-28.md` | Separate runtime/project migration boundaries. |
| `ops/migration/receipts/rules-assets-phase-4-*-receipt-2026-06-28.md` | Record any later authorized Phase 4 package work. |

## Explicit Stop Conditions

Stop and request separate authorization before:

- executing any validator script
- running any additional scan
- parsing any additional file
- installing or fetching dependencies
- changing executable bits
- editing consumers or registry data
- creating maintenance/sync helpers
- reading private-state, active env, cache, log, runtime, or full project trees
- moving, copying, deleting, syncing, committing, pushing, releasing, deploying,
  or touching remote state

## Phase 4 Planning Result

```text
PHASE_4_SCOPE_PLAN_CREATED_NO_EXECUTION
```

This plan only defines possible Phase 4 scope. The recommended next safe action
is Package A planning for consumer integration evidence, still with no execution.
