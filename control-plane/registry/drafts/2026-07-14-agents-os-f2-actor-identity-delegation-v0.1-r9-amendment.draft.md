# AGENTS OS F2 Actor Identity and Delegation v0.1 R9 Binding Bootstrap and Impact Membership Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R9_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r9
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

R9 closes only `F2-R8-IR-B01` through `B03` and `M01` through `M03`. Fixed
R1-R8 hashes remain unchanged. R9 has exact precedence over:

```text
R8 Section 2.1 mutation-kind and target-kind enums
R8 Section 2.2 Binding and manifest-activation body projections
R8 Section 3 authority-basis watermark and Profile-controller fields
R8 Section 5 CompromiseImpact target-membership transition rules
R8 Sections 6.3-6.4 manifest activation and derived Binding rules
R8 Section 8.2 materialization requirement
```

All other R1-R8 rules remain effective. R1-R9 form one indivisible proposed
acceptance unit.

## 2. Acyclic manifest activation

### 2.1 Exact pre-action body

`SYNTHETIC_M0_MANIFEST_ACTIVATION` body is replaced by:

```yaml
SyntheticM0ManifestActivationBodyV0_1R9:
  activation_stream_id:
  activation_revision:
  expected_previous_activation_revision: positive_revision | null
  manifest_ref:
  manifest_fingerprint:
  transition: ACCEPT | REVOKE
  authority_basis_ref:
  authority_basis_fingerprint:
  expected_ledger_head_event_sequence:
  effective_at_event_sequence:
```

It excludes every later Jenn decision ref/fingerprint, action ref/fingerprint,
intent ref/fingerprint, replay identity, and final activation fingerprint. The
body is hashed, then the intent is fixed, then Jenn's immutable decision binds
that exact intent and body, then the final activation revision derives:

```text
Jenn_decision_ref = lifecycle_action_ref.action_ref
Jenn_decision_fingerprint = lifecycle_action_ref.action_fingerprint
```

The final activation fingerprint includes the derived decision fields. The
pre-action body does not. This is the only valid order; fixed points reject.

### 2.2 Activation revision consistency

The final R8 activation schema remains effective, with these additional exact
predicates:

```text
lifecycle_action_ref.action_kind = JENN_GOVERNANCE_DECISION
lifecycle_action_ref.mutation_intent_fingerprint = final mutation intent fingerprint
lifecycle_action_ref.committed_event_sequence = effective_at_event_sequence
derived Jenn decision fields exactly equal lifecycle_action_ref fields
final revision recomputes the R9 body without derived decision/action fields
```

## 3. Complete Binding issuance mutation

### 3.1 Mutation kind and authority

R9 adds:

```text
mutation_kind = BINDING_REVISION
target_kind = BINDING
```

The exact mutation authority object is `TransitionAuthorityBasisV0_1R9`.
Binding issuance uses this total table:

| Activation mode | Allowed exact basis kinds | Required current facts |
|---|---|---|
| `JENN_INTERACTIVE_AUTHENTICATION` | `JENN_ROOT_ACTION`, or `JENN_GOVERNANCE_DECISION_BASIS` for bootstrap only | exact Actor, Principal, Profile, proof, scope, and time inputs |
| `RESIDENT_ATTESTED_AGENT_SESSION` | `IDENTITY_STEWARD_ACTION` | exact steward identity/Binding and target Actor/Principal/Profile inputs |
| `SERVICE_PROVISIONING_ATTESTATION` | `ACCEPTED_PROVISIONING_ACTION` | exact component, provisioning basis, Principal, Profile, scope, and time inputs |
| `WORKER_ASSIGNMENT_HANDSHAKE` | `DIRECT_DELEGATOR_ACTION` | exact responsible Actor identity/Binding and current responsibility assessment |
| `SYNTHETIC_M0_FIXTURE` | Section 6 manifest-derived group intent only | exact ACTIVE manifest, controller, Binding creation spec, synthetic Actor/Principal/Profile refs |

Every unlisted mode/basis tuple rejects.

### 3.2 Complete effective Binding schema

R9 replaces the assembled R1/R3/R7 Binding subject field lists and R3/R4
subject fingerprint with:

