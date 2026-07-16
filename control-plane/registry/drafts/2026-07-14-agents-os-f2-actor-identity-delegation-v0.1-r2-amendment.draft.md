# AGENTS OS F2 Actor Identity and Delegation v0.1 R2 Narrow Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R2_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r2
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

This amendment resolves only:

```text
F2-IR-B01 responsibility assignment provenance, lineage, and attenuation
F2-IR-B02 binding and delegation activation evidence
F2-IR-B03 Command boundary ownership and replay handoff
F2-IR-M01 identity creation and compromise-recovery provenance
```

It does not modify the fixed R1 bytes:

```text
control-plane/registry/drafts/
2026-07-14-agents-os-actor-identity-delegation-v0.1.draft.md

SHA-256:
639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
```

R1 plus this amendment form one indivisible acceptance unit. On conflict, this
amendment replaces only the exact R1 clauses named below. All other R1 clauses
remain unchanged.

The accepted permission direction remains:

```text
one Prohibited Behavior List
ordinary work autonomous by default
identity is not permission
responsibility is not permission
delegation does not grant permission
domain invariants are not permission levels
```

This amendment adds no permission ladder, risk matrix, ordinary-action
allowlist, trust score, or `ALLOW / DENY` authorization state machine.

## 2. Common external action-attribution interface

F2 needs exact evidence that an identified Principal performed an action, but
F2 does not own the Command bus. The following is an external reference
interface, not a new F2 Command object:

```yaml
AuthenticatedActorActionRef:
  interface_version: agents-os.authenticated-actor-action-ref.v0.1
  action_ref_id:
  F3_contract_version:
  command_id:
  command_envelope_ref:
  command_envelope_fingerprint:
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_revision:
  principal_binding_ref:
  authentication_assertion_ref:
  authentication_assessment_ref:
  responsibility_source_ref:
  delegation_chain_fingerprint: optional
  prohibited_behavior_list_revision:
  prohibited_boundary_evidence_ref:
  F3_intake_event_sequence:
  F3_intake_state_ref:
```

The reference is valid only when F3 proves that all fields describe the same
immutable Command envelope and the same atomically accepted intake fact. A
caller cannot construct or self-attest it. Until F3 is accepted and implemented,
only deterministic synthetic contract fixtures may contain this interface.
Only an F3 `COMMITTED` intake state may back an action used as stewardship,
issuance, or activation evidence. `PENDING`, `REJECTED`, and
`OUTCOME_INDETERMINATE` cannot do so.

## 3. Responsibility assignment provenance and lineage

This section replaces R1 Section 9.2 `ResponsibilityAssignmentRevision`.

```yaml
ResponsibilityAssignmentRevisionR2:
  assignment_id:
  assignment_revision:
  expected_previous_assignment_revision: null | integer
  supersedes_assignment_revision: null | integer

  actor_id:
  actor_identity_revision:
  responsibility_kind:
  responsibility_scope: ResponsibilityScope
  may_redelegate: true | false
  max_redelegation_depth:
  not_before_utc_ms:
  expires_at_utc_ms: optional

  source_responsibility:
    kind: JENN_ROOT_DIRECTION | PARENT_ASSIGNMENT
    source_ref:
  issued_by_actor_id:
  issued_by_actor_identity_revision:
  issued_by_principal_binding_ref:
  issuance_action_ref: AuthenticatedActorActionRef
  responsibility_basis_ref:
  issuer_currentness_event_sequence:

  status: ACTIVE | SUSPENDED | REVOKED | SUPERSEDED
  created_at_event_sequence:
  canonical_fingerprint: FingerprintEnvelope
```

### 3.1 Closed issuance sources

`JENN_ROOT_DIRECTION` is valid only when:

```text
issued_by_actor_id is the current Jenn root Actor
issuance_action_ref identifies that same Jenn Actor and an active Jenn Principal binding
the referenced root direction or governance decision is current
the assignment does not cross the Prohibited Behavior List
```

`PARENT_ASSIGNMENT` is valid only when:

