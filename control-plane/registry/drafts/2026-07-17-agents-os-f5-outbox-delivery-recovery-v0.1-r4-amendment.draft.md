# AGENTS OS F5 Outbox Delivery Recovery v0.1 R4 Amendment

Status: Draft fixed candidate for fresh full atomic review  
Date: 2026-07-17  
Owner: Jenn  
Author steward: Nobao  
Revision: R4  
Review unit: `F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R4_ATOMIC_BUNDLE`

## 1. Purpose And Atomic Precedence

R4 closes exactly three independently reproduced R3 proof defects:

1. incomplete closed inventory, exact field type and disposition matrix checks;
2. precedence rows that were labelled as two orders without proving exact
   reversal;
3. arm replay records that did not bind canonical bytes, recomputable request
   identity and stored-first accounting.

R4 does not add a delivery state, receipt type, retry model, provider protocol,
database layout, runtime implementation, authentication mechanism or F6
semantic.

The proposed acceptance unit is indivisible:

```text
R1 contract
+ R1 builder / fixture / validator
+ R2 amendment / builder / fixture / validator
+ R3 amendment / builder / fixture / validator
+ R4 amendment / builder / fixture / validator
= one sixteen-subject atomic bundle
```

Partial acceptance is forbidden. Effective precedence is:

```text
R4 explicit replacements
> R3 other explicit replacements
> R2 other explicit replacements
> R1 all other clauses
```

R1-R3 subject, manifest and review bytes remain immutable.

## 2. Unchanged Authority Boundary

R4 remains a synthetic, nonauthority proof surface.

```yaml
environment: SYNTHETIC_TEST
authority_eligible: false
runtime_consumable: false
accepted_real_handoff_count: 0
claim_event_count: 0
armed_dispatch_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

R4 MUST NOT:

- classify an Actor, Task, role, relationship, trust, urgency, color or P0-P3
  label as an authority level;
- recompute F1, F2, F3 or F4 authority;
- turn synthetic evidence into production authority;
- authorize a real handoff, physical call, runtime activation or provider use;
- start F6 or implementation.

## 3. R3 Finding Disposition

| R3 finding | R4 disposition | Required executable proof |
|---|---|---|
| `F5_R3_BLOCKER_001_CLOSED_SCHEMA_AND_CROSS_FIELD_VALIDATION_REMAINS_INCOMPLETE` | close | every root, section, row and canonical object has an exact inventory; effective types and disposition matrices reject fully re-signed illegal values before fingerprints are checked |
| `F5_R3_MAJOR_001_PRECEDENCE_PROOF_ACCEPTS_DUPLICATED_RAW_ORDERING` | close | every one of 147 pairs has exactly two trials and the second raw sequence is the exact reverse of the first |
| `F5_R3_BLOCKER_002_ARM_REPLAY_DOES_NOT_BIND_CANONICAL_BYTES_OR_STORED_FIRST_ACCOUNTING` | close | request payload, canonical bytes, fingerprint, ID and stored-first replay accounting are independently recomputed |

R5 is not preplanned. Only a new, independent, reproducible security
counterexample against fixed R4 bytes may require R5.

## 4. Closed Fixture Inventory

The R4 fixture interface is:

```text
agents-os.f5-r4-three-finding-proof-closure-fixture.v0.1
```

The proof domain is:

```text
agents-os.f5-r4-three-finding-proof-closure-proof.v0.1
```

The root field set MUST equal, with no additions or omissions:

```text
fixture_interface
environment
authority_eligible
runtime_consumable
fixture_canonical_sha256

schema_profiles
schema_profiles_fingerprint
schema_shape_examples
schema_shape_examples_fingerprint
synthetic_nonauthority_scenario
synthetic_nonauthority_scenario_fingerprint
identity_formula_graph
identity_formula_graph_fingerprint
precedence_ordering_trials
precedence_ordering_trials_fingerprint
arm_state_derivation_cases
arm_state_derivation_cases_fingerprint
receipt_compatibility_cases
receipt_compatibility_cases_fingerprint
receipt_currentness_cases
receipt_currentness_cases_fingerprint
transition_cases
transition_cases_fingerprint
adversarial_cases
adversarial_cases_fingerprint
assertions
assertions_fingerprint
summary
summary_fingerprint
```

Every section has a closed row shape:

```yaml
schema_profiles_row:
  - schema_name
  - interface_version
  - fingerprint_field
  - fields
  - field_types
  - schema_profile_fingerprint

schema_shape_examples_row:
  - schema_name
  - semantic_role
  - occurrence_count
  - object