```yaml
ActorPrincipalBindingRevisionR9:
  schema_version: agents-os.actor-principal-binding-revision.v0.1-r9
  binding_id:
  binding_revision:
  expected_previous_binding_revision: positive_revision | null
  supersedes_binding_revision: positive_revision | null

  actor_id:
  actor_identity_revision:
  principal_id:
  principal_revision:
  principal_class:
  authenticator_profile_ref:
  environment:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  binding_scope:
  issued_by_actor_ref: optional
  issuance_basis_ref:
  activation_mode: JENN_INTERACTIVE_AUTHENTICATION | RESIDENT_ATTESTED_AGENT_SESSION | SERVICE_PROVISIONING_ATTESTATION | WORKER_ASSIGNMENT_HANDSHAKE | SYNTHETIC_M0_FIXTURE
  status: ACTIVE

  authority_basis: TransitionAuthorityBasisV0_1R9
  authority_basis_fingerprint:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  binding_issuance_source_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Create uses revision 1 and null predecessor fields. A successor is contiguous,
uses exact current-head CAS, preserves `binding_id`, `actor_id`, and
`principal_id`, and may only advance exact Actor/Principal/Profile revisions,
narrow scope, or shorten the window. Different Actor or Principal requires a
new `binding_id`. Administrative state changes remain transition facts.

For an authenticated Actor issuance route, `issued_by_actor_ref` equals the
action Actor. Governance, component, and synthetic routes require null. The
issuance source is the exact R8 lifecycle action for non-synthetic issuance.

### 3.3 Binding mutation body and fingerprint

The `BINDING_REVISION` body contains every Section 3.2 field except:

```text
mutation_body_fingerprint
mutation_intent_ref
mutation_intent_fingerprint
binding_issuance_source_ref
mutation_replay_identity
created_at_event_sequence
canonical_fingerprint
```

For non-synthetic issuance, the final source ref is derived from the committed
action after the intent. The final Binding fingerprint is:

```text
SHA-256(JCS([
  "agents-os.actor-principal-binding-revision.v0.1-r9",
  exact_Section_3_2_known_object_without_canonical_fingerprint
]))
```

It includes the verified authority object, authority fingerprint, body and
intent fingerprints, exact issuance-source object, replay identity, and Event.
Unknown fields, old R3/R4 positional fingerprints, missing provenance, or a
mismatched body reject.

### 3.4 Synthetic Binding derivation

At manifest `ACCEPT`, each Binding spec materializes the same Section 3.2
schema using:

```text
mutation_body_fingerprint = exact Binding creation-spec fingerprint
mutation_intent_ref/fingerprint = manifest activation intent ref/fingerprint
binding_issuance_source_ref = exact Binding SyntheticManifestDerivedLifecycleRefV0_1
mutation_replay_identity = that ref's derivation replay identity
created_at_event_sequence = manifest activation Event
authority_basis = exact manifest Jenn governance basis bound by the group intent
```

The exact Binding creation-spec fingerprint is the same R8 mutation-body
formula for `BINDING_REVISION`; it is not a second digest domain. Therefore the
manifest's Binding spec fingerprint and the created Binding
`mutation_body_fingerprint` are byte-identical.

No unnamed generic Binding overlay exists. Binding is part of the same atomic
all-or-none manifest materialization as Profile and Principal.

## 4. Immutable CompromiseImpact membership

For one `impact_stream_id`, the revision-1 exact sorted
`complete_target_action_refs` and `complete_target_set_fingerprint` are
immutable stream identity.

```text
revision 1 CHALLENGE or INVALIDATE -> fixes exact target set
CHALLENGED -> CLEAR_CHALLENGE or INVALIDATE, exact same target set required
INVALIDATED -> terminal, exact target set remains discoverable forever
CLEARED -> terminal for that stream; exact target set remains audit-visible
any added, omitted, reordered, or changed target/fingerprint -> reject
```

Partial clear or partial invalidation requires a new impact stream whose
revision 1 names its own complete target set; it cannot mutate or hide the old
stream. The ledger index retains every stream's terminal current head by every
member action, including `CLEARED` and `INVALIDATED`. Therefore a successor can
never make an earlier challenged or invalidated action disappear from the
HistoricalImpactInputSet.

## 5. Authority watermark and Profile-controller split

### 5.1 Exact currentness boundary

R9 replaces `TransitionAuthorityBasisV0_1R8` with the same fields and enum plus:

```yaml
TransitionAuthorityBasisV0_1R9_additions:
  target_profile_assessment_ref: optional
  controller_currentness_assessment_ref: optional
