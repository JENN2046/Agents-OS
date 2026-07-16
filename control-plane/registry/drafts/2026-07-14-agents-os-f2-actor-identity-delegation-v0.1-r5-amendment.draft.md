# AGENTS OS F2 Actor Identity and Delegation v0.1 R5 Final Scalar Encoding Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R5_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r5
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and exact precedence

R5 resolves only:

```text
F2-R4-IR-B01 exact SHA-derived digest scalar storage and JCS insertion
F2-R4-IR-B02 exact BindingScope context scalar types and bounds
```

The fixed R1-R4 subjects remain unchanged:

```text
R1 639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
R2 8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
R3 d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
R4 a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
```

R1 through R5 form one indivisible acceptance unit. R5 replaces only:

```text
R3 SHA-derived replay_identity and stable evidence_id result representations
R4 Section 2 where its fingerprint-result rule does not cover replay_identity
  or evidence_id
R4 Section 3 context_id and context_revision scalar constraints
R4 Sections 4.3, 5, and 6 insertion semantics for replay_identity and evidence_id
R4 Section 9 atomic acceptance clause
```

All other R1-R4 semantics and formulas remain unchanged.

## 2. CanonicalDigestScalarV0_1

Every SHA-derived field named `replay_identity` or stable `evidence_id` in the
R3-R5 activation contracts uses this exact value type:

```yaml
CanonicalDigestScalarV0_1:
  JSON_type: string
  derivation_algorithm: SHA-256
  canonicalization_contract_version: agents-os.f2-digest-scalar.v0.1
  owning_input_serialization: RFC_8785_JCS_under_the_exact_domain_tagged_formula
  digest_source: raw_32_octet_SHA256_result
  persisted_encoding: lowercase_hex
  encoded_length: 64_ASCII_characters
  accepted_pattern: "^[0-9a-f]{64}$"
  JCS_inserted_value: the_exact_persisted_JSON_string
```

Derivation is exact:

```text
1. Construct the owning formula's JCS bytes exactly.
2. Compute the 32-octet SHA-256 digest.
3. Encode each octet as two lowercase hexadecimal ASCII characters.
4. Persist the resulting 64-character JSON string.
5. Whenever a later JCS formula contains this field, insert that exact JSON
   string value, without decoding, prefixing, wrapping, or re-encoding it.
```

The following representations are rejected:

```text
raw byte array
JSON number or object
FingerprintEnvelope
uppercase or mixed-case hexadecimal
base64 or base64url
0x prefix
sha256: prefix
leading or trailing whitespace
length other than 64
non-hexadecimal character
```

The algorithm and canonicalization version are fixed by the owning
domain-separated formula, not repeated inside the persisted scalar. This type
is deliberately distinct from R4 `R4FingerprintEnvelope`, which remains the
stored representation for fields named `*_fingerprint` and
`canonical_fingerprint`.

## 3. Exact field coverage

`CanonicalDigestScalarV0_1` applies to exactly these existing fields:

| Field | Owning derivation |
|---|---|
| `DelegationActivationAcknowledgementRef.replay_identity` | R3 `agents-os.delegation-activation-ack.v0.1` formula |
| `BindingActivationEvidence.evidence_id` | R3 `agents-os.binding-activation-evidence-id.v0.1` formula |
| `DelegationActivationEvidence.evidence_id` | R3 `agents-os.delegation-activation-evidence-id.v0.1` formula |
| `BindingActivationEvidence.replay_identity` | R4 `agents-os.binding-activation-evidence-replay.v0.1` formula |
| `DelegationActivationEvidence.replay_identity` | R4 `agents-os.delegation-activation-evidence-replay.v0.1` formula |

Every occurrence of one of these fields in an R4 acknowledgement, evidence,
assessment, recovery, or current-projection formula inserts the exact persisted
lowercase-hex JSON string. It never inserts raw digest bytes or an envelope.

R3 stable evidence IDs remain stable per exact target revision. Evidence status
revisions reuse the same scalar ID. R4 replay identities continue to exclude
evidence revision, status, and Event sequence as already specified; R5 changes
only their result representation, not their semantic input projection.

## 4. Closed BindingScope context scalars

