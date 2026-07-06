# Phase 5 Validator Exact-Run Authorization Plan - 2026-06-28

Status: authorization plan only; no validator execution, shell execution, shell
syntax check, executable-bit change, validator output capture, registry edit,
consumer edit, YAML parsing, semantic re-evaluation, runtime inspection, or
remote action has been performed.

Notice: This plan defines the exact authorization shape for a possible future
run of `ops/validation/validate-workspace.sh`. It does not authorize that run.

## Authorization

User authorization:

```text
自动推进到 validate-workspace.sh exact-run preflight PASS
```

Interpreted scope:

- create this exact-run authorization plan
- create a matching authorization receipt
- perform a read-only exact-run preflight
- stop at preflight `PASS`
- do not execute `validate-workspace.sh`
- do not execute any validator
- do not change executable bits
- do not edit validator scripts or registry data

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-5-scope-plan-2026-06-28.md` | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367` | `644` | Phase 5 scope authority. |
| `ops/migration/receipts/rules-assets-phase-4-closeout-receipt-2026-06-28.md` | `216e35687100c2ae3785b765293fc3245921857af20db5dfa8a449f370d1eaec` | `644` | Phase 4 closeout authority. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Validation execution boundary. |
| `ops/validation/validate-workspace.sh` | `b924ebaa5bf5396ae9b8bb5136cdd4265bfacfe9c11143d45e1fd18a81000ff5` | `644` | Candidate exact-run script. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Accepted `L1` static registry semantic authority. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Exact-Run Candidate

| Field | Planned value |
| --- | --- |
| Script | `ops/validation/validate-workspace.sh` |
| Working directory | `/home/jenn/AGENTS_OS_Workspace` |
| Invocation shape | `bash ops/validation/validate-workspace.sh` |
| Script mode before run | Must remain `644`; no `chmod`. |
| Shell tracing | Not allowed. |
| Sourcing | Not allowed. |
| Arguments | None. |
| Network or remote access | Not allowed. |

## Observed Script Scope

The script checks a fixed list of required workspace paths:

```text
_ROOT_POLICY.md
_DIRECTORY_PRINCIPLES.md
_MIGRATION_MAP.md
control-plane/README.md
control-plane/registry/WORKSPACE_REGISTRY.yaml
runtime/README.md
governance/README.md
governance/SECURITY_BOUNDARIES.md
execution/README.md
extensions/README.md
domains/README.md
state-private/README.md
ops/README.md
labs/README.md
memory/README.md
archive/README.md
```

The script also checks a deferred-warning list:

```text
AGENTS.md
README.md
README.AGENTS_OS.md
```

The future exact-run gate may report:

- required path present or missing labels
- deferred path present or warning-absent labels
- final success/failure summary

It must not print file contents or secret values.

## Output Policy

Future execution evidence should record:

- exit code
- required path present count
- missing required path count
- deferred path present count
- deferred warning absent count
- final summary line
- redacted excerpt only if separately needed

Future receipts should not copy raw output by default. Full raw output may be
recorded only if separately authorized after reviewing path-disclosure risk.

## Failure Policy

| Failure | Required handling |
| --- | --- |
| Preflight input hash drift | Stop before execution authorization. |
| Script mode is not `644` | Stop before execution authorization. |
| Working directory is not exact | Stop before execution authorization. |
| Future evidence or receipt target already exists | Stop before execution authorization. |
| Missing required path discovered by read-only preflight | Stop before execution authorization or require explicit override. |
| Future script exit code is non-zero | Create failure evidence/receipt; do not auto-fix. |
| Future output includes unexpected sensitive-looking data | Stop, redact summary, and request user review. |

## Exact-Run Preflight Requirements

Before any future run, preflight must confirm:

| Check | Required result |
| --- | --- |
| Current working directory | `/home/jenn/AGENTS_OS_Workspace`. |
| Phase 5 scope plan hash | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367`. |
| This authorization plan hash | Stable after creation. |
| Authorization receipt hash | Stable after creation. |
| Validation README hash | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77`. |
| `validate-workspace.sh` hash | `b924ebaa5bf5396ae9b8bb5136cdd4265bfacfe9c11143d45e1fd18a81000ff5`. |
| `validate-workspace.sh` mode | `644`; not executable. |
| Registry hash | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d`. |
| Required paths | Present in read-only path existence check. |
| Future execution evidence target | Absent. |
| Future execution receipt target | Absent. |

## Planned Future Outputs

If a future exact-run is separately authorized, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-5-validate-workspace-exact-run-evidence-2026-06-28.md` | Record exact-run evidence for `validate-workspace.sh`. |
| `ops/migration/receipts/rules-assets-phase-5-validate-workspace-exact-run-receipt-2026-06-28.md` | Record exact-run authorization, command shape, exit code, summarized output, and limits. |

This plan does not create those future execution outputs.

## Stop Conditions

Stop and request separate authorization before:

- executing `bash ops/validation/validate-workspace.sh`
- executing any validator
- running shell syntax checks
- sourcing scripts
- using shell tracing
- changing executable bits
- editing validator scripts, registry data, consumers, prompts, governance
  files, or README files
- printing raw validator output into receipts
- creating execution evidence or execution receipt
- running other validators
- scanning private state, logs, caches, full project trees, or remote systems
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Planning Result

```text
PHASE_5_VALIDATE_WORKSPACE_EXACT_RUN_AUTHORIZATION_PLAN_CREATED_NO_EXECUTION
```

The exact-run authorization shape for `validate-workspace.sh` is planned. The
script has not been executed.