synthetic_nonauthority_scenario:
  - raw_input
  - derived

identity_formula_graph:
  - proof_mode
  - authority_eligible
  - runtime_consumable
  - occurrence_count
  - objects
  - derived_identities

precedence_ordering_trial_row:
  - unordered_case_id
  - kind
  - ordering
  - raw_conditions
  - derived

precedence_raw_condition_row:
  - reason
  - is_true

arm_state_derivation_row:
  - case_id
  - proof_mode
  - raw_input
  - derived

receipt_compatibility_row:
  - receipt_kind
  - effect_status
  - derived_compatibility

receipt_currentness_row:
  - case_id
  - raw_input
  - derived

transition_row:
  - from_state
  - to_state
  - derived

adversarial_row:
  - check
  - expected_decision
```

The scenario raw and derived objects, graph objects, arm raw/stored/submitted
objects, receipt raw/stored/submitted objects, assertions and summary also MUST
match their exact closed inventories frozen by the R4 builder and validator.
Unknown root, section, row or canonical-object fields MUST reject.

Validation order is normative:

```text
strict JSON parse and duplicate-key rejection
→ recursive JSON value validation
→ closed root / section / row / object inventories
→ exact scalar, enum and cross-field semantics
→ reducer and formula recomputation
→ section fingerprint verification
→ root fingerprint verification
```

A fingerprint MUST NOT substitute for inventory, type, semantic or reducer
validation.

## 5. Exact Effective Field Types

The R4 schema profiles MUST be derived from the effective R4 > R3 > R2 > R1
field inventories and MUST match the validator's exact per-schema type table.

The following four R1 fields are explicitly `positive_safe_integer`, not
`non_negative_safe_integer`:

```text
F5OutboxIntentV0_1R1.start_authority_expires_at_utc_ms
F5OutboxClaimFactV0_1R1.lease_expires_at_utc_ms
F5OutboxLeaseFactV0_1R1.previous_lease_expiry_utc_ms
F5OutboxLeaseFactV0_1R1.new_lease_expiry_utc_ms
```

For each:

```text
type(value) == integer
0 < value <= 9007199254740991
boolean is not an integer
```

All other effective schema types remain as frozen by R1-R3. A fully re-signed
profile that weakens any of these fields to nonnegative MUST reject. A fully
re-signed canonical object using zero MUST reject.

## 6. Complete Arm Disposition Matrix

`F5DispatchArmDispositionV0_1R2` remains the effective schema name. R4 closes
its cross-field semantics.

Success and replay rows are exact:

| primary reason | replay relation | result | reason codes | Event | physical call | first arm ref/fingerprint |
|---|---|---|---|---:|---:|---|
| `ARMED_FIRST_APPLY` | `NO_EXISTING_ARM` | `APPLIED` | `[]` | true | true | absent |
| `EXACT_DUPLICATE_REPLAY` | `EXACT_DUPLICATE` | `REPLAYED` | `[]` | false | false | present |
| `REQUEST_BYTES_CONFLICT` | `CHANGED_BYTES_SAME_IDENTITY` | `REJECTED` | exactly `[REQUEST_BYTES_CONFLICT]` | false | false | absent |
| `ARM_LOOKUP_UNAVAILABLE` | `LOOKUP_INDETERMINATE` | `INDETERMINATE` | exactly `[ARM_LOOKUP_UNAVAILABLE]` | false | false | absent |

All other closed arm failure reasons use `NO_EXISTING_ARM`, no occurrence and
no first-arm reference. `OBSERVATION_UNAVAILABLE` is `INDETERMINATE`; all
other failure primaries are `REJECTED`.

```text
arm_failure_precedence =
  INTEGRITY_FAILURE
  SYNTHETIC_INPUT
  TERMINAL_ALREADY_RECORDED
  CLAIM_STALE
  TOKEN_MISMATCH
  AUTHORITY_STALE
  FENCED
  EPOCH_STALE
  HOST_MISMATCH
  EXPIRED
  OBSERVATION_UNAVAILABLE
  CAS_MISMATCH