R5 replaces the two under-typed R4 `BindingScopeV0_1.contexts` fields with:

```yaml
BindingScopeContextV0_1:
  context_kind: SESSION | SURFACE | HOST_PROCESS | SERVICE_INSTANCE | SYNTHETIC_FIXTURE
  context_id: NFC_nonempty_UTF8_JSON_string
  context_revision: JCS_SAFE_UINT
```

### 4.1 context_id

`context_id` must satisfy all of:

```text
JSON type is string
input is a valid Unicode scalar-value sequence
value is normalized with Unicode 15.1.0 NFC data before validation and comparison
normalized value contains 1 through 256 Unicode scalar values inclusive
normalized value contains no U+0000-U+001F, U+007F, or U+0080-U+009F
normalized UTF-8 bytes are used for ordering and equality
```

Empty normalized value, wrong JSON type, invalid Unicode, excessive length, or
forbidden control character is rejected. Two source strings that normalize to
the same NFC value are the same context ID; duplicate tuple rules apply after
normalization.

### 4.2 context_revision

`context_revision` is `JCS_SAFE_UINT`:

```text
JSON type is number
mathematical value is an integer
minimum = 0
maximum = 9007199254740991
fraction, exponent that does not represent an in-range exact integer,
  negative value, NaN, infinity, string, boolean, null, and overflow are rejected
```

After RFC 8785 JSON number parsing, acceptance is exactly equivalent to:

```text
ECMAScript Number.isSafeInteger(value) && value >= 0
```

`9007199254740991` is `2^53 - 1`, the largest integer exactly interoperable in
the RFC 8785 / ECMAScript number domain. `0` retains the R4 meaning of an
immutable context namespace without a separate revision counter.

### 4.3 Scope sorting and fingerprint insertion

R4 ordering remains:

```text
context_kind NFC UTF-8 bytes
then normalized context_id UTF-8 bytes
then context_revision numeric ascending
```

The exact normalized string and exact JCS number are inserted into the R4
`binding_scope_fingerprint` tuple. Different input order produces the same
sorted tuple array. A normalization collision or duplicate normalized tuple is
rejected.

`BindingScopeV0_1` remains representation-only. These fields do not express an
action allowlist, capability, trust, responsibility, or permission.

## 5. Cross-writer and boundary fixtures

A future authorized implementation must provide byte-identical results from at
least two independent implementations for:

```text
all-zero and all-0xff 32-octet digests encoded as lowercase hex
each of the five fields in Section 3
embedding each scalar into its immediate parent JCS formula
context_id NFC-equivalent source strings
context_id lengths 1 and 256 Unicode scalar values
context_revision values 0, 1, 9007199254740990, and 9007199254740991
BindingScope tuples supplied in different input orders
```

Negative fixtures must reject:

```text
raw-byte, array, number, object, Envelope, base64, prefixed, uppercase,
  mixed-case, short, long, whitespace-padded, or non-hex digest values
empty, non-string, invalid-Unicode, 257-scalar, or control-bearing context_id
two context IDs that collide after NFC normalization
context_revision -1, 9007199254740992, fraction, inexact exponent,
  string, boolean, null, NaN, or infinity
```

Startup recovery validates scalar types and bounds before recomputing parent
fingerprints. Any persisted representation mismatch produces rejection or the
owning reducer's `INDETERMINATE`; recovery never silently converts legacy or
alternate encodings.

## 6. Finding disposition and non-authorization

| Finding | R5 disposition |
|---|---|
| `F2-R4-IR-B01` | resolved by Sections 2, 3, and 5 |
| `F2-R4-IR-B02` | resolved by Sections 4 and 5 |

The R4 independent review already confirmed the complete
`AuthenticatedActorActionRef` binding and acyclic intent/action/subject graph;
R5 does not change them.

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R5_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - F2_R2_amendment_sha256_8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
  - F2_R3_amendment_sha256_d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
  - F2_R4_amendment_sha256_a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
  - this_exact_R5_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R5 does not implement an encoder, migrate stored data, create identity or
credential facts, start F3, change a database, issue a TaskPermit, run a service
or provider, admit a host effect, or activate runtime behavior.
