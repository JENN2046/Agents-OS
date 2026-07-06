# Phase 5 Validate Extension Manifests Exact-Run Authorization Plan - 2026-06-28

Status: authorization plan only; no validator execution, exact-run preflight,
shell execution, shell syntax check, executable-bit change, validator output
capture, registry edit, consumer edit, YAML parsing, semantic re-evaluation,
runtime inspection, maintenance/sync action, or remote action has been
performed.

Notice: This plan defines the exact authorization shape for a possible future
run of `ops/validation/validate-extension-manifests.sh`. It does not authorize
that run. It also does not grant extension manifest validator acceptance,
extension loader acceptance, broader validator/runtime acceptance, or consumer
activation.

## Authorization

User authorization:

```text
进入 Phase 5 的下一个安全 gate，规划 validate-extension-manifests.sh exact-run authorization，仍然先只做 plan。
```

Authorized scope:

- create this exact-run authorization plan
- plan the next Phase 5 safety gate after workspace validator `V1` partial
  acceptance closeout
- define future preflight, output, failure, and receipt boundaries for
  `validate-extension-manifests.sh`
- do not perform the exact-run preflight in this step
- do not execute `validate-extension-manifests.sh`
- do not execute any validator
- do not change executable bits
- do not edit validator scripts, registry data, consumers, prompts, governance
  files, README files, or extension files

## Inputs Rechecked

| Input | SHA-256 | Mode | Use |
| --- | --- | --- | --- |
| `ops/migration/plans/phase-5-scope-plan-2026-06-28.md` | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367` | `644` | Phase 5 scope authority. |
| `ops/migration/receipts/rules-assets-phase-5-workspace-validator-partial-acceptance-review-closeout-receipt-2026-06-28.md` | `ecc1060c3a0453d28c087de096bb2d7ce640f13df5c35beb63c1fbbc3f570a07` | `644` | Prior safe gate closeout. |
| `ops/migration/receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md` | `2d67d70374eb168f78f6e91210d64f6a7aab7124d310363d6a745b49543f9963` | `644` | Validation script migration receipt. |
| `ops/migration/receipts/rules-assets-phase-3-validation-receipt-2026-06-28.md` | `d47ce57ca5671abd8306ed115515e55ab6df00c085d9a7de452ec474524bf0d4` | `644` | Prior syntax-only validation receipt. |
| `ops/validation/README.md` | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77` | `644` | Validation execution and output boundary. |
| `ops/validation/validate-extension-manifests.sh` | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4` | `644` | Candidate exact-run script. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | `644` | Accepted `L1` static registry semantic authority. |
| `extensions/` | n/a | directory | Present; top-level observed child is `extensions/vcp-toolbox-jenn`. |
| This plan target | n/a | n/a | Target was absent before creation. |
| Workspace Git state | n/a | n/a | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Gate Decision

| Question | Decision | Reason |
| --- | --- | --- |
| Is this the next safe Phase 5 gate after workspace validator `V1` closeout? | `YES_PLAN_ONLY` | The Phase 5 scope plan deferred this validator until after the workspace validator gate. That gate is now closed as `V1` local fixed-path partial acceptance. |
| Should this plan authorize execution? | `NO` | The user requested planning only. |
| Should this plan authorize exact-run preflight? | `NO` | Preflight is the next separate safe step. |
| Should output paths be copied raw into future receipts? | `NO_BY_DEFAULT` | The script may print extension-like relative paths; path disclosure should be summarized unless separately authorized. |
| Should executable bits be changed? | `NO` | The script remains mode `644`; a future run can use `bash` without `chmod`. |

## Exact-Run Candidate

| Field | Planned value |
| --- | --- |
| Script | `ops/validation/validate-extension-manifests.sh` |
| Working directory | `/home/jenn/AGENTS_OS_Workspace` |
| Invocation shape | `bash ops/validation/validate-extension-manifests.sh` |
| Script mode before run | Must remain `644`; no `chmod`. |
| Shell tracing | Not allowed. |
| Sourcing | Not allowed. |
| Arguments | None. |
| Network or remote access | Not allowed. |

## Observed Script Scope

The script is a workspace-relative extension manifest checker. It:

- starts from `./extensions`
- searches directories from depth 2 through depth 5
- considers names matching extension, pack, Bridge, or bridge patterns
- skips placeholder container directories such as `plugin-packs`,
  `agent-packs`, `admin-extensions`, `bridge-plugins`, `templates`, `docs`,
  and `examples`
- accepts `jenn-extension.manifest.json` as the manifest file
- skips pure placeholder directories that contain only doorplate files
- prints `extension_missing_manifest: <relative-path>` for concrete
  extension-like directories missing a manifest
- exits `1` if any concrete extension-like directory is missing a manifest
- exits `0` only when no missing manifest is detected

The script does not intentionally print file contents or secret values. Its
main disclosure risk is relative path output.

## Output Policy

Future execution evidence should record:

- exit code
- candidate directory count if gathered during authorized preflight
- missing manifest count
- skipped placeholder/container count if gathered
- final summary line
- whether relative paths were emitted

Future receipts should not copy raw validator output by default. If the script
reports missing manifests, the failure receipt should prefer counts and a
redacted or summarized path-disclosure note unless the user separately
authorizes full relative path capture.

## Failure Policy

| Failure | Required handling |
| --- | --- |
| Preflight input hash drift | Stop before execution authorization. |
| Script mode is not `644` | Stop before execution authorization. |
| Working directory is not exact | Stop before execution authorization. |
| `extensions/` is absent | Stop before execution authorization; otherwise the script could pass without checking real extension assets. |
| Future preflight/evidence/receipt target already exists | Stop before execution authorization. |
| Future candidate discovery would require printing full relative paths | Stop unless path disclosure is explicitly authorized. |
| Future script exit code is non-zero | Create failure evidence/receipt; do not auto-fix or create manifests. |
| Future output includes unexpected sensitive-looking data | Stop, redact summary, and request user review. |

## Exact-Run Preflight Requirements

Before any future run, a separate preflight must confirm:

| Check | Required result |
| --- | --- |
| Current working directory | `/home/jenn/AGENTS_OS_Workspace`. |
| Phase 5 scope plan hash | `4111f2cccc662a259f192e48c3e0df4313174fcf05a58adb129c819aa1210367`. |
| Workspace validator partial acceptance closeout hash | `ecc1060c3a0453d28c087de096bb2d7ce640f13df5c35beb63c1fbbc3f570a07`. |
| This authorization plan hash | Stable after creation. |
| Validation README hash | `b1d265aabc133c71f4c00ab16243f7a587e07d991f62870dea894364b7c3ec77`. |
| `validate-extension-manifests.sh` hash | `5b4a6cf5ddc9fa32280a353f728a1482f04dd9de939f3818d861993c219d5ac4`. |
| `validate-extension-manifests.sh` mode | `644`; not executable. |
| Registry hash | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d`. |
| `extensions/` directory | Present. |
| Path disclosure policy | Confirm whether future evidence may include full relative paths or counts only. |
| Future preflight evidence target | Absent. |
| Future preflight receipt target | Absent. |
| Future execution evidence target | Absent. |
| Future execution receipt target | Absent. |

