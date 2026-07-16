# AGENTS OS F2 Actor Identity and Delegation v0.1 R7 Lifecycle, Currentness, Revocation, Scope and Scalar Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R7_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r7
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and precedence

R7 closes only the lifecycle, currentness, revocation, responsibility-scope,
lineage, and numeric-scalar gaps recorded after the R6 independent review. It
does not replace the F2 architectural direction and does not rewrite R1-R6.

The fixed subjects are:

```text
R1 639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
R2 8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
R3 d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
R4 a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
R5 cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be
R6 bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932
```

R7 has exact precedence over:

```text
R1 Sections 5.1-5.4 for Actor lifecycle and validity windows
R1 Sections 7.2-7.5 for Principal and Binding currentness
R1 Section 8 for Authenticator Profile lifecycle
R1 Sections 9.2-9.3 and R2 Section 3 for assignment source and lineage
R1 Sections 11.4-13 and R3 Sections 2-4 where activation is called currentness
R1 Section 18 and R4 Section 2 for F2 numeric scalar admission
R2 Sections 5-7 for activation-evidence state transitions and identity transitions
R2 assignment and delegation rules that require an issuing session Binding to remain current
R3 binding_current_projection and delegation_current_projection names and meanings
R4-R6 numeric rules only where R7 generalizes the same parsed-number rule
```

Every other R1-R6 rule remains effective. R1 through R7 form one indivisible
acceptance unit. No individual amendment may be accepted separately.

## 2. R7 canonical record and scalar profile

### 2.1 Canonical record rule

Every schema newly introduced by R7 uses:

```text
canonical bytes = RFC 8785 JCS of [domain_tag, schema_known_object]
text = Unicode 15.1.0 NFC before validation and JCS
optional absent schema field = JSON null
unknown field = reject
undefined = reject
normalized-key collision = reject
fingerprint = R4FingerprintEnvelope over SHA-256(canonical bytes)
```

The `schema_known_object` contains every field shown in the schema in this
amendment except its own `canonical_fingerprint`. Arrays use the exact ordering
rule stated by their owning schema; an array without an ordering rule is
rejected. A `*_ref` is an exact normalized stable reference containing the
target stable ID, revision where applicable, and verified target fingerprint.

### 2.2 F2CanonicalScalarProfileV0_1

All F2 JSON numbers are validated after standards-compliant parsing to the
ECMAScript `Number` / IEEE 754 binary64 data model. Original token spelling is
not normative. Every admitted numeric scalar rejects `-0`, non-finite values,
wrong JSON types, and any parsed value outside its declared range.

```yaml
F2CanonicalScalarProfileV0_1:
  contract_version: agents-os.f2-canonical-scalars.v0.1
  safe_uint:
    predicate: Number.isSafeInteger(value) && value >= 0 && !Object.is(value, -0)
    range: 0..9007199254740991
  positive_revision:
    predicate: safe_uint && value >= 1
    range: 1..9007199254740991
  nullable_previous_revision:
    create_value: null
    successor_value: positive_revision
  event_sequence:
    predicate: safe_uint
    range: 0..9007199254740991
  utc_milliseconds:
    predicate: safe_uint
    range: 0..9007199254740991
  duration_milliseconds:
    predicate: safe_uint && value >= 1
    range: 1..9007199254740991
  delegation_policy_maximum_edges:
    exact_value_in_v0_1: 3
  delegation_remaining_depth:
    range: 0..2
  assignment_max_redelegation_depth:
    range: 0..3
```

The profile applies to every numeric occurrence in F2 R1-R7, including:

```text
actor_identity_revision
principal_revision
binding_revision
assignment_revision
delegation_revision
profile_revision
verifier_revision
evidence_revision
policy_revision
command_registry_revision
prohibited_behavior_list_revision when represented as a JSON number
expected_previous_*_revision
supersedes_*_revision
created_at_event_sequence
assessed_at_event_sequence
based_on_event_sequence
effective_at_event_sequence
F3_intake_event_sequence where inserted into an F2 fingerprint
not_before_utc_ms
expires_at_utc_ms
issued_at_utc_ms
assessed_at_utc_ms
assertion_max_age_ms
remaining_depth
max_redelegation_depth
maximum_edges_per_chain
BindingScope context_revision
```

Revision fields use `positive_revision`; nullable predecessor and supersession
fields use `nullable_previous_revision`; Event fields use `event_sequence`; time
instants use `utc_milliseconds`; positive TTL and maximum-age fields use
`duration_milliseconds`; depth fields use their exact bounded domains.

An F2 fingerprint projection containing an F3-owned structured numeric field is
valid only when the accepted F3 contract supplies the same parsed-number and
range semantics. Otherwise the F2 assessment is `INDETERMINATE`. No writer may
substitute a u64 value above `2^53 - 1`, a decimal string, bigint, float, or
source-token-preserving value into an F2 v0.1 formula.

`1e3`, `1000.0`, and `1000` are the same admitted parsed value and insert JCS
`1000`. R6 negative-zero and rounded-fraction rules remain unchanged and are
now inherited by every F2 numeric scalar.

### 2.3 Cross-field numeric invariants

```text
revision 1 -> expected_previous_revision = null and supersedes_revision = null
revision N > 1 -> both predecessor fields equal N - 1
not_before_utc_ms < expires_at_utc_ms
issued_at_utc_ms <= expires_at_utc_ms
assessment Event sequence <= current recovered Event sequence
remaining_depth <= maximum_edges_per_chain - 1
```

