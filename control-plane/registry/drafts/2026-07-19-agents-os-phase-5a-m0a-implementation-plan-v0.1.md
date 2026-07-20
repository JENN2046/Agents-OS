# AGENTS OS Phase 5A M0-A Implementation Plan v0.1

```yaml
plan_id: PHASE_5A_M0_DETERMINISTIC_ORCHESTRATOR_CORE_IMPLEMENTATION_PLAN_V0_1
date: 2026-07-19
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_HASH_BOUND_INDEPENDENT_REVIEW
acceptance_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_ATOMIC_BUNDLE
partial_acceptance: forbidden
implementation_authorized: false
runtime_activation_authorized: false
```

## 1. Purpose

Phase 5A builds the first isolated, deterministic implementation slice of the
AGENTS OS Orchestrator. This plan freezes how that future implementation will
be constructed; it does not construct or activate it.

The M0-A implementation must prove only:

```text
one logical Resident and one live canonical writer
one Rust-owned ledger thread and one SQLite read-write connection
closed authenticated Command intake and illegal Command rejection
Current State + Event + Inbox + Outbox atomicity
idempotent replay and protocol-conflict rejection
mock-only effect admission and dispatch
UNKNOWN for ambiguous external outcome with no automatic retry
crash-window recovery without duplicate effects
minimum current Validation decision and Task completion boundary
```

Home candidates, Memory, Presence, relationship mutation, real provider work,
production authentication, active runtime configuration and real effects are
outside M0-A.

## 2. Source and runtime ownership

The source of truth is a Jenn-owned external capability package:

```text
extensions/agents-os-resident/
```

It is materialized for compatibility tests at:

```text
<clean VCPToolBox worktree>/Plugin/AGENTSOSResident/
```

The materialized directory is an installation output, not the source of truth.
It must carry the source commit, package-manifest fingerprint and content-tree
fingerprint. It must contain `plugin-manifest.json.block`; an enabled
`plugin-manifest.json` is forbidden in Phase 5A.

The VCPToolBox base is fixed to commit:

```text
555b3b538f6eb736e530c2912de678c5941f9985
```

Installation and compatibility tests use a new clean linked worktree. The
existing `runtime/VCPToolBox` worktree and all of its local modifications,
blocked manifests, runtime data and configuration remain untouched.

The allowed VCPToolBox diff for M0-A is zero. In particular, the implementation
may not modify `server.js`, `Plugin.js`, root package metadata, routes, modules,
existing plugins or active configuration. A future need for a core hook is a
new architecture and authorization gate.

## 3. Work packages

Implementation after the separate Jenn start decision proceeds in this exact
order:

| Work package | Result | Advancement condition |
|---|---|---|
| WP0 Reproducible skeleton | external package layout, locks, blocked install manifest, deterministic package manifest | source-tree and install-tree hashes reproduce |
| WP1 Canonical primitives | strict JSON decoding, duplicate-key rejection, NFC, safe integers, JCS bytes and SHA-256 | fixed F1-F6 canonical vectors pass |
| WP2 Resident ownership | OS exclusive lock, identity/epoch state, one ledger thread, one connection, cleanup hook | dual-start and wrong-thread tests pass |
| WP3 Ledger v1 | schema metadata, immutable facts, current pointers, Event, Inbox, replay and transactional CAS | transaction and integrity tests pass |
| WP4 Command boundary | five closed N-API methods, synthetic principal verification, registry and intake dispositions | Node ABI, illegal input and replay tests pass |
| WP5 Permit and Outbox | F4 admission consumption, mock Host, Outbox claim/receipt/reconcile and UNKNOWN | stale fence and crash-window matrix pass |
| WP6 Validation completion | F6 current-decision consumption and same-transaction completion guard | disagreement and completion CAS tests pass |
| WP7 Integrated M0-A witness | three synthetic Tasks, deterministic event/root hashes, restart replay | two clean runs are byte-identical and zero real occurrences |

No work package may begin before its predecessor passes. A failed work package
is repaired within its frozen scope; it cannot skip forward or expand runtime
authority.

## 4. Closed interface

The only N-API method identifiers are:

```text
execute_command
execute_query
claim_outbox
acknowledge_outbox
reconcile
```

Each method accepts and returns canonical UTF-8 JSON using the frozen F3
`NapiRequestFrameV0_1` and `NapiResponseFrameV0_1`. Filesystem paths, SQL,
callbacks, functions, credentials, provider handles and arbitrary JavaScript
objects are rejected before ledger access.

Lifecycle is not a sixth method. Module initialization creates one process-wide
kernel handle. A Node environment cleanup hook stops intake, completes or rolls
back the current transaction, closes SQLite and joins the ledger thread.

The JavaScript shell exposes Promise-returning wrappers. N-API async work may
enqueue and wait for the ledger thread, but it may not own the database or
execute a reducer. Tokio, a Rust sidecar and network IPC are forbidden.

## 5. Persistence and recovery

M0-A uses one temporary isolated SQLite database under a test-created directory.
The path is supplied only through the synthetic test harness environment and
never through a Command or N-API frame.

The fixed database settings are:

```yaml
transaction: BEGIN_IMMEDIATE
journal_mode: DELETE
synchronous: EXTRA
foreign_keys: true
authoritative_connections: 1
writer: Rust_ledger_thread_only
busy_behavior: fail_closed_no_hidden_retry
schema_transition: empty_database_to_v1_only
```

Immutable Event, envelope, assessment, snapshot and receipt rows are never
updated. Current pointers are separate rows advanced with compare-and-set in
the same transaction as their Event and all required Inbox/Outbox changes.
Recovery derives no authority from projections and never guesses a lost effect
outcome.

## 6. Synthetic authority profile

All M0 identities, credentials, Hosts, Commands, Tasks and effects use a
`SYNTHETIC_TEST` namespace and a production-incompatible domain tag. The closed
M0 command registry contains only test definitions necessary to exercise F1-F6.

```text
M0_SYNTHETIC_CREATE_GOAL_AND_TASKS
M0_SYNTHETIC_RECORD_VALIDATION
M0_SYNTHETIC_ENQUEUE_MOCK_EFFECT
M0_SYNTHETIC_COMPLETE_TASK
```

These identifiers are implementation-test fixtures, not accepted production
F3 Command types. They cannot be loaded when the profile is not
`SYNTHETIC_TEST`, cannot be installed with an enabled manifest, and cannot
create production facts.

## 7. Delivery and stop rules

Implementation source begins on a local AGENTS OS task branch. No source is
pushed to the public `JENN2046/VCPToolBox` fork. Publication, a private mirror,
plugin enablement, runtime integration and Phase 5B each require a new decision.

The Build Profile freeze is not the implementation start. After an independent
`PASS_NO_BLOCKER` and Jenn atomic plan freeze, governance must stop at:

```text
AWAITING_JENN_PHASE_5A_IMPLEMENTATION_START_DECISION
```

Only that second exact decision may authorize WP0.
