# AGENTS OS F5 Outbox Delivery / Recovery v0.1 R5 Amendment

Date: 2026-07-17  
Status: fixed candidate for fresh full atomic hash-bound independent review  
Owner: Jenn  
Agent steward: Nobao

## 1. Atomic Scope And Effective Precedence

This amendment closes exactly the two fully re-signed counterexamples in the
fixed R4 independent review:

1. receipt replay fields were detached from the fingerprint-bound receipt
   bytes;
2. the arm `LOOKUP_INDETERMINATE` branch ran before stored/submitted request
   identity equality.

Effective precedence is:

```text
R5 explicit replacements
→ R4 other explicit replacements
→ R3 other explicit replacements
→ R2 other explicit replacements
→ R1 all other clauses
```

R1-R4 subjects, manifests, reviews and dispositions remain immutable. R5 does
not add a delivery state, receipt kind, retry model, authority source,
implementation profile, runtime path, provider protocol or F6 semantic.

## 2. Closed Canonical Receipt Replay Record

For replay derivation, each stored or submitted receipt is represented by
exactly:

```yaml
source_id: stable_ref
receipt_id: stable_ref
receipt_fingerprint: lowercase_sha256
receipt_canonical_utf8_hex: lowercase_even_length_hex
```

`receipt_canonical_utf8_hex` MUST decode as strict UTF-8 JSON with no duplicate
keys, floats, unsafe integers, non-NFC strings, unknown fields, unknown enums or
type errors. Its decoded payload is exactly:

```yaml
interface_version: agents-os.f5-delivery-receipt-replay-payload.v0.1-r5
receipt_id: stable_ref
source_id: stable_ref
source_receipt_revision: positive_safe_integer
attempt_ref: stable_ref
attempt_fingerprint: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
effect_id: stable_ref
invocation_identity_fingerprint: lowercase_sha256
execution_epoch: positive_safe_integer
host_fence_generation: non_negative_safe_integer
effect_fence_generation: non_negative_safe_integer
receipt_kind: closed_R1_receipt_kind
effect_status: closed_R1_effect_status
observed_at_utc_ms: non_negative_safe_integer
received_at_utc_ms: non_negative_safe_integer
source_attestation_ref: stable_ref
source_attestation_fingerprint: lowercase_sha256
```

Validation order is mandatory:

1. strict-decode the exact bytes;
2. enforce the closed payload inventory and all field types;
3. require the supplied bytes to equal the canonical UTF-8 JSON encoding
   byte-for-byte;
4. require outer `source_id` and `receipt_id` to equal the decoded payload;
5. recompute `receipt_fingerprint = SHA-256(exact canonical bytes)`.

No detached `receipt_kind` or `effect_status` input exists. Compatibility,
currentness and disposition MUST use the values parsed from the submitted bound
receipt record.

## 3. Receipt Replay Relation Replacement

Both stored and submitted records MUST independently pass Section 2. When a
stored record exists, the two deduplication keys `(source_id, receipt_id)`
MUST match before any replay branch is selected.

```text
lookup not reproducible
  → LOOKUP_INDETERMINATE

no stored receipt
  → NEW

same key + same fingerprint + exact canonical bytes
  → EXACT_DUPLICATE

same key + any bound-byte or fingerprint difference
  → CHANGED_BYTES_SAME_KEY
```

`EXACT_DUPLICATE` may return `REPLAYED` only after the two complete canonical
records are byte-identical and fingerprint-identical. A changed bound
`receipt_kind`, `effect_status`, attempt, effect, invocation, epoch, fence,
time or attestation field is changed bytes and cannot replay.

The original R3 counterexample is preserved as an attack:

```text
keep stored/submitted bound records identical
add or change detached receipt_kind/effect_status
re-sign section and root
→ REJECT_CLOSED_INVENTORY
```

## 4. Arm Identity Equality Before Lookup Branching

R4 Section 9 canonical arm request parsing remains effective. R5 replaces the
branch order.

The reducer MUST:

1. parse and bind the submitted request;
2. if stored state exists, parse and bind its request record;
3. if stored state exists, require
   `stored.request_id == submitted.request_id`;
4. only then inspect `lookup_reproducible` and derive the relation.

The relation remains:

```text
identity mismatch
  → reject the proof input before relation selection

lookup not reproducible with equal identity
  → LOOKUP_INDETERMINATE

no stored arm
  → NO_EXISTING_ARM

equal identity + equal fingerprint + exact bytes
  → EXACT_DUPLICATE

equal identity + changed fingerprint or bytes
  → CHANGED_BYTES_SAME_IDENTITY
```

A complete, valid, canonical submitted request for a different request identity
MUST reject even when lookup is indeterminate and every section/root hash is
recomputed.

## 5. Fixed R5 Constructive Surface

The R5 subject surface is exactly:

```text
control-plane/registry/drafts/2026-07-17-agents-os-f5-outbox-delivery-recovery-v0.1-r5-amendment.draft.md
control-plane/registry/build-f5-r5-bound-replay-evidence-closure.py
control-plane/registry/examples/2026-07-17-agents-os-f5-r5-bound-replay-evidence-closure-v0.1.json
control-plane/registry/validate-f5-r5-bound-replay-evidence-closure.py
```

The fixture is synthetic, nonauthority, non-runtime-consumable and
non-recovery-importable. It models no accepted real handoff, claim Event,
armed dispatch, runtime action, external effect or provider call.

## 6. Required Fully Re-Signed Attacks

The R5 validator MUST reject after all attacker-controlled section and root
fingerprints are recomputed:

1. the original detached receipt-kind/status exact-replay override;
2. a changed submitted bound receipt kind/status presented as exact replay;
3. changed stored receipt bytes presented as exact replay;
4. noncanonical receipt bytes with their SHA-256 recomputed;
5. a receipt fingerprint not equal to the exact canonical bytes;
6. receipt outer key values not equal to the bound payload;
7. lookup-indeterminate arm input containing two different valid request IDs;
8. noncanonical or formula-invalid arm request records;
9. unknown root, section, row or nested raw fields.

R1-R4 validators MUST remain green and the R5 builder MUST reproduce the fixed
R5 fixture byte-for-byte.

## 7. R5 Acceptance Candidate Gate

```yaml
receipt_payload_inventory_closed: true
receipt_kind_and_effect_status_bound_in_canonical_bytes: true
stored_and_submitted_receipts_independently_recomputed: true
exact_receipt_replay_requires_bound_byte_identity: true
original_R3_receipt_probe_rejected: true

arm_records_independently_parsed_and_bound: true
stored_submitted_request_identity_checked_before_lookup_branch: true
R4_lookup_indeterminate_different_identity_probe_rejected: true

R1_R2_R3_R4_validators_pass: true
R5_builder_fixture_byte_equal: true
fresh_full_atomic_review: PASS_NO_BLOCKER
```

`PASS_NO_BLOCKER` stops F5 revision and prepares a Jenn-only atomic freeze
decision surface. It does not itself accept or freeze F5.

## 8. Explicit Non-Authorization

This amendment does not authorize:

```text
F5 acceptance or freeze
F6 start or semantics
Rust or JavaScript implementation
database layout or write
runtime activation
production authentication
provider or service access
real handoff, dispatch or physical effect
commit, push, PR, merge, release, deploy, publish or tag
formal Memory or private raw memory access
```
