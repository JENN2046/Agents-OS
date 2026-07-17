# AGENTS OS F5 Outbox Delivery / Recovery v0.1 R2 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-17  
Base R1 contract SHA-256: `96a04ae8fd83006255bf7cb5fc3902bfd07b50e22d01736bb3a36b531766e79f`  
Blocking R1 independent-review SHA-256: `7f19c21612aba636680f4b730a2e665371409e24a5707165a3a71084f480c00a`

## 1. Scope and precedence

This amendment closes exactly:

```text
F5_R1_BLOCKER_001_ARM_REPLAY_RELATION_NOT_CLOSED
F5_R1_BLOCKER_002_VALIDATOR_CLAIM_EXCEEDS_EXECUTABLE_COVERAGE
F5_R1_MAJOR_001_REASON_PRECEDENCE_NOT_NORMATIVELY_TOTAL
F5_R1_MAJOR_002_RECEIPT_KIND_STATUS_MATRIX_NOT_CLOSED
```

The effective reading order is:

```text
1. R2 explicit replacements
2. R1 all other clauses
3. frozen F4 R1-R9 for effect-admission authority and handoff semantics
4. frozen F3 R1-R4 for Resident, Command and canonical-writer authority
5. frozen F2 R1-R22 for identity, responsibility and delegation authority
6. accepted F1 for Task authority
```

The atomic acceptance literal is:

```text
F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R2_ATOMIC_BUNDLE
```

All four R1 subjects and the R1 independent review remain immutable inputs.
R2 does not recompute any F1/F2/F3/F4 reducer and does not classify an Actor,
Task, role, relationship, color, trust level, urgency, P0-P3 or past success as
delivery authority. It creates no identity, policy, permit, Host authentication
or effect authority.

## 2. Canonical helper rules

R1 Section 3 remains in force. R2 additionally freezes:

```text
JCS(value)
  = UTF-8 encoding of JSON with sorted object keys, compact separators,
    NFC strings, JSON booleans/null, and safe integers only

H(domain, values...)
  = lowercase_hex(SHA256(JCS([domain, values...])))

object_fingerprint(object)
  = H(interface_version + "-fingerprint",
      ordered values excluding canonical_fingerprint or projection_fingerprint)
```

`reason_codes` is the lexicographically sorted unique set of every true
non-success reason. `primary_reason` is selected only from the explicit ordered
list for that reducer. A literal's enum display order is never precedence.

## 3. Claim and lease total reason precedence

This section replaces only reason derivation for R1 Sections 4.5 and 4.6.

### 3.1 Claim

For a new or safe pre-arm reclaimed claim, derive every true candidate and
select the first candidate in this exact order:

```text
INTEGRITY_FAILURE
SYNTHETIC_INPUT
TERMINAL_ALREADY_RECORDED
DISPATCH_ALREADY_ARMED
CLAIM_ALREADY_ACTIVE
INTENT_NOT_PENDING
CLAIMANT_STALE
CLAIMANT_UNAVAILABLE
AUTHORITY_STALE
AUTHORITY_UNAVAILABLE
EXPIRED
CAS_MISMATCH
CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY
CLAIMED_NEW
```

`CLAIMANT_UNAVAILABLE` or `AUTHORITY_UNAVAILABLE` yields `INDETERMINATE` only
when no earlier proven negative exists. Either `CLAIMED_*` yields `CLAIMED`.
Every other primary yields `NOT_EXECUTABLE`.

### 3.2 Lease

The exact lease precedence is:

```text
INTEGRITY_FAILURE
CLAIM_STALE
TOKEN_MISMATCH
DISPATCH_ALREADY_ARMED
EXPIRED
CAS_MISMATCH
RENEWED
```

Only `RENEWED` yields `RENEWED`; all other values yield `REJECTED`. Lease
expiry and authority expiry are exclusive upper bounds; renewal is rejected
unless `renewed_at < new_lease_expiry <= min(current_authority_expiry,
current_handoff_expiry)`.

Every unordered pair of non-success candidates for claim and lease is part of
the R2 executable precedence proof. For each pair, both orderings of raw input
construction must yield the earlier normative reason and the same sorted
`reason_codes`.

## 4. Arm request, replay relation, disposition and fact

This section replaces R1 Section 4.7 and the arm-related sentences in Sections
5-9 and 13.

### 4.1 `F5DispatchArmRequestV0_1R2`

