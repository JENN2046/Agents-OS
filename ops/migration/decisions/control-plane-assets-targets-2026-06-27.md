# Control Plane Assets Target Decision - 2026-06-27

Status: target-placement decision only，非迁移授权。

This decision record resolves the WSL target locations and handling rules for
the lower-risk `contracts` and registry example assets from the Windows
reference root. It does not authorize copying, moving, deleting, executing,
pushing, syncing, or changing source assets.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Target placement and handling |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source areas reviewed | `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts`, `A:\AGENTS_OS_Workspace\AGENTS_OS\registry` |
| Assets included | Contract schema, contract README, registry example files, registry README |
| Assets excluded | `WORKSPACE_REGISTRY.yaml`, prompts, runbooks, scripts, templates, private state |
| Evidence used | Source file content read, WSL target directory check, `_DIRECTORY_PRINCIPLES.md`, `control-plane/README.md`, Phase 0 inventory, registry/security target decision |
| Migration performed | No |

## Decisions

| Source file | Authoritative WSL target for planning | Handling decision | Reason |
| --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\jenn-extension.manifest.schema.json` | `/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/jenn-extension.manifest.schema.json` | Phase 2 migration candidate as a control-plane contract schema after JSON syntax validation and secret-name scan. | The file is a JSON Schema for Jenn extension manifests. `control-plane/contracts/` already exists and is the right place for contract-shaped assets. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/README.md` | Rewrite or adapt into the target directory README instead of preserving the old filename as canonical. | The source README describes contracts, expected schema files, interfaces, validation, and ownership. WSL target directories currently use normal `README.md` naming, so the content should become target-native documentation. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\extensions.example.yaml` | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/extensions.example.yaml` | Phase 2 migration candidate as example-only registry material after path freshness review. | The file contains sample extension entries, not a verified live registry. Keeping it under `examples/` prevents it from being mistaken for authoritative state. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\protected-paths.example.yaml` | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/protected-paths.example.yaml` | Phase 2 migration candidate as example-only protected-path material after path freshness review. | The file contains sample protected paths and default actions. It should inform policy and validation work, but should not become an active protection registry without review. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/README.md` | Rewrite or adapt into the target directory README instead of preserving the old filename as canonical. | The source README explains registry purpose, contains examples, security boundaries, validation, and ownership. Target-native README naming keeps the WSL layout simpler. |

## Directory Decisions

| Target directory | Decision | Notes |
| --- | --- | --- |
| `control-plane/contracts/` | Use existing directory. | Do not create extra nesting for the current extension manifest schema. |
| `control-plane/registry/` | Create only during a later approved Phase 2 migration patch. | This will also be the planned location for canonical `WORKSPACE_REGISTRY.yaml` per the previous target decision. |
| `control-plane/registry/examples/` | Use for `.example.yaml` registry files. | This keeps examples separate from authoritative registry files. |

## Handling Rules

- Preserve source attribution in any future migration receipt.
- Do not carry `README.AGENTS_OS.md` as the canonical target filename when a
  target-native `README.md` is clearer.
- Do not treat `.example.yaml` files as active registry state.
- Do not create `extensions.yaml` or `protected-paths.yaml` from examples
  without a separate content review and authority decision.
- Do not run validator scripts as part of this decision.
- Do not create target directories or copy files until Phase 2.

## Required Review Before Phase 2 Copy

| Asset group | Required review |
| --- | --- |
| Contract schema | Parse as JSON; confirm schema name and `$id`; check that no example secret values are embedded. |
| Contract README | Remove or update references to validation scripts until those scripts are separately reviewed and migrated. |
| Registry examples | Verify paths such as `extensions/Jenn-VCP-Extensions/...` against current WSL naming and source-path decisions. |
| Registry README | Clarify example-only vs authoritative registry files; update validation references if script targets change. |

## Phase 2 Stop Conditions

- Do not copy contract or registry files until a scoped Phase 2 patch exists.
- Do not treat `.example.yaml` files as active registry state.
- Do not create `extensions.yaml`, `protected-paths.yaml`, or other active
  registry files from examples without a separate authority decision.
- Do not run validator scripts during migration.
- Do not create target directories or copy files until Phase 2.

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Place contract schema under `control-plane/schemas/` | Rejected for this file | The source belongs to the contracts family and the WSL `contracts/` directory already exists. A later schema-wide normalization can still create cross-links if needed. |
| Preserve source README filenames as canonical target files | Rejected | `README.AGENTS_OS.md` was useful in the Windows layout, but WSL target directories already use plain `README.md` for local directory guidance. |
| Place registry examples directly beside `WORKSPACE_REGISTRY.yaml` | Rejected | Examples should not sit at the same authority level as the canonical registry file. |
| Treat `extensions.example.yaml` as `extensions.yaml` | Rejected | The source file is explicitly an example and contains unverified historical paths. |
| Treat `protected-paths.example.yaml` as an active protected-path registry | Rejected | It needs review against current WSL root policy, security boundaries, and high-risk paths first. |

## Relationship To Existing Decisions

- `WORKSPACE_REGISTRY.yaml` itself is already planned for
  `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/WORKSPACE_REGISTRY.yaml`.
- The registry examples in this document sit below that target in
  `control-plane/registry/examples/`.
- Security boundary content remains governed by
  `governance/SECURITY_BOUNDARIES.md`, not by these example files.

## Related Documents

- `workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `source-path-reconciliation-2026-06-27.md`
