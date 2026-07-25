# AGENTS OS Phase 5D M0-D Host Lifecycle Contract Closure v0.1 R1

```yaml
schema_version: agents-os.phase5d.m0d.host-lifecycle-contract-closure.v0.1-r1
contract_id: PHASE_5D_M0D_HOST_LIFECYCLE_CONTRACT_CLOSURE_V0_1_R1
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
owner: Jenn
agent_steward: Nobao
atomic: true
partial_acceptance: forbidden
current_execution_eligibility: false
runtime_usable: false
terminal_outcome: NOT_EXECUTED
```

## 1. Purpose

This closure freezes the exact evidence shape that a future Phase 5D Host smoke
would have to consume. It is not a Host lifecycle contract itself and it does
not create Host authority. The only currently permitted result is a deterministic
offline determination that the required owner-issued contract is missing or that
a synthetic test shape is well formed.

## 2. Frozen prospective lifecycle

The prospective smoke remains exactly:

```text
Host discovery
-> initialize
-> {"initialized": false}
-> shutdown
-> {"shutdown": true}
-> cleanup
```

The prospective sequence has no command, N-API, native-addon, database,
provider, private-Memory, sensing, recording, or effect step.

## 3. Required future owner evidence

A future execution candidate must provide one immutable, hash-bound,
owner-issued contract containing all four sections below. Each section must
carry an exact reference, positive revision, and lowercase SHA-256 fingerprint.

```yaml
required_owner_contract_sections:
  host_discovery:
    binds: exact_Host_selector_and_owner_API_binding
  initialize:
    binds: exact_argument_bytes_and_expected_result_initialized_false
  shutdown:
    binds: exact_argument_bytes_and_expected_result_shutdown_true
  quarantine_cleanup:
    binds: exact_delivery_location_cleanup_order_and_residue_observation
```

No role name, source-tree name, sealed commit alone, inferred default,
conversation text, caller-provided path, or synthetic value may replace one of
these owner-issued inputs.

## 4. Current fail-closed rule

```yaml
missing_owner_contract_result: BLOCKED_MISSING_HASH_BOUND_HOST_LIFECYCLE_CONTRACT
synthetic_shape_result: SYNTHETIC_CONTRACT_SHAPE_VALIDATED
synthetic_shape_runtime_usable: false
synthetic_shape_actual_host_smoke_authorized: false
all_other_results: BLOCKED
```

`SYNTHETIC_CONTRACT_SHAPE_VALIDATED` proves only that the closed schema can be
validated offline. It never upgrades an input to a Host contract and never
permits Host discovery, lifecycle invocation, package delivery, enabled manifest
creation, plugin loading, or native loading.

## 5. Exact boundary

This closure may create only its control-plane contract, evidence profile,
synthetic fixture, offline validator, author review, and hash-bound review
package. It may not create or read a VCPToolBox worktree, deliver an archive,
create an enabled manifest, discover or load a plugin, invoke `initialize`,
`shutdown`, `processToolCall`, or native/N-API, start a runtime, use a database,
install dependencies, access provider/authentication/private Memory/state-private
data, sense, record, or produce a real effect.

## 6. Future execution admission prerequisites

Actual Host smoke remains blocked until all of the following are separately
accepted and bound to one future execution decision:

1. an immutable owner-issued lifecycle contract matching Section 3;
2. a sealed Host worktree preflight at the frozen commit and exact source tuple;
3. a separately authorized quarantine delivery and transient-enabled-manifest
   contract;
4. a rollback/cleanup receipt contract that observes a real owned-root outcome;
5. a current Jenn execution decision naming the exact allowed action and stop
   conditions.

This R1 stops at Fresh Full Atomic Independent Review. It does not create a
Host smoke decision record and does not start Host smoke.
