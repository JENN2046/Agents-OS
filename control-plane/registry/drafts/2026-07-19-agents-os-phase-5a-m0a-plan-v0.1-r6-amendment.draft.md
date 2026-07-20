# AGENTS OS Phase 5A M0-A Plan v0.1 R6 Narrow Closure Amendment

Date: 2026-07-19
Status: fixed for fresh full atomic independent review
Owner: Jenn
Agent steward: Nobao

## 1. Atomic precedence

R6 is reviewed only with the full R1–R6 bundle. Partial review is forbidden.
R6 replaces only clauses explicitly named by its correction profiles:

```text
R6 explicit replacements
R5 all other clauses
R4 all other clauses
R3 all other clauses
R2 all other clauses
R1 all other clauses
```

R1–R5 subjects and manifests remain immutable.

## 2. Closed scope

R6 closes exactly the six Plan R5 independent-review blockers:

1. exact F5 authorization subject and replay identity binding;
2. frozen F3 witness COMMIT byte/hash/tuple validation and actual READY writes;
3. inherited N-API method and CommonJS export consistency;
4. semantic enforcement of all nonauthorization boundary flags;
5. relational rejection of same-revision canonical fact rewrites;
6. duplicate-key rejection for every YAML and JSON input before semantics.

R6 adds no permission, identity, Task, Command, state, delivery capability,
provider protocol, runtime capability, database table or Phase 5B semantic. The
effective database inventory remains exactly 18 tables.

## 3. F3 witness and lifecycle closure

Before READY, the consumer must parse the exact current `F3_WITNESS_COMMIT`
canonical bytes with a duplicate-key-rejecting JSON parser and require exact
canonical encoding and SHA-256 equality. The decoded object must exactly bind:

```text
resident_id
authority_epoch
incarnation_id
epoch_fingerprint
witness_reservation_ref
witness_reservation_fingerprint
ownership_event_sequence
ownership_event_id
ownership_event_fingerprint
```

The READY transaction re-reads the same authority-epoch tuple and writes a new
immutable `RESIDENT_LIFECYCLE` READY fact, current pointer and Event atomically.
Graph-local labels or fingerprints not derived from exact bytes are rejected.

## 4. F5 stored-first closure

`dispatch_arm` stores the exact call-authorization `subject_ref` and
`subject_revision`. They equal `attempt_id` and `attempt_revision` by CHECK and
participate in the composite foreign key to the canonical authorization fact.

Exact replay reads the stored row twice without INSERT or UPDATE and proves:

```text
returned stored Event identity unchanged
returned stored authorization identity including subject tuple unchanged
Event count before == Event count after
authorization count before == authorization count after
additional Event count == 0
additional authorization count == 0
```

## 5. Immutable history closure

`canonical_fact` is append-only. `BEFORE UPDATE` and `BEFORE DELETE` triggers
abort every mutation, including a coordinated current-pointer rewrite in the
same transaction. A new revision remains constructible only as a new INSERT
with the exact predecessor tuple.

## 6. Effective JavaScript ABI

The fixed synthetic wrapper exports exactly, in order:

```text
initialize
processToolCall
shutdown
```

Only `processToolCall(args)` projects the three allowed fields and calls the
already inherited method `residentNative.execute_command(nativeFrame)`.
`initialize(config, dependencies)` and `shutdown()` return fixed inert values;
neither starts runtime nor forwards inputs. No sixth native method exists.

## 7. Structured input totality and boundaries

All YAML and JSON loaders reject duplicate mapping keys before fingerprint or
semantic validation. Malformed or duplicate input returns `BLOCK`, never a
last-key-wins object or uncaught exception.

Every R6 validator run also requires all planning boundary fields to remain
strict JSON/YAML booleans equal to `false`, including runtime, implementation,
database, VCPToolBox, plugin, provider, private Memory, sensing and effect
occurrence flags.

## 8. Stop boundary

R6 is planning evidence only. It does not authorize implementation, dependency
installation, database creation, VCPToolBox modification/start, plugin
enablement, runtime activation, production authentication, private Memory,
sensing, provider calls or effects. A fresh full atomic independent review must
return `PASS_NO_BLOCKER` before a Jenn plan-freeze decision surface is prepared.