Skipped revision, stale predecessor, numeric overflow, wrong scalar class, or
range mismatch rejects the write before fingerprinting.

## 3. Common lifecycle provenance

### 3.1 LifecycleActionRefV0_1

Every lifecycle transition names one committed provenance source:

```yaml
LifecycleActionRefV0_1:
  action_kind: AUTHENTICATED_ACTOR_ACTION | JENN_GOVERNANCE_DECISION | ACCEPTED_PROVISIONING_ACTION | SYNTHETIC_M0_MANIFEST
  action_ref:
  action_fingerprint:
  authority_basis_ref:
  authority_basis_fingerprint:
  committed_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.lifecycle-action-ref.v0.1
```

`AUTHENTICATED_ACTOR_ACTION` must be an R4-complete
`AuthenticatedActorActionRef` backed by F3 `COMMITTED` intake.
`JENN_GOVERNANCE_DECISION` is limited to a hash-bound immutable Jenn decision.
`ACCEPTED_PROVISIONING_ACTION` must be an accepted deployment/provisioning fact;
production use remains separately gated. `SYNTHETIC_M0_MANIFEST` is limited to
Section 6.5 and its authority basis must be the separate Jenn decision accepting
the exact manifest fingerprint.

The caller cannot construct, self-attest, or change a lifecycle action ref.

### 3.2 R7 array ordering

R7 arrays use these exact orders:

| Array family | Canonical order |
|---|---|
| reason codes, principal classes, environments | NFC UTF-8 byte lexical; duplicates rejected |
| credential handles, trust anchors, assessment refs | stable ref kind, stable ID, revision; duplicates rejected |
| current transition facts | effective Event sequence, then transition fact ID |
| compromise-impact facts | effective Event sequence, then impact fact ID |
| complete target actions | action ref ID, then action fingerprint |
| M0 creation specs | subject kind, then stable subject ID |
| responsibility resource refs | resource kind, resource ID, then revision with null first |
| delegation lineage | semantic root-to-leaf order; broken adjacency or duplicate Actor rejected |

Any R7 array not covered here or by an effective R1-R6 ordering rule is rejected
until a reviewed amendment defines its semantic order.

### 3.3 Current-head CAS

Every Actor, Principal, Authenticator Profile, Binding, Assignment, Delegation,
and activation-evidence revision stream has exactly one current head.

```text
create revision 1
  -> expected_previous_revision = null
  -> supersedes_revision = null

successor revision N
  -> expected_previous_revision = N - 1
  -> supersedes_revision = N - 1
  -> N - 1 is the current head in the accepting transaction
```

Rust accepts the new immutable revision, advances the one current pointer, and
appends the Event in one transaction. A skipped revision, fork, stale CAS,
duplicate head, or mismatched fingerprint is rejected. Derived assessments do
not own or advance revision heads.

R7 adds these missing CAS fields to the effective subjects:

```yaml
ActorPrincipalBindingRevisionR7CAS:
  expected_previous_binding_revision: null | positive_revision

DelegationGrantRevisionR7CAS:
  expected_previous_delegation_revision: null | positive_revision
```

Their existing `supersedes_*_revision` fields obey the same create/successor
rule. Assignment and activation-evidence streams retain the R2 CAS fields.

## 4. Actor identity lifecycle closure

### 4.1 IdentityValidityWindowV0_1

```yaml
IdentityValidityWindowV0_1:
  schema_version: agents-os.identity-validity-window.v0.1
  not_before_utc_ms:
  expires_at_utc_ms:
```

Domain tag:

```text
agents-os.identity-validity-window.v0.1
```

Both values use `utc_milliseconds` and `not_before_utc_ms < expires_at_utc_ms`.
Every Temporary Worker requires this exact window. Other Actor classes omit it
unless a later accepted profile requires a bounded identity lifetime.

### 4.2 ActorIdentityRevisionR7 additions

R7 adds or replaces these lifecycle fields:

```yaml
ActorIdentityRevisionR7Lifecycle:
  expected_previous_actor_identity_revision: null | positive_revision
  supersedes_actor_identity_revision: null | positive_revision
  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | COMPROMISE | RECOVER | RETIRE
  source_status: null | ACTIVE | SUSPENDED | COMPROMISED
  target_status: ACTIVE | SUSPENDED | COMPROMISED | RETIRED
  validity_window: IdentityValidityWindowV0_1 | null
  lifecycle_action_ref: LifecycleActionRefV0_1
  identity_steward_ref:
  recovery_evidence_ref: optional
```

Domain tag for the complete effective Actor revision remains the owning R1-R4
Actor identity tag with these fields inserted before Event sequence. Every
numeric field uses Section 2.

`actor_id`, `actor_class`, and identity-stewardship lineage are immutable across
revisions. An actor-class change creates a new `actor_id`.

### 4.3 Actor identity transition matrix

| Transition | Source | Target | Required authority and evidence |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | R1/R2 exact identity steward or Jenn root bootstrap |
| `UPDATE` | `ACTIVE` | `ACTIVE` | current identity steward; status cannot change |
| `UPDATE` | `SUSPENDED` | `SUSPENDED` | current identity steward; status cannot change |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | current identity steward, or the Actor's own authenticated action |
| `RESUME` | `SUSPENDED` | `ACTIVE` | current identity steward; self-resume forbidden |
| `COMPROMISE` | `ACTIVE` or `SUSPENDED` | `COMPROMISED` | current identity steward, Jenn, or accepted incident action |
| `RECOVER` | `COMPROMISED` | `ACTIVE` | R2 recovery evidence and same-or-higher identity steward |
| `RETIRE` | `ACTIVE`, `SUSPENDED`, or `COMPROMISED` | `RETIRED` | current identity steward; self-retire forbidden |

