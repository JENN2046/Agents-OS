# Phase 5 Scope Plan - 2026-06-28

Status: scope plan only; no validator execution, exact-run authorization
receipt, shell execution, YAML parsing, semantic re-evaluation, registry edit,
consumer edit, executable-bit change, Phase 5 evidence collection, or remote
action has been performed.

Notice: This plan opens Phase 5 planning after Phase 4 closed only the
rules-asset and `L1` static registry semantic acceptance track. It plans the
first safe Phase 5 gate: validator exact-run authorization. It is not
authorization to run any validator.

## Authorization

User authorization:

```text
进入 Phase 5 scope plan，先只规划第一个安全 gate：validator exact-run authorization plan。
```

Authorized scope:

- create this Phase 5 scope plan
- identify the first safe Phase 5 gate
- plan the validator exact-run authorization gate
- do not execute validators
- do not create executable-bit changes
- do not parse YAML
- do not edit registry data, consumers, prompts, governance files, or validator
  scripts
- do not start runtime, sync, migration, or remote work

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-4-closeout-receipt-2026-06-28.md` | `216e35687100c2ae3785b765293fc3245921857af20db5dfa8a449f370d1eaec` | `644` | Phase 4 closeout authority. |
| `ops/migration/plans/phase-4-closeout-readiness-plan-2026-06-28.md` | `5f940a0d217f3a295568b21e1ceb487116d4a728e6ad6952b6e96c5b1d7049cc` | `644` | Phase 5 gates source. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Validation boundary guidance. |
| `ops/validation/validate-workspace.sh` | `b924ebaa5bf5396ae9b8bb5136cdd4265bfacfe9c11143d45e1fd18a81000ff5` | `644` | Candidate first exact-run script. |
| `ops/validation/validate-extension-manifests.sh` | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4` | `644` | Deferred validator candidate. |
| `ops/validation/validate-no-secrets.sh` | `7bd0222675d7167e3c56f94b0734dcc683a0d4107f398b76c090c7bfcc8e23e6` | `644` | Deferred sensitive-path validator candidate. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Accepted `L1` static registry semantic authority. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Phase 5 Opening Boundary

Phase 5 should start with execution authorization, not execution.

Allowed now:

- plan the exact-run authorization gate
- rank validator candidates by risk
- define preflight, output redaction, failure handling, and receipt requirements
- keep all scripts non-executable

Not allowed now:

- run any validator
- run shell syntax checks
- source scripts
- use `bash -x` or tracing
- change executable bits
- edit scripts to make them safer
- scan private state, logs, caches, broad project trees, or remote systems
- commit, push, sync, release, or deploy

## Validator Candidate Risk Order

| Candidate | Observed behavior | Relative risk | Phase 5 handling |
| --- | --- | --- | --- |
| `ops/validation/validate-workspace.sh` | Checks a fixed list of required workspace paths and a short deferred-warning path list. | Lowest. It is local, fixed-path, and does not use `find`. | First gate candidate. |
| `ops/validation/validate-extension-manifests.sh` | Uses `find ./extensions` and may print extension-like directory paths missing manifests. | Medium. It traverses a scoped tree and can expose paths. | Defer until after workspace validator gate. |
| `ops/validation/validate-no-secrets.sh` | Uses `find .` and prints suspicious paths for secret-like filenames. | Higher. It can reveal sensitive filenames even though it does not print file contents. | Defer until a stronger output-redaction and path-disclosure policy exists. |

## First Safe Gate Decision

| Question | Decision | Reason |
| --- | --- | --- |
| What is the first Phase 5 gate? | `VALIDATOR_EXACT_RUN_AUTHORIZATION_PLAN` | Phase 4 carried validator execution forward as the first explicit gate. |
| Which validator should be planned first? | `ops/validation/validate-workspace.sh` | It is the narrowest script and checks fixed paths only. |
| Should the script be executed by this scope plan? | `NO` | The user requested planning only. |
| Should executable bits be changed? | `NO` | Scripts remain mode `644`; future run, if authorized, can use `bash` without `chmod`. |
| Should output be copied raw into future receipts? | `NO_BY_DEFAULT` | Receipts should prefer counts and summarized labels unless exact output disclosure is authorized. |

