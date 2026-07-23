# AGENTS OS Phase 5D M0-D Quarantined Host Smoke Integration Plan v0.1 R1

```yaml
plan_id: PHASE_5D_M0D_QUARANTINED_HOST_SMOKE_INTEGRATION_PLAN_V0_1_R1
date: 2026-07-23
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
acceptance_unit: PHASE_5D_M0D_PLAN_BUILD_PROFILE_V0_1_R1_ATOMIC_BUNDLE
partial_acceptance: forbidden
implementation_authorized: false
host_smoke_execution_authorized: false
runtime_activation_authorized: false
```

## 1. Objective

Phase 5D M0-D defines the future, quarantined first-use boundary between the
already durable `agents-os-resident` external extension and a sealed
VCPToolBox Host contract. It is a planning unit only. Its immediate terminal
result is:

```text
QUARANTINED_HOST_SMOKE_PREFLIGHT_READY
```

That result means that a later decision can evaluate an exact, reversible Host
smoke run. It does **not** mean that a package was delivered, a plugin was
enabled, a Host was started, or a native addon was loaded.

The future smoke is intentionally narrower than the existing synthetic command
surface. Its intended lifecycle surface is only:

```text
Host discovery
-> initialize
-> exact inert result {"initialized": false}
-> shutdown
-> exact inert result {"shutdown": true}
-> cleanup
```

`processToolCall` is excluded because it requires the native addon. No
`execute_command`, `execute_query`, `claim_outbox`, `acknowledge_outbox`, or
`reconcile` call belongs to M0-D.

## 2. Fixed baseline and ownership

The implementation owner remains:

```text
extensions/agents-os-resident/
```

Phase 5D consumes only already sealed, hash-bound inputs: the durable Phase 5C
source package, the canonical blocked plugin manifest, the inert CommonJS entry
point, and the seven-path VCPToolBox commitment at
`555b3b538f6eb736e530c2912de678c5941f9985`. It must not read a VCPToolBox
worktree during Plan R1 authoring, validation, or review.

VCPToolBox remains the owner of its core, plugin discovery, enablement, loader
and runtime lifecycle. M0-D may never create a parallel Host loader, identity,
permission, Task, Command or effect authority.

## 3. What a future implementation may and may not do

After this plan is independently reviewed, frozen, durable on `main`, and
separately authorized by Jenn, a future implementation may create only a
quarantine harness under the extension owner:

```text
extensions/agents-os-resident/tools/prepare-quarantined-host-smoke.mjs
extensions/agents-os-resident/tools/validate-quarantined-host-smoke.mjs
extensions/agents-os-resident/fixtures/quarantined-host-smoke-contract.v0.1.json
extensions/agents-os-resident/tests/quarantined-host-smoke.mjs
```

It may update the extension README and package manifest only to record that
future harness. It may not modify VCPToolBox-tracked files, the public N-API
surface, Rust reducers, SQLite schema, dependencies, lockfiles, MCP schemas or
plugin source ownership.

No implementation authorization is granted by this plan. In particular, the
following are separate Jenn-only gates:

```text
1. create or inspect a clean VCPToolBox worktree at the sealed revision
2. deliver an archive into a newly created owned quarantine root
3. create a transient enabled manifest inside that owned root
4. allow Host discovery and lifecycle invocation
5. allow a native addon load or any processToolCall invocation
6. allow any runtime, provider, database, private Memory or real effect
```

## 4. Future quarantine contract

The future execution environment must be newly created, owned by the harness,
non-production, no-network-by-default, and free of active provider, credential,
private Memory, existing database, Session, browser, runtime and user-content
inputs. It cannot accept a caller-selected source root, output root, Host root,
archive path, manifest path or configuration path.

A future Host worktree must be a clean, disposable checkout at the exact sealed
commit. Before any delivery or discovery, the harness must independently verify
the seven committed Host paths, blob IDs and SHA-256 values already frozen by
Phase 5C. Mismatch, unavailability, extra local state, a different commit or an
unknown Host lifecycle contract is `BLOCKED`.

The canonical source package must retain `plugin-manifest.json.block`; it must
never be renamed or modified in the workspace. If a future, separately
authorized experiment needs an enabled manifest, it must be generated solely
inside the newly owned quarantine root, bound to the exact blocked-manifest
preimage and deleted during cleanup. It cannot be copied back to the workspace
or Host source tree.

## 5. Future smoke state machine

The only valid state sequence is:

```text
NOT_STARTED
-> QUARANTINE_CREATED
-> SEALED_INPUTS_VERIFIED
-> BLOCKED_PACKAGE_STAGED
-> FUTURE_JENN_ENABLEMENT_GATE
-> FUTURE_JENN_HOST_LOAD_GATE
-> INITIALIZED_INERT
-> SHUTDOWN_INERT
-> QUARANTINE_REMOVED
```

Every transition is fail-closed. Any mismatch, unexpected Host call, native
require, `processToolCall`, N-API method invocation, network attempt, database
open, provider/authentication access, user-content read, residual file, or
unexpected lifecycle output terminates as `BLOCKED` and must reach cleanup
without promoting the package or retaining the generated manifest.

The future lifecycle arguments are deliberately not invented by M0-D. They must
come from a later hash-bound, sealed Host lifecycle contract. Until that exact
contract is available and separately accepted, the state machine cannot pass
`FUTURE_JENN_ENABLEMENT_GATE` and must return `NOT_EXECUTED`.

## 6. Planned work packages

| WP | Future result | Direct gate |
|---|---|---|
| WP0 | sealed source and Host commitment revalidation | every fixed hash and Host commitment matches |
| WP1 | owned quarantine topology and path policy | no caller-selected or pre-existing root is accepted |
| WP2 | blocked-manifest preservation and transient-manifest rule | workspace canonical manifest remains blocked |
| WP3 | inert lifecycle-only smoke contract | `processToolCall` and native load are trapped before use |
| WP4 | cleanup, rollback and residue observation contract | all generated artifacts stay inside and leave the owned root |
| WP5 | integrated synthetic preflight witness | all positive and adversarial offline cases pass |

No work package may modify or start VCPToolBox, deliver an archive, enable a
plugin, load native code, start a runtime or write a database during this plan
phase.

## 7. Validation and privacy

The plan's fixture and validator use only synthetic strings, sealed hashes and
static source facts. Required adversarial cases include source/Host commitment
substitution, caller-selected paths, an enabled workspace manifest, a transient
manifest escaping the owned root, `processToolCall` inclusion, native-load
claims, unexpected lifecycle output, pre-existing quarantine state, residue,
network/provider/auth/database/private-Memory claims and unknown fields.

No secret, credential, token, cookie, active configuration, raw Session,
private Memory, provider response, database content or `state-private/` byte may
be read, copied, logged, placed in a fixture or included in a review archive.

## 8. Stop rules

This R1 unit requires Fresh Full Atomic Hash-Bound Independent Review. Author
evidence cannot substitute for an independent conclusion. `PASS_NO_BLOCKER`
closes only the review gate; Jenn must separately accept and freeze the plan.
Even after freeze and Git durability, Host worktree creation, package delivery,
plugin enablement, Host loading and runtime execution remain separately gated.

The mandatory terminal state for this plan is:

```text
AWAITING_JENN_PHASE_5D_M0D_PLAN_ATOMIC_FREEZE_DECISION
```
