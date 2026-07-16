# AGENTS OS F2 Actor Identity and Delegation v0.1 R3 Final Narrow Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R3_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r3
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Amendment scope and precedence

This amendment resolves only the three blockers in the fixed R2 independent
review:

```text
F2-R2-IR-B01 non-circular delegation activation acknowledgement
F2-R2-IR-B02 acyclic and exact activation fingerprint graphs
F2-R2-IR-B03 assignment self-issuance and delegation issuance provenance
```

It does not modify the fixed R1 or R2 bytes:

```text
R1 SHA-256:
639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b

R2 SHA-256:
8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
```

R1, R2, and this R3 amendment form one indivisible acceptance unit. On
conflict, R3 replaces only the exact R1/R2 clauses named here. All other clauses
remain unchanged.

The exact replacements are:

```text
R2 Section 6 acknowledging_action_ref and its responsibility-dependent path
R2 Section 5 activation_evidence_ref as an immutable binding-subject field
R1 Section 11.1 activation_evidence_ref as an immutable grant-subject field
R2 Section 9 activation fingerprint/head bullets where they conflict with
  the acyclic subject -> evidence -> assessment graphs in R3 Sections 3-4
R2 Section 12 atomic acceptance clause, replaced by R3 Section 8
```

The single-boundary direction remains unchanged:

```text
identity answers who acts
responsibility and delegation answer who owns work
domain invariants define correct state changes
one canonical Prohibited Behavior List defines the prohibited line
```

R3 adds no permission level, risk tier, ordinary-action allowlist, trust score,
or parallel authorization model.

## 2. Non-circular delegation activation acknowledgement

R3 replaces R2 Section 6 field `acknowledging_action_ref` with the following
narrow external interface:

```yaml
DelegationActivationAcknowledgementRef:
  interface_version: agents-os.delegation-activation-acknowledgement-ref.v0.1
  acknowledgement_ref_id:
  F3_contract_version:
  intake_state: COMMITTED
  intake_purpose: DELEGATION_ACTIVATION_ACK
  intake_event_sequence:

  command_envelope_ref:
  command_envelope_fingerprint:
  command_type_id: DELEGATION_ACTIVATION_ACK

  delegation_ref:
  delegation_subject_fingerprint:
  delegate_actor_id:
  delegate_actor_identity_revision:

  acknowledging_principal_id:
  acknowledging_principal_revision:
  acknowledging_principal_binding_ref:
  authentication_assertion_ref:
  authentication_assessment_ref:

  responsibility_source_mode: NONE_ACTIVATION_PURPOSE_ONLY
  prohibited_behavior_list_revision:
  prohibited_boundary_evidence_ref:
  replay_identity:
```

This acknowledgement proves only that a currently authenticated Principal,
through a current active binding to the exact delegate Actor revision,
acknowledged one exact pending delegation subject. It does not prove current
responsibility, does not make the pending grant a responsibility source, and
cannot carry a domain mutation or effect request.

F3 must define `DELEGATION_ACTIVATION_ACK` as a closed activation-purpose
Command type. In one Rust single-writer transaction it must:

```text
authenticate the exact Principal and current active binding
verify the binding belongs to the exact delegate Actor revision
verify the exact delegation revision is current, pending activation,
  unexpired, unrecalled, and not superseded
verify the envelope names the exact delegation subject fingerprint
require responsibility_source_mode = NONE_ACTIVATION_PURPOSE_ONLY
verify the current canonical Prohibited Behavior List boundary
reserve command and acknowledgement replay identities
commit the acknowledgement, activation evidence, activation assessment,
  and activation Event atomically
```

It must reject:

```text
PENDING, REJECTED, or OUTCOME_INDETERMINATE intake
use of the pending grant as its own responsibility source
any assignment or delegation offered as the acknowledgement responsibility
wrong, stale, suspended, revoked, or indeterminate Principal binding
wrong Actor, identity revision, grant revision, or subject fingerprint
expired, recalled, superseded, already-active, or indeterminate grant
unknown fields, domain mutation payload, provider request, or effect request
duplicate replay identity with different canonical bytes
```

The replay identity is:

```text
SHA-256(JCS([
  "agents-os.delegation-activation-ack.v0.1",
  command_envelope_fingerprint,
  delegation_ref,
  delegation_subject_fingerprint,
  acknowledging_principal_binding_ref
]))
```

JCS means RFC 8785 JSON Canonicalization Scheme over the exact array above.
String values are Unicode NFC before JCS; normalized-key collisions are
rejected. This narrow interface remains an F3 implementation dependency. R3
does not start F3 or authorize runtime intake.