## Validator Exact-Run Authorization Plan Shape

A future exact-run authorization plan should name these fields before any run:

| Required field | Planned value or requirement |
| --- | --- |
| Script path | `ops/validation/validate-workspace.sh`. |
| Working directory | `/home/jenn/AGENTS_OS_Workspace`. |
| Invocation style | `bash ops/validation/validate-workspace.sh`; no `chmod`, no sourcing, no tracing. |
| Expected scope | Fixed required-path and deferred-warning path checks listed inside the script. |
| Output policy | Prefer summary counts; do not print file contents; do not expand to private-state or secret values. |
| Failure policy | Non-zero exit should stop the gate and create a failure receipt; no auto-fix without a separate patch plan. |
| Receipt target | A future receipt target must be named before execution. |
| Hash preflight | Phase 4 closeout, this scope plan, validation README, script hash, and registry hash must be stable. |
| Mode preflight | Script should remain `644`; no executable-bit change. |
| Stop condition | Stop if the script hash drifts, the working directory is not exact, or the receipt target already exists. |

## Planned Future Outputs

If separately authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/plans/phase-5-validator-exact-run-authorization-plan-2026-06-28.md` | Plan the exact execution gate for `validate-workspace.sh` without executing it. |
| `ops/migration/receipts/rules-assets-phase-5-validator-exact-run-authorization-receipt-2026-06-28.md` | Record the authorization plan creation and boundaries. |

Only after that, a separate exact-run preflight and exact-run authorization
would be required before any validator execution evidence can be created.

## Future Gate Sequence

| Order | Gate | Status after this plan |
| --- | --- | --- |
| 1 | Validator exact-run authorization plan for `validate-workspace.sh`. | `PLANNED_FIRST` |
| 2 | Validator exact-run preflight for `validate-workspace.sh`. | `DEFERRED` |
| 3 | Exact-run execution evidence for `validate-workspace.sh`. | `DEFERRED_REQUIRES_EXPLICIT_RUN_AUTHORIZATION` |
| 4 | Validator/runtime acceptance review. | `DEFERRED` |
| 5 | Extension-manifest validator authorization. | `DEFERRED` |
| 6 | No-secrets validator authorization with stronger redaction policy. | `DEFERRED_HIGHER_SENSITIVITY` |

## Phase 5 Gates Still Carried Forward

| Gate | Status |
| --- | --- |
| `L2` consumer readiness acceptance | Deferred. |
| Extension loader behavior | Deferred. |
| Governance runtime enforcement | Deferred. |
| Prompt catalog behavior | Deferred. |
| Subjective layer-policy review | Deferred. |
| Registry wording improvement | Deferred. |
| Optional repository descriptions | Deferred. |
| Registry examples/schema validation | Deferred. |
| Maintenance/sync helper planning | Deferred. |
| Runtime/domain/memory/project migration | Deferred or separate track. |
| Remote/operational actions | Forbidden without explicit remote intent and high-risk preflight. |

## Stop Conditions

Stop and request separate authorization before:

- creating the validator exact-run authorization plan
- executing any validator
- running shell syntax checks
- sourcing scripts
- changing executable bits
- editing validator scripts, registry data, consumers, prompts, governance
  files, or README files
- printing full validator output into receipts
- scanning secret/private files beyond an authorized validator scope
- creating maintenance/sync helpers
- starting runtime/domain/memory/project migration
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Planning Result

```text
PHASE_5_SCOPE_PLAN_CREATED_VALIDATOR_EXACT_RUN_AUTHORIZATION_GATE_PLANNED_NO_EXECUTION
```

Phase 5 is opened as a planning track only. The first safe gate is a future
validator exact-run authorization plan for `ops/validation/validate-workspace.sh`.
No validators were executed.
