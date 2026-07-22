# AGENTS OS Phase 5C M0-C Offline Plugin Packaging Implementation Plan v0.1 R1

```yaml
plan_id: PHASE_5C_M0C_OFFLINE_PLUGIN_PACKAGING_IMPLEMENTATION_PLAN_V0_1_R1
date: 2026-07-22
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
acceptance_unit: PHASE_5C_M0C_PLAN_BUILD_PROFILE_V0_1_R1_ATOMIC_BUNDLE
partial_acceptance: forbidden
implementation_authorized: false
runtime_activation_authorized: false
```

## 1. Objective

Phase 5C M0-C will prove that the durable `agents-os-resident` extension can be
assembled into a deterministic, low-disclosure, **disabled** external-plugin
package and checked offline against the sealed VCPToolBox host contract.

It does not install that package into VCPToolBox, create an enabled manifest,
load the native addon through VCPToolBox, start a service, or process real data.
The planned terminal result is only:

```text
PACKAGE_COMPATIBLE_PREVIEW
```

That result is evidence, not activation or execution authority.

## 2. Fixed baseline and ownership

The only implementation source owner remains:

```text
extensions/agents-os-resident/
```

The package consumes the durable Phase 5B content tree and the seven previously
verified Git objects from VCPToolBox commit
`555b3b538f6eb736e530c2912de678c5941f9985`. Phase 5C does not read the dirty
VCPToolBox worktree or reinterpret host authority. A compatibility verifier may
compare only the fixed paths, blob IDs, byte hashes and structural requirements
recorded in the accepted preflight.

VCPToolBox core ownership, plugin loading and runtime lifecycle stay with
VCPToolBox. Phase 5C cannot become a second loader, permission system, identity
authority, Task authority, Command authority or effect authority.

## 3. Exact future implementation scope

After a separate Jenn implementation-start decision, M0-C may create:

```text
extensions/agents-os-resident/tools/build-offline-package.mjs
extensions/agents-os-resident/tools/validate-sealed-host-contract.mjs
extensions/agents-os-resident/fixtures/sealed-vcptoolbox-host-contract.v0.1.json
extensions/agents-os-resident/tests/offline-packaging.mjs
```

It may modify only:

```text
extensions/agents-os-resident/package.json
extensions/agents-os-resident/README.md
extensions/agents-os-resident/package-manifest.json
```

No dependency, lockfile, Rust, N-API, SQLite schema, VCPToolBox-tracked file,
public API or MCP schema change is planned.

## 4. Package and host-contract rules

The package builder operates only in a newly created temporary staging
directory. It copies the closed inventory from the source package, rejects
symlinks, duplicate paths, traversal, absolute paths, device files, unknown
inventory members and any digest mismatch, then emits a deterministic inventory
and archive checksum. It never follows caller-selected filesystem paths.

The staged package must contain `plugin-manifest.json.block` with its exact
hash. It must not contain `plugin-manifest.json`. The CommonJS entry point must
remain inert on import, keep only `initialize`, `processToolCall`, `shutdown`,
and preserve the existing five native N-API methods.

The host compatibility check is exact and fail-closed:

```text
sealed commit + seven Git path/blob/hash commitments
+ disabled package manifest + closed package inventory
+ exact CommonJS and N-API surface
-> PACKAGE_COMPATIBLE_PREVIEW
```

Unknown, unavailable, stale, malformed, conflicting or additional input returns
`BLOCKED`; a newer upstream VCPToolBox revision requires a new reviewed profile.

## 5. Planned work packages

| WP | Future result | Direct gate |
|---|---|---|
| WP0 | sealed baseline and source inventory checker | all durable Phase 5B hashes match |
| WP1 | deterministic temporary staging builder | closed inventory and path safety pass |
| WP2 | disabled-manifest and inert-entrypoint verifier | enabled or ambiguous manifest rejects |
| WP3 | sealed host-contract compatibility verifier | seven exact source commitments resolve |
| WP4 | archive determinism and tamper suite | two clean builds are byte-identical |
| WP5 | rollback/cleanup proof for owned temporary staging | no bytes remain outside owned temp root |
| WP6 | integrated offline compatibility witness | all positive and adversarial cases pass |

Every WP remains synthetic/offline. No WP may write a VCPToolBox worktree,
enable a plugin, load the addon through a host, create a database or start a
runtime.

## 6. Validation and privacy

Validation uses fixture bytes and temporary package trees containing only
repository-controlled synthetic content. It must cover path traversal,
symlinks, duplicate paths, manifest substitution, inventory addition/removal,
same-path byte replacement, source-commit substitution, host-object
substitution, N-API expansion, eager native loading and incomplete cleanup.

Secrets, credentials, tokens, cookies, active configuration, raw Session,
private Memory, provider responses, database contents and state-private data are
not inputs and must not appear in diagnostics or archives.

## 7. Stop rules

This R1 unit requires Fresh Full Atomic Hash-Bound Independent Review. Author
evidence cannot substitute for independent judgment. `PASS_NO_BLOCKER` closes
only the review gate; Jenn must separately accept and freeze the atomic plan.
Even a freeze does not start implementation.

The mandatory stop state is:

```text
AWAITING_JENN_PHASE_5C_M0C_PLAN_ATOMIC_FREEZE_DECISION
```

VCPToolBox modification or startup, plugin enablement, native runtime loading,
real database access, production authentication, private Memory, provider,
sensing, effect, release, deploy and publish remain outside Phase 5C R1.
