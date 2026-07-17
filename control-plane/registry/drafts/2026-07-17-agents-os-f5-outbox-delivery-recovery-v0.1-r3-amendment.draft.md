# AGENTS OS F5 Outbox Delivery / Recovery v0.1 R3 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-17  
Base R1 contract SHA-256: `96a04ae8fd83006255bf7cb5fc3902bfd07b50e22d01736bb3a36b531766e79f`  
R2 amendment SHA-256: `de34f32e4c41df935c7b0c3ed0cb359fa0955bf97b55179f204c77f0264e7fd7`  
Blocking R2 independent-review SHA-256: `9c4296dd144b52e7a32492c6b3c4565968ec68fda1f05d535e24cb9247e86e1d`

## 1. Exact scope and precedence

R3 closes exactly these seven findings and nothing else:

```text
F5_R2_BLOCKER_001_VALIDATOR_ACCEPTS_FULLY_RESIGNED_SCHEMA_INVALID_VALUES
F5_R2_BLOCKER_002_RECEIPT_COMPATIBILITY_FALSELY_ESCALATES_TO_APPLIED
F5_R2_BLOCKER_003_ARM_REPLAY_RELATION_REMAINS_DECLARATIVE_NOT_STATE_DERIVED
F5_R2_MAJOR_001_PAIRWISE_PRECEDENCE_PROOF_DOES_NOT_EXECUTE_BOTH_RAW_ORDERINGS
F5_R2_MAJOR_002_CANONICAL_INSTANCE_SET_VIOLATES_EFFECTIVE_SEMANTICS
F5_R2_MAJOR_003_TRANSITION_PROOF_COUNT_IS_INTERNALLY_CONTRADICTORY
F5_R2_MAJOR_004_DERIVED_ID_MUTATIONS_DO_NOT_MUTATE_THE_CANONICAL_OBJECT_GRAPH
```

The effective reading order is:

```text
1. R3 explicit replacements
2. R2 all clauses not replaced by R3
3. R1 all clauses not replaced by R2 or R3
4. frozen F4, F3 and F2 authority boundaries
5. accepted F1 Task authority
```

The atomic acceptance literal is:

```text
F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R3_ATOMIC_BUNDLE
```

R1 and R2 fixed subjects and both blocking independent reviews remain immutable
lineage. R3 adds no delivery capability, provider protocol, database layout,
Rust module, network transport, production authentication or F6 semantics.

## 2. Closed pre-hash value validation

This section replaces the executable-validation claim in R2 Sections 2 and 8.
Before any object, section or root fingerprint is calculated or trusted, the R3
validator recursively validates the complete parsed JSON value tree.

It rejects:

```text
duplicate JSON object keys
all floats, NaN and Infinity
integers outside [-9007199254740991, 9007199254740991]
non-NFC strings, keys or values
unknown root, section, row or canonical-object fields
unknown enum values
wrong scalar, nullable or collection types
non-lowercase or non-64-character SHA-256 values
empty or non-NFC stable references
unsorted or duplicate closed sets
violated normative cross-field constraints
```

JSON booleans are never accepted as integers. JCS is applied only after this
validation succeeds; validation never silently normalizes an invalid value.

The executable negative suite fully re-signs every changed object, affected
section and root before validation. It includes at least one mutation for each
rejection class above, including unknown root and object fields.

## 3. Schema shapes versus semantic occurrences

R2's `canonical_instances` fixture section is superseded. R3 separates:

```text
schema_shape_examples
  one closed, fingerprint-valid, type-valid shape for each of the 16 effective
  schemas; explicitly NON_OCCURRING_SHAPE_EXAMPLE; never occurrence evidence

synthetic_nonauthority_scenario
  raw synthetic inputs reduced to NOT_EXECUTABLE with no claim, arm, runtime or
  physical-effect occurrence

identity_formula_graph
  an ABSTRACT_NONOCCURRING_FORMULA_PROOF used only to prove identity formulas,
  reference propagation and graph-level mutation rejection
```

No shape example or formula graph is authority-eligible, runtime-consumable,
recoverable as production state or countable toward a real occurrence.

The synthetic scenario must derive:

```yaml
enqueue_result: NOT_EXECUTABLE
enqueue_primary_reason: SYNTHETIC_INPUT
claim_result: NOT_EXECUTABLE
claim_primary_reason: SYNTHETIC_INPUT
arm_result: REJECTED
arm_primary_reason: SYNTHETIC_INPUT
claim_event_created: false
arm_event_created: false
physical_call_authorized: false
```

All claim shapes satisfy `claim_epoch = expected_previous_claim_epoch + 1`.
Every `RENEWED` lease shape satisfies:

```text
renewed_at_utc_ms < previous_lease_expiry_utc_ms
renewed_at_utc_ms < new_lease_expiry_utc_ms
previous_lease_expiry_utc_ms < new_lease_expiry_utc_ms
new_lease_expiry_utc_ms <= current authority and handoff expiry
```