```text
source_ref is one exact current ACTIVE ResponsibilityAssignmentRevisionR2
the source assignment belongs to issued_by_actor_id and its exact identity revision
the issuing Principal binding and issuance_action_ref identify that same Actor
source assignment may_redelegate = true
source assignment max_redelegation_depth > 0
child responsibility_kind equals parent responsibility_kind in v0.1
child ResponsibilityScope is a deterministic subset of the parent scope
child time window is contained by the parent time window
child max_redelegation_depth <= parent max_redelegation_depth - 1
child may_redelegate = false when child max_redelegation_depth = 0
```

F2 v0.1 permits no responsibility-kind substitution or narrowing registry.
Different kinds require a new Jenn-root assignment. This keeps attenuation
deterministic without creating a permission taxonomy.

`responsibility_kind` is a stable versioned identifier normalized with Unicode
NFC and compared by exact UTF-8 bytes. It describes work ownership, not an
allowed-action class.

### 3.2 Assignment head and CAS

```text
revision 1
  -> expected_previous_assignment_revision = null
  -> supersedes_assignment_revision = null

revision N > 1
  -> both fields equal N - 1
  -> that revision must be the current head in the accepting transaction

stale head, skipped revision, forked successor, different source root,
or mismatched issuer currentness
  -> reject the assignment Event
```

The Rust single writer accepts the new revision, advances the current pointer,
and appends the Event atomically. Assignment provenance is immutable.

### 3.3 Assignment current-state assessment

R1 `ResponsibilityAssignmentAssessment` additionally binds:

```yaml
R2_assignment_assessment_additions:
  source_responsibility_fingerprint:
  assignment_lineage_fingerprint:
  issuer_actor_identity_revision:
  issuer_principal_binding_revision:
  issuance_action_ref:
  issuer_currentness_event_sequence:
```

If the source, issuer identity, issuing binding, issuance action, or exact
predecessor is missing, stale, conflicting, revoked, or indeterminate, the
assignment cannot become `ACTIVE`.

## 4. Delegation attenuation corrections

This section supplements R1 Sections 11.1-11.3.

For the first delegation edge, the immediate source assignment must be current
and satisfy:

```text
assignment belongs to delegator
assignment may_redelegate = true
assignment max_redelegation_depth > 0
delegation responsibility_kind equals assignment responsibility_kind
delegation scope and time are contained by the assignment
delegation remaining_depth = min(assignment.max_redelegation_depth,
                                 policy.maximum_edges_per_chain) - 1
delegation may_redelegate = false when remaining_depth = 0
```

Alternatively, Jenn may create the first edge from `JENN_ROOT_DIRECTION` only
through an exact authenticated Jenn action bound to the current root direction.
Its kind, scope, time, and redelegation depth are explicit in the delegation;
`remaining_depth = policy.maximum_edges_per_chain - 1`. No other Actor may use
the root-direction source.

For every child delegation edge:

```text
immediate parent delegation is current ACTIVE
parent delegate is the child delegator
parent may_redelegate = true
parent remaining_depth > 0
child responsibility_kind equals parent responsibility_kind
child scope and time are contained by the parent
child remaining_depth = parent remaining_depth - 1
child may_redelegate = false when parent may_redelegate = false
child may_redelegate = false when child remaining_depth = 0
```

The child retains the exact root source-responsibility ref and names the exact
immediate parent revision. No parallel-chain union, kind substitution, implicit
delegation, relationship expansion, or Prohibited Boundary waiver is permitted.

## 5. Binding activation evidence

This section supplements R1 `ActorPrincipalBindingRevision` with:

```yaml
R2_binding_revision_additions:
  activation_mode: JENN_INTERACTIVE_AUTHENTICATION | RESIDENT_ATTESTED_AGENT_SESSION | SERVICE_PROVISIONING_ATTESTATION | WORKER_ASSIGNMENT_HANDSHAKE | SYNTHETIC_M0_FIXTURE
  activation_evidence_ref:
```