`RETIRED` is terminal. `COMPROMISED` permits only `RECOVER` or `RETIRE`.
Self-suspension is fail-safe and cannot alter identity facts other than status;
it does not permit self-resume, self-recovery, or self-retirement.

The exact steward relation remains:

```text
Jenn root -> Jenn-attributable hash-bound governance decision
Nobao -> Jenn
Domain Agent -> Jenn or Nobao
Temporary Worker -> Jenn, Nobao, or responsible Domain Agent
System Service / Execution Host -> accepted provisioning authority
```

For `SUSPEND` and `COMPROMISE`, Jenn is always a same-or-higher steward. A
mechanical incident action may only move toward a safer state; it cannot resume,
recover, update, or retire an Actor.

The R1 `ActorIdentityAssessment` remains the only effective Actor current-state
reducer. It first verifies the one current head and transition matrix, then
applies validity window, assignment binding, time authority, and recovery
evidence. Any missing or conflicting input produces `INDETERMINATE`.

## 5. Authenticator Profile lifecycle closure

### 5.1 LifecycleControllerRefV0_1

```yaml
LifecycleControllerRefV0_1:
  controller_kind: SYSTEM_SERVICE_ACTOR | ACCEPTED_PROVISIONING_COMPONENT | SYNTHETIC_FIXTURE_CONTROLLER
  controller_ref:
  controller_revision:
  controller_fingerprint:
  provisioning_basis_ref:
```

Domain tag:

```text
agents-os.lifecycle-controller-ref.v0.1
```

A `SYSTEM_SERVICE_ACTOR` controller must name an exact current ACTIVE System
Service Actor identity. An `ACCEPTED_PROVISIONING_COMPONENT` must name an exact
accepted component and provisioning basis; production use remains separately
gated. A `SYNTHETIC_FIXTURE_CONTROLLER` exists only inside one accepted Section
6.5 manifest. Controller availability and fingerprint are checked by the
Authenticator Profile assessment. The controller is a deterministic verifier
and transition committer, not an independent permission source.

### 5.2 AuthenticatorProfileRevisionR7

R7 replaces the lifecycle-opaque R1 profile with:

```yaml
AuthenticatorProfileRevisionR7:
  profile_id:
  profile_revision:
  expected_previous_profile_revision: null | positive_revision
  supersedes_profile_revision: null | positive_revision
  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | RETIRE
  source_status: null | ACTIVE | SUSPENDED
  status: ACTIVE | SUSPENDED | RETIRED

  proof_kind: SYNTHETIC_FIXTURE | LOCAL_OS_SESSION | ASYMMETRIC_SIGNATURE | PROCESS_ATTESTATION | HOST_ATTESTATION
  supported_principal_classes: []
  supported_environments: []
  verifier_id:
  verifier_revision:
  lifecycle_controller_ref: LifecycleControllerRefV0_1
  credential_status_provider_ref:
  trust_anchor_refs: []
  assertion_max_age_ms:
  clock_policy_ref:
  replay_policy_ref:

  profile_steward_ref:
  lifecycle_action_ref: LifecycleActionRefV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.authenticator-profile-revision.v0.1-r7
```

`profile_id`, `proof_kind`, `lifecycle_controller_ref`, and the profile-steward
lineage are immutable. A change to any of them creates a new `profile_id`.
Every profile reference is exact to `profile_revision` and fingerprint.

`profile_steward_ref` is exactly one of:

```text
JENN_GOVERNANCE_STEWARD
  -> exact Jenn governance identity and decision route

ACCEPTED_PROVISIONING_STEWARD
  -> exact accepted provisioning component and provisioning basis

SYNTHETIC_M0_STEWARD
  -> exact accepted Section 6.5 manifest and Jenn acceptance decision
```

The `credential_status_provider_ref` must be the lifecycle controller itself or
an exact accepted component named by the same profile steward and provisioning
basis. Its availability and fingerprint are part of Profile assessment;
unavailable or conflicting status produces `INDETERMINATE`.

Profile transition matrix:

| Transition | Source | Target | Authority |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | Jenn decision, synthetic M0 manifest, or accepted provisioning action |
| `UPDATE` | `ACTIVE` | `ACTIVE` | current profile steward or accepted provisioning action |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | current steward, Jenn, or accepted incident action |
| `RESUME` | `SUSPENDED` | `ACTIVE` | current steward or Jenn; incident mechanism alone forbidden |
| `RETIRE` | `ACTIVE` or `SUSPENDED` | `RETIRED` | current steward or Jenn |

`RETIRED` is terminal. A superseded profile revision cannot verify new proofs.
Updating a profile therefore requires affected Principals to rotate to the new
exact profile revision; historical assertions remain governed by Section 9.

### 5.3 AuthenticatorProfileAssessmentR7

```yaml
AuthenticatorProfileAssessmentR7:
  profile_ref:
  assessment: ACTIVE | SUSPENDED | RETIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.authenticator-profile-assessment.v0.1-r7
```

The reducer verifies the current-head CAS, transition authority, verifier and
clock-policy availability, exact lifecycle-controller currentness, and
fingerprint. Only `ACTIVE` may provision a new Principal, verify a new
assertion, or support an effective Binding.

