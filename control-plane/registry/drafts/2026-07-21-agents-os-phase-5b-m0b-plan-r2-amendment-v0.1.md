# AGENTS OS Phase 5B M0-B Plan R2 Narrow Closure Amendment v0.1

```yaml
amendment_id: PHASE_5B_M0B_PLAN_R2_NARROW_CLOSURE_V0_1
date: 2026-07-21
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_HASH_BOUND_INDEPENDENT_REVIEW
precedence: R2_explicit_replacements_then_R1_all_other_clauses
R1_subjects_modified: false
implementation_authorized: false
runtime_usable: false
```

## 1. Exact scope

R2 closes only:

```text
PHASE5B_PLAN_R1_IR_B01 exact implementable source inventory and single writer
PHASE5B_PLAN_R1_IR_B02 exact F8 handoff to F3 payload and replay identity
PHASE5B_PLAN_R1_IR_B03 constructive history/owner/writer/transaction/crash graph
PHASE5B_PLAN_R1_IR_M01 exact schema-v2 and migration totality
```

The four R1 subjects and R1 manifest remain immutable. R2 does not change F1
through F8 semantics, Phase 5A public ABI, the one-writer topology or any
authorization boundary.

## 2. Replacement: exact future source inventory

R2 replaces the R1 `future_source_change_inventory` with the exact inventory
in the R2 source and F3 seam profile. The public five-method N-API surface is
unchanged, but internal `napi_frame.rs` dispatch is explicitly permitted to
change after a separate implementation-start decision.

Every Home candidate, handoff and F3 terminal mutation must travel:

```text
existing execute_command or synthetic Rust test call
-> closed reducer / decoder
-> new exact LedgerCommand variant
-> existing LedgerThread receiver
-> the LedgerThread-owned single rusqlite::Connection
-> one BEGIN IMMEDIATE transaction
```

No Home module receives a `Connection`, SQL string, filesystem path or direct
writer handle. No second thread, connection, plugin, service, sidecar or N-API
method is permitted.

## 3. Replacement: F8 to F3 synthetic Command seam

`M0_SYNTHETIC_SUBMIT_HOME_INTENT` has one closed type-specific payload. It
contains the exact F8 handoff tuple, exact source Intent Candidate tuple,
owner-commitment-set fingerprint, canonical-history fingerprint and minimum
trusted Event sequence. The payload schema, schema fingerprint domain,
payload fingerprint, Command ID and replay identity are frozen in the R2 source
and F3 seam profile.

Two different handoff tuples cannot derive the same Command ID. The same
Command ID with different canonical request bytes is `PROTOCOL_CONFLICT`.
Exact replay returns the first F3-owned response bytes and accounting. Home and
F8 cannot write or claim an F3 row.

## 4. Replacement: schema v2

R2 replaces the R1 prose table list with the exact closed table, column,
constraint, index, trigger, foreign-key, migration and transaction inventories
in the R2 persistence profile.

Schema v2 may exist only in a future per-test temporary database after a
separate implementation-start decision. Migration is all-or-zero under
`BEGIN IMMEDIATE`; `schema_metadata` advances last. Existing non-test or
unrecognized databases fail closed without modification.

## 5. Replacement: constructive proof surface

The R2 graph fixture materializes:

- immutable Life Stream and Intent Candidate revisions and exact predecessor;
- the candidate-head pointer and Event bindings;
- exact F7/F8/F3 owner commitments and canonical candidate history;
- the F8 handoff revision;
- the complete F3 payload, Command and replay identity;
- the exact source routing to one LedgerThread and one connection;
- candidate, handoff and F3 transaction traces;
- every pre-commit, post-commit and restart crash disposition;
- schema v2 inventory and schema fingerprint.

The R1 28-case reducer catalog remains independently validated and is not
replaced by the R2 graph.

## 6. Stop rule

R2 requires Fresh Full Atomic Hash-Bound Independent Review of the combined
R1+R2 unit. A pass does not freeze the plan or start implementation. Jenn keeps
both decisions.

```yaml
automatic_plan_acceptance_or_freeze: false
automatic_implementation_start: false
Rust_JavaScript_NAPI_SQL_or_database_change: false
VCPToolBox_change_or_start: false
runtime_activation: false
production_authentication: false
private_Memory_access: false
provider_sensing_or_real_effect: false
```
