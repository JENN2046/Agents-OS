# Phase 6 Scope Plan - 2026-06-28

Status: scope plan only; no consumer/runtime integration evidence collection,
consumer rewrite, runtime inspection, validator execution, shell execution,
YAML parsing, secret scan, file repair, migration, sync, or remote action has
been performed.

Notice: This plan opens Phase 6 after Phase 5 closed only the local validation
layer partial evidence track. It plans the first Phase 6 gate:
consumer/runtime integration. It is not authorization to inspect runtime trees,
execute code, change consumers, change registry data, change validator scripts,
create maintenance/sync helpers, or perform remote, branch, release, deploy, or
sync actions.

Terminology note: names such as "consumer", "runtime", and "gate" are local
planning words for this migration track. They do not create permanent
architecture categories or fixed labels.

## Authorization

User authorization:

```text
开 Phase 6 scope plan，先从“consumer/runtime integration gate”开始，继续保持只规划再授权的节奏。
```

Authorized scope:

- create this Phase 6 scope plan
- identify consumer/runtime integration as the first Phase 6 gate
- plan the next authorization step for that gate
- do not collect new integration evidence in this step
- do not execute validators or runtime code
- do not edit consumers, runtime files, registry data, governance files,
  prompts, runbooks, templates, or validator scripts
- do not open private-state, logs, caches, active env files, or full project
  trees
- do not perform commit, push, sync, release, deploy, branch, or remote actions

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-5-closeout-receipt-2026-06-28.md` | `c44d05cd9b6cf6ca3337a372166a247dcd580b78db94afdd6f3fee120556ef36` | `644` | Phase 5 closeout source. |
| `ops/migration/receipts/rules-assets-phase-5-validation-layer-acceptance-review-closeout-receipt-2026-06-28.md` | `d58fb310aac5a373330d7619d8752c7677da54d1f9081e7bcdee43285f7bcaa0` | `644` | Validation-layer local partial closeout. |
| `ops/migration/inventory/phase-4-consumer-integration-evidence-2026-06-28.md` | `6f95fa0bb3aba567585f2c6fb8d76e12c06e3d2317f57ceb03f37a53fd10d9a4` | `644` | Prior static consumer evidence. |
| `ops/migration/receipts/rules-assets-phase-4-consumer-rewrite-review-closeout-receipt-2026-06-28.md` | `c040cb4a33480ec7ebb0f5583485032f7c5977ce50f5eb9bbbc1be836fcf89bd` | `644` | Consumer README/runbook rewrite closeout. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Current validation consumer guidance. |
| `control-plane/runbooks/README.md` | `acc0049db6e621a63498a99d0b102385f07ec3dd9128e4b75d53aaa1ddab787d` | `644` | Current runbook consumer guidance. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Registry authority accepted at static level. |
| `ops/validation/validate-workspace.sh` | `b924ebaa5bf5396ae9b8bb5136cdd4265bfacfe9c11143d45e1fd18a81000ff5` | `644` | Existing validated local script. |
| `ops/validation/validate-extension-manifests.sh` | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4` | `644` | Existing validated local script. |
| `ops/validation/validate-no-secrets.sh` | `7bd0222675d7167e3c56f94b0734dcc683a0d4107f398b76c090c7bfcc8e23e6` | `644` | Existing validated local script. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Phase 6 Opening Boundary

Phase 6 should not jump straight from validator evidence into runtime edits. It
should first ask what "integration" can be proven locally and safely.

Allowed now:

- name consumer/runtime integration as the first Phase 6 gate
- define the next plan-only artifact for that gate
- define what evidence would be collected if separately authorized
- keep runtime behavior, consumer writes, and script execution closed

Not allowed now:

- inspect full runtime, domain, memory, state-private, archive, project, cache,
  log, or env trees
- execute runtime code, validators, loaders, tests, shell scripts, or helper
  commands
- edit consumers, registry data, prompts, governance files, runbooks, templates,
  validator scripts, or runtime files
- create migration, maintenance, sync, copy, move, delete, or remote helpers
- promote Phase 5 local validator evidence into full runtime acceptance

## First Phase 6 Gate

| Question | Phase 6 opening decision | Reason |
| --- | --- | --- |
| What starts Phase 6? | Consumer/runtime integration gate. | Phase 5 explicitly carried consumer/runtime integration forward. |
| Should this scope plan collect integration evidence? | No. | The user asked to keep the plan-then-authorize rhythm. |
| Should runtime directories be opened now? | No. | Runtime inspection is broader than a scope plan and may expose project/private state. |
| Should existing validators be re-run now? | No. | Validator execution already has partial local acceptance; this gate is about integration boundaries. |
| Should consumers be rewritten now? | No. | Any consumer change needs its own patch plan and preflight. |
| What is the next safe artifact? | A consumer/runtime integration gate plan. | It can define exact read surfaces and evidence limits before any collection. |

## Planned Next Artifact