F2 accepts no production profile, algorithm, trust anchor, key, or constant.

## 6. Principal lifecycle closure

### 6.1 PrincipalRevisionR7

R7 replaces R1 `PrincipalRevision` with:

```yaml
PrincipalRevisionR7:
  principal_id:
  principal_revision:
  expected_previous_principal_revision: null | positive_revision
  supersedes_principal_revision: null | positive_revision
  transition_kind: CREATE | ROTATE_CREDENTIALS | SUSPEND | RESUME | REVOKE | RETIRE
  source_status: null | ACTIVE | SUSPENDED | REVOKED

  principal_class: HUMAN_SESSION | AGENT_SESSION | SERVICE_PROCESS | WORKER_PROCESS | HOST_PROCESS | SYNTHETIC_TEST_PRINCIPAL
  environment: SYNTHETIC_TEST | LOCAL_DEVELOPMENT | PRODUCTION
  authenticator_profile_ref:
  credential_handle_refs: []
  status: ACTIVE | SUSPENDED | REVOKED | RETIRED

  provisioning_source_ref: LifecycleActionRefV0_1
  transition_action_ref: LifecycleActionRefV0_1
  lifecycle_controller_ref:
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.principal-revision.v0.1-r7
```

Credential handles are sorted exact opaque references and contain no secret.
`principal_id`, `principal_class`, `environment`, and lifecycle-controller
lineage are immutable. A class or environment change creates a new Principal.
Only `ROTATE_CREDENTIALS` may change credential handles or advance the exact
Authenticator Profile revision for the same profile ID.

### 6.2 Principal transition matrix

| Transition | Source | Target | Authority |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | current profile lifecycle controller and valid provisioning source |
| `ROTATE_CREDENTIALS` | `ACTIVE` | `ACTIVE` | current profile controller; old credentials receive explicit disposition |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | profile controller, Jenn, bound Actor request, or accepted incident action |
| `RESUME` | `SUSPENDED` | `ACTIVE` | profile controller after current proof; incident mechanism alone forbidden |
| `REVOKE` | `ACTIVE` or `SUSPENDED` | `REVOKED` | profile controller, Jenn, bound Actor request, or accepted incident action |
| `RETIRE` | `ACTIVE`, `SUSPENDED`, or `REVOKED` | `RETIRED` | profile controller or Jenn |

`REVOKED` permits only `RETIRE`; `RETIRED` is terminal. A Principal cannot
create or attest itself. The Actor represented by a current Binding may request
suspension or revocation, but the profile lifecycle controller verifies and
commits the canonical transition.

### 6.3 CredentialHandleStatusAssessmentRefV0_1

```yaml
CredentialHandleStatusAssessmentRefV0_1:
  assessment_ref:
  principal_ref:
  authenticator_profile_ref:
  credential_handle_ref:
  assessment: ACTIVE | REVOKED | INDETERMINATE
  controller_ref:
  based_on_event_sequence:
  assessed_at_utc_ms:
  assessment_fingerprint:
```

Domain tag for reference validation:

```text
agents-os.credential-handle-status-assessment-ref.v0.1
```

This reference discloses no credential or proof bytes. Every handle in an
effective Principal must have one exact current `ACTIVE` assessment. Missing,
conflicting, revoked, or unverifiable status fails closed.

### 6.4 PrincipalAssessmentR7

```yaml
PrincipalAssessmentR7:
  principal_ref:
  authenticator_profile_assessment_ref:
  credential_status_assessment_refs: []
  assessment: ACTIVE | SUSPENDED | REVOKED | RETIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.principal-assessment.v0.1-r7
```

Only the exact current Principal head with `ACTIVE` status, an `ACTIVE` exact
profile revision, all `ACTIVE` credential handles, valid transition provenance,
and matching fingerprints assesses `ACTIVE`.

### 6.5 Synthetic M0 fixture provisioning

```yaml
SyntheticM0PrincipalProvisioningManifestV0_1:
  manifest_id:
  manifest_revision:
  workspace_fixture_id:
  synthetic_profile_creation_specs: []
  synthetic_principal_creation_specs: []
  permitted_binding_creation_specs: []
  deterministic_credential_handle_refs: []
  creation_authority_ref:
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.synthetic-m0-principal-provisioning-manifest.v0.1
```

The manifest is valid only in `SYNTHETIC_TEST`, uses deterministic synthetic
credential handles, and cannot contain production trust anchors, real secrets,
active Jenn credentials, an active host identity, or a production Actor
binding. Creation specs contain only stable IDs and the exact proposed subject
fields that do not reference the manifest, a resulting subject fingerprint, or
an acceptance record. They are sorted by subject kind and stable ID.

A separate immutable Jenn decision accepts the exact manifest fingerprint.
That decision may reference the manifest, but the manifest never references
that later decision; therefore the graph is acyclic. Every synthetic Principal
and Profile revision then references the accepted manifest as its
`SYNTHETIC_M0_MANIFEST` lifecycle action and is created atomically from one
exact spec under the Rust single writer. An omitted, extra, or mismatched spec
is rejected. No synthetic subject may be promoted to local-development or
production state.

## 7. Activation is not effective currentness

### 7.1 Binding subject issuance and lifecycle

R7 replaces R1 Binding issuance provenance with:

```yaml
ActorPrincipalBindingRevisionR7Issuance:
  expected_previous_binding_revision: null | positive_revision
  binding_issuance_source_ref: LifecycleActionRefV0_1
  issued_by_actor_ref: optional
  status: ACTIVE
```

