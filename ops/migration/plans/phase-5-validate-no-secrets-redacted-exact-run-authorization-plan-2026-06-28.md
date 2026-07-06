# Phase 5 Validate No Secrets Redacted Exact-Run Authorization Plan - 2026-06-28

Status: authorization plan only; no validator execution, exact-run preflight,
shell execution, shell syntax check, executable-bit change, suspicious-path
scan, validator output capture, registry edit, consumer edit, runtime
inspection, maintenance/sync action, or remote action has been performed.

Notice: This plan defines the exact authorization shape for a possible future
redacted run of `ops/validation/validate-no-secrets.sh`. It does not authorize
that run. It also does not grant no-secrets evidence acceptance, all-validator
acceptance, broader validator/runtime acceptance, consumer activation,
credential handling approval, or remote/operational action.

## Authorization

User authorization:

```text
进入 Phase 5 下一个 gate，规划 validate-no-secrets.sh 的 redacted exact-run authorization。
```

Authorized scope:

- create this redacted exact-run authorization plan
- plan the next Phase 5 safety gate after extension-manifest validator `E1`
  evidence acceptance closeout
- define future preflight, output redaction, failure, and receipt boundaries for
  `validate-no-secrets.sh`
- do not perform the exact-run preflight in this step
- do not execute `validate-no-secrets.sh`
- do not execute any validator
- do not run shell syntax checks
- do not change executable bits
- do not inspect suspicious paths
- do not edit validator scripts, registry data, consumers, prompts, governance
  files, README files, or workspace files

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-5-scope-plan-2026-06-28.md` | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367` | `644` | Phase 5 scope authority. |
| `ops/migration/receipts/rules-assets-phase-5-extension-manifest-validator-evidence-acceptance-review-closeout-receipt-2026-06-28.md` | `ab0abbad7db385449e8ceb3079f3a2694a8ac42cfcf22185ae6fa612b0b41391` | `644` | Prior `E1` extension-manifest evidence acceptance closeout. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Validation execution and output boundary. |
| `ops/validation/validate-no-secrets.sh` | `7bd0222675d7167e3c56f94b0734dcc683a0d4107f398b76c090c7bfcc8e23e6` | `644` | Candidate redacted exact-run script. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Accepted `L1` static registry semantic authority. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Gate Decision

| Question | Decision | Reason |
| --- | --- | --- |
| Is this the next Phase 5 validator gate after extension-manifest `E1` closeout? | `YES_PLAN_ONLY` | Workspace validator and extension-manifest validator evidence gates have been closed locally; no-secrets remains the deferred higher-sensitivity validator. |
| Should this plan authorize execution? | `NO` | The user requested planning only. |
| Should this plan authorize exact-run preflight? | `NO` | Preflight is the next separate safe step. |
| Is raw script output allowed in future evidence or receipts? | `NO` | The script can print sensitive filenames through `suspicious_path:` lines. |
| Should executable bits be changed? | `NO` | The script remains mode `644`; a future run can use `bash` without `chmod`. |

## Exact-Run Candidate

| Field | Planned value |
| --- | --- |
| Script | `ops/validation/validate-no-secrets.sh` |
| Working directory | `/home/jenn/AGENTS_OS_Workspace` |
| Invocation shape | `bash ops/validation/validate-no-secrets.sh` |
| Output handling | Future run must capture stdout/stderr in-process and emit only redacted counts into evidence/receipt. |
| Script mode before run | Must remain `644`; no `chmod`. |
| Shell tracing | Not allowed. |
| Sourcing | Not allowed. |
| Arguments | None. |
| Network or remote access | Not allowed. |

## Observed Script Scope

The script is a path-only suspicious filename scanner. It:

- starts from the current workspace root with `find .`
- searches for file names containing these patterns:

```text
.env
.env.
config.env
id_rsa
id_ed25519
credentials.json
token.json
.pem
.key
.p12
.pfx
```

- skips files ending with `.example` or `.template`
- skips paths matching `README.AGENTS_OS.md`
- prints `suspicious_path: <path>` for each matched path
- exits `1` if any suspicious path is found
- exits `0` only when no suspicious paths are found

The script does not intentionally read file contents or print secret values.
Its main disclosure risk is filename/path output, which can itself be
sensitive.

## Redacted Output Policy

Future execution evidence must record only:

- exit code
- result label: `PASS_REDACTED` or `FAIL_REDACTED`
- total non-empty output line count
- started line count
- pass summary line count
- failure summary line count
- `suspicious_path` line count
- redaction status: `raw_suspicious_paths_redacted=true`
- secret-like output hit count after in-memory scan
- script hash and mode after run

Future execution evidence and receipts must not record:

- full `suspicious_path:` lines
- full file paths or filenames discovered by the validator
- raw validator output
- file contents
- secret values
- shell trace output

If the future run reports suspicious paths, the failure evidence should still
use counts and redacted categories only unless the user separately authorizes
full path disclosure.

## Redacted Wrapper Requirements

