# AGENTS OS F2 Actor Identity and Delegation v0.1 R4 Final Canonicalization Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R4_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r4
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope, fixed inputs, and exact precedence

R4 resolves only:

```text
F2-R3-IR-B01 complete activation canonicalization
F2-R3-IR-B02 complete issuance-action fingerprint binding
```

The fixed subjects remain unchanged:

```text
R1 SHA-256:
639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b

R2 SHA-256:
8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd

R3 SHA-256:
d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
```

R1, R2, R3, and R4 form one indivisible acceptance unit. R4 replaces only:

```text
R3 Section 3 binding_scope canonicalization
R2 Section 5 binding activation replay formula
R3 Section 3 binding evidence and assessment fingerprint prose
R2 Section 6 delegation activation replay formula
R3 Section 4 delegation evidence and assessment fingerprint prose
R3 Section 5.3 final delegation subject fingerprint formula
R3 Section 8 atomic acceptance clause
```

All other R1-R3 semantics remain unchanged. R4 adds no object to the five
canonical orchestration objects, no permission level, no risk matrix, no
ordinary-action allowlist, and no F3 implementation.

## 2. Canonicalization primitives

Every R4 formula uses:

```text
hash algorithm: SHA-256
serialization: RFC 8785 JSON Canonicalization Scheme (JCS)
text normalization: Unicode NFC before JCS
undefined value: forbidden
optional absent value in a listed position: JSON null
integer: JSON integer within the contract-declared range; float forbidden
boolean: JSON true or false
object member with unknown key: rejected
normalized-key collision: rejected
```

A field named `*_ref` in an R4 fingerprint projection is one normalized,
non-empty UTF-8 scalar stable-reference string. A structured referenced object
is never embedded directly. It contributes only the exact canonical fingerprint
defined for that object. Unknown fingerprint schema or algorithm is rejected.

Every `reason_codes` array is sorted by NFC-normalized UTF-8 byte order and
contains no duplicate. Array order not explicitly declared by this amendment or
an already accepted schema is forbidden rather than guessed.

Every named R4 fingerprint result is stored as the existing
`FingerprintEnvelope`:

```yaml
R4FingerprintEnvelope:
  algorithm: SHA-256
  canonicalization_contract_version: agents-os.f2-r4-jcs.v0.1
  digest_lowercase_hex: exactly_64_lowercase_hex_characters
```

When one R4 formula contains another `*_fingerprint`, the inserted JCS value is
the verified `digest_lowercase_hex` string, not the envelope object. An invalid
algorithm, version, or digest encoding is rejected.

## 3. Closed BindingScope v0.1

R4 replaces the undefined R1 `binding_scope` value with:

```yaml
BindingScopeV0_1:
  schema_version: agents-os.binding-scope.v0.1
  scope_kind: EXACT_REPRESENTATION_CONTEXT_SET
  contexts:
    - context_kind: SESSION | SURFACE | HOST_PROCESS | SERVICE_INSTANCE | SYNTHETIC_FIXTURE
      context_id:
      context_revision: nonnegative_integer
```

This scope describes only where one Principal may represent one Actor. It does
not describe allowed actions, capabilities, responsibility, trust, or
permission.

`contexts` must be non-empty. It is sorted by:

```text
context_kind UTF-8 bytes
then context_id UTF-8 bytes
then integer context_revision ascending
```

Duplicate normalized `(context_kind, context_id, context_revision)` tuples are
rejected. Wildcard, glob, regex, subtree, future context, free-form map, and
unknown context kind are forbidden in v0.1.

`context_revision = 0` denotes an immutable context namespace that has no
separate revision counter; positive values bind an explicit revision.

The exact scope fingerprint is:

```text
binding_scope_fingerprint = SHA-256(JCS([
  "agents-os.binding-scope.v0.1",
  "EXACT_REPRESENTATION_CONTEXT_SET",
  [[context_kind, context_id, context_revision], ...]
]))
```

R3 `binding_subject_fingerprint` replaces its raw `binding_scope` position with
`binding_scope_fingerprint`. The binding subject stores both the validated
`BindingScopeV0_1` value and its fingerprint. Any mismatch is rejected.

