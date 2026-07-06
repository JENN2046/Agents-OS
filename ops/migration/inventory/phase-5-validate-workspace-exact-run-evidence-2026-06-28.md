# Phase 5 Validate Workspace Exact-Run Evidence - 2026-06-28

Status: exact-run evidence collected; `PASS`.

Notice: This evidence records the explicitly authorized run of
`ops/validation/validate-workspace.sh`. It does not grant broader validator
runtime acceptance, consumer activation, extension loader behavior, governance
runtime enforcement, registry edits, additional validator runs, maintenance/sync
behavior, or remote/operational actions.

## Authorization

User authorization:

```text
授权执行 validate-workspace.sh exact-run
```

Authorized scope:

- execute exactly `bash ops/validation/validate-workspace.sh`
- use working directory `/home/jenn/AGENTS_OS_Workspace`
- do not change executable bits
- do not source the script
- do not use shell tracing
- do not execute other validators
- create exact-run evidence and receipt

## Inputs Rechecked Before Execution

| Input | SHA-256 | Mode | Result |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-5-scope-plan-2026-06-28.md` | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367` | `644` | Stable. |
| `ops/migration/plans/phase-5-validator-exact-run-authorization-plan-2026-06-28.md` | `02171c0895920607d5b074ea7f3fb6976b1ea8d40bf23bc7c1ae44769ecedda5` | `644` | Stable. |
| `ops/migration/receipts/rules-assets-phase-5-validator-exact-run-authorization-receipt-2026-06-28.md` | `1cf2f6f873ecebdbffa122b4a8712679ed81e6f734a99423fe77e053df9f672d` | `644` | Stable. |
| `ops/migration/inventory/phase-5-validate-workspace-exact-run-preflight-evidence-2026-06-28.md` | `7f568abf77ec21b18e810b1018da0f0acf566dd4f5d66f481dad74538a7b4fcb` | `644` | Stable. |
| `ops/migration/receipts/rules-assets-phase-5-validate-workspace-exact-run-preflight-receipt-2026-06-28.md` | `292c2e841013195477fd041d710c983fd296005f06e519af7bffe671c7982d9c` | `644` | Stable. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Stable. |
| `ops/validation/validate-workspace.sh` | `b924ebaa5bf5396ae9b8bb5136cdd4265bfacfe9c11143d45e1fd18a81000ff5` | `644` | Stable; not executable. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Stable. |
| This evidence target | n/a | n/a | Target was absent before execution evidence creation. |
| Matching exact-run receipt target | n/a | n/a | Target was absent before execution. |

## Exact Run

| Field | Result |
| --- | --- |
| Working directory | `/home/jenn/AGENTS_OS_Workspace` |
| Command | `bash ops/validation/validate-workspace.sh` |
| Arguments | None. |
| Script mode during run | `644`. |
| Executable-bit change | Not performed. |
| Sourcing | Not performed. |
| Shell tracing | Not performed. |
| Exit code | `0`. |

## Output Summary

Raw output was not copied into this evidence by default. The summarized output
counts are:

| Output category | Count |
| --- | ---: |
| `required_path_present` | 16 |
| `missing_required_path` | 0 |
| `deferred_path_present` | 0 |
| `deferred_path_warning_absent` | 3 |

Deferred warning paths reported:

```text
AGENTS.md
README.md
README.AGENTS_OS.md
```

Final summary line:

```text
[validate-workspace] required paths present; deferred warnings reported
```

## Interpretation

| Item | Result |
| --- | --- |
| Required workspace path check | `PASS`. |
| Deferred path warnings | `PRESENT_AS_WARNINGS`; not blockers. |
| Validator exact-run result | `PASS_WITH_DEFERRED_WARNINGS`. |
| Broader validator/runtime acceptance | Not granted by this evidence. |

## Not Performed

| Action | Status |
| --- | --- |
| Other validator execution | Not performed. |
| Shell syntax validation | Not performed. |
| Sourcing scripts | Not performed. |
| Shell tracing | Not performed. |
| Executable-bit changes | Not performed. |
| Registry edits | Not performed. |
| Consumer edits | Not performed. |
| Runtime behavior validation beyond this exact script run | Not performed. |
| Extension loader inspection | Not performed. |
| Governance runtime enforcement validation | Not performed. |
| Maintenance/sync helper creation | Not performed. |
| Remote, branch, release, deploy, or sync actions | Not performed. |

## Evidence Result

```text
PHASE_5_VALIDATE_WORKSPACE_EXACT_RUN_EVIDENCE_COLLECTED_PASS_WITH_DEFERRED_WARNINGS
```

`validate-workspace.sh` was executed exactly as authorized and exited `0`.
Required paths were present. Deferred warning paths remain absent as warnings.