```yaml
interface_version: agents-os.f5-dispatch-arm-request.v0.1-r2
dispatch_arm_request_id: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
invocation_identity_fingerprint: lowercase_sha256
claim_ref: stable_ref
claim_fingerprint: lowercase_sha256
claim_epoch: positive_safe_integer
claim_fencing_token: lowercase_sha256
attempt_ordinal: positive_safe_integer
attempt_id: lowercase_sha256
idempotency_key: stable_ref
physical_boundary_observation_ref: stable_ref
physical_boundary_observation_fingerprint: lowercase_sha256
requested_at_utc_ms: non_negative_safe_integer
requested_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

The logical identity is stable across delivery of the same request:

```text
dispatch_arm_request_id = H(
  "agents-os.f5-dispatch-arm-request-id.v0.1",
  outbox_intent_fingerprint,
  invocation_identity_fingerprint,
  attempt_ordinal
)
```

The canonical fingerprint commits every ordered field except itself. A caller
cannot supply an alternative request ID or idempotency key; `idempotency_key`
must equal the F4-bound `effect_id`.

### 4.2 Canonical replay relation

In the one canonical-writer transaction, lookup by
`dispatch_arm_request_id` derives exactly one closed relation:

```text
NO_EXISTING_ARM
  no committed arm exists for the request ID or bound invocation

EXACT_DUPLICATE
  one committed first arm exists and its bound arm-request fingerprint equals
  the submitted request canonical fingerprint byte-for-byte

CHANGED_BYTES_SAME_IDENTITY
  one committed arm exists for the request ID or bound invocation but its
  request fingerprint differs

LOOKUP_INDETERMINATE
  canonical writer state cannot be reproduced at the transaction watermark
```

This relation is reducer-derived, never caller supplied.

Relation handling occurs before currentness evaluation:

```text
EXACT_DUPLICATE
  -> REPLAYED / EXACT_DUPLICATE_REPLAY
  -> return first arm ref and fingerprint
  -> Event created false
  -> physical call authorized false

CHANGED_BYTES_SAME_IDENTITY
  -> REJECTED / REQUEST_BYTES_CONFLICT
  -> Event created false
  -> physical call authorized false

LOOKUP_INDETERMINATE
  -> INDETERMINATE / ARM_LOOKUP_UNAVAILABLE
  -> Event created false
  -> physical call authorized false

NO_EXISTING_ARM
  -> evaluate first-apply eligibility below
```

An exact duplicate never rechecks current authority because it cannot create a
new call; it only returns immutable first accounting. Changed bytes can never
be converted into a fresh request by changing claim epoch or observation.

### 4.3 First-apply reason precedence

For `NO_EXISTING_ARM`, the exact precedence is:

```text
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
ARMED_FIRST_APPLY
```

`OBSERVATION_UNAVAILABLE` yields `INDETERMINATE`. `ARMED_FIRST_APPLY` yields
`APPLIED`. Every other primary yields `REJECTED`. Every unordered pair of
non-success first-apply candidates is part of the executable pairwise proof.

### 4.4 `F5DispatchArmDispositionV0_1R2`

```yaml
interface_version: agents-os.f5-dispatch-arm-disposition.v0.1-r2
dispatch_arm_request_id: lowercase_sha256
dispatch_arm_request_fingerprint: lowercase_sha256
replay_relation: NO_EXISTING_ARM | EXACT_DUPLICATE | CHANGED_BYTES_SAME_IDENTITY | LOOKUP_INDETERMINATE
first_arm_ref: stable_ref | null
first_arm_fingerprint: lowercase_sha256 | null
result: APPLIED | REPLAYED | REJECTED | INDETERMINATE
primary_reason: ARMED_FIRST_APPLY | EXACT_DUPLICATE_REPLAY | REQUEST_BYTES_CONFLICT | ARM_LOOKUP_UNAVAILABLE | SYNTHETIC_INPUT | CLAIM_STALE | TOKEN_MISMATCH | TERMINAL_ALREADY_RECORDED | AUTHORITY_STALE | FENCED | EPOCH_STALE | HOST_MISMATCH | EXPIRED | OBSERVATION_UNAVAILABLE | CAS_MISMATCH | INTEGRITY_FAILURE
reason_codes: sorted_unique_closed_set
event_created: boolean
physical_call_authorized: boolean
observed_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Only `APPLIED/ARMED_FIRST_APPLY` has `event_created=true` and
`physical_call_authorized=true`. Exact replay has both false and binds the
immutable first arm. First apply binds the arm created in the same atomic
transaction. Rejected or indeterminate dispositions have both first-arm fields
null. No other combination is valid.

### 4.5 `F5DispatchArmFactV0_1R2`