The exact issuance route is determined by `activation_mode`:

```text
JENN_INTERACTIVE_AUTHENTICATION
  -> Jenn bootstrap/registration decision plus current Profile proof

RESIDENT_ATTESTED_AGENT_SESSION
  -> current Actor identity steward action plus current Profile proof

SERVICE_PROVISIONING_ATTESTATION
  -> accepted provisioning action plus current Profile proof

WORKER_ASSIGNMENT_HANDSHAKE
  -> current responsible Actor action plus current Profile proof

SYNTHETIC_M0_FIXTURE
  -> exact accepted Section 6.5 manifest spec
```

`issued_by_actor_ref` is present only for an authenticated Actor route and must
match the issuance action. Bootstrap, provisioning, and synthetic routes omit
it rather than inventing an Actor issuer.

Across revisions, `binding_id`, `actor_id`, and `principal_id` are immutable.
A successor may bind newer exact Actor, Principal, or Profile revisions, narrow
the representation scope, or shorten the time window only through the exact
issuance route and current-head CAS. A different Actor or Principal creates a
new `binding_id`. New subjects always use `status: ACTIVE`; administrative
changes after issuance use Section 8 transition facts.

### 7.2 Binding activation projection

R7 renames and narrows R3 `BindingActivationAssessment` to:

```yaml
BindingActivationAssessmentR7:
  binding_ref:
  binding_subject_fingerprint:
  activation_evidence_ref:
  activation_evidence_fingerprint:
  current_transition_fact_refs: []
  assessment: ACTIVATED | NOT_ACTIVATED | INDETERMINATE
  reason_codes: []
  assessed_at_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

The only projection it owns is:

```text
binding_activation_projection
```

It proves only that the exact activation evidence is valid and current for the
exact binding subject. It does not assess current Actor, Principal, Profile,
credential, Binding administrative transition, or time-window state.

### 7.3 ActorPrincipalBindingAssessmentR7

```yaml
ActorPrincipalBindingAssessmentR7:
  binding_ref:
  binding_subject_fingerprint:
  actor_identity_assessment_ref:
  principal_assessment_ref:
  authenticator_profile_assessment_ref:
  credential_status_assessment_refs: []
  binding_activation_assessment_ref:
  current_transition_fact_refs: []
  time_authority_ref:
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.actor-principal-binding-assessment.v0.1-r7
```

This assessment is the sole authority for:

```text
binding_effective_current_projection
whether the Binding may represent the Actor for a new Command
```

Reduction order:

```text
explicit binding REVOKE transition -> REVOKED
binding head no longer current -> SUPERSEDED
explicit SUSPEND without later valid RESUME -> SUSPENDED
missing/forked head, transition, Actor, Principal, Profile, credential,
  activation, time, or fingerprint fact -> INDETERMINATE
trusted now < not_before_utc_ms -> NOT_YET_ACTIVE
trusted now >= expires_at_utc_ms -> EXPIRED
Actor SUSPENDED -> SUSPENDED
Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
Actor INDETERMINATE -> INDETERMINATE
Principal SUSPENDED -> SUSPENDED
Principal REVOKED or RETIRED -> REVOKED
Principal SUPERSEDED -> SUPERSEDED
Principal INDETERMINATE -> INDETERMINATE
Profile SUSPENDED -> SUSPENDED
Profile RETIRED -> REVOKED
Profile SUPERSEDED -> SUPERSEDED
Profile INDETERMINATE -> INDETERMINATE
any credential REVOKED -> REVOKED
any credential INDETERMINATE -> INDETERMINATE
activation assessment NOT_ACTIVATED -> NOT_YET_ACTIVE
activation assessment INDETERMINATE -> INDETERMINATE
all exact dependencies current and valid -> ACTIVE
```

Only `ACTIVE` may support a new AuthenticationAssertion or Command. R3
`binding_current_projection` is replaced by the two projections above and has
no independent authority.

### 7.4 Delegation activation projection

R7 narrows R3 `DelegationActivationAssessment` to:

```yaml
DelegationActivationAssessmentR7:
  delegation_ref:
  delegation_subject_fingerprint:
  activation_acknowledgement_ref:
  activation_evidence_ref:
  activation_evidence_fingerprint:
  current_transition_fact_refs: []
  assessment: ACTIVATED | NOT_ACTIVATED | INDETERMINATE
  reason_codes: []
  assessed_at_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Its only projection is:

```text
delegation_activation_projection
```

R1 `DelegationAssessment`, as corrected by Sections 9-11 of R7, remains the
only effective delegation reducer and owns:

```text
delegation_effective_current_projection
```

R3 `delegation_current_projection` is replaced by these two names and has no
independent authority.

## 8. Governed state transitions

### 8.1 GovernedStateTransitionFactV0_1

Binding, Assignment, Delegation, and activation-evidence state changes use one
common immutable envelope with target-specific authority rules:

```yaml
GovernedStateTransitionFactV0_1:
  transition_fact_id:
  target_kind: ACTOR_PRINCIPAL_BINDING | RESPONSIBILITY_ASSIGNMENT | DELEGATION_GRANT | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE
  target_ref:
  target_fingerprint:
  transition: SUSPEND | RESUME | REVOKE | RENOUNCE
  requested_by_actor_ref: optional
  requested_by_action_ref: LifecycleActionRefV0_1
  authority_basis_ref:
  expected_target_head:
    target_revision:
    target_fingerprint:
    last_transition_event_sequence: event_sequence | null
  effective_at_event_sequence:
  reason_codes: []
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.governed-state-transition-fact.v0.1
```