```

Failure `reason_codes` MUST be a sorted unique subset of this exact list, MUST
contain the primary reason, and the primary reason MUST be its first active
entry in this precedence.

The synthetic shape example remains:

```text
NO_EXISTING_ARM + REJECTED + SYNTHETIC_INPUT
+ no Event + no physical call + no first-arm reference
```

Changing only its replay relation to `EXACT_DUPLICATE` MUST reject even after
all object, section and root fingerprints are recomputed.

## 7. Complete Receipt Disposition Matrix

`F5DeliveryReceiptDispositionV0_1R3` remains the effective schema. R4 closes
its cross-field semantics.

| primary reason | relation | result | reason codes | Event | reconciliation | projection | Task advancement |
|---|---|---|---|---:|---:|---:|---:|
| `APPLIED_CURRENT` | `NEW` | `APPLIED` | `[]` | true | false | true | false |
| `EXACT_DUPLICATE_REPLAY` | `EXACT_DUPLICATE` | `REPLAYED` | `[]` | false | false | false | false |
| `RECEIPT_BYTES_CONFLICT` | `CHANGED_BYTES_SAME_KEY` | `REJECTED` | exactly `[RECEIPT_BYTES_CONFLICT]` | false | true | false | false |
| `RECEIPT_LOOKUP_UNAVAILABLE` | `LOOKUP_INDETERMINATE` | `INDETERMINATE` | exactly `[RECEIPT_LOOKUP_UNAVAILABLE]` | false | false | false | false |

For `NEW`, error/currentness precedence is:

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
```

`reason_codes` MUST be a sorted unique subset of that list. The primary MUST be
the first active entry. Result mapping is exact:

```text
no active reason                   → APPLIED / APPLIED_CURRENT
SOURCE_ATTESTATION_UNAVAILABLE     → INDETERMINATE
EPOCH_STALE                        → HISTORY_ONLY / HISTORY_ONLY_EPOCH_STALE
FENCE_STALE                        → HISTORY_ONLY / HISTORY_ONLY_FENCE_STALE
ATTEMPT_STALE                      → HISTORY_ONLY / HISTORY_ONLY_ATTEMPT_STALE
all earlier error reasons          → REJECTED
```

Only `CHANGED_BYTES_SAME_KEY` may set `reconciliation_opened=true`. A `NEW`
receipt rejected for invalid attestation MUST NOT open reconciliation. All
Task advancement flags remain false.

## 8. Exact Precedence Two-Order Proof

The R4 precedence universe is exactly every unordered pair of closed failure
reasons for the claim, lease and arm reducers used by R3:

```text
unordered pairs: 147
raw ordering trials: 294
trials per unordered case: 2
```

For every `unordered_case_id`:

1. exactly two rows exist;
2. ordering labels equal `{1, 2}`;
3. each raw sequence contains exactly two closed, distinct, true reasons;
4. ordering 1 equals the canonical pair order;
5. ordering 2 equals the exact element-wise reverse of ordering 1;
6. both true-reason sets are equal;
7. both sorted reason-code sets, primary reasons and reducer results are equal.

Copying ordering 1 into ordering 2, recomputing its derived output and fully
re-signing the section and root MUST reject.

## 9. Closed Canonical Arm Replay Request

The replay request payload interface is:

```text
agents-os.f5-dispatch-arm-replay-request-payload.v0.1-r4
```

Its exact field set is:

```text
payload_interface
outbox_intent_ref
outbox_intent_fingerprint
bound_invocation_identity_fingerprint
claim_ref
claim_fingerprint
claim_epoch
claim_fencing_token
attempt_ordinal
attempt_id
idempotency_key
physical_boundary_observation_ref
physical_boundary_observation_fingerprint
requested_at_utc_ms
requested_event_sequence
```

The request record exact field set is:

```text
request_id
request_fingerprint
request_canonical_utf8_hex
```

Validation MUST:

1. decode lowercase even-length hexadecimal as UTF-8;
2. parse strict JSON with duplicate-key rejection;
3. recursively reject floats, non-NFC strings, unsafe integers and unsupported
   JSON values;
4. require the exact payload inventory and scalar types;
5. require supplied bytes to equal the canonical encoding of the parsed
   payload byte-for-byte;
6. recompute `request_fingerprint = SHA256(canonical_payload_bytes)`;
7. recompute:

```text
attempt_id = H(
  agents-os.f5-delivery-attempt-id.v0.1,
  outbox_intent_fingerprint,
  attempt_ordinal
)

request_id = H(
  agents-os.f5-dispatch-arm-request-id.v0.1,
  outbox_intent_fingerprint,
  bound_invocation_identity_fingerprint,
  attempt_ordinal
)
```

Pretty-printed, indented, reordered or otherwise noncanonical bytes MUST reject
even if they parse to the same value and the attacker recomputes the request,
section and root fingerprints.

## 10. State-Derived Replay And Stored-First Accounting

The R4 arm raw input exact field set is:

```text
lookup_reproducible
bound_invocation_identity_fingerprint
stored_arm_state
submitted_request
first_apply_eligibility
```

Caller-supplied previous Event or call-authorization counts are removed.

When present, `stored_arm_state` contains exactly:

```text
request_id
request_fingerprint
request_canonical_utf8_hex
first_arm_ref
first_arm_fingerprint
first_event_ref
first_event_fingerprint
first_call_authorization_ref
first_call_authorization_fingerprint
committed_event_count
committed_call_authorization_count
```

Both stored and submitted request records MUST independently pass Section 9.
Both MUST bind the raw invocation fingerprint. When a stored state exists, the
stored and submitted request IDs MUST match the same replay identity.

Relation derivation remains:

```text
lookup not reproducible            → LOOKUP_INDETERMINATE
no stored arm                      → NO_EXISTING_ARM
same ID + fingerprint + exact bytes→ EXACT_DUPLICATE
same ID but changed bytes          → CHANGED_BYTES_SAME_IDENTITY
```

The constructive synthetic first apply models exactly one Event and one call
authorization. Stored-first accounting is exactly one Event and one call
authorization.

For `EXACT_DUPLICATE`:

```text
modeled_event_delta = 0
modeled_call_authorization_delta = 0
total_event_count = stored.committed_event_count
total_call_authorization_count = stored.committed_call_authorization_count
returned_first_arm_* = stored.first_arm_*
returned_first_event_* = stored.first_event_*
returned_first_call_authorization_* = stored.first_call_authorization_*
```

No second accounting input may override those totals or returned references.
Changed-bytes and indeterminate observations also cannot manufacture new Event
or call accounting.

## 11. Required Fully Re-Signed Attacks

The R4 validator MUST reject, after all attacker-controlled object, section and
root hashes are recomputed:

1. unknown root field;
2. unknown section field;
3. unknown proof-row field;
4. weakened positive-integer schema profile;
5. zero in each of the four positive time fields;
6. illegal receipt disposition tuple;
7. illegal arm disposition tuple;
8. duplicated precedence ordering;
9. noncanonical arm request bytes;
10. wrong arm request fingerprint;
11. wrong arm request ID formula;
12. exact replay total-accounting divergence;
13. exact replay returned-reference divergence;
14. stored-first accounting divergence.

The prior seven independently demonstrated R3 counterexamples MUST be rejected
7/7. Existing R3 graph-level formula, schema-value, transition, reducer and
synthetic authority attacks remain required.

## 12. Fixed Constructive Surface

The R4 subject surface is exactly:

```text
control-plane/registry/drafts/2026-07-17-agents-os-f5-outbox-delivery-recovery-v0.1-r4-amendment.draft.md
control-plane/registry/build-f5-r4-three-finding-proof-closure.py
control-plane/registry/examples/2026-07-17-agents-os-f5-r4-three-finding-proof-closure-v0.1.json
control-plane/registry/validate-f5-r4-three-finding-proof-closure.py
```

The fixture is constructive proof only. Validator success means the fixed
synthetic proof satisfies the effective contract and attack suite; it does not
authorize implementation, runtime, a provider, authentication or any physical
effect.

## 13. R4 Acceptance Candidate Gate

R4 may be presented to Jenn for an atomic freeze decision only when:

```yaml
prior_7_additional_probes_rejected: 7_of_7
unknown_root_section_row_fields_rejected: true
disposition_cross_field_matrices_complete: true
positive_safe_integer_profiles_exact: true

precedence_unordered_pairs: 147
precedence_raw_trials: 294
precedence_exact_reverse_pairs: 147_of_147
duplicated_order_mutation_rejected: true

arm_request_bytes_are_canonical: true
request_id_recomputed_from_complete_payload: true
request_fingerprint_recomputed_from_complete_payload: true
exact_replay_totals_equal_stored_first_accounting: true
noncanonical_formula_and_accounting_mutations_rejected: true

fresh_full_atomic_review: PASS_NO_BLOCKER
```

`PASS_NO_BLOCKER` stops F5 revision and prepares a Jenn-only freeze decision
surface. It does not itself accept or freeze F5. Any `BLOCK` preserves all
fixed bytes and routes only a new, independent, reproducible security finding.

## 14. Explicit Non-Authorization

This amendment authorizes none of the following:

```text
F5 acceptance or freeze
F6 start or semantics
implementation
Rust or JavaScript runtime modules
database or provider transport
production authentication
runtime activation
real handoff, Host work or physical effect
commit, push, PR, merge, release, deploy, publish or tag
formal Memory or private raw-memory access
```