```

The ambiguous R8 `profile_assessment_ref` is removed. For every current-state
basis:

```text
authority_basis.based_on_event_sequence
  = mutation_intent.expected_ledger_head_event_sequence
```

Every identity, Binding, responsibility, target Profile, controller, manifest,
policy, and component assessment in the basis must be current at that exact
watermark. Older or future assessment watermarks reject.

`JENN_GOVERNANCE_DECISION_BASIS` is the only immutable-prior exception. Its
source decision Event is strictly less than or equal to expected ledger head;
its validity window contains intent issuance; Rust revalidates its fingerprint,
scope, non-revocation, and expiry at expected ledger head. Its
`based_on_event_sequence` still equals expected ledger head and records that
revalidation, not the source decision Event.

The R9 authority-basis domain tag is
`agents-os.transition-authority-basis.v0.1-r9`. Its fingerprint uses the R8
default exact-known-object formula with every R8 retained field, the two R9
assessment fields, and no removed `profile_assessment_ref`.

The same watermark rule applies to
`ActorIdentityTransitionAuthorityBasisV0_1R8`: all current-state inputs are
assessed at the intent expected ledger head. Its Jenn governance basis uses the
same immutable-prior revalidation exception. R9 does not otherwise change the
Actor authority union or Actor fingerprint.

### 5.2 Profile target versus controller currentness

For a Profile lifecycle mutation:

```text
target_profile_assessment_ref
  -> exact target Profile assessment at required source status

controller_currentness_assessment_ref
  -> exact controller Actor/component/manifest assessment
```

For `CREATE`, target assessment is null. For `UPDATE` and `SUSPEND`, it is
`ACTIVE`. For `RESUME`, it is `SUSPENDED`. For `RETIRE`, it is `ACTIVE` or
`SUSPENDED`. The controller assessment must be current and operational for all
controller routes; it is never inferred from the target Profile status.

For a Principal or Binding mutation, `target_profile_assessment_ref` names the
exact required ACTIVE authenticator Profile and
`controller_currentness_assessment_ref` names its separate controller. For
other target kinds both fields are forbidden unless their exact R9 table row
requires them.

## 6. Required materialization and fixtures

The R8 materialization remains historical author evidence and is not
implementation-safe. R9 requires a new derived materialization that prints:

```text
every R9 changed schema in full
the complete Profile, Principal, Binding, transition, Actor, and impact authority tables
the exact manifest pre-action and post-action order
the complete Binding body and fingerprint
the immutable impact target-set reducer
all R8 unchanged total reducers used by R9
source subject/hash/section for every effective block
```

Mandatory future authorized fixtures add:

```text
activation body containing Jenn decision fingerprint -> reject
non-synthetic Binding issuance without BINDING_REVISION intent -> reject
synthetic partial Binding materialization -> reject
Binding old R3/R4 fingerprint under R9 schema -> reject
impact successor omits or adds one action -> reject
invalidated or cleared stream remains indexed by every original action
authority basis watermark one Event stale -> reject
suspended target Profile plus current separate controller -> RESUME route valid
suspended controller or missing controller assessment -> reject
```

## 7. Finding disposition and non-authorization

| Finding | R9 disposition |
|---|---|
| `F2-R8-IR-B01` | resolved by Section 2 pre-action/post-action separation |
| `F2-R8-IR-B02` | resolved by Section 3 complete Binding path |
| `F2-R8-IR-B03` | resolved by Section 4 immutable stream membership |
| `F2-R8-IR-M01` | resolved by Section 5.1 exact watermark |
| `F2-R8-IR-M02` | resolved by Section 5.2 separate assessments |
| `F2-R8-IR-M03` | resolved only by the regenerated R9 materialization |

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R9_ATOMIC_BUNDLE
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R9 creates no runtime object, database, service, credential, Binding, impact,
provider call, permit, or effect. It does not accept F2, start F3, converge the
canonical Prohibited List, or authorize implementation or runtime activation.