The fact is accepted only when `expected_target_head` matches the exact current
head and last effective transition in the same Rust transaction. It appends one
Event and advances the target transition projection atomically. It never edits
the target subject or impersonates the original issuer.

`REVOKE` and `RENOUNCE` are terminal for the target revision. `RESUME` is valid
only after `SUSPEND`; there is no `RESTORE` transition in v0.1. A content change
uses a properly issued successor subject revision rather than a transition
fact.

### 8.2 Target-specific authority matrix

| Target | `SUSPEND` | `RESUME` | `REVOKE` | `RENOUNCE` |
|---|---|---|---|---|
| Binding | Jenn, identity steward, profile controller, bound Actor self-suspend | identity steward or profile controller after all dependencies validate | Jenn, identity steward, profile controller, bound Actor request, accepted incident action | forbidden |
| Assignment | Jenn or original assigning Actor while its responsibility remains current | same authority as suspend and current source responsibility | Jenn or original assigning Actor | forbidden in v0.1 |
| Delegation | Jenn or delegator while its source responsibility remains current | Jenn or delegator after source and parent chain validate | Jenn or delegator; Nobao for subordinate chain in accepted scope | delegate only |
| Binding activation evidence | Jenn, evidence steward, target Binding lifecycle authority | evidence steward after new current proof | Jenn, evidence steward, target Binding lifecycle authority | forbidden |
| Delegation activation evidence | Jenn, evidence steward, delegator | evidence steward after exact acknowledgement remains valid | Jenn, evidence steward, delegator | delegate only |

An accepted incident mechanism may only `SUSPEND` or `REVOKE`; it cannot resume.
The `requested_by_action_ref` must prove the exact actor when an Actor is the
authority. Mechanical incident action uses `ACCEPTED_PROVISIONING_ACTION` and
an exact accepted security-policy basis.

`RENOUNCE` closes only the delegate's exact Delegation and its effective
descendant chain. It does not transfer, widen, or create responsibility.

### 8.3 Prospective effect and cascade

All transition facts are prospective from `effective_at_event_sequence`.
Earlier committed Events remain historical facts. Revoking or renouncing a
parent does not synthesize child transition facts; the child effective reducer
derives its safe non-active state from the exact ancestor transition and Event
sequence. This preserves one event order without pretending multiple writes
were atomic.

R1/R2 subject `status` fields for Binding, Assignment, Delegation, and activation
evidence are creation facts only. A new R7-conformant subject or evidence head
must be created with `status: ACTIVE`; `SUSPENDED`, `REVOKED`, and
`SUPERSEDED` are derived through transition facts or current-head replacement.
This removes the prior dual route of either forging a new issuer revision or
creating an unspecified revocation fact.

## 9. Historical action validity is not current session validity

### 9.1 HistoricalActionValidityAssessmentR7

```yaml
HistoricalActionValidityAssessmentR7:
  action_ref:
  action_fingerprint:
  actor_ref_at_commit:
  principal_ref_at_commit:
  binding_ref_at_commit:
  authentication_assessment_ref_at_commit:
  committed_event_sequence:
  validity_at_commit: VALID | INVALID | INDETERMINATE
  current_assurance: CONFIRMED | CHALLENGED | INVALIDATED | INDETERMINATE
  compromise_impact_fact_refs: []
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.historical-action-validity-assessment.v0.1-r7
```

An Assignment, Delegation, identity transition, or lifecycle transition may be
accepted only when its action was `VALID` at its commit Event. After commit:

```text
routine session end -> no retroactive effect
Binding expiry -> no retroactive effect
routine Principal or Binding replacement -> no retroactive effect
credential rotation -> no retroactive effect
issuer's later identity update -> no retroactive effect
explicit target revocation -> prospective target effect only
```

The current issuer session, Principal revision, Binding revision, and
Authenticator Profile revision are not continuing operational dependencies of
the already committed action.

### 9.2 CompromiseImpactFactV0_1

```yaml
CompromiseImpactFactV0_1:
  impact_fact_id:
  impact_stream_id:
  impact_revision:
  expected_previous_impact_revision: positive_revision | null
  compromised_actor_or_principal_ref:
  incident_basis_ref:
  selection_basis_event_sequence:
  complete_target_action_refs: []
  complete_target_set_fingerprint:
  impact: CHALLENGE | INVALIDATE | CLEAR_CHALLENGE
  requested_by_action_ref: LifecycleActionRefV0_1
  authority_basis_ref:
  expected_previous_impact_event_sequence: event_sequence | null
  effective_at_event_sequence:
  reason_codes: []
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.compromise-impact-fact.v0.1
```

Targets are an explicit complete sorted set of exact action refs; an open-ended
time range alone cannot alter historical assurance. Jenn or the affected
Actor's same-or-higher identity steward may `INVALIDATE` or
`CLEAR_CHALLENGE`. An accepted incident mechanism may only `CHALLENGE`.

One `impact_stream_id` exists per compromised Actor or Principal incident.
Revision 1 has null predecessor fields; every successor uses revision `N - 1`
and the current impact Event sequence under CAS. A fork or stale impact head is
rejected. `CLEAR_CHALLENGE` must target exactly the still-challenged action set;
it cannot clear an omitted, added, or previously invalidated action.

