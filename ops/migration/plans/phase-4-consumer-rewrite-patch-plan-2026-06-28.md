# Phase 4 Consumer Rewrite Patch Plan - 2026-06-28

Status: patch plan only; no README, runbook, validator, registry, prompt,
governance, runtime, or consumer files were modified.

Notice: This plan names candidate targets for a possible future consumer rewrite
patch. It is not authorization to edit those targets, execute validators, source
scripts, change executable bits, inspect broader project trees, activate
prompts, change runtime behavior, create maintenance/sync helpers, or perform
remote, branch, release, deploy, secret, private-state, log, cache, runtime, or
project-repository actions.

## Authorization

User authorization:

```text
做 Phase 4 consumer rewrite patch plan，只规划 README/runbook/validator 三类候选目标，不直接改文件。
```

Authorized scope:

- create this patch plan
- classify README, runbook, and validator candidate targets
- plan future preflight, patch boundaries, and receipt output
- do not modify candidate targets
- do not execute validators
- do not inspect broader project trees

## Inputs Rechecked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-4-scope-plan-2026-06-28.md` | `14d2efce1f39ac8a05d0c81aea008e860968e5b736e7876da96bdb603f041fcc` | Rechecked as Phase 4 scope authority. |
| `ops/migration/inventory/phase-4-consumer-integration-evidence-2026-06-28.md` | `6f95fa0bb3aba567585f2c6fb8d76e12c06e3d2317f57ceb03f37a53fd10d9a4` | Rechecked as Package A evidence. |
| `ops/migration/receipts/rules-assets-phase-4-package-a-review-closeout-receipt-2026-06-28.md` | `c2df4c5e617e396cb48837a746179681175c47b78c0b116bc16d948469afb28c` | Rechecked as Package A closeout authority. |
| This plan target | n/a | Target was absent before creation. |
| Workspace Git state | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Candidate Target Decision

| Class | Target | Current evidence | Future patch decision |
| --- | --- | --- | --- |
| README | `ops/validation/README.md` | Mentions `validate-workspace.sh` as not included in the prior validation batch and says it references old paths, while Package A evidence shows the script now exists and includes `control-plane/registry/WORKSPACE_REGISTRY.yaml`. | `PLAN_PATCH`: align status wording; keep execution forbidden without exact approval. |
| README | `control-plane/runbooks/README.md` | Says validation script migration is pending and warns against treating validation paths as existing commands. Validation files now exist as candidates, but execution remains gated. | `PLAN_PATCH`: align wording from "pending migration" to "migrated candidates; execution deferred." |
| README | `control-plane/registry/README.md` | Already states registry data does not authorize consumer integration and names `validate-workspace.sh` as an observed static consumer. | `REFERENCE_ONLY`: no default edit planned; use as wording anchor. |
| Runbook | `control-plane/runbooks/add-new-extension.md` | References the authority registry path and keeps registry writes separately authorized. | `REVIEW_ONLY`: no default edit planned unless future preflight finds conflict with README wording. |
| Runbook | `control-plane/runbooks/onboard-new-agent.md` | No registry or validator consumer evidence found in the scoped search. | `OUT_OF_BATCH`: do not edit in this consumer rewrite batch. |
| Runbook | `control-plane/runbooks/run-codex-task.md` | Contains generic handoff wording for validation run/not-run, not registry consumer evidence. | `OUT_OF_BATCH`: do not edit in this consumer rewrite batch. |
| Validator | `ops/validation/validate-workspace.sh` | Contains local required-path logic and includes `control-plane/registry/WORKSPACE_REGISTRY.yaml`; remains unexecuted. | `PLAN_PATCH_OPTIONAL`: only status/header or narrowly named path-policy comments unless a later authorization permits logic edits. |
| Validator | `ops/validation/validate-extension-manifests.sh` | Existing validation candidate, not registry consumer evidence. | `REFERENCE_ONLY`: no edit in this consumer rewrite batch. |
| Validator | `ops/validation/validate-no-secrets.sh` | Existing validation candidate, not registry consumer evidence. | `REFERENCE_ONLY`: no edit in this consumer rewrite batch. |

## Planned Future Patch Shape

If separately authorized, the smallest useful consumer rewrite patch should use
this order:

1. Update `ops/validation/README.md` so it no longer frames
   `validate-workspace.sh` as outside the current migrated validation index or
   still bound to old registry/security paths.
2. Update `control-plane/runbooks/README.md` so ordinary runbooks know validation
   scripts exist as reviewed candidates while still forbidding execution without
   exact approval.
3. Recheck `control-plane/runbooks/add-new-extension.md` as a runbook candidate;
   patch it only if the README wording update creates a mismatch.
4. Touch `ops/validation/validate-workspace.sh` only if the authorized future
   patch explicitly allows a non-executable, non-runtime script text change.

The default future patch should not change validator behavior. Any validator
logic change must be named separately before the patch starts.

## Future Preflight Required Before Any Patch

| Check | Required result |
| --- | --- |
| This plan exists and hash is stable | Required before patch authorization. |
| Target hashes stable | Recheck all `PLAN_PATCH`, `PLAN_PATCH_OPTIONAL`, and `REVIEW_ONLY` targets before editing. |
| `ops/validation/validate-workspace.sh` mode | Must remain `644`; no executable-bit change. |
| Script execution | Must not execute validators unless a separate exact-run authorization names script, working directory, scope, output policy, and receipt. |
| Secret-like scan | Scan target text before and after any future patch; do not print secret values. |
| Copy-ready command review | Future README/runbook wording must not introduce copy-ready validator commands. |
| Receipt target absence | Future receipt target must be absent before creation. |

## Planned Future Receipt

If a later patch is authorized, create a receipt such as:

```text
ops/migration/receipts/rules-assets-phase-4-consumer-rewrite-patch-receipt-2026-06-28.md
```

The receipt must record:

- exact target files touched
- before and after hashes
- file modes
- whether any validator script was changed
- whether any validator script was executed
- skipped validation and remaining risk

## Explicit Non-Goals

This plan does not admit:

| Area | Reason |
| --- | --- |
| Direct consumer patch | Package A closeout admitted planning only, not direct patching. |
| Validator execution | Requires separate exact-run authorization. |
| Executable-bit changes | Outside scope and default-denied. |
| Extension loader rewrite | Still `documented_only`; broader loader inspection was not authorized. |
| Prompt behavior rewrite | Prompt surfaces are catalog/reference only. |
| Governance runtime enforcement rewrite | Governance docs are authority references, not runtime proof. |
| Registry data rewrite | Not part of this consumer rewrite plan. |
| Maintenance/sync helper creation | Deferred high-risk area. |

## Stop Conditions

Stop and request separate authorization before:

- editing any README, runbook, validator, registry, prompt, governance, runtime,
  or project file
- executing or sourcing any script
- changing executable bits
- adding copy-ready validation commands
- reading active env, credentials, private state, logs, caches, runtime output,
  or full project trees
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Plan Result

```text
PHASE_4_CONSUMER_REWRITE_PATCH_PLAN_CREATED_NO_CONSUMER_CHANGES
```

This plan admits a future, separately authorized README/runbook/validator patch
preflight. It does not authorize the patch itself.
