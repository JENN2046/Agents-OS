# AGENTS OS Phase 5B M0-B Plan R5 Narrow Closure Amendment v0.1

```yaml
amendment_id: PHASE_5B_M0B_PLAN_R5_NARROW_CLOSURE_V0_1
date: 2026-07-21
owner: Jenn
agent_steward: Nobao
status: FIXED_FOR_HASH_BOUND_INDEPENDENT_REVIEW
precedence: R5_explicit_replacements_then_R4_then_R3_then_R2_then_R1
R1_R2_R3_R4_subjects_modified: false
implementation_authorized: false
runtime_usable: false
```

## Exact scope

R5 closes only `PHASE5B_PLAN_R4_IR_B01`.

The two consumed occurrences of `claimed_principal_revision` must satisfy:

```text
JSON token category = integer
host-language exact type = int, excluding bool
value = 1
```

This rule applies independently to:

```text
R4 derived_sealed_binding.claimed_principal_revision
R3 Command.claimed_principal_revision consumed through the R4 fixture
```

Dictionary equality, numeric coercion, `== 1`, truthiness or fingerprint
agreement cannot substitute for the exact JSON-type proof.

## Totality

The validator must reject before a favorable closure result:

```text
true
false
1.0
1e0
null
string
array
object
zero
negative integer
integer other than 1
```

Malformed JSON, duplicate keys and non-finite numeric constants remain stable
`BLOCK` inputs under the inherited strict parser.

## Fixed regressions

The four R4 independent favorable-invalid paths become fixed R5 regressions:

```text
inner_revision_integer_1_to_boolean_true
inner_revision_integer_1_to_float_1_0
derived_and_inner_revision_to_boolean_true
derived_and_inner_revision_to_float_1_0
```

Each regression must propagate all dependent R3 and R4 fingerprints and the R5
root. Rejection must arise from `R5_PRINCIPAL_REVISION_JSON_INTEGER_INVALID`,
not only the immutable fixture seal.

## Stop rule

The combined R1–R5 unit requires Fresh Full Atomic Hash-Bound Independent
Review. A pass does not freeze the plan or start implementation.

```yaml
automatic_plan_acceptance_or_freeze: false
automatic_implementation_start: false
Rust_JavaScript_NAPI_SQLite_or_VCPToolBox_change: false
runtime_database_provider_private_Memory_sensing_or_effect: false
```