```text
no prior impact -> CHALLENGE or INVALIDATE
CHALLENGED -> CLEAR_CHALLENGE or INVALIDATE
INVALIDATED -> terminal; CLEAR_CHALLENGE is forbidden
```

```text
CHALLENGED -> dependent effective assessment becomes INDETERMINATE
INVALIDATED -> dependent object cannot be used after the impact Event
CLEAR_CHALLENGE -> restores CONFIRMED only with exact steward evidence
```

Invalidation does not delete the action, rewrite its commit Event, or silently
undo an already committed domain mutation. Any compensation requires the owning
domain contract.

### 9.3 Assignment and Delegation correction

R2 Section 3.3 is replaced as follows:

```text
Assignment currentness requires:
  exact current Assignment head
  recipient Actor identity current and ACTIVE
  source responsibility current
  historical issuance action current_assurance = CONFIRMED
  no effective transition closing the Assignment
  current time inside the Assignment window

It does not require:
  issuing Principal revision to remain current
  issuing Binding to remain active
  issuing session to remain open
  issuing Authenticator Profile revision to remain current
```

The Jenn root direction and responsibility-basis decision are historical
issuance bases unless they contain an explicit validity window or a later Jenn
decision explicitly names the Assignment for transition. A routine newer root
direction does not silently invalidate an earlier Assignment.

R1 Delegation reducer receives the same correction. The exact issuance and
activation actions must have been valid at commit and remain `CONFIRMED`, but
their historical Principal Bindings are not current operational dependencies.

## 10. ResponsibilityScope v0.1 closure

### 10.1 ResponsibilityResourceRefV0_1

```yaml
ResponsibilityResourceRefV0_1:
  resource_kind: GOAL | TASK | RUN | DOMAIN | ARTIFACT_METADATA
  resource_id:
  resource_revision: positive_revision | null
  resource_fingerprint: optional
```

Refs sort by `resource_kind`, NFC UTF-8 `resource_id`, then revision with null
before a positive revision. Duplicate stable tuples are rejected.

### 10.2 ResponsibilityScopeV0_1R7

R7 replaces R1 `ResponsibilityScope` with:

```yaml
ResponsibilityScopeV0_1R7:
  scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  workspace_id:
  scope_mode: EXACT_SET
  resource_refs: ResponsibilityResourceRefV0_1[]
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.responsibility-scope.v0.1-r7
```

`resource_refs` is non-empty and uses the exact sort above. Wildcard, glob,
regex, natural-language set, future resource, ambient workspace access, and
`DECLARED_SUBTREE` are rejected in F2 v0.1. A later accepted containment
contract may introduce a new scope-contract version with exact contract ref,
revision, and fingerprint; it cannot reinterpret an existing R7 scope.

Subset comparison is literal normalized set inclusion over exact resource refs.
No mutable domain containment rule participates.

## 11. One responsibility lineage

### 11.1 Root Assignment only

R7 removes R2 `PARENT_ASSIGNMENT` in v0.1. Every durable
`ResponsibilityAssignmentRevisionR7` has:

```yaml
source_responsibility:
  kind: JENN_ROOT_DIRECTION
  source_ref:
issued_by_actor_id: exact_current_Jenn_root_actor
max_redelegation_depth: 0..3
```

The exact authenticated Jenn issuance action is historical proof under Section
9. A Responsibility Assignment cannot issue another Responsibility Assignment.
All downstream responsibility transfer uses `DelegationGrantRevision`.

This does not make responsibility a permission. It removes the second transfer
channel and keeps accountability lineage singular.

### 11.2 Unified delegation lineage

Every Delegation chain has exactly one root:

```text
Jenn root direction
or
one current root ResponsibilityAssignmentRevisionR7
```

Every child retains that exact root, names its exact immediate parent, narrows
the exact-set scope and time window, and decrements remaining depth exactly
once. Actor IDs across the entire root-to-leaf chain are unique; a repeated
Actor is a cycle and is rejected.

```text
maximum Delegation edges per chain = 3
parallel chain union = forbidden
Assignment recursion = forbidden
Assignment plus Delegation combined depth = root Assignment + at most 3 edges
```

The lineage fingerprint is:

```text
SHA-256(JCS([
  "agents-os.responsibility-lineage.v0.1-r7",
  root_source_ref,
  root_source_fingerprint,
  [[delegation_ref, delegation_subject_fingerprint], ... root-to-leaf]
]))
```

No scope, depth, actor cycle, or source change may be hidden by starting a child
Assignment.

## 12. Corrected effective reducers

### 12.1 ResponsibilityAssignmentAssessmentR7

R1/R2 Assignment assessment remains the sole effective Assignment reducer and
additionally binds:

```yaml
ResponsibilityAssignmentAssessmentR7Additions:
  historical_issuance_validity_assessment_ref:
  current_transition_fact_refs: []
  responsibility_scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
```

Reduction order:

```text
REVOKE transition -> REVOKED
non-current head -> SUPERSEDED
SUSPEND without valid later RESUME -> SUSPENDED
missing/conflicting head, action assurance, recipient identity, scope,
  transition, time, source, or fingerprint -> INDETERMINATE
recipient Actor SUSPENDED -> SUSPENDED
recipient Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
trusted now before start -> NOT_YET_ACTIVE
trusted now at/after expiry -> EXPIRED
all exact current inputs valid -> ACTIVE
```

### 12.2 DelegationAssessment R7 correction