## 4. Canonical referenced-object fingerprints

### 4.1 Principal control proof assessment ref

The exact fingerprint for the R2
`PrincipalControlProofAssessmentRef` is:

```text
principal_control_proof_assessment_ref_fingerprint = SHA-256(JCS([
  "agents-os.principal-control-proof-assessment-ref.v0.1",
  interface_version,
  assessment_ref_id,
  principal_id,
  principal_revision,
  authenticator_profile_ref,
  verifier_id,
  verifier_revision,
  challenge_fingerprint,
  "VERIFIED",
  assessed_at_event_sequence
]))
```

No other assessment value can be referenced by activation evidence.

### 4.2 Authenticated actor action ref

R2 `AuthenticatedActorActionRef` gains:

```yaml
R4_authenticated_actor_action_ref_addition:
  canonical_action_ref_fingerprint:
```

Its exact fingerprint is:

```text
canonical_action_ref_fingerprint = SHA-256(JCS([
  "agents-os.authenticated-actor-action-ref.v0.1",
  interface_version,
  action_ref_id,
  F3_contract_version,
  command_id,
  command_envelope_ref,
  command_envelope_fingerprint,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_binding_ref,
  authentication_assertion_ref,
  authentication_assessment_ref,
  responsibility_source_ref,
  delegation_chain_fingerprint_or_null,
  prohibited_behavior_list_revision,
  prohibited_boundary_evidence_ref,
  F3_intake_event_sequence,
  F3_intake_state_ref
]))
```

The fingerprint excludes only `canonical_action_ref_fingerprint` itself. Every
listed `*_ref` is a scalar stable reference under Section 2. F3 must emit this
fingerprint from the immutable COMMITTED action-attribution bytes. F2 verifies
it; F2 cannot construct or self-attest it.

Every R2/R3 F2 fingerprint that includes an `AuthenticatedActorActionRef`
includes only this complete fingerprint at that position, never a partial field
projection and never implementation-specific object serialization.

### 4.3 Delegation activation acknowledgement ref

The exact fingerprint for R3
`DelegationActivationAcknowledgementRef` is:

```text
delegation_activation_ack_ref_fingerprint = SHA-256(JCS([
  "agents-os.delegation-activation-acknowledgement-ref.v0.1",
  interface_version,
  acknowledgement_ref_id,
  F3_contract_version,
  "COMMITTED",
  "DELEGATION_ACTIVATION_ACK",
  intake_event_sequence,
  command_envelope_ref,
  command_envelope_fingerprint,
  "DELEGATION_ACTIVATION_ACK",
  delegation_ref,
  delegation_subject_fingerprint,
  delegate_actor_id,
  delegate_actor_identity_revision,
  acknowledging_principal_id,
  acknowledging_principal_revision,
  acknowledging_principal_binding_ref,
  authentication_assertion_ref,
  authentication_assessment_ref,
  "NONE_ACTIVATION_PURPOSE_ONLY",
  prohibited_behavior_list_revision,
  prohibited_boundary_evidence_ref,
  replay_identity
]))
```

The first `DELEGATION_ACTIVATION_ACK` is `intake_purpose`; the second is
`command_type_id`. Both positions are retained so a changed or omitted field
cannot produce the same fingerprint.

## 5. Exact binding activation projections

### 5.1 Binding evidence replay identity

R4 replaces the R2 binding replay formula with:

```text
binding_activation_evidence_replay_identity = SHA-256(JCS([
  "agents-os.binding-activation-evidence-replay.v0.1",
  evidence_id,
  target_binding_ref,
  binding_subject_fingerprint,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_class,
  environment,
  authenticator_profile_ref,
  verifier_revision,
  principal_control_proof_assessment_ref_fingerprint,
  activation_mode,
  stewardship_source.kind,
  stewardship_source.source_ref,
  steward_actor_id_or_null,
  steward_actor_identity_revision_or_null,
  steward_principal_binding_ref_or_null,
  canonical_steward_action_ref_fingerprint_or_null,
  not_before_utc_ms,
  expires_at_utc_ms
]))
```

