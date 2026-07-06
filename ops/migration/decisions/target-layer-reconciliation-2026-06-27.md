# Target Layer Reconciliation - 2026-06-27

Status: target-layer decision only，非迁移授权。

This decision record resolves the target layer for
`Codex_Autonomous_Work_Harness`. It does not authorize copying, moving,
deleting, executing, pushing, syncing, or changing any project.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Target layer reconciliation |
| Candidate | `Codex_Autonomous_Work_Harness` |
| Authoritative source path | `A:\AGENTS_OS_Workspace\execution\Codex_Autonomous_Work_Harness` |
| Candidate target layers | WSL `execution/` vs WSL `governance/` |
| Evidence used | `_DIRECTORY_PRINCIPLES.md`, `WORKSPACE_REGISTRY.yaml`, `README.AGENTS_OS.md`, project `README.md`, shallow source-path decision |
| Private state review | Not performed |
| Secret value review | Not performed |
| Project source review | Limited to root-level entry docs and directory shape |

## Decision

| Item | Decision |
| --- | --- |
| Target layer | `governance/` |
| Target path for planning | `/home/jenn/AGENTS_OS_Workspace/governance/Codex_Autonomous_Work_Harness` |
| Candidate label after decision | `迁移`, pending scoped migration plan |

## Rationale

`Codex_Autonomous_Work_Harness` should be planned under `governance/` as a
governance framework and safety-boundary repository, not under `execution/` as
an active execution harness.

This is a target-layer decision, not a new permanent category label. The
repository currently belongs with governance because its dominant role is
rules, hard gates, validation rails, and operating guidance.

Evidence:

- The project README identifies it as a reusable governance harness for
  Codex-assisted autonomous work.
- The project README lists its contents as a governance framework, hard-gate
  policy library, validation matrix reference, runbook collection, template
  source, and human-controlled safety boundary.
- `README.AGENTS_OS.md` says it provides governance material and local
  validation rails for bounded Codex work.
- `README.AGENTS_OS.md` explicitly says the repository must not be treated as
  an automatic execution engine.
- `_DIRECTORY_PRINCIPLES.md` defines `governance/` as the layer for governance,
  safety, authorization, routing, and hard gates.
- `_DIRECTORY_PRINCIPLES.md` defines `execution/` as the layer for execution
  harnesses, workers, provider adapters, and bridge runners.
- The current repository is policy/runbook/validation-rail oriented. It may
  describe bounded local execution, but it does not currently serve as the
  canonical runtime executor, provider adapter, or bridge runner.

## Decision Rule

Use this boundary for future planning:

| If the artifact is... | Target layer |
| --- | --- |
| Policy, hard gate, autonomy rule, validation matrix, runbook, project profile, checkpoint discipline, adoption guidance, or similar governance-oriented material | `governance/` |
| A real runner, worker, provider adapter, bridge runner, process launcher, or active execution implementation extracted from the harness | `execution/` |

## Notes

- The Windows source path currently lives under `A:\AGENTS_OS_Workspace\execution\...`.
  That old location is treated as historical layout evidence, not as the target
  layer authority.
- The WSL `_MIGRATION_MAP.md` already points the target to `governance/`, which
  aligns with this decision.
- The migration map source path still differs from the observed source path;
  that was resolved separately in `source-path-reconciliation-2026-06-27.md`.
- A future scoped migration plan should not enable this repository as an active
  execution engine by default.

## Follow-Up Required

| Item | Required before migration |
| --- | --- |
| Migration method | Decide fresh clone vs sanitized copy. |
| Validation | Identify report-only validation commands from the source repository. |
| Sensitive exclusions | Exclude `.agent_board` private state if needed, logs, runtime outputs, env files, and generated artifacts unless explicitly approved. |
| Migration map | Update `_MIGRATION_MAP.md` only under a separate scoped docs/config change. |

## Related Documents

- `source-path-reconciliation-2026-06-27.md`
- `../inventory/roots-inventory-2026-06-27.md`
- `../candidates/migration-candidates-2026-06-27.md`