R2 `DelegationActivationEvidence` is corrected to contain:

```yaml
R3_delegation_activation_evidence_replacement:
  acknowledgement_ref: DelegationActivationAcknowledgementRef
```

and no `acknowledging_action_ref`. The acknowledgement is valid without an
`AuthenticatedActorActionRef` and without a responsibility source. All later
ordinary Commands still require the responsibility attribution defined by F3.

## 3. Acyclic binding activation fingerprint graph

R3 replaces the R2 rule that places `activation_evidence_ref` inside the target
binding revision. The immutable binding subject never points to activation
evidence or activation assessment.

The only valid dependency order is:

```text
ActorPrincipalBindingRevision subject
-> binding_subject_fingerprint
-> BindingActivationEvidence
-> binding_activation_evidence_fingerprint
-> BindingActivationAssessment
-> binding_current_projection
```

`ActorPrincipalBindingRevision` gains `principal_revision`. Its subject
fingerprint is:

```text
SHA-256(JCS([
  "agents-os.actor-principal-binding-subject.v0.1",
  binding_id,
  binding_revision,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_class,
  authenticator_profile_ref,
  environment,
  not_before_utc_ms,
  expires_at_utc_ms_or_null,
  binding_scope,
  issued_by_actor_ref,
  issuance_basis_ref,
  activation_mode,
  status,
  created_at_event_sequence,
  supersedes_binding_revision_or_null
]))
```

JCS and Unicode rules are those in Section 2. `binding_scope` uses its
declared schema order; any unordered collection inside it must be sorted by its
stable key before JCS, with duplicate keys rejected.

The subject fingerprint excludes:

```text
activation_evidence_ref or fingerprint
activation assessment ref or fingerprint
current-head and projection pointers
display, cache, and recovery-only fields
```

The stable evidence identity is exact:

```text
evidence_id = SHA-256(JCS([
  "agents-os.binding-activation-evidence-id.v0.1",
  binding_id,
  binding_revision
]))
```

R2 `BindingActivationEvidence.target_binding_fingerprint` means only the exact
`binding_subject_fingerprint`. The evidence canonical fingerprint covers every
declared evidence field, including `evidence_id`, revision/CAS fields, exact
subject ref and fingerprint, proof assessment, stewardship, replay identity,
time, status, and Event sequence. It excludes only its own
`canonical_fingerprint` field.

```yaml
BindingActivationAssessment:
  binding_ref:
  binding_subject_fingerprint:
  activation_evidence_id:
  activation_evidence_revision:
  activation_evidence_fingerprint:
  assessment: ACTIVE | INACTIVE | INDETERMINATE
  reason_codes: []
  assessed_at_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint:
```

The current projection points to this assessment; the immutable binding subject
does not point backward. A fixed-point fingerprint, wrong subject revision,
wrong evidence ID, stale or forked evidence head, mismatched subject
fingerprint, unknown schema version, or indeterminate dependency cannot produce
an `ACTIVE` assessment.

The R2 sentence requiring binding evidence and a binding current pointer to be
accepted atomically is replaced with: after the immutable binding subject
exists, the Rust single writer accepts the exact evidence revision, derives the
assessment, appends the activation Event, and advances the current assessment
projection in one transaction. The subject bytes and subject fingerprint do not
change in that transaction.

## 4. Acyclic delegation activation fingerprint graph

R3 likewise removes R1 `activation_evidence_ref` from the immutable
`DelegationGrantRevision` subject. The only valid dependency order is:

```text
DelegationGrantRevision subject
-> delegation_subject_fingerprint
-> DelegationActivationAcknowledgementRef
-> DelegationActivationEvidence
-> delegation_activation_evidence_fingerprint
-> DelegationActivationAssessment
-> delegation_current_projection
```

The delegation subject fingerprint is computed only after the issuance action
has committed. It covers the exact ordered field list defined in Section 5.3.
It excludes:

```text
activation acknowledgement, evidence, and assessment refs or fingerprints
current-head and projection pointers
display, cache, and recovery-only fields
its own canonical_fingerprint field
```

R2 `delegation_fingerprint` is replaced by the exact term
`delegation_subject_fingerprint` wherever activation evidence is created or
verified.

The stable evidence identity is exact:

```text
evidence_id = SHA-256(JCS([
  "agents-os.delegation-activation-evidence-id.v0.1",
  delegation_id,
  delegation_revision
]))
```

