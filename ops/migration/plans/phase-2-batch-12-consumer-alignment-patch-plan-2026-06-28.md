# Phase 2 Batch 12 Consumer Alignment Patch Plan - 2026-06-28

Status: patch plan only; no consumer files changed.

Notice: This plan covers a narrow local wording and static-validator alignment
after Batch 11. It is not authorization to execute validation scripts, not
authorization to create maintenance/sync helpers, not authorization to change
executable bits, and not authorization for remote, branch, release, deploy,
secret, private-state, log, cache, or runtime actions.

## Goal

Plan a follow-up consumer-alignment patch for the three stale points identified
by Batch 11 evidence:

1. `control-plane/registry/README.md`
2. `control-plane/runbooks/add-new-extension.md`
3. `ops/validation/validate-workspace.sh`

The patch should align wording and static path classification with the Batch 10
authority registry while avoiding broader consumer integration.

## Inputs Already Observed

| Evidence | Path | SHA-256 | Observed fact |
| --- | --- | --- | --- |
| Batch 11 evidence | `ops/migration/inventory/registry-consumer-readiness-evidence-2026-06-28.md` | `0027a932a92d21c3486cfebc7ba514a8d2eb7c59c19edf6e8a398f53b559cb4d` | Names the three consumer-alignment candidates. |
| Batch 11 receipt | `ops/migration/receipts/rules-assets-batch-11-registry-consumer-readiness-receipt-2026-06-28.md` | `9a3fd96329146aff619ca4c766ad522a5c166553007b13256e86232a7989a8be` | Confirms no consumer files were changed in Batch 11. |
| Authority registry | `control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | Registry authority exists and parses as local structured data. |
| Registry README | `control-plane/registry/README.md` | `255d71dffedcbc9415a4f8f62abe70d8d34f3d72eea2055001cc6a278793cc56` | Still has Batch 1-era future-authority wording and broad consumer claims. |
| Add-extension runbook | `control-plane/runbooks/add-new-extension.md` | `5058a5b80d8e383408cd9d4595850a53c00c9b47b33a1fc51f5e9fcae2c8c00c` | Still says registry registration is pending registry-file migration. |
| Workspace validator | `ops/validation/validate-workspace.sh` | `daab2f5ebdcb89d52c39f2c4162edf17079ea607d64ddceba6d7155366c3c87f` | Still lists the authority registry under deferred warning paths. |

## Planned Patch Scope

If later authorized, Batch 12 should modify exactly these consumer files and
create exactly one receipt:

| Planned path | Planned handling |
| --- | --- |
| `control-plane/registry/README.md` | Rewrite stale authority and consumer wording to match Batch 10 and Batch 11 evidence. |
| `control-plane/runbooks/add-new-extension.md` | Separate "registry file exists" from "registry entry/update still needs separate authorization". |
| `ops/validation/validate-workspace.sh` | Move `control-plane/registry/WORKSPACE_REGISTRY.yaml` from deferred warning paths to required paths, keeping the script non-executable. |
| `ops/migration/receipts/rules-assets-batch-12-consumer-alignment-receipt-2026-06-28.md` | Record the authorized local patch and validation results. |

No prompt, governance, extension-loader, registry-data, or maintenance/sync file
should be modified in this batch.

## Planned Alignment Details

### Registry README

Current stale points:

| Current wording area | Problem | Planned resolution |
| --- | --- | --- |
| Purpose and contains sections | Still says authority registry files are future. | State that `WORKSPACE_REGISTRY.yaml` is now present as the authority registry data file. |
| Interfaces | Broad `used_by` wording can be read as proven integration. | Split observed static reference from declared or future consumers. |
| Examples versus authority | Still says `WORKSPACE_REGISTRY.yaml` is reserved for a later authority batch and not created by Batch 1. | State examples remain examples; `WORKSPACE_REGISTRY.yaml` is the active authority data file created by a later authority batch. |
| Validation section | Still describes validators as future migration references. | State validation scripts exist as local files, but execution remains separately authorized. |

Planned final meaning:

- `WORKSPACE_REGISTRY.yaml` exists and is authoritative registry data.
- Example files under `examples/` remain examples only.
- Registry data does not authorize remote actions, validation execution,
  executable-bit changes, permission expansion, or consumer integration.
- Ops validator reference is observed statically.
- Codex prompts, extension loader, and governance layer remain declaration-only
  until direct integration evidence exists.

### Add-Extension Runbook

Current stale points:

| Current wording area | Problem | Planned resolution |
| --- | --- | --- |
| Procedure step 5 | Says validation script migration is pending. | Replace with wording that validation scripts require scoped execution authorization before use. |
| Procedure step 7 | Says registry registration is deferred until registry file migration. | Replace with wording that registry entry updates still need separate authorization even though the registry file exists. |
| Registry Registration section | Mixes registry-file migration with registry-registration readiness. | State the registry file exists, but adding or updating entries is a separate controlled patch. |

Planned final meaning:

- Extension authors may reference the authority registry path.
- Adding or updating registry entries is not automatic.
- Historical source paths remain forbidden.
- Example registry files remain examples only.
- No activation, publication, shell access, release, deploy, or secret access is
  authorized by the runbook wording.

### Workspace Validator

Current stale point:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
```

