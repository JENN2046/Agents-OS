# Phase 5 Validate Extension Manifests Exact-Run Evidence - 2026-06-28

Status: exact-run evidence collected; `PASS`; counts/redacted output policy
applied.

Notice: This evidence records the authorized exact run of
`ops/validation/validate-extension-manifests.sh`. It records counts and
redacted output metadata only. It does not grant extension manifest validator
acceptance, extension loader acceptance, broader validator/runtime acceptance,
consumer activation, registry edits, maintenance/sync behavior, or remote
operations.

## Authorization

User authorization:

```text
权 validate-extension-manifests.sh exact-run，并继续采用 counts/redacted 输出策略。
```

Interpreted as explicit authorization to execute:

```text
bash ops/validation/validate-extension-manifests.sh
```

Authorized scope:

- execute `validate-extension-manifests.sh` once from
  `/home/jenn/AGENTS_OS_Workspace`
- keep the script non-executable and invoke it through `bash`
- capture counts/redacted output only
- create exact-run evidence and receipt
- do not copy full relative paths into evidence or receipt
- do not execute any other validator
- do not edit extension files, manifests, registry data, consumers, or scripts

## Inputs Rechecked Before Execution

| Input | SHA-256 | Mode | Result |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-5-validate-extension-manifests-exact-run-authorization-plan-2026-06-28.md` | `7bb2b97c5405b5c37ef8c2a76841d8d9012b4311dff50967cffecdc560db689a` | `644` | Stable. |
| `ops/migration/inventory/phase-5-validate-extension-manifests-exact-run-preflight-evidence-2026-06-28.md` | `cd03bb67c8d795cc929f015b28bb7014d9290639487d1ee3c1548f1a1ff20793` | `644` | Stable. |
| `ops/migration/receipts/rules-assets-phase-5-validate-extension-manifests-exact-run-preflight-receipt-2026-06-28.md` | `ede3a6bec8207b08fc5fe02b5578b6396896c8880f0521c6f2109b1be51456b9` | `644` | Stable. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Stable. |
| `ops/validation/validate-extension-manifests.sh` | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4` | `644` | Stable; not executable. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Stable. |
| This evidence target | n/a | n/a | Target was absent before creation. |
| Matching execution receipt target | n/a | n/a | Target was absent before creation. |

Workspace Git state: not a Git repository.

## Exact-Run Command

| Field | Value |
| --- | --- |
| Working directory | `/home/jenn/AGENTS_OS_Workspace` |
| Command | `bash ops/validation/validate-extension-manifests.sh` |
| Arguments | None |
| Shell tracing | Not used |
| Sourcing | Not used |
| `chmod` | Not used |
| Raw output copied | No |

## Counts/Redacted Output Summary

| Output field | Value |
| --- | ---: |
| Validator exit code | `0` |
| Result | `PASS` |
| Total non-empty output lines | `2` |
| Started line count | `1` |
| Complete line count | `1` |
| Failure summary line count | `0` |
| Missing manifest count | `0` |
| Relative path output lines | `0` |
| Secret-like output hits | `0` |

Raw relative path output was not copied into this evidence. The run emitted no
missing-manifest relative path lines.

## Post-Run State

| Check | Result |
| --- | --- |
| Script hash after run | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4` |
| Script mode after run | `644` |
| Script executable bit after run | `false` |
| Registry hash after run | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` |

## Wrapper Notes

| Event | Status |
| --- | --- |
| Initial command wrapper attempt | Failed during shell quoting before validator execution; no validator result was recorded from that attempt. |
| Authorized exact command invocation | Completed and reported validator `exit_code=0`. |
| Post-summary wrapper status | A shell wrapper syntax error occurred after the counts/redacted summary was emitted. A separate read-only follow-up check confirmed script hash, mode, and executable-bit state without rerunning the validator. |

## Not Performed

| Action | Status |
| --- | --- |
| Other validator execution | Not performed. |
| Full relative path capture | Not performed. |
| Raw validator output copied to evidence | Not performed. |
| Shell syntax validation | Not performed. |
| Sourcing scripts | Not performed. |
| Shell tracing | Not performed. |
| Executable-bit changes | Not performed. |
| Manifest creation or repair | Not performed. |
| Extension file edits | Not performed. |
| Registry edits or parsing | Not performed. |
| Consumer edits | Not performed. |
| Runtime behavior acceptance | Not performed. |
| Remote, branch, release, deploy, or sync actions | Not performed. |

## Evidence Result

```text
PHASE_5_VALIDATE_EXTENSION_MANIFESTS_EXACT_RUN_EVIDENCE_COLLECTED_PASS_COUNTS_REDACTED
```

The authorized exact run of `validate-extension-manifests.sh` completed with
validator exit code `0`. No missing manifest lines were emitted.
