# Phase 2 Batch 10 Registry Authority Patch Plan - 2026-06-28

Status: patch plan only; no registry file created.

Notice: This document plans a future registry authority patch. It is not
migration authorization, not authorization to create
`control-plane/registry/WORKSPACE_REGISTRY.yaml` yet, not authorization to create
a root registry copy, not authorization to create maintenance/sync helpers, not
authorization to execute validation scripts, not authorization to change
executable bits, and not authorization for remote, branch, push, release,
deploy, secret, private-state, log, cache, or runtime actions.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 10 |
| Batch name | Registry authority |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source registry | `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` |
| Source SHA-256 | `4abadb46ce14df8116d1e2205ccda9c66bd61ca84b781a80d1f18e3456c5fc40` |
| Source size | 3074 bytes |
| Source YAML parse | Passed during candidate selection. |
| Planned target registry | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/WORKSPACE_REGISTRY.yaml` |
| Registry file created now | No |
| Script execution performed | No |

## Planned File Creation

If this patch is later authorized, create exactly one registry authority file:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
```

If authorized and applied, also create the receipt:

```text
ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md
```

Do not update `control-plane/registry/README.md` in this batch unless a later
preflight finds that the README must be changed to avoid misleading authority
wording. The first authority patch should stay focused on the registry file.

## Source Structure

The source registry contains:

| Area | Observed source structure |
| --- | --- |
| Top-level keys | `workspace`, `layers`, `repositories`, `security` |
| Layer count | 8 |
| Repository count | 6 |
| Security block | Present |

The source registry is structured data. It is not a script and must not be
treated as remote-action authorization even where it records repository URLs or
policy names.

## Normalization Rules

### Authority Placement

| Topic | Rule |
| --- | --- |
| Target path | Create only `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| Root registry | Do not create root `WORKSPACE_REGISTRY.yaml`. |
| Governance registry | Do not create `governance/WORKSPACE_REGISTRY.yaml`. |
| Examples | Do not modify files under `control-plane/registry/examples/`. |
| Maintenance/sync | Do not create `ops/maintenance/sync-upstream-vcp.sh`. |

### Layer Normalization

| Source registry entry | Planned target handling | Reason |
| --- | --- | --- |
| Layer id `agents_os` | Rename to `control_plane`. | Current WSL control-plane layer is `control-plane/`, not old `AGENTS_OS/`. |
| Layer path `AGENTS_OS/` | Rewrite to `control-plane/`. | Matches target-layer and directory-principles decisions. |
| Layer role `control_plane` | Preserve. | Role is still accurate after path normalization. |
| Existing source layers `runtime`, `governance`, `execution`, `extensions`, `domains`, `state_private`, `ops` | Preserve ids and paths unless a direct WSL decision says otherwise. | These source paths match current first-level WSL paths. |
| WSL-only layer `labs/` | Add only if `labs/README.md` still exists during implementation preflight. | Current WSL root has this layer and directory principles list it. |
| WSL-only layer `memory/` | Add only if `memory/README.md` still exists during implementation preflight. | Current WSL root has this layer and directory principles list it. |
| WSL-only layer `archive/` | Add only if `archive/README.md` still exists during implementation preflight. | Current WSL root has this layer and directory principles list it. |

### Repository Record Normalization

| Source repository record | Planned target handling | Reason |
| --- | --- | --- |
| `VCPToolBox` | Preserve as registry metadata under `runtime`. | Source and migration map agree that VCPToolBox belongs to runtime. |
| `codex-router` | Preserve as registry metadata under `governance`. | Existing WSL repo is under governance. |
| `Bounded-High-Autonomy` | Preserve as registry metadata under `governance`. | Existing target decisions keep this in governance. |
| `agent-image-lab` | Normalize layer from `domains` to `labs` if still supported by `_MIGRATION_MAP.md` and `labs/README.md`. | Current WSL migration map places `agent-image-lab` under labs. |
| `Photo_Studio_OS` | Preserve under `domains`. | Current WSL migration map places Photo Studio under domains. |
| `Jenn-VCP-Extensions` | Preserve under `extensions`. | Source and migration map agree that Jenn extensions belong to extensions. |

Do not add missing repository records in this batch. In particular, do not infer
new records for memory projects, governance harnesses, local state, or other
repositories that are not present in the source registry. Missing repository
records need a separate registry expansion decision.

### Security Metadata

| Source security item | Planned target handling |
| --- | --- |
| `default_forbidden` entries such as push, release, deploy, secret-value printing, real env reading, direct main modification, and destructive delete | Preserve as policy metadata. |

Security metadata in the registry must not be treated as executable policy code
or as permission to run checks. It is registry data used by governance and
validators.

### URL And Remote Boundary

Repository URLs may be preserved as metadata, but the target registry must state
or imply no remote action. A URL in the registry is not authorization to fetch,
pull, clone, push, open a PR, release, deploy, or contact a network service.

## Explicitly Out Of Scope

| Item | Reason |
| --- | --- |
| `ops/maintenance/sync-upstream-vcp.sh` | Maintenance/sync helper remains deferred and remote/branch-sensitive. |
| Root `WORKSPACE_REGISTRY.yaml` | Rejected authority placement; would create drift risk. |
| Root `SECURITY_BOUNDARIES.md` | Security authority already belongs under governance. |
| Registry expansion for missing projects | Requires separate evidence and decision. |
| Running `validate-workspace.sh` | Batch 10 is a registry patch plan, not validation execution. |
| Updating registry examples | Examples stay separate from authority. |

## Strict Preflight Before Implementation

| Check | Pass condition |
| --- | --- |
| Reconfirm source registry hash | Source `WORKSPACE_REGISTRY.yaml` still matches `4abadb46ce14df8116d1e2205ccda9c66bd61ca84b781a80d1f18e3456c5fc40`. |
| Parse source YAML | Source registry parses as YAML with `workspace`, `layers`, `repositories`, and `security`. |
| Reconfirm target absence | `control-plane/registry/WORKSPACE_REGISTRY.yaml` is still absent. |
| Reconfirm root registry absence | Root `WORKSPACE_REGISTRY.yaml` is still absent. |
| Reconfirm maintenance/sync absence | `ops/maintenance/sync-upstream-vcp.sh` remains absent and outside scope. |
| Re-read target decision | Registry authority target is still `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| Re-read registry README | README still separates examples from authoritative registry files. |
| Reconfirm WSL-only layer evidence | `labs/README.md`, `memory/README.md`, and `archive/README.md` still exist before adding those layer entries. |
| Reconfirm `agent-image-lab` target evidence | `_MIGRATION_MAP.md` and `labs/README.md` still support placing `agent-image-lab` under labs. |
| Source live-secret scan | Source registry contains no live secret, token, credential, password, private endpoint, or private account value. |
| Target draft YAML parse | Target draft parses as YAML before file creation. |
| Target draft normalization scan | Target draft contains `control-plane/` and does not preserve `AGENTS_OS/` as an active layer path. |
| Target draft authority scan | Target draft does not create root registry/security authority and does not authorize remote actions. |
| Command-risk scan | Target draft and receipt contain no runnable remote, branch, network, destructive, copy, move, sync, or script-execution commands. |