The replay identity intentionally excludes evidence revision, status, and Event
sequence so later revoke/supersede revisions remain in the same evidence stream.
Changing any activation-defining input changes the replay identity.

### 5.2 Binding activation evidence fingerprint

The exact fingerprint is:

```text
binding_activation_evidence_fingerprint = SHA-256(JCS([
  "agents-os.binding-activation-evidence.v0.1",
  evidence_id,
  evidence_revision,
  expected_previous_evidence_revision_or_null,
  supersedes_evidence_revision_or_null,
  target_binding_ref,
  binding_subject_fingerprint,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_class,
  environment,
  authenticator_profile_ref,
  verifier_revision,
  principal_control_proof_assessment_ref_fingerprint,
  activation_mode,
  stewardship_source.kind,
  stewardship_source.source_ref,
  steward_actor_id_or_null,
  steward_actor_identity_revision_or_null,
  steward_principal_binding_ref_or_null,
  canonical_steward_action_ref_fingerprint_or_null,
  not_before_utc_ms,
  expires_at_utc_ms,
  binding_activation_evidence_replay_identity,
  status,
  created_at_event_sequence
]))
```

It excludes only its own fingerprint field. The bootstrap path requires all
four steward fields/fingerprint positions to be null; every non-bootstrap path
requires all of them to be non-null and current.

### 5.3 Binding activation assessment fingerprint

The exact fingerprint is:

```text
binding_activation_assessment_fingerprint = SHA-256(JCS([
  "agents-os.binding-activation-assessment.v0.1",
  binding_ref,
  binding_subject_fingerprint,
  activation_evidence_id,
  activation_evidence_revision,
  binding_activation_evidence_fingerprint,
  assessment,
  sorted_unique_reason_codes,
  assessed_at_event_sequence,
  assessed_at_utc_ms
]))
```

It excludes only `canonical_fingerprint`, whose value must equal this result.

## 6. Exact delegation activation projections

R3's replacement of `acknowledging_action_ref` remains effective. No R4 formula
contains that removed field.

### 6.1 Delegation evidence replay identity

R4 replaces the R2 delegation replay formula with:

```text
delegation_activation_evidence_replay_identity = SHA-256(JCS([
  "agents-os.delegation-activation-evidence-replay.v0.1",
  evidence_id,
  delegation_ref,
  delegation_subject_fingerprint,
  activation_mode,
  delegate_actor_id,
  delegate_actor_identity_revision,
  acknowledging_principal_binding_ref,
  delegation_activation_ack_ref_fingerprint,
  not_before_utc_ms,
  expires_at_utc_ms
]))
```

It excludes evidence revision, status, and Event sequence for the same reason as
Section 5.1. It binds the complete R3 acknowledgement through its exact
fingerprint.

### 6.2 Delegation activation evidence fingerprint

The exact fingerprint is:

```text
delegation_activation_evidence_fingerprint = SHA-256(JCS([
  "agents-os.delegation-activation-evidence.v0.1",
  evidence_id,
  evidence_revision,
  expected_previous_evidence_revision_or_null,
  supersedes_evidence_revision_or_null,
  delegation_ref,
  delegation_subject_fingerprint,
  activation_mode,
  delegate_actor_id,
  delegate_actor_identity_revision,
  acknowledging_principal_binding_ref,
  delegation_activation_ack_ref_fingerprint,
  not_before_utc_ms,
  expires_at_utc_ms,
  delegation_activation_evidence_replay_identity,
  status,
  created_at_event_sequence
]))
```

It excludes only its own fingerprint field.

### 6.3 Delegation activation assessment fingerprint

The exact fingerprint is:

```text
delegation_activation_assessment_fingerprint = SHA-256(JCS([
  "agents-os.delegation-activation-assessment.v0.1",
  delegation_ref,
  delegation_subject_fingerprint,
  delegation_activation_ack_ref_fingerprint,
  activation_evidence_id,
  activation_evidence_revision,
  delegation_activation_evidence_fingerprint,
  assessment,
  sorted_unique_reason_codes,
  assessed_at_event_sequence,
  assessed_at_utc_ms
]))
```

It excludes only `canonical_fingerprint`, whose value must equal this result.

## 7. Complete issuance-action binding