R1 `DelegationAssessment` remains the sole effective reducer and additionally
binds:

```yaml
DelegationAssessmentR7Additions:
  delegation_activation_assessment_ref:
  historical_issuance_validity_assessment_ref:
  historical_activation_action_validity_assessment_ref:
  current_transition_fact_refs: []
  responsibility_scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
```

Corrected reduction order:

```text
target REVOKE or RENOUNCE -> REVOKED
non-current grant head or superseded exact parent -> SUPERSEDED
target or ancestor SUSPEND without later valid RESUME -> SUSPENDED
missing/conflicting head, actor identity, source Assignment, parent grant,
  activation, historical action assurance, scope, lineage, transition, time,
  policy, or fingerprint -> INDETERMINATE
delegator or delegate Actor SUSPENDED -> SUSPENDED
delegator or delegate Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
trusted now at/after expiry -> EXPIRED
trusted now before start or activation NOT_ACTIVATED -> NOT_YET_ACTIVE
all exact current operational inputs valid -> ACTIVE
```

Current operational inputs are the exact Actor identity revisions, root source
responsibility, parent delegation assessments, scope/lineage, transition facts,
time/policy, and activation assessment. Historical issuer or acknowledging
Principal Bindings are not current operational inputs.

## 13. Recovery, tests, and materialization

### 13.1 Fail-closed recovery

Before F3 Command intake may open, recovery must verify:

```text
one current head and contiguous revision chain for every Actor, Principal,
  Authenticator Profile, Binding, Assignment, Delegation, and evidence stream
every lifecycle transition matches its matrix and exact authority
every transition fact CAS and Event sequence is unique and ordered
every effective projection is reproducible from activation plus current inputs
historical action assurance is separate from current session state
all compromise-impact target sets and fingerprints are complete
all ResponsibilityScopes use EXACT_SET and literal subset comparison
no PARENT_ASSIGNMENT exists in an R7-conformant v0.1 state
every responsibility lineage has at most three Delegation edges and no Actor cycle
every numeric scalar satisfies the exact R7 profile
synthetic M0 subjects match one accepted manifest and no production subject
```

Any duplicate head, fork, missing Event, ambiguous transition authority,
unresolved historical assurance, scalar mismatch, projection disagreement, or
unknown schema stops affected intake as `INDETERMINATE`. Recovery never repairs
or rewrites a historical fact silently.

### 13.2 Mandatory negative and race tests

An authorized future implementation must include at least:

```text
Principal create/update fork and stale-head rejection
Principal class/environment mutation rejection
Profile update invalidating new use of the superseded exact profile revision
synthetic fixture with extra, omitted, production, Jenn-credential, or host subject rejection
activation ACTIVATED while Binding effective state is expired/revoked/suspended
routine issuing-session expiry leaving committed Assignment/Delegation effective
explicit compromise challenge moving only named actions to INDETERMINATE
explicit invalidation preventing future use without deleting historical Events
Jenn revoking another issuer's Delegation without changing issuer provenance
delegate renunciation closing only its exact chain
revocation-before-Command and Command-commit-before-revocation race ordering
SUSPEND/RESUME CAS conflict and REVOKE terminality
PARENT_ASSIGNMENT rejection
DECLARED_SUBTREE rejection
Assignment plus Delegation cycle and depth rejection
all listed numeric fields at -0, fraction, 0, 1, 2^53-1, and 2^53 boundaries
cross-writer byte identity for every new R7 record fingerprint
recovery rebuild equality for activation and effective projections
```

### 13.3 Effective materialization requirement

Before fresh independent review, the author run must create a read-only:

```text
F2 Effective Contract Materialization v0.1-r7
```

It must bind R1-R7 hashes, identify every replaced section, present the
effective rules without treating superseded prose as current, and contain no
new semantics. The materialization is a reviewer and implementer reading
surface, not an acceptance subject and not a new source of authority. Any
disagreement is resolved by the fixed R1-R7 subjects and R7 precedence.

## 14. Finding disposition

| Finding | R7 disposition |
|---|---|
| `F2-R6-SR-B01` | Principal and Profile lifecycle closed by Sections 3, 5, and 6 |
| `F2-R6-SR-B02` | activation/effective currentness separated by Sections 7 and 12 |
| `F2-R6-SR-B03` | historical/current dependency separated by Section 9 |
| `F2-R6-SR-B04` | executable transition facts closed by Section 8 |
| `F2-R6-SR-B05` | Actor transition matrix and validity window closed by Section 4 |
| `F2-R6-SR-B06` | all F2 numeric scalars closed by Section 2 |
| `F2-R6-SR-M01` | upgraded blocker; `DECLARED_SUBTREE` rejected by Section 10 |
| `F2-R6-SR-M02` | upgraded blocker; recursive Assignment rejected by Section 11 |
| `F2-R6-SR-M03` | materialization required by Section 13.3 |

## 15. Atomic acceptance and non-authorization

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R7_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - F2_R2_amendment_sha256_8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
  - F2_R3_amendment_sha256_d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
  - F2_R4_amendment_sha256_a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
  - F2_R5_amendment_sha256_cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be
  - F2_R6_amendment_sha256_bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932
  - this_exact_R7_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
effective_materialization_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R7 does not create runtime objects, database tables, profiles, Principals,
credentials, bindings, assignments, delegations, transition facts, services,
providers, TaskPermits, or host effects. It does not converge the canonical
Prohibited Behavior List. It does not accept F2, start F3, or authorize
implementation or runtime activation.