The activation evidence canonical fingerprint covers every declared evidence
field, including the exact acknowledgement ref, subject ref/fingerprint,
revision/CAS fields, time, replay identity, status, and Event sequence. It
excludes only its own `canonical_fingerprint` field.

```yaml
DelegationActivationAssessment:
  delegation_ref:
  delegation_subject_fingerprint:
  activation_acknowledgement_ref:
  activation_evidence_id:
  activation_evidence_revision:
  activation_evidence_fingerprint:
  assessment: ACTIVE | INACTIVE | INDETERMINATE
  reason_codes: []
  assessed_at_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint:
```

The current projection points to the assessment. A fixed-point fingerprint,
wrong grant revision, wrong evidence ID, stale or forked evidence head, wrong
delegate acknowledgement, mismatched subject fingerprint, unknown schema
version, or indeterminate dependency cannot produce an `ACTIVE` assessment.

## 5. Assignment self-issuance and delegation issuance provenance

### 5.1 Responsibility assignment self-issuance is forbidden

Every `ResponsibilityAssignmentRevisionR2` must satisfy:

```text
actor_id != issued_by_actor_id
```

There is no v0.1 exception. A Jenn-root assignment uses
`source_responsibility.kind = JENN_ROOT_DIRECTION`: Jenn issues responsibility
to another Actor and does not assign responsibility to herself. Any revision
whose subject Actor equals its issuing Actor is rejected before current-state
assessment, including bootstrap, recovery, replacement, and superseding
revisions.

### 5.2 Delegation grant issuance provenance

Every R1 `DelegationGrantRevision` gains:

```yaml
R3_delegation_grant_issuance_fields:
  expected_previous_delegation_revision: null | integer

  issued_by_actor_id:
  issued_by_actor_identity_revision:
  issued_by_principal_binding_ref:
  issuance_action_ref: AuthenticatedActorActionRef
  issuer_currentness_event_sequence:

  root_direction_ref: optional
  root_direction_fingerprint: optional
  source_assignment_ref: optional
  source_assignment_fingerprint: optional

  delegation_issuance_intent_fingerprint:
```

These fields are immutable and are included in the delegation subject
fingerprint before any activation acknowledgement or evidence is created.

### 5.3 Acyclic issuance-intent and grant-subject fingerprints

Grant issuance follows this only valid order:

```text
proposed grant fields without issuance_action_ref
-> delegation_issuance_intent_fingerprint
-> F3 COMMITTED issuance action
-> immutable DelegationGrantRevision subject
-> delegation_subject_fingerprint
-> activation acknowledgement and evidence
```

The issuance-intent fingerprint is exact:

```text
SHA-256(JCS([
  "agents-os.delegation-issuance-intent.v0.1",
  delegation_id,
  delegation_revision,
  expected_previous_delegation_revision_or_null,
  supersedes_delegation_revision_or_null,
  delegator_actor_id,
  delegator_identity_revision,
  delegate_actor_id,
  delegate_identity_revision,
  parent_delegation_ref_or_null,
  source_responsibility_ref,
  responsibility_kind,
  responsibility_scope,
  may_redelegate,
  remaining_depth,
  not_before_utc_ms,
  expires_at_utc_ms,
  activation_mode,
  issued_by_actor_id,
  issued_by_actor_identity_revision,
  issued_by_principal_binding_ref,
  issuer_currentness_event_sequence,
  root_direction_ref_or_null,
  root_direction_fingerprint_or_null,
  source_assignment_ref_or_null,
  source_assignment_fingerprint_or_null,
  reason,
  status
]))
```

The F3 issuance Command must name this exact intent fingerprint. After F3
commits, the final delegation subject fingerprint is exact:

```text
SHA-256(JCS([
  "agents-os.delegation-grant-subject.v0.1",
  delegation_issuance_intent_fingerprint,
  issuance_action_ref.action_ref_id,
  issuance_action_ref.command_envelope_fingerprint,
  issuance_action_ref.F3_intake_event_sequence,
  created_at_event_sequence
]))
```

The final subject therefore commits to every pre-issuance grant field through
the intent fingerprint, then to the exact committed issuance action and final
grant Event sequence, without either fingerprint containing itself.
`canonical_fingerprint` on the grant equals this delegation subject
fingerprint. `responsibility_scope` and any nested unordered collection follow
the deterministic ordering rule in Section 3.

For every delegation grant:

```text
delegator_actor_id equals issued_by_actor_id
delegator_identity_revision equals issued_by_actor_identity_revision
issuance_action_ref identifies that same Actor revision and Principal binding
issuance_action_ref is backed by an F3 COMMITTED intake
issuer identity and binding are current at issuer_currentness_event_sequence
the issuance action names the exact delegation_issuance_intent_fingerprint
the final delegation subject fingerprint binds the exact committed action ref
```

