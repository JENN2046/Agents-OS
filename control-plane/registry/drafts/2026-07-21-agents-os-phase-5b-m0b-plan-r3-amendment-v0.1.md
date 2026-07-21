# AGENTS OS Phase 5B M0-B Plan R3 Narrow Closure Amendment v0.1

```yaml
amendment_id: PHASE_5B_M0B_PLAN_R3_NARROW_CLOSURE_V0_1
date: 2026-07-21
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_HASH_BOUND_INDEPENDENT_REVIEW
precedence: R3_explicit_replacements_then_R2_then_R1
R1_R2_subjects_modified: false
implementation_authorized: false
runtime_usable: false
```

## 1. Exact scope

R3 closes only the five findings in the fixed R2 independent review:

```text
PHASE5B_PLAN_R2_IR_B01 sealed public N-API inventory
PHASE5B_PLAN_R2_IR_B02 candidate genesis and predecessor lineage
PHASE5B_PLAN_R2_IR_B03 exact sealed F3 Command and request shapes
PHASE5B_PLAN_R2_IR_B04 implementable composite foreign keys
PHASE5B_PLAN_R2_IR_B05 target-semantic fully re-signed validation
```

No F1-F8 authority is recomputed. R3 is a plan-only, synthetic,
runtime-unusable proof surface. It changes no Rust, JavaScript, N-API, SQLite,
VCPToolBox, runtime, provider, Memory, sensing or effect implementation.

## 2. Sealed source truth and prospective delta

The current public N-API surface is derived from the sealed Rust source, in
source order:

```text
execute_command
execute_query
claim_outbox
acknowledge_outbox
reconcile
```

R3 distinguishes two facts that R2 conflated:

1. the existing sealed F3 envelope and N-API request shapes;
2. the prospective, implementation-only addition of
   `M0_SYNTHETIC_SUBMIT_HOME_INTENT` and its closed payload.

The prospective command type is not currently accepted by the sealed runtime.
Freezing this plan does not activate it.

## 3. Candidate lineage replacement

Life Stream candidate revision 1 and Intent candidate revision 1 are separate
genesis rows. Both have all predecessor fields null. Intent revision 2 may
advance only from Intent revision 1 with the same `candidate_id`, exact
revision-minus-one and exact predecessor ref/fingerprint. Cross-candidate
history order is represented by the canonical history object, never by a
predecessor foreign key.

The constructive witness selects Intent revision 2 for the F8 handoff. This
proves both legal genesis and legal same-identity revision advance.

## 4. Implementable schema replacement

`home_candidate_revision` declares the exact composite unique key:

```text
(candidate_id, candidate_revision, candidate_ref, candidate_fingerprint)
```

Every four-column candidate foreign key targets that exact key with identical
arity, order, storage class and collation. The offline validator derives parent
key coverage from the schema inventory; it does not accept a declared
`foreign_key_valid` label.

## 5. Semantic validation replacement

R3 separates byte sealing from semantic validation:

```text
validate_semantics(fixture)
  -> closed schemas, source facts, derivations, lineage, FK coverage,
     crash/replay and boundary rules

validate_fixed_fixture(fixture)
  -> optional exact canonical witness byte seal
```

The R2 fourteen-case catalog is replayed against `validate_semantics` with the
fixed-fixture seal disabled. Every case must be fully dependency-propagated and
re-signed, then rejected by its named target semantic code. A rejection caused
only by exact fixture inequality is a failed test.

## 6. Stop rule

The combined R1+R2+R3 unit requires a Fresh Full Atomic Hash-Bound Independent
Review. A pass does not freeze the plan or start implementation. Jenn retains
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