If separately authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/plans/phase-6-consumer-runtime-integration-gate-plan-2026-06-28.md` | Plan exact read surfaces, evidence targets, and stop conditions for consumer/runtime integration evidence. |

That future gate plan should still be plan-only. It should not collect evidence
or change files by itself.

## Candidate Evidence Shape For Later Authorization

If a later evidence package is separately authorized, it should answer these
plain questions:

| Question | Planned evidence style |
| --- | --- |
| Which files currently claim to consume registry, validation, runbook, prompt, or governance assets? | Read listed consumer surfaces only; record file/path evidence and current wording. |
| Which runtime-adjacent surfaces are merely named versus locally present? | Start from top-level presence and already listed evidence; do not deep-read runtime trees without a separate allowlist. |
| Which integration claims are documentation only? | Preserve as limited evidence; do not treat wording as runtime proof. |
| Which integration claims have local implementation logic but no executed behavior proof? | Record script or file existence and hash only; avoid execution. |
| Which areas require a later exact-run or behavior test? | Carry forward with explicit future authorization requirements. |

## Candidate Consumer Surfaces To Plan Precisely Later

The next gate plan may consider these already-known surfaces as candidates:

| Area | Candidate surfaces | Current handling |
| --- | --- | --- |
| Registry authority consumers | `control-plane/registry/README.md`, `control-plane/registry/WORKSPACE_REGISTRY.yaml`, `control-plane/runbooks/add-new-extension.md` | Candidate read-only review. |
| Validation consumers | `ops/validation/README.md`, `ops/validation/validate-workspace.sh`, `ops/validation/validate-extension-manifests.sh`, `ops/validation/validate-no-secrets.sh` | Candidate read-only review; no execution. |
| Runbook consumers | `control-plane/runbooks/README.md` and selected runbooks already migrated under `control-plane/runbooks/` | Candidate read-only review; exact file list must be named later. |
| Prompt catalog consumers | `control-plane/prompts/README.md`, `control-plane/prompts/agents/README.md`, `control-plane/prompts/codex/README.md`, `control-plane/prompts/reference/legacy-listed-prompts.md` | Candidate read-only review; no prompt activation. |
| Governance authority references | `governance/SECURITY_BOUNDARIES.md`, `_ROOT_POLICY.md`, `_DIRECTORY_PRINCIPLES.md`, `_MIGRATION_MAP.md` | Candidate read-only review; no runtime enforcement claim. |
| Runtime-adjacent roots | `runtime/`, `execution/`, `extensions/`, `domains/`, `memory/`, `state-private/`, `archive/`, `labs/`, `governance/codex-router/` | Named only for boundary planning; not opened by this plan. |

## Gate Sequence Draft

Phase 6 should stay staged:

| Order | Gate | Status after this plan |
| --- | --- | --- |
| 1 | Consumer/runtime integration gate plan. | Planned next; not created by this scope plan. |
| 2 | Consumer/runtime integration preflight. | Deferred; should confirm target absence, stable hashes, exact read allowlist, and no execution. |
| 3 | Read-only integration evidence package. | Deferred; should create inventory evidence and receipt only. |
| 4 | Integration evidence review and limited acceptance decision. | Deferred; may only grant a static/local readiness judgment unless runtime behavior is executed later. |
| 5 | Any consumer rewrite patch. | Deferred; requires patch plan, preflight, and separate authorization. |
| 6 | Runtime behavior or loader exact-run gate. | Deferred high-risk; requires exact command, working directory, output policy, and failure policy. |

## Future Preflight Requirements

A future consumer/runtime integration gate plan should require:

| Preflight item | Required result |
| --- | --- |
| Phase 6 scope plan hash stable | Required before the next gate plan. |
| Phase 5 closeout hash stable | Required because it carries Phase 6 gates forward. |
| Phase 4 consumer evidence hash stable | Required because it is the prior static consumer baseline. |
| Existing validator scripts remain mode `644` | Required; no executable-bit changes. |
| Exact future evidence and receipt targets absent | Required to avoid overwriting evidence. |
| Exact read allowlist named | Required before reading beyond already listed surfaces. |
| Runtime/private roots stay closed by default | Required unless a later plan names a narrow read surface. |

## Stop Conditions

Stop and request separate authorization before:

- creating the next consumer/runtime integration gate plan
- collecting new consumer/runtime evidence
- reading runtime internals or broader project trees
- executing validators, loaders, tests, scripts, or runtime code
- parsing additional structured files
- editing consumers, registry data, prompts, governance files, runbooks,
  templates, validator scripts, or runtime files
- changing executable bits
- scanning active env, private-state, logs, caches, credentials, or secret-like
  content
- creating maintenance/sync helpers or copy/move/delete workflows
- committing, pushing, syncing, releasing, deploying, branching, or performing
  remote/external actions

## Planning Result

```text
PHASE_6_SCOPE_PLAN_CREATED_CONSUMER_RUNTIME_INTEGRATION_GATE_PLANNED_NO_EXECUTION
```

Phase 6 is opened as a planning track only. The next safe action is a separate
consumer/runtime integration gate plan that names exact read surfaces and future
evidence outputs before any evidence collection or file change.