```yaml
PrincipalControlProofAssessmentRef:
  interface_version: agents-os.principal-control-proof-assessment-ref.v0.1
  assessment_ref_id:
  principal_id:
  principal_revision:
  authenticator_profile_ref:
  verifier_id:
  verifier_revision:
  challenge_fingerprint:
  assessment: VERIFIED
  assessed_at_event_sequence:
```

This reference contains no raw proof. `REJECTED` or indeterminate proof cannot
be referenced by activation evidence.

```yaml
BindingActivationEvidence:
  evidence_id:
  evidence_revision:
  expected_previous_evidence_revision: null | integer
  supersedes_evidence_revision: null | integer

  target_binding_ref:
  target_binding_fingerprint:
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_revision:
  principal_class:
  environment:
  authenticator_profile_ref:
  verifier_revision:
  target_proof_assessment_ref: PrincipalControlProofAssessmentRef

  activation_mode:
  stewardship_source:
    kind: JENN_ROOT_BOOTSTRAP_DECISION | AUTHENTICATED_STEWARD_ACTION
    source_ref:
  steward_actor_id: optional
  steward_actor_identity_revision: optional
  steward_principal_binding_ref: optional
  steward_action_ref: AuthenticatedActorActionRef | null

  not_before_utc_ms:
  expires_at_utc_ms:
  replay_identity:
  status: ACTIVE | REVOKED | SUPERSEDED
  created_at_event_sequence:
  canonical_fingerprint: FingerprintEnvelope
```

The evidence is valid only when its target binding fingerprint, Actor, identity
revision, Principal revision, environment, authenticator, verifier, proof
assessment, mode, time window, and stewardship source all match the binding.
Revision and CAS rules are identical to Section 3.2.

One stable `evidence_id` is derived for each target binding; all later status
changes advance that same evidence stream. For bootstrap mode the steward Actor,
binding, and action fields must be absent. For every other mode they are
required. Evidence time must be contained by the target binding time window.

`JENN_ROOT_BOOTSTRAP_DECISION` is restricted to the accepted Jenn bootstrap
path. Every other mode requires an already active steward Principal binding and
an exact `AuthenticatedActorActionRef`. Evidence replay identity is unique in
the identity domain. Revoked, superseded, expired, replayed, or mismatched
evidence cannot activate a binding. The replay identity is
`SHA-256(evidence_kind, target_binding_ref, target_binding_fingerprint,
steward_or_bootstrap_source_ref, activation_mode)` under the fingerprint
canonicalization contract and is unique in the identity domain.

Binding evidence and the binding current pointer are accepted atomically. Raw
proof, credential, secret, biometric, cookie, token, private Memory, or provider
output is never stored in the evidence.

## 6. Delegation activation evidence

This section replaces the narrative-only portion of R1 Section 11.4.

```yaml
DelegationActivationEvidence:
  evidence_id:
  evidence_revision:
  expected_previous_evidence_revision: null | integer
  supersedes_evidence_revision: null | integer

  delegation_ref:
  delegation_fingerprint:
  activation_mode: EXPLICIT_ACK | WORKER_ASSIGNMENT_HANDSHAKE
  delegate_actor_id:
  delegate_actor_identity_revision:
  acknowledging_principal_binding_ref:
  acknowledging_action_ref: AuthenticatedActorActionRef

  not_before_utc_ms:
  expires_at_utc_ms:
  replay_identity:
  status: ACTIVE | REVOKED | SUPERSEDED
  created_at_event_sequence:
  canonical_fingerprint: FingerprintEnvelope
```

The acknowledging Principal binding must be current, active, and bound to the
exact delegate Actor and identity revision. The action ref must acknowledge the
exact delegation fingerprint. Evidence creation, replay reservation, and the
delegation activation Event are atomic under the Rust single writer.

One stable `evidence_id` is derived for each delegation. Evidence time must be
contained by the delegation time window. The replay identity is
`SHA-256(evidence_kind, delegation_ref, delegation_fingerprint,
acknowledging_action_ref, activation_mode)` and is unique in the identity
domain.