The R3 fixed fixture contains no occurring `F5DispatchArmFact` and no synthetic
`APPLIED/ARMED_FIRST_APPLY` occurrence.

## 4. Executed total reason precedence

This section replaces the executable pairwise-proof claim in R2 Sections 3, 4
and 8, without changing the frozen claim, lease or first-arm precedence lists.

For each of the 147 unordered pairs of non-success reasons, R3 executes the
relevant reducer twice over raw boolean conditions:

```text
[A=true, B=true]
[B=true, A=true]
```

The raw input order is preserved in the fixture. The validator independently
derives `reason_codes`, `primary_reason` and reducer result from the booleans
and the normative precedence list. Both orderings must yield identical values.

Exact required counts:

```yaml
unordered_pair_count: 147
raw_ordering_trial_count: 294
claim_unordered_pairs: 66
lease_unordered_pairs: 15
arm_unordered_pairs: 66
```

Expected answers are validation targets, never reducer inputs.

## 5. State-derived arm replay and accounting

This section replaces R2 Section 4.2's executable proof shape. The normative
four relations remain unchanged, but the relation field is never accepted as
input. The raw reducer input is:

```yaml
lookup_reproducible: boolean
bound_invocation_identity_fingerprint: lowercase_sha256
stored_arm_state:
  request_id: lowercase_sha256
  request_fingerprint: lowercase_sha256
  request_canonical_utf8_hex: lowercase_hex
  bound_invocation_identity_fingerprint: lowercase_sha256
  first_arm_ref: stable_ref
  first_arm_fingerprint: lowercase_sha256
  committed_event_count: 1
  committed_call_authorization_count: 1
  # or null when no stored arm exists
submitted_request:
  request_id: lowercase_sha256
  request_fingerprint: lowercase_sha256
  request_canonical_utf8_hex: lowercase_hex
  bound_invocation_identity_fingerprint: lowercase_sha256
first_apply_eligibility: ELIGIBLE_PROOF_PRECONDITION | NOT_ELIGIBLE
previous_event_count: non_negative_safe_integer
previous_call_authorization_count: non_negative_safe_integer
```

The reducer independently verifies the submitted and stored canonical bytes and
fingerprints, then derives:

```text
lookup not reproducible
  -> LOOKUP_INDETERMINATE

no stored arm
  -> NO_EXISTING_ARM

same bound invocation + same request ID + same fingerprint + byte-equal request
  -> EXACT_DUPLICATE

any stored/submitted difference for the bound invocation
  -> CHANGED_BYTES_SAME_IDENTITY
```

Required accounting results are:

```text
NO_EXISTING_ARM + eligible proof precondition
  -> APPLIED; modeled Event delta 1; modeled call-authorization delta 1

EXACT_DUPLICATE
  -> REPLAYED; return stored first accounting; both deltas 0

CHANGED_BYTES_SAME_IDENTITY
  -> REJECTED; both deltas 0

LOOKUP_INDETERMINATE
  -> INDETERMINATE; both deltas 0
```

These are abstract reducer trials, not real or synthetic authority occurrences.
Their modeled deltas never contribute to fixture runtime/effect counters.

## 6. Receipt compatibility and currentness are separate reducers

This section replaces R2 Sections 6 and 8 for executable proof purposes.

### 6.1 Compatibility reducer

The exact 5 × 5 matrix emits only:

```text
COMPATIBLE
RECEIPT_KIND_STATUS_MISMATCH
```

Compatibility never emits `APPLIED`, advances a projection or creates an
Event. `EFFECT_QUERY_RESULT` additionally requires separately authenticated
proof that the query addressed the existing bound `effect_id`.

### 6.2 Raw currentness reducer

The receipt reducer derives its dedup relation from reproducible stored state
and receives these raw facts for a new receipt:

```yaml
source_attestation_status: VALID | INVALID | UNAVAILABLE
attempt_effect_identity_match: boolean
existing_effect_query_authenticated: boolean
epoch_current: boolean
fences_current: boolean
attempt_current: boolean
from_state: closed_state
to_state: closed_state
```

It independently calls compatibility and transition reducers. It emits one of:

```text
APPLIED
HISTORY_ONLY
REJECTED
INDETERMINATE
REPLAYED
```

`APPLIED` requires all of the following:

```text
NEW dedup relation
COMPATIBLE kind/status
VALID source attestation
exact attempt and effect identity
authenticated existing-effect query when receipt_kind=EFFECT_QUERY_RESULT
current epoch, fences and attempt
allowed state transition
```

An otherwise authentic stale epoch, fence or attempt produces `HISTORY_ONLY`:
historical evidence may be recorded, but the current projection and Task do not
advance. Invalid authentication, identity, compatibility or transition produces
`REJECTED`; unavailable lookup or attestation produces `INDETERMINATE`.

R3 replaces `F5DeliveryReceiptDispositionV0_1R2` with
`F5DeliveryReceiptDispositionV0_1R3`. It keeps the same fields, adds
`HISTORY_ONLY` to `result`, and freezes these booleans:

```yaml
interface_version: agents-os.f5-delivery-receipt-disposition.v0.1-r3
source_id: stable_ref
receipt_id: stable_ref
receipt_fingerprint: lowercase_sha256
dedup_relation: NEW | EXACT_DUPLICATE | CHANGED_BYTES_SAME_KEY | LOOKUP_INDETERMINATE
result: APPLIED | HISTORY_ONLY | REPLAYED | REJECTED | INDETERMINATE
primary_reason: APPLIED_CURRENT | HISTORY_ONLY_EPOCH_STALE | HISTORY_ONLY_FENCE_STALE | HISTORY_ONLY_ATTEMPT_STALE | EXACT_DUPLICATE_REPLAY | RECEIPT_BYTES_CONFLICT | RECEIPT_LOOKUP_UNAVAILABLE | INTEGRITY_FAILURE | SOURCE_ATTESTATION_INVALID | ATTEMPT_OR_EFFECT_MISMATCH | EXISTING_EFFECT_QUERY_INVALID | RECEIPT_KIND_STATUS_MISMATCH | TRANSITION_INVALID | SOURCE_ATTESTATION_UNAVAILABLE
reason_codes: sorted_unique_closed_set
event_created: boolean
reconciliation_opened: boolean
current_projection_advanced: boolean
task_advancement_eligible: false
observed_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

For `NEW`, every true raw failure is retained in sorted `reason_codes` and the
exact primary precedence is:

```text
INTEGRITY_FAILURE
SOURCE_ATTESTATION_INVALID
ATTEMPT_OR_EFFECT_MISMATCH
EXISTING_EFFECT_QUERY_INVALID
RECEIPT_KIND_STATUS_MISMATCH
TRANSITION_INVALID
SOURCE_ATTESTATION_UNAVAILABLE
EPOCH_STALE
FENCE_STALE
ATTEMPT_STALE
APPLIED_CURRENT
```

The three stale primary values are serialized as
`HISTORY_ONLY_EPOCH_STALE`, `HISTORY_ONLY_FENCE_STALE` or
`HISTORY_ONLY_ATTEMPT_STALE`; their underlying stale codes remain in
`reason_codes`.

```text
APPLIED      -> event_created=true,  current_projection_advanced=true
HISTORY_ONLY -> event_created=true,  current_projection_advanced=false
REPLAYED     -> event_created=false, current_projection_advanced=false
REJECTED     -> event_created=false, current_projection_advanced=false
INDETERMINATE-> event_created=false, current_projection_advanced=false
task_advancement_eligible=false for every result
```

`CHANGED_BYTES_SAME_KEY` additionally opens reconciliation; no compatibility
cell alone can do so.

## 7. Exact transition inventory

R2 Section 7's ten-state inventory and allowed edges remain unchanged. The
contradictory `121` statement in R2 Section 8 is replaced everywhere by:

```text
10 states × 10 states = 100 ordered transition trials
```

There is no eleventh state and no 121-case interpretation.

## 8. Graph-level derived-identity mutations

This section replaces the identity-mutation claim in R2 Sections 5, 8 and 9.
For each of the six identity domains, the negative suite:

```text
1. changes the canonical ID or fencing token to a formula-wrong value;
2. propagates that value through every dependent ref and object;
3. recomputes every affected dependent identity using its correct formula;
4. recomputes every affected object fingerprint;
5. re-signs the identity graph section and fixture root;
6. requires the independent formula validator to reject the coherent graph.
```

The six targets are:

```text
outbox_intent_id
claim_id
claim_fencing_token
attempt_id
dispatch_arm_request_id
dispatch_arm_id
```

A detached proof-map edit does not count as a graph-level mutation.

## 9. R3 executable proof and stop rule

The deterministic R3 fixture and independent validator bind at least:

```yaml
effective_schema_profiles: 16
schema_shape_examples: 16
precedence_unordered_pairs: 147
precedence_ordering_trials: 294
arm_state_derived_relations: 4
receipt_compatibility_pairs: 25
receipt_currentness_cases: positive_stale_invalid_indeterminate_and_replay
transition_pairs: 100
graph_level_identity_mutations: 6
schema_invalid_fully_resigned_mutations: all_required_classes
accepted_real_handoff_count: 0
armed_dispatch_count: 0
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

R3 is freeze-eligible only if all seven findings are independently closed and a
fresh full atomic hash-bound review returns `PASS_NO_BLOCKER`. A new amendment
is required only for a remaining real F5 semantic or proof defect; provider,
database, Rust, network, production-authentication or F6 implementation-profile
questions do not trigger R4.

## 10. Non-authorization

R3 does not accept or freeze F5, start F6, authorize implementation, create a
database, start Resident/dispatcher/Host/service/provider, enable production
authentication, consume a real F4 handoff, arm or execute a real effect, or
authorize commit, push, PR, merge, release, deploy, publish or tag.