## Post-Patch Validation Plan

If later authorized and applied, validate by:

| Validation | Method | Notes |
| --- | --- | --- |
| Target file check | Confirm `control-plane/registry/WORKSPACE_REGISTRY.yaml` and receipt exist. | No other target files should be created. |
| Root absence check | Confirm root `WORKSPACE_REGISTRY.yaml` remains absent. | Avoid duplicate authority. |
| YAML parse | Parse target registry as YAML. | Structural validation only. |
| Normalization check | Confirm old active `AGENTS_OS/` path is replaced by `control-plane/`. | Historical mentions, if any, must be explicitly labeled non-authoritative. |
| Registry README boundary check | Confirm examples remain separate from authority. | No example file should become active registry state. |
| Live-secret scan | Scan target registry and receipt. | No live secrets. |
| Command-risk scan | Search target registry and receipt for runnable remote/sync/destructive commands. | None should appear. |
| Validator execution | Not run in this patch. | Any later validator run needs exact explicit approval through the validation authorization template. |

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md
```

The receipt should record:

- exact authorization wording
- source registry hash
- normalization rules applied
- target registry created
- target registry hash
- YAML parse result
- live-secret scan result
- command-risk scan result
- files not created
- validation not run
- remaining risks
- rollback path

## Rollback Outline

If the future Batch 10 registry patch is later applied and must be rolled back,
remove only files created by that future patch after confirming no later user
work depends on them:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md
```

Do not remove `control-plane/registry/`, registry examples, registry README,
validation scripts, prior migration plans, prior receipts, or any source files
under `A:\AGENTS_OS_Workspace`.

## Open Items Before Authorization

None for the planned Batch 10 scope. The planned registry-file creation is
closed:

```text
Create exactly one authority registry file at control-plane/registry/WORKSPACE_REGISTRY.yaml.
```

The future implementation preflight must still pass before any registry file is
created.

## Related Documents

- `phase-2-batch-10-candidate-selection-2026-06-28.md`
- `phase-2-batch-9-workspace-validator-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../../../control-plane/registry/README.md`
- `../../../_MIGRATION_MAP.md`
- `../../../_DIRECTORY_PRINCIPLES.md`