Stale grant revision, wrong delegate, wrong Principal, wrong fingerprint,
expired evidence, duplicate replay identity, revocation, or supersession leaves
the delegation non-active. Evidence revision and CAS follow Section 3.2.

R1 `DelegationAssessment` and recovery fingerprints now include the exact
activation-evidence revision and fingerprint.

## 7. Identity transition and recovery provenance

This section supplements R1 `ActorIdentityRevision` with:

```yaml
R2_identity_revision_additions:
  transition_kind: CREATE | UPDATE | SUSPEND | COMPROMISE | RECOVER | RETIRE
  stewardship_source:
    kind: JENN_ROOT_BOOTSTRAP_DECISION | AUTHENTICATED_STEWARD_ACTION | ACCEPTED_PROVISIONING_ACTION
    source_ref:
  steward_actor_id: optional
  steward_actor_identity_revision: optional
  steward_principal_binding_ref: optional
  steward_action_ref: AuthenticatedActorActionRef | null
  recovery_evidence_ref: optional
```

### 7.1 Closed stewardship relation

```text
Jenn root bootstrap or root identity transition
  -> exact Jenn-attributable root governance decision

Nobao identity create, material update, recover, or retire
  -> authenticated current Jenn steward action

Domain Agent identity create, material update, recover, or retire
  -> authenticated current Jenn or Nobao steward action

Temporary Worker identity create, update, or retire
  -> authenticated current Jenn, Nobao, or responsible Domain Agent action

System Service or Execution Host identity transition
  -> exact accepted provisioning action; production path remains outside F2
```

No non-root Actor may create, recover, or retire itself. A Jenn root transition
uses the exact root governance decision path and is not treated as an Agent
self-action. Every other `RECOVER` requires the exact steward class above and
cannot use the compromised Actor's own Principal.
“Responsible Domain Agent” means one exact current assignment or delegation
whose scope contains the Worker assignment; it is an accountability fact, not
a permission grant.

### 7.2 IdentityRecoveryEvidence

```yaml
IdentityRecoveryEvidence:
  recovery_evidence_id:
  actor_id:
  compromised_actor_identity_revision:
  recovering_actor_identity_revision:
  incident_basis_ref:

  affected_binding_set_basis_event_sequence:
  complete_affected_binding_refs: []
  complete_affected_binding_set_fingerprint:
  binding_dispositions:
    - binding_ref:
      disposition: REVOKED | SUPERSEDED_BY_REPLACEMENT
      disposition_event_ref:
      replacement_binding_ref: optional

  steward_actor_id:
  steward_actor_identity_revision:
  steward_principal_binding_ref:
  steward_action_ref: AuthenticatedActorActionRef
  recovery_event_sequence:
  canonical_fingerprint: FingerprintEnvelope
```

The complete affected set is every binding current for the Actor at
`affected_binding_set_basis_event_sequence`. Recovery becomes `ACTIVE` only in
one Rust transaction that verifies the exact current `COMPROMISED` head,
verifies the steward relation, confirms every affected binding is revoked or
replaced, confirms no omitted current binding exists, and appends the recovery
revision and Event. Otherwise recovery remains inactive.

## 8. Command, replay, and crash-recovery ownership correction

This section replaces R1 Sections 10.1, 14.1, 15, the Command-specific portion
of 17, and the Command/replay portion of 19.

F2 owns:

```text
stable Actor identity
Principal-to-Actor binding
responsibility assignment and delegation attribution
authentication assessment interface
single Prohibited Boundary semantics
AuthenticatedActorActionRef interface
```

F3 owns:

```text
CommandTypeDefinition and versioned payload schema
CommandEnvelope and canonical bytes
payload canonicalization and every permitted array-order rule
Unicode normalization and normalized-key collision rejection
command_id and nonce replay identity/window
atomic inbox/intake CAS and replay reservation
PENDING / COMMITTED / REJECTED / OUTCOME_INDETERMINATE intake state
crash recovery and no-auto-retry behavior for unknown effects
atomic binding of identity, responsibility, delegation, registry,
  Prohibited Behavior List revision, command_id, nonce, and domain handoff
```