is listed in `deferred_warning_paths` even though Batch 10 created it as the
authority registry.

Planned resolution:

- Add `control-plane/registry/WORKSPACE_REGISTRY.yaml` to `required_paths`.
- Remove it from `deferred_warning_paths`.
- Keep `AGENTS.md`, `README.md`, and `README.AGENTS_OS.md` as deferred warning
  paths.
- Do not add execution side effects.
- Do not change file mode or executable bit.

Planned final meaning:

- The workspace validator statically expects the authority registry path to
  exist.
- Missing registry becomes a required-path failure if the validator is later
  executed under separate authorization.
- Root README and AGENTS-family files remain advisory/deferred.

## Explicit Non-Goals

- Do not execute `ops/validation/validate-workspace.sh`.
- Do not execute any validation script.
- Do not modify `control-plane/registry/WORKSPACE_REGISTRY.yaml`.
- Do not modify prompt catalog files.
- Do not modify governance files.
- Do not modify extension-loader or extension files.
- Do not create or modify `ops/maintenance/sync-upstream-vcp.sh`.
- Do not create root or governance copies of `WORKSPACE_REGISTRY.yaml`.
- Do not change executable bits.
- Do not perform remote, branch, release, deploy, destructive, copy, move, sync,
  private-state, log, cache, runtime, or secret actions.

## Strict Preflight Before Patch

| Check | Expected result |
| --- | --- |
| Receipt target absence | `ops/migration/receipts/rules-assets-batch-12-consumer-alignment-receipt-2026-06-28.md` does not exist. |
| Plan hash stability | This plan hash is recorded before patch execution. |
| Batch 11 evidence hash stability | Hash remains `0027a932a92d21c3486cfebc7ba514a8d2eb7c59c19edf6e8a398f53b559cb4d`. |
| Batch 11 receipt hash stability | Hash remains `9a3fd96329146aff619ca4c766ad522a5c166553007b13256e86232a7989a8be`. |
| Registry README hash stability | Hash remains `255d71dffedcbc9415a4f8f62abe70d8d34f3d72eea2055001cc6a278793cc56`. |
| Add-extension runbook hash stability | Hash remains `5058a5b80d8e383408cd9d4595850a53c00c9b47b33a1fc51f5e9fcae2c8c00c`. |
| Workspace validator hash stability | Hash remains `daab2f5ebdcb89d52c39f2c4162edf17079ea607d64ddceba6d7155366c3c87f`. |
| Authority registry hash stability | Hash remains `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d`. |
| Authority registry YAML parse | YAML parses with expected top-level keys. |
| Workspace validator mode | File remains non-executable before patch. |
| Deferred targets absence | Maintenance/sync helper, root registry, and governance registry remain absent. |

## Planned Validation After Patch

Use static validation only unless a later authorization explicitly allows more:

| Validation | Method |
| --- | --- |
| Changed file set | Confirm only the three consumer files plus receipt changed. |
| README wording | Confirm stale Batch 1-era authority wording is gone and declaration-only consumers are not overclaimed. |
| Runbook wording | Confirm registry-file migration and registry-entry authorization are no longer conflated. |
| Validator path classification | Confirm registry path is in `required_paths` and not in `deferred_warning_paths`. |
| Validator syntax | Perform syntax-only shell parsing if explicitly allowed in the patch authorization or preflight. |
| File modes | Confirm validator remains non-executable. |
| Authority registry parse | Confirm registry YAML still parses and is not modified. |
| Live-secret scan | Scan changed files and receipt for live-secret patterns. |
| Command-risk scan | Scan changed files and receipt for copy-ready remote, branch, destructive, sync, and validator-execution instructions. |

## Receipt Requirements

If later authorized, the receipt must record:

- exact user authorization
- preflight hashes
- changed files and resulting hashes
- validator mode before and after
- whether syntax-only parsing was run
- whether any validation scripts were executed
- live-secret scan result
- command-risk scan result
- deferred targets that remained absent
- remaining risks and next candidate

## Authorization Needed For Next Step

Before applying this patch, request explicit authorization for:

```text
Authorize Batch 12 consumer-alignment patch: update registry README, add-extension runbook, workspace validator, and create the Batch 12 receipt only; do not execute validators.
```

That authorization still would not allow remote actions, maintenance/sync helper
creation, validation execution, executable-bit changes, prompt/governance/loader
integration, or registry-data changes.