A future exact run, if separately authorized, should execute the script once and
capture output without printing raw output. The wrapper may compute counts from
the captured output, then discard the raw output.

Required wrapper behavior:

| Requirement | Reason |
| --- | --- |
| Capture stdout/stderr instead of streaming raw output. | Prevent `suspicious_path:` lines from appearing in terminal logs or receipts. |
| Count `^suspicious_path: ` lines without copying them. | Preserve validation result while redacting filenames. |
| Count expected start/pass/failure summary lines. | Allow result consistency checks without raw output. |
| Scan captured output in memory for secret-like shapes and record count only. | Detect unexpected output risk without persisting values. |
| Discard captured raw output after summarization. | Avoid leaving sensitive paths in artifacts. |
| Use no shell tracing. | Avoid leaking captured variables or raw output. |

## Failure Policy

| Failure | Required handling |
| --- | --- |
| Preflight input hash drift | Stop before execution authorization. |
| Script mode is not `644` | Stop before execution authorization. |
| Working directory is not exact | Stop before execution authorization. |
| Future preflight/evidence/receipt target already exists | Stop before execution authorization. |
| Redacted wrapper cannot be expressed without printing raw output | Stop before execution authorization. |
| Future script exit code is non-zero | Create redacted failure evidence/receipt; do not auto-fix, delete, rename, or move suspicious files. |
| Future output includes unexpected secret-like values | Record count only, do not copy value, and request user review. |
| Future wrapper itself errors before validator result is known | Create wrapper-failure evidence/receipt; do not infer validator result. |

## Exact-Run Preflight Requirements

Before any future run, a separate preflight must confirm:

| Check | Required result |
| --- | --- |
| Current working directory | `/home/jenn/AGENTS_OS_Workspace`. |
| Phase 5 scope plan hash | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367`. |
| Extension-manifest `E1` acceptance closeout hash | `ab0abbad7db385449e8ceb3079f3a2694a8ac42cfcf22185ae6fa612b0b41391`. |
| This authorization plan hash | Stable after creation. |
| Validation README hash | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77`. |
| `validate-no-secrets.sh` hash | `7bd0222675d7167e3c56f94b0734dcc683a0d4107f398b76c090c7bfcc8e23e6`. |
| `validate-no-secrets.sh` mode | `644`; not executable. |
| Registry hash | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d`. |
| Raw path disclosure policy | `FORBIDDEN_BY_DEFAULT`. |
| Redacted wrapper plan | Present and does not print raw validator output. |
| Future preflight evidence target | Absent. |
| Future preflight receipt target | Absent. |
| Future execution evidence target | Absent. |
| Future execution receipt target | Absent. |

The preflight must not execute the validator and must not perform a suspicious
path scan.

## Planned Future Outputs

If separately authorized for preflight, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-5-validate-no-secrets-redacted-exact-run-preflight-evidence-2026-06-28.md` | Record read-only redacted exact-run preflight evidence for `validate-no-secrets.sh`. |
| `ops/migration/receipts/rules-assets-phase-5-validate-no-secrets-redacted-exact-run-preflight-receipt-2026-06-28.md` | Record preflight result and stop at preflight `PASS` or failure. |

If separately authorized for execution after preflight, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-5-validate-no-secrets-redacted-exact-run-evidence-2026-06-28.md` | Record redacted exact-run evidence for `validate-no-secrets.sh`. |
| `ops/migration/receipts/rules-assets-phase-5-validate-no-secrets-redacted-exact-run-receipt-2026-06-28.md` | Record command shape, exit code, redacted counts, failure policy, and limits. |

This plan does not create those future outputs.

## Acceptance Limits

Even if a future redacted exact run passes, it would support only a later
no-secrets validator evidence review. It would not by itself grant:

- guarantee that no secrets exist in file contents
- full credential audit acceptance
- all-validator acceptance
- broader validator/runtime acceptance
- consumer activation
- registry edits or registry semantic changes
- deletion, quarantine, or repair of suspicious files
- remote, release, deploy, sync, branch, commit, push, or operational action

## Stop Conditions

Stop and request separate authorization before:

- performing exact-run preflight
- executing `bash ops/validation/validate-no-secrets.sh`
- executing any validator
- running shell syntax checks
- sourcing scripts
- using shell tracing
- changing executable bits
- printing or storing full `suspicious_path:` output
- listing suspicious files or paths
- reading file contents from suspicious paths
- deleting, moving, renaming, quarantining, or repairing suspicious files
- editing validator scripts, registry data, consumers, prompts, governance
  files, README files, or workspace files
- creating execution evidence or execution receipt
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Planning Result

```text
PHASE_5_VALIDATE_NO_SECRETS_REDACTED_EXACT_RUN_AUTHORIZATION_PLAN_CREATED_NO_EXECUTION
```

The redacted exact-run authorization shape for `validate-no-secrets.sh` is
planned. The script has not been executed, no suspicious-path scan has been
performed, and no exact-run preflight has been performed.