R1's `CanonicalCommand`, `CommandTypeDefinition`, command payload
canonicalization, `AuthenticatedCommandContext`, nonce rule, and “idempotent
original result” text are not
accepted as complete F2-owned contracts. They are replaced by this ownership
boundary and become mandatory F3 closure requirements.

R1 Sections 14.2-14.3 remain as the authentication assertion and assessment
interfaces, but their `command_id` and command fingerprint fields refer to the
F3-owned immutable Command envelope. R1 Section 16 remains the single
Prohibited Boundary semantic rule; F3 must realize that check in its atomic
intake transaction.

F3 must not emit `AuthenticatedActorActionRef` until its intake transaction has:

```text
validated one exact payload schema and canonicalization version
rejected normalized-key collisions, duplicates, unknown fields, and undefined array order
reserved exact command_id and nonce replay keys atomically
bound current identity, binding, responsibility/delegation, and prohibited-list revisions
recorded a durable intake state before domain handoff
defined deterministic same-bytes replay and different-bytes conflict behavior
defined OUTCOME_INDETERMINATE without automatic effect retry
```

Until F3 closes these requirements, AGENTS OS cannot open Command intake from
this interface or activate the related runtime. This is an explicit dependency,
not a claim that the missing protocol already exists.

## 9. Fingerprint and recovery additions

F2 fingerprints and startup recovery additionally cover:

```text
assignment predecessor, source responsibility, issuer identity/binding/action, and lineage
binding activation evidence head, target fingerprint, proof assessment, stewardship, and replay identity
delegation activation evidence head, acknowledging binding/action, target fingerprint, and replay identity
identity transition stewardship and complete recovery evidence set
the F3 contract version and immutable AuthenticatedActorActionRef fields when such refs exist
```

New R2 array ordering is fixed as follows:

| Field | Canonical order and uniqueness |
|---|---|
| `complete_affected_binding_refs` | binding ID, then binding revision; duplicate stable keys rejected |
| `binding_dispositions` | contained `binding_ref` ID, then revision; exactly one entry per affected binding |

The disposition set must have exact set equality with
`complete_affected_binding_refs`; missing and extra entries are rejected.

Missing, forked, stale, conflicting, or unknown-version evidence stops the
affected identity, binding, assignment, delegation, or action attribution. It
does not create a new permission state and is not automatically retried.

## 10. Required negative tests

A future authorized implementation must add at least:

```text
self-issued assignment rejection
stale assignment-head and forked-successor rejection
issuer scope/time/depth expansion rejection
responsibility-kind substitution rejection
source may_redelegate=false rejection
child may_redelegate=true with remaining_depth=0 rejection
binding activation with wrong actor/principal/fingerprint/verifier rejection
binding evidence replay, expiry, revocation, and supersession rejection
delegation acknowledgement by wrong or stale binding rejection
delegation activation replay and stale-grant rejection
self-create and self-recover identity rejection
recovery with wrong steward or incomplete affected-binding set rejection
recovery while an omitted compromised binding remains active rejection
AuthenticatedActorActionRef before accepted F3 rejection
unknown F3 contract version rejection
Command outcome unknown does not trigger automatic retry
```

## 11. Prior finding disposition

| Finding | R2 disposition |
|---|---|
| `F2-IR-B01` | resolved by Sections 3-4 |
| `F2-IR-B02` | resolved by Sections 5-6 |
| `F2-IR-B03` | resolved by explicit ownership replacement in Sections 2 and 8 |
| `F2-IR-M01` | resolved by Section 7 |

The three previously documented implementation blockers remain true: canonical
Prohibited Behavior List convergence, production authentication, and downstream
F3/F4 runtime contracts are not completed by R2.

## 12. Atomic acceptance and non-authorization

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R2_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - this_exact_R2_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

Accepting this atomic bundle would accept architecture semantics only. It would
not create identities, assignments, bindings, credentials, database schema,
services, providers, TaskPermits, host effects, or runtime activation.