```yaml
interface_version: agents-os.f5-dispatch-arm-fact.v0.1-r2
dispatch_arm_id: lowercase_sha256
dispatch_arm_ref: stable_ref
dispatch_arm_request_id: lowercase_sha256
dispatch_arm_request_fingerprint: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
claim_ref: stable_ref
claim_fingerprint: lowercase_sha256
claim_epoch: positive_safe_integer
claim_fencing_token: lowercase_sha256
attempt_ordinal: positive_safe_integer
attempt_id: lowercase_sha256
idempotency_key: stable_ref
physical_boundary_observation_ref: stable_ref
physical_boundary_observation_fingerprint: lowercase_sha256
armed_at_utc_ms: non_negative_safe_integer
armed_event_sequence: non_negative_safe_integer
arm_transaction_ref: stable_ref
arm_transaction_fingerprint: lowercase_sha256
canonical_fingerprint: lowercase_sha256
```

The fact exists only for the first successful apply:

```text
dispatch_arm_id = H(
  "agents-os.f5-dispatch-arm-id.v0.2",
  dispatch_arm_request_id
)
dispatch_arm_ref = "dispatch-arm:" + dispatch_arm_id
```

One arm fact uniquely consumes the F4 invocation. Neither exact replay nor any
rejection emits another arm Event or authorizes a physical call.

## 5. Complete derived identities

This section replaces R1 Section 5 only to make executable coverage explicit.
The following formulas are normative and independently recomputed:

```text
outbox_intent_id = H(
  "agents-os.f5-outbox-intent-id.v0.1",
  source_handoff_fingerprint,
  invocation_identity_fingerprint,
  effect_id
)

claim_id = H(
  "agents-os.f5-outbox-claim-id.v0.1",
  outbox_intent_fingerprint,
  claim_epoch
)

claim_fencing_token = H(
  "agents-os.f5-outbox-claim-fence.v0.1",
  outbox_intent_fingerprint,
  claim_epoch,
  claimant_assessment_fingerprint
)

attempt_id = H(
  "agents-os.f5-delivery-attempt-id.v0.1",
  outbox_intent_fingerprint,
  attempt_ordinal
)

dispatch_arm_id = H(
  "agents-os.f5-dispatch-arm-id.v0.2",
  dispatch_arm_request_id
)
```

R2 executable subjects contain one canonical instance for every effective
schema, recompute every object fingerprint, these five inherited formulas and
the R2 arm-request identity formula from Section 4.1, and reject a fully
re-signed mutation of each identity or fingerprint.

## 6. Receipt compatibility and currentness reducer

This section replaces R1 Section 4.9 receipt compatibility and receipt reducer
prose. The R1 receipt fields remain, with these effective rules.

### 6.1 Total compatibility matrix

`receipt_kind × effect_status` is valid exactly as follows:

| receipt_kind | Allowed effect_status |
|---|---|
| `TRANSPORT_ACK` | `ACKED_ONLY` |
| `EFFECT_SUCCEEDED` | `SUCCEEDED` |
| `EFFECT_FAILED` | `FAILED` |
| `EFFECT_STATUS_UNKNOWN` | `UNKNOWN` |
| `EFFECT_QUERY_RESULT` | `SUCCEEDED`, `FAILED`, `UNKNOWN`, `NOT_EXECUTED` |

Every other Cartesian pair is `REJECTED / RECEIPT_KIND_STATUS_MISMATCH`.
`TRANSPORT_ACK` can never advance a projection to `SUCCEEDED`, `FAILED`, or
`NOT_EXECUTED`. `EFFECT_QUERY_RESULT` requires authenticated evidence that the
query used the existing `effect_id`; it cannot create an attempt or call.

### 6.2 Dedup relation

Lookup by `(source_id, receipt_id)` occurs first:

```text
EXACT_DUPLICATE -> REPLAYED, no Event, return first accounting
CHANGED_BYTES_SAME_KEY -> REJECTED / RECEIPT_BYTES_CONFLICT, open reconciliation
LOOKUP_INDETERMINATE -> INDETERMINATE / RECEIPT_LOOKUP_UNAVAILABLE
NEW -> evaluate currentness and compatibility
```

### 6.3 New-receipt precedence

For `NEW`, derive all true candidates and use this exact order:

```text
INTEGRITY_FAILURE
SOURCE_ATTESTATION_INVALID
ATTEMPT_OR_EFFECT_MISMATCH
EPOCH_STALE
FENCE_STALE
ATTEMPT_STALE
RECEIPT_KIND_STATUS_MISMATCH
TRANSITION_INVALID
SOURCE_ATTESTATION_UNAVAILABLE
APPLIED_CURRENT
```

`SOURCE_ATTESTATION_UNAVAILABLE` yields `INDETERMINATE`; `APPLIED_CURRENT`
yields `APPLIED`; all earlier values yield `REJECTED`. An authentic old-epoch
or stale-fence receipt is retained as historical evidence only through a
separate accounting disposition; it cannot mutate the current projection or
advance Task state.