The preflight may use read-only file metadata and scoped `extensions/`
inspection only. It must not execute the validator.

## Planned Future Outputs

If separately authorized for preflight, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-5-validate-extension-manifests-exact-run-preflight-evidence-2026-06-28.md` | Record read-only exact-run preflight evidence for `validate-extension-manifests.sh`. |
| `ops/migration/receipts/rules-assets-phase-5-validate-extension-manifests-exact-run-preflight-receipt-2026-06-28.md` | Record preflight result and stop at preflight `PASS` or failure. |

If separately authorized for execution after preflight, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-5-validate-extension-manifests-exact-run-evidence-2026-06-28.md` | Record exact-run evidence for `validate-extension-manifests.sh`. |
| `ops/migration/receipts/rules-assets-phase-5-validate-extension-manifests-exact-run-receipt-2026-06-28.md` | Record exact-run authorization, command shape, exit code, summarized output, and limits. |

This plan does not create those future outputs.

## Acceptance Limits

Even if a future exact run passes, it would support only a later
extension-manifest validator evidence review. It would not by itself grant:

- all-validator acceptance
- broader validator/runtime acceptance
- extension loader acceptance
- governance runtime enforcement acceptance
- consumer activation
- registry edits or registry semantic changes
- manifest schema acceptance beyond previously recorded JSON/schema gates
- remote, release, deploy, sync, or operational action

## Stop Conditions

Stop and request separate authorization before:

- performing exact-run preflight
- executing `bash ops/validation/validate-extension-manifests.sh`
- executing any validator
- running shell syntax checks
- sourcing scripts
- using shell tracing
- changing executable bits
- editing validator scripts, registry data, consumers, prompts, governance
  files, README files, or extension files
- printing full relative path output into receipts
- creating execution evidence or execution receipt
- running `validate-no-secrets.sh`
- scanning private state, logs, caches, full project trees, or remote systems
- creating maintenance/sync helpers
- taking remote, branch, release, deploy, sync, commit, push, delete, move, or
  destructive actions

## Planning Result

```text
PHASE_5_VALIDATE_EXTENSION_MANIFESTS_EXACT_RUN_AUTHORIZATION_PLAN_CREATED_NO_EXECUTION
```

The exact-run authorization shape for `validate-extension-manifests.sh` is
planned. The script has not been executed, and no exact-run preflight has been
performed.