The R3 intent-first acyclic order remains unchanged:

```text
delegation issuance intent
-> F3 COMMITTED issuance action
-> complete AuthenticatedActorActionRef fingerprint
-> final DelegationGrantRevision subject
-> activation acknowledgement and evidence
```

R4 replaces the R3 final delegation subject formula with:

```text
delegation_subject_fingerprint = SHA-256(JCS([
  "agents-os.delegation-grant-subject.v0.1-r4",
  delegation_issuance_intent_fingerprint,
  issuance_action_ref.F3_contract_version,
  issuance_action_ref.canonical_action_ref_fingerprint,
  created_at_event_sequence
]))
```

The final subject stores the complete `AuthenticatedActorActionRef` and its
fingerprint. The reducer recomputes the fingerprint from every declared action
ref field and requires exact equality before accepting the grant. Changing any
Actor, identity revision, Principal, binding, authentication ref,
responsibility source, delegation-chain fingerprint, Prohibited Behavior List
revision, boundary evidence, F3 version, intake sequence, or intake-state ref
therefore changes or invalidates the final delegation subject fingerprint.

The issuance action still commits only the pre-action
`delegation_issuance_intent_fingerprint`; it never references the final subject.
The cycle remains broken.

## 8. Cross-writer, recovery, and tamper fixtures

A future authorized implementation must provide identical canonical fixture
bytes and hashes from at least two independent implementations for:

```text
BindingScopeV0_1 with two differently ordered inputs that normalize to
  byte-identical canonical context arrays and fingerprints
PrincipalControlProofAssessmentRef fingerprint
AuthenticatedActorActionRef with and without delegation_chain_fingerprint
DelegationActivationAcknowledgementRef fingerprint
binding evidence replay and evidence fingerprint
binding assessment fingerprint with unsorted input reason codes
delegation evidence replay and evidence fingerprint
delegation assessment fingerprint with unsorted input reason codes
final delegation subject fingerprint
```

Negative fixtures must change each projected field one at a time while holding
all other fields constant and prove that the relevant fingerprint changes or
the object is rejected. They must additionally cover:

```text
unknown BindingScope field or context kind
empty, duplicate, wildcard, or invalid-revision BindingScope contexts
unknown nested fingerprint schema
raw structured object supplied where a scalar ref is required
removed acknowledging_action_ref supplied to delegation evidence
partial AuthenticatedActorActionRef projection
same old three action fields with changed Actor, Principal binding,
  responsibility source, Prohibited Boundary evidence, or F3 version
fixed-point/self-field inclusion
stale or forked evidence revision
startup recovery with one persisted fingerprint byte changed
```

Startup recovery recomputes in this order:

```text
closed scope and referenced-object fingerprints
immutable binding and delegation subject fingerprints
activation acknowledgement fingerprint
evidence replay identities and evidence fingerprints
assessment fingerprints
current projections
```

Any mismatch, unknown version, missing dependency, or cross-writer disagreement
produces `INDETERMINATE` or rejection under the owning reducer. Recovery never
chooses an implementation-specific serialization and never repairs persisted
bytes silently.

## 9. Finding disposition and non-authorization

| Finding | R4 disposition |
|---|---|
| `F2-R3-IR-B01` | resolved by Sections 2-6 and 8 |
| `F2-R3-IR-B02` | resolved by Sections 4.2, 7, and 8 |

R4 does not reopen findings already resolved by R2/R3. Remaining downstream
dependencies are unchanged:

```text
one canonical Prohibited Behavior List and synchronized governance convergence
accepted F3 Command/intake/immutable-action-ref/single-writer contract
accepted F4 TaskPermit, host authentication, and effect-fencing contract
separate production authenticator, credential, trust-anchor, and provisioning review
explicit Jenn implementation and runtime-activation decisions
```

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R4_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - F2_R2_amendment_sha256_8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
  - F2_R3_amendment_sha256_d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
  - this_exact_R4_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

Accepting this bundle would accept architecture semantics only. It would not
implement canonicalization code, create identities or credentials, change a
database, start F3, issue TaskPermits, run services or providers, admit host
effects, or activate runtime behavior.
