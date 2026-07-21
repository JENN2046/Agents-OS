# AGENTS OS Phase 5B M0-B Plan R4 Narrow Closure Amendment v0.1

```yaml
amendment_id: PHASE_5B_M0B_PLAN_R4_NARROW_CLOSURE_V0_1
date: 2026-07-21
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_HASH_BOUND_INDEPENDENT_REVIEW
precedence: R4_explicit_replacements_then_R3_then_R2_then_R1
R1_R2_R3_subjects_modified: false
implementation_authorized: false
runtime_usable: false
```

## Exact scope

R4 closes only:

```text
PHASE5B_PLAN_R3_IR_B01 complete sealed F3 identity/authentication binding
PHASE5B_PLAN_R3_IR_B02 candidate PK/ref/history identity uniqueness
PHASE5B_PLAN_R3_IR_B03 exact duplicate-free three-entry composite FK inventory
```

All other R1–R3 clauses remain unchanged. R4 changes no implementation source,
runtime, database, VCPToolBox, provider, private Memory, sensing or effect.

## Sealed F3 value binding

Field inventory is insufficient. The exact Actor, Principal, Principal
revision, binding ref, principal-binding fingerprint and synthetic credential
must be derived from sealed `command_intake.rs` constants and its canonical
fingerprint domain. A fully re-signed substitution of any one value must fail
at `R4_F3_AUTHORITY_BINDING_INVALID`.

## Candidate uniqueness

The constructive set must enforce, before map construction:

```text
UNIQUE(candidate_id, candidate_revision)
UNIQUE(candidate_ref)
UNIQUE(history ordered candidate refs)
distinct candidate identities for the two genesis witnesses
unambiguous selected candidate resolution
```

No dictionary overwrite may serve as identity resolution.

## Composite FK inventory

The fixture inventory must equal the normative ordered three-entry list
exactly. Missing, extra, duplicated, substituted or reordered rows are invalid
before parent-key, arity, order, storage-class and collation checks execute.

## Stop rule

The combined R1+R2+R3+R4 unit requires Fresh Full Atomic Hash-Bound Independent
Review. A pass does not freeze the plan or start implementation.

```yaml
automatic_plan_acceptance_or_freeze: false
automatic_implementation_start: false
Rust_JavaScript_NAPI_SQLite_or_VCPToolBox_change: false
runtime_database_provider_private_Memory_sensing_or_effect: false
```