The first Jenn-root delegation edge additionally requires:

```text
issued_by_actor_id is the current Jenn root Actor
root_direction_ref and root_direction_fingerprint are both present and current
source_assignment_ref and source_assignment_fingerprint are both absent
issuance_action_ref identifies the same Jenn Actor and active Jenn binding
issuance_action_ref responsibility source is that exact JENN_ROOT_DIRECTION
```

The first assignment-rooted delegation edge requires:

```text
source_assignment_ref and source_assignment_fingerprint are both present
the exact assignment is current ACTIVE and belongs to issued_by_actor_id
the assignment permits redelegation and contains kind, scope, time, and depth
root_direction fields are absent unless already normative in that assignment
issuance_action_ref responsibility source is that exact source assignment
```

Every child delegation edge requires:

```text
the exact current ACTIVE parent names issued_by_actor_id as its delegate
delegator_actor_id equals issued_by_actor_id
the parent permits redelegation and contains the child kind, scope, time,
  and remaining depth
the child preserves the exact root source and immediate parent revision
issuance_action_ref responsibility source is that exact active parent delegation
```

Delegation revision CAS is exact:

```text
revision 1
  -> expected_previous_delegation_revision = null
  -> supersedes_delegation_revision = null

revision N > 1
  -> expected_previous_delegation_revision = N - 1
  -> supersedes_delegation_revision = N - 1
  -> N - 1 is the current head in the accepting transaction
```

Missing, stale, forged, non-committed, indeterminate, wrong-Actor,
wrong-binding, wrong-subject, or forked issuance provenance rejects the grant.
No grant may cite its own pending or active delegation as issuance
responsibility for that same grant revision.

## 6. Recovery and required negative tests

Startup recovery order is fixed:

```text
rebuild immutable identity, binding, assignment, and delegation subject heads
recompute subject fingerprints
verify evidence streams against exact subject fingerprints and stable IDs
recompute activation assessments
publish current projections only after assessment currentness succeeds
```

Recovery cannot infer missing evidence, repair a fork by choosing one branch,
or promote an indeterminate dependency to active.

A future authorized implementation must add at least:

```text
first-responsibility delegation acknowledgement without responsibility succeeds
activation acknowledgement using pending grant as responsibility is rejected
activation acknowledgement carrying a domain mutation is rejected
activation acknowledgement from wrong or stale binding is rejected
binding subject/evidence fingerprint fixed point is rejected
delegation subject/evidence fingerprint fixed point is rejected
wrong subject revision, wrong subject fingerprint, and wrong evidence ID rejected
stale and forked activation evidence heads rejected
self-issued responsibility assignment rejected on every revision
Jenn-root delegation missing root ref/fingerprint/action rejected
Jenn-root delegation from wrong Actor or Principal binding rejected
assignment-rooted delegation with stale or mismatched assignment rejected
child delegation whose issuer differs from delegator rejected
non-COMMITTED or indeterminate issuance action rejected
```

## 7. Finding disposition and remaining dependencies

| Finding | R3 disposition |
|---|---|
| `F2-R2-IR-B01` | resolved by the responsibility-free, activation-only acknowledgement in Section 2 |
| `F2-R2-IR-B02` | resolved by the acyclic subject, evidence, assessment graphs and exact evidence IDs in Sections 3-4 |
| `F2-R2-IR-B03` | resolved by the no-self-issuance invariant and canonical grant provenance in Section 5 |

The original `F2-IR-B03` Command/replay ownership finding remains resolved by
R2's explicit F3 ownership replacement. The original `F2-IR-M01` identity
recovery finding remains resolved by R2 Section 7.

Remaining dependencies are explicit and are not supplied by R3:

```text
one canonical Prohibited Behavior List and synchronized governance convergence
accepted F3 Command/intake/single-writer contract
accepted F4 TaskPermit, host authentication, and effect-fencing contract
separate production authenticator, credential, trust-anchor, and provisioning review
authorized implementation and runtime activation decisions
```

## 8. Atomic acceptance and non-authorization

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R3_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - F2_R2_amendment_sha256_8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
  - this_exact_R3_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

Accepting this atomic bundle would accept architecture semantics only. It would
not create identities, bindings, assignments, delegations, credentials,
database schema, services, providers, TaskPermits, host effects, production
authentication, F3 implementation, or runtime activation.