The receipt reducer emits exactly one canonical disposition:

```yaml
interface_version: agents-os.f5-delivery-receipt-disposition.v0.1-r2
source_id: stable_ref
receipt_id: stable_ref
receipt_fingerprint: lowercase_sha256
dedup_relation: NEW | EXACT_DUPLICATE | CHANGED_BYTES_SAME_KEY | LOOKUP_INDETERMINATE
result: APPLIED | REPLAYED | REJECTED | INDETERMINATE
primary_reason: APPLIED_CURRENT | EXACT_DUPLICATE_REPLAY | RECEIPT_BYTES_CONFLICT | RECEIPT_LOOKUP_UNAVAILABLE | INTEGRITY_FAILURE | SOURCE_ATTESTATION_INVALID | ATTEMPT_OR_EFFECT_MISMATCH | EPOCH_STALE | FENCE_STALE | ATTEMPT_STALE | RECEIPT_KIND_STATUS_MISMATCH | TRANSITION_INVALID | SOURCE_ATTESTATION_UNAVAILABLE
reason_codes: sorted_unique_closed_set
event_created: boolean
reconciliation_opened: boolean
current_projection_advanced: boolean
task_advancement_eligible: false
observed_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

F5 never makes Task completion eligible; that remains F6-owned.

## 7. Total transition table

This section replaces R1 Section 6's informal arrows with the closed allowed
transition set below. Any unlisted pair is `TRANSITION_INVALID`:

```text
PENDING -> CLAIMED | DEAD_LETTERED
CLAIMED -> CLAIMED | DISPATCH_ARMED | DEAD_LETTERED
DISPATCH_ARMED -> DISPATCHED | ACKED | SUCCEEDED | FAILED | UNKNOWN
DISPATCHED -> ACKED | SUCCEEDED | FAILED | UNKNOWN
ACKED -> SUCCEEDED | FAILED | UNKNOWN
FAILED -> RECONCILED
UNKNOWN -> RECONCILED
DEAD_LETTERED -> RECONCILED
```

`SUCCEEDED` and `RECONCILED` have no outgoing delivery transition. Same-state
receipt replay is accounting replay, not a new transition. The executable R2
proof enumerates all 10×10 state pairs and rejects every unlisted pair.

## 8. R2 witness and validator claim limit

This section replaces R1 Section 14.

The R2 builder deterministically emits:

```text
16 effective schema profiles
16 canonical synthetic object instances with independently checkable fingerprints
all six effective derived-ID formula outputs: the five inherited domains plus the R2 arm-request domain
claim, lease and arm pairwise precedence cases
four arm replay-relation cases
all 25 receipt-kind/status Cartesian pairs
all 121 state-transition pairs
all 28 mandatory R1 adversarial decisions
fully re-signed semantic mutations for every protected proof family
zero-authority, zero-runtime and zero-effect assertions
```

The R2 validator independently implements JCS, hashing, field inventories,
six effective identity formulas, object fingerprints, precedence reducers, replay
relations, receipt compatibility, transition legality and adversarial expected
decisions. It imports no builder or R1 implementation module.

A R2 validator PASS proves only that those enumerated executable surfaces are
mutually consistent and constructible. It does not prove unencoded production
behavior, authorize implementation or turn synthetic evidence into authority.
The independent reviewer must still judge the effective R1+R2 semantics.

## 9. Required R2 adversarial decisions

All 28 R1 manifest attacks remain mandatory and executable. R2 additionally
binds these direct closure decisions:

```text
arm first apply -> APPLIED, one Event, one call authorization
arm exact duplicate -> REPLAYED, zero Event, zero call authorization
arm changed bytes same identity -> REJECTED integrity conflict
arm lookup unavailable -> INDETERMINATE, zero Event, zero call
every pair of claim failures -> earlier normative reason
every pair of lease failures -> earlier normative reason
every pair of arm first-apply failures -> earlier normative reason
TRANSPORT_ACK + SUCCEEDED -> REJECTED
EFFECT_SUCCEEDED + ACKED_ONLY -> REJECTED
all 25 receipt pairs -> exact matrix decision
all unlisted state transitions -> REJECTED
each mutated derived ID -> REJECTED after full fixture re-signing
each mutated object fingerprint -> REJECTED after full fixture re-signing
```

## 10. Non-authorization

R2 is a semantic correction and synthetic proof surface only. It does not
accept or freeze F5, start F6, authorize implementation, create a database,
start Resident/dispatcher/Host/service/provider, enable production
authentication, consume a real F4 handoff, arm or execute a real effect, write
formal Memory, or authorize commit, push, PR, merge, release, deploy, publish
or tag.
