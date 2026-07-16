# AGENTS OS F2 Actor Identity and Delegation v0.1 R8 Deterministic Action, Assurance and M0 Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R8_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r8
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

R8 closes only the six blockers and one materialization major returned by the
fresh R7 independent review. It does not expand the F2 architectural direction.

Fixed subjects:

```text
R1 639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
R2 8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
R3 d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
R4 a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
R5 cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be
R6 bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932
R7 343881f2292fbb3c09b0cc572b0d9a9c8f77eef1e4b5957134de31796228187c
```

R8 has exact precedence over:

```text
R7 Section 3.1 LifecycleActionRef
R7 Sections 4-6 where lifecycle actions lack exact mutation-intent binding
R7 Section 8 target-specific transition authority and transition fact action binding
R7 Sections 8.3 and 12.2 Delegation descendant cascade
R7 Section 9 historical-action multi-impact aggregation
R7 Sections 5.1 and 6.5 synthetic M0 controller and manifest graph
R7 Section 4.2 complete ActorIdentityRevision schema and fingerprint
R7 Section 13.3 materialization requirement only where R8 requires regeneration
```

All other R1-R7 rules remain effective. R1 through R8 form one indivisible
acceptance unit.

## 2. Canonical mutation intent and exact action binding

### 2.1 MutationIntentV0_1

Every F2 lifecycle revision, governed transition, compromise impact, and
synthetic manifest creation must begin with one immutable exact intent. A
Section 6 derived synthetic `CREATE` uses the one manifest-activation intent as
its group intent and creates no second intent:

```yaml
MutationIntentV0_1:
  intent_id:
  intent_revision: 1
  mutation_kind: ACTOR_IDENTITY_REVISION | AUTHENTICATOR_PROFILE_REVISION | PRINCIPAL_REVISION | GOVERNED_STATE_TRANSITION | COMPROMISE_IMPACT | SYNTHETIC_M0_MANIFEST_CREATE | SYNTHETIC_M0_MANIFEST_ACTIVATION

  target_kind: ACTOR_IDENTITY | AUTHENTICATOR_PROFILE | PRINCIPAL | BINDING | ASSIGNMENT | DELEGATION | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE | COMPROMISE_IMPACT_STREAM | SYNTHETIC_M0_MANIFEST | SYNTHETIC_M0_MANIFEST_ACTIVATION
  target_stable_id:
  target_current_ref: optional
  target_current_fingerprint: optional
  expected_target_head:
    target_revision: positive_revision | null
    target_fingerprint: CanonicalDigestScalarV0_1 | null
    last_transition_event_sequence: event_sequence | null

  authority_basis_ref:
  authority_basis_fingerprint:
  mutation_body_fingerprint:

  expected_ledger_head_event_sequence:
  effective_at_event_sequence:
  issued_at_utc_ms:
  expires_at_utc_ms:
  nonce:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.mutation-intent.v0.1
```

The intent uses the R7 scalar profile and exact R7 array rules. It is valid only
when:

```text
intent_revision = 1
effective_at_event_sequence = expected_ledger_head_event_sequence + 1
issued_at_utc_ms < expires_at_utc_ms
target_kind is the exact target implied by mutation_kind and Section 2.2
target_current_ref/fingerprint are both null only for a create operation
expected_target_head matches the exact target stream or is all-null for create
mutation_body_fingerprint matches the mutation-kind projection in Section 2.2
```

The intent authority object is closed by mutation kind:

| Mutation kind | Exact authority object |
|---|---|
| `ACTOR_IDENTITY_REVISION` | `ActorIdentityTransitionAuthorityBasisV0_1R8` |
| `AUTHENTICATOR_PROFILE_REVISION`, `PRINCIPAL_REVISION`, `GOVERNED_STATE_TRANSITION` | `TransitionAuthorityBasisV0_1R8` |
| `COMPROMISE_IMPACT` | `TransitionAuthorityBasisV0_1R8` with `ACCEPTED_INCIDENT_POLICY_ACTION` or `JENN_ROOT_ACTION` only |
| `SYNTHETIC_M0_MANIFEST_CREATE`, `SYNTHETIC_M0_MANIFEST_ACTIVATION` | `TransitionAuthorityBasisV0_1R8` with `JENN_GOVERNANCE_DECISION_BASIS` only |

The referenced object ID and verified fingerprint must equal the intent fields.
No other authority object type or basis kind is accepted.

The one Event at `effective_at_event_sequence` is both the F3 committed intake
Event and the F2 lifecycle/transition Event. F3 may not allocate an intervening
Event. A future F3 design requiring multiple Events must amend this contract;
it may not guess another mapping.

### 2.2 Mutation body projections

The body fingerprint is:

```text
SHA-256(JCS([
  "agents-os.mutation-body.v0.1",
  mutation_kind,
  mutation_kind_specific_schema_known_object
]))
```

It contains every caller- or decision-chosen mutation field and excludes only
the later action ref, replay identity, final canonical fingerprint, and fields
derived exactly from the intent.

| Mutation kind | Complete body projection |
|---|---|
| `ACTOR_IDENTITY_REVISION` | every Section 7 Actor field except `mutation_body_fingerprint`, `mutation_intent_ref`, `mutation_intent_fingerprint`, `lifecycle_action_ref`, `mutation_replay_identity`, `created_at_event_sequence`, and `canonical_fingerprint`; `created_at_event_sequence` is fixed by intent effective sequence |
| `AUTHENTICATOR_PROFILE_REVISION` | every effective R7 Profile semantic field except the R8 common provenance/result fields listed below; its R7 `lifecycle_action_ref` is replaced by the R8 field |
| `PRINCIPAL_REVISION` | every effective R7 Principal semantic field except the R8 common provenance/result fields listed below; for non-synthetic `CREATE`, `provisioning_source_ref` is derived from and equals the same action ref, while later revisions include the immutable original provisioning source in the body; `transition_action_ref` is replaced by the R8 action field |
| `GOVERNED_STATE_TRANSITION` | target kind/ref/fingerprint, transition, typed authority basis fingerprint, expected target head, effective Event sequence, and ordered reason codes |
| `COMPROMISE_IMPACT` | impact stream/revision/CAS, compromised subject, incident basis, selection watermark, complete target set/fingerprint, impact, authority basis fingerprint, and effective Event sequence |
| `SYNTHETIC_M0_MANIFEST_CREATE` | every Section 6.2 manifest body field and spec fingerprint except creation action, activation, Event, and final fingerprint |
| `SYNTHETIC_M0_MANIFEST_ACTIVATION` | activation stream/revision/CAS, exact manifest ref/fingerprint, transition, Jenn decision ref/fingerprint, and effective Event sequence |

Optional fields occupy explicit JSON `null` positions. Unknown fields,
projection omissions, alternate order, or a mismatched body fingerprint reject
the intent.

Every final Actor, Profile, and Principal revision has this common R8
provenance/result overlay:

```yaml
R8LifecycleMutationProvenance:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
```

For Profile, this overlay replaces R7 `lifecycle_action_ref`. For Principal,
it replaces R7 `transition_action_ref`; the effective field name is
`lifecycle_action_ref`. On a non-synthetic Principal `CREATE`, the R7
`provisioning_source_ref` equals this same action ref and is derived after the
intent; on later Principal revisions it remains the immutable original create
source and is included in the mutation body. Synthetic M0 `CREATE` uses the
exact Section 6.4 group-intent and derived-ref rules. None of the six overlay
fields, nor the final canonical fingerprint, is included in its own mutation
body projection.

### 2.3 LifecycleActionRefV0_1R8

R8 replaces R7 `LifecycleActionRefV0_1` with:

```yaml
LifecycleActionRefV0_1R8:
  interface_version: agents-os.lifecycle-action-ref.v0.1-r8
  action_kind: AUTHENTICATED_ACTOR_ACTION | JENN_GOVERNANCE_DECISION | ACCEPTED_PROVISIONING_ACTION
  action_ref:
  action_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  mutation_replay_identity: CanonicalDigestScalarV0_1
  committed_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.lifecycle-action-ref.v0.1-r8
```

For `AUTHENTICATED_ACTOR_ACTION`, the exact F3 Command envelope payload must
contain only the mutation-kind Command fields plus the exact intent ref and
fingerprint. Its `F3_intake_event_sequence` equals the intent effective Event.
The complete R4 `AuthenticatedActorActionRef` is recomputed from committed F3
bytes and must name the same Actor as the typed authority basis.

For `JENN_GOVERNANCE_DECISION` and `ACCEPTED_PROVISIONING_ACTION`, the immutable
decision/action bytes must contain the exact intent ref, intent fingerprint,
mutation body fingerprint, expected target head, and effective Event sequence.
This is the non-F3 equivalent of exact payload binding.

The replay identity is:

```text
SHA-256(JCS([
  "agents-os.lifecycle-mutation-replay.v0.1-r8",
  mutation_intent_fingerprint,
  action_ref,
  action_fingerprint
]))
```

One `intent_id` may commit exactly one action and one mutation. Same intent,
action, and bytes is idempotent. Same intent with a different action, body,
target, head, authority, Event, or bytes is a replay conflict and is rejected.

### 2.4 Acyclic commit order

The only valid order is:

```text
mutation body
-> mutation_body_fingerprint
-> MutationIntent
-> mutation_intent_fingerprint
-> committed F3 Command / Jenn decision / provisioning action
-> LifecycleActionRef
-> mutation_replay_identity
-> final lifecycle revision or transition fact
-> final canonical fingerprint
```

The intent never contains the later action ref or final subject/fact
fingerprint. The final subject/fact contains both intent and action refs and
must recompute the body fingerprint. Fixed points are rejected.

Unless a later R8 section gives a more specific formula, every R8 canonical
fingerprint is:

```text
SHA-256(JCS([
  exact_R8_domain_tag,
  exact_schema_known_object_without_canonical_fingerprint
]))
```

Every displayed field, including explicit nulls, embedded known objects, and
separately displayed verified digest fields, is included. Unknown or omitted
fields reject. The Actor formula in Section 7.3 is the only R8 specialization
that inserts verified embedded-object digest strings instead of the objects.
The effective Profile and Principal revision domain tags become:

```text
agents-os.authenticator-profile-revision.v0.1-r8
agents-os.principal-revision.v0.1-r8
```

Their exact known objects are the complete R7 semantic schema after the field
replacements in Section 2.2 plus all R8 common provenance/result fields. Thus
the final revision fingerprint binds the body, intent, action, replay identity,
and committed Event.

## 3. Typed transition authority

### 3.1 TransitionAuthorityBasisV0_1R8

R8 replaces R7's narrative `authority_basis_ref` with:

```yaml
JennRootGovernanceAuthorityRefV0_1R8:
  authority_ref_id:
  authority_contract_version: agents-os.jenn-root-governance-authority-ref.v0.1-r8
  authority_kind: JENN_EXPLICIT_PROJECT_DECISION_AUTHORITY
  source_decision_ref:
  source_decision_fingerprint:
  permitted_basis_uses: []
  environment: SYNTHETIC_TEST
  not_before_utc_ms:
  expires_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.jenn-root-governance-authority-ref.v0.1-r8
```

This is a low-disclosure exact reference to a prior immutable Jenn project
decision. It is not a runtime identity, Binding, credential, permission level,
or reusable authorization for production. Its source decision must predate the
mutation intent, its validity window must contain intent issuance, and its
declared basis use must match the mutation. `permitted_basis_uses` is a sorted,
non-empty, duplicate-free subset of `IDENTITY_BOOTSTRAP` and
`SYNTHETIC_M0_MANIFEST_GOVERNANCE`. The later Jenn decision action is still
required to bind the exact intent and body.

The transition basis is:

```yaml
TransitionAuthorityBasisV0_1R8:
  authority_basis_id:
  basis_kind: JENN_ROOT_ACTION | JENN_GOVERNANCE_DECISION_BASIS | IDENTITY_STEWARD_ACTION | PROFILE_CONTROLLER_ACTION | BOUND_ACTOR_SELF_ACTION | DIRECT_DELEGATOR_ACTION | ANCESTOR_DELEGATOR_ACTION | DELEGATE_RENUNCIATION_ACTION | ACCEPTED_INCIDENT_POLICY_ACTION | ACCEPTED_PROVISIONING_ACTION
  requested_by_actor_ref: optional
  requested_by_actor_identity_assessment_ref: optional
  requested_by_effective_binding_assessment_ref: optional
  Jenn_root_authority_ref: optional
  Jenn_root_authority_fingerprint: optional
  target_relation_ref: optional
  target_relation_fingerprint: optional
  responsibility_assessment_ref: optional
  profile_assessment_ref: optional
  lifecycle_controller_ref: optional
  incident_policy_ref: optional
  incident_policy_fingerprint: optional
  incident_controller_ref: optional
  provisioning_component_ref: optional
  provisioning_component_fingerprint: optional
  provisioning_basis_ref: optional
  provisioning_basis_fingerprint: optional
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.transition-authority-basis.v0.1-r8
```

Every optional field is required or forbidden by basis kind:

| Basis kind | Required exact current inputs | Forbidden inputs |
|---|---|---|
| `JENN_ROOT_ACTION` | Jenn Actor ref, ACTIVE identity assessment, ACTIVE effective Jenn Binding, Jenn root relation | Profile/controller/incident inputs |
| `JENN_GOVERNANCE_DECISION_BASIS` | exact current `JennRootGovernanceAuthorityRefV0_1R8`; the later decision action binds the exact mutation intent | requested Actor/Binding, Profile/controller, responsibility, incident, and provisioning inputs |
| `IDENTITY_STEWARD_ACTION` | steward Actor ref, ACTIVE identity and Binding assessments, exact current stewardship relation to target | Profile/controller/incident inputs |
| `PROFILE_CONTROLLER_ACTION` | exact ACTIVE Profile assessment and matching lifecycle-controller ref; for an Actor controller, exact current controller Actor identity/Binding; for a component controller, exact accepted component and provisioning basis; for synthetic M0, exact ACTIVE manifest assessment | incident inputs; Actor fields are required only for an Actor controller and forbidden otherwise |
| `BOUND_ACTOR_SELF_ACTION` | target Actor ref, ACTIVE identity assessment, ACTIVE effective Binding that is the target or represents its Actor | Profile/controller/incident inputs |
| `DIRECT_DELEGATOR_ACTION` | target grant relation, exact delegator Actor ACTIVE identity/Binding, current source-responsibility assessment | Profile/controller/incident inputs |
| `ANCESTOR_DELEGATOR_ACTION` | exact current lineage containing the Actor as an ancestor delegator, ACTIVE identity/Binding, current source responsibility | Profile/controller/incident inputs |
| `DELEGATE_RENUNCIATION_ACTION` | target grant relation, exact delegate Actor ACTIVE identity/Binding | responsibility, Profile/controller/incident inputs |
| `ACCEPTED_INCIDENT_POLICY_ACTION` | exact accepted policy revision/fingerprint and matching incident controller | requested Actor, Actor Binding, responsibility inputs |
| `ACCEPTED_PROVISIONING_ACTION` | exact accepted provisioning component ref/fingerprint and provisioning basis ref/fingerprint | requested Actor, Actor Binding, responsibility, and incident inputs |

Actor-action bases require `requested_by_actor_ref` and the committed action
Actor to equal the basis Actor. Incident and provisioning bases forbid
`requested_by_actor_ref`. `PROFILE_CONTROLLER_ACTION` follows the closed
controller kind: a System Service Actor controller requires the exact Actor
fields and `AUTHENTICATED_ACTOR_ACTION`; an accepted component controller
forbids Actor fields and requires `ACCEPTED_PROVISIONING_ACTION`; a synthetic
controller uses only the Section 6 manifest-derived path. Other actor bases
require `AUTHENTICATED_ACTOR_ACTION`; `JENN_ROOT_ACTION` requires the exact
Jenn authenticated action; `JENN_GOVERNANCE_DECISION_BASIS` requires
`JENN_GOVERNANCE_DECISION`; incident basis uses the action kind fixed by its
accepted incident policy.
`authority_basis_ref` in an intent equals this immutable
`authority_basis_id`, and its fingerprint equals the verified basis
fingerprint. Missing, extra, stale, non-ACTIVE, mismatched, or indeterminate
basis input rejects the transition.

### 3.2 Total target/transition predicate

Only these combinations are valid:

| Target kind | Transition | Allowed basis kinds | Additional predicate |
|---|---|---|---|
| Authenticator Profile | `CREATE` | `JENN_ROOT_ACTION`, `JENN_GOVERNANCE_DECISION_BASIS`, `ACCEPTED_PROVISIONING_ACTION` | no current head; synthetic create uses Section 6 derived-ref exception |
| Authenticator Profile | `UPDATE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` | current target `ACTIVE`; immutable fields unchanged |
| Authenticator Profile | `SUSPEND` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | current target `ACTIVE` |
| Authenticator Profile | `RESUME` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` | current target `SUSPENDED`; dependencies otherwise ACTIVE |
| Authenticator Profile | `RETIRE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` | current target `ACTIVE` or `SUSPENDED` |
| Principal | `CREATE` | `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_PROVISIONING_ACTION` | no current head; exact ACTIVE Profile; synthetic create uses Section 6 derived-ref exception |
| Principal | `ROTATE_CREDENTIALS` | `PROFILE_CONTROLLER_ACTION` | current target `ACTIVE`; immutable class/environment unchanged |
| Principal | `SUSPEND` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | current target `ACTIVE` |
| Principal | `RESUME` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` | current target `SUSPENDED`; Profile and credential status ACTIVE |
| Principal | `REVOKE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | current target `ACTIVE` or `SUSPENDED` |
| Principal | `RETIRE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` | current target `ACTIVE`, `SUSPENDED`, or `REVOKED` |
| Binding | `SUSPEND` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | target currently `ACTIVE` |
| Binding | `RESUME` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` | target currently `SUSPENDED`; all effective dependencies otherwise ACTIVE |
| Binding | `REVOKE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | target `ACTIVE` or `SUSPENDED` |
| Binding | `RENOUNCE` | none | always reject |
| Assignment | `SUSPEND` | `JENN_ROOT_ACTION` | target currently `ACTIVE` |
| Assignment | `RESUME` | `JENN_ROOT_ACTION` | target currently `SUSPENDED`; root direction and recipient ACTIVE |
| Assignment | `REVOKE` | `JENN_ROOT_ACTION` | target `ACTIVE` or `SUSPENDED` |
| Assignment | `RENOUNCE` | none | always reject in v0.1 |
| Delegation | `SUSPEND` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION`, `ANCESTOR_DELEGATOR_ACTION` | target currently `ACTIVE` |
| Delegation | `RESUME` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION`, `ANCESTOR_DELEGATOR_ACTION` | target currently `SUSPENDED`; source and all ancestors ACTIVE |
| Delegation | `REVOKE` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION`, `ANCESTOR_DELEGATOR_ACTION` | target `ACTIVE` or `SUSPENDED` |
| Delegation | `RENOUNCE` | `DELEGATE_RENUNCIATION_ACTION` | exact current delegate only |
| Binding activation evidence | `SUSPEND` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | evidence currently `ACTIVATED` |
| Binding activation evidence | `RESUME` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` | current proof reverified; target otherwise effective |
| Binding activation evidence | `REVOKE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` | evidence active or suspended |
| Binding activation evidence | `RENOUNCE` | none | always reject |
| Delegation activation evidence | `SUSPEND` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` | evidence currently `ACTIVATED` |
| Delegation activation evidence | `RESUME` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` | exact acknowledgement reverified; grant/source ACTIVE |
| Delegation activation evidence | `REVOKE` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` | evidence active or suspended |
| Delegation activation evidence | `RENOUNCE` | `DELEGATE_RENUNCIATION_ACTION` | exact current delegate only |

The table contains only exact Section 3.1 enum values. There is no evidence
steward, implicit lifecycle authority, accepted-scope narrative, or role-name
shortcut.

Incident policy is valid only for the listed safer `SUSPEND` or `REVOKE`
transitions. It cannot resume, renounce, update content, change responsibility,
or create a target.

Profile and Principal rows create their ordinary contiguous lifecycle revision;
the remaining rows create `GovernedStateTransitionFactV0_1R8`. Actor revision
authority is the separate complete union and matrix in Section 7. Any lifecycle
transition or target/basis tuple not listed here or in Section 7 rejects.

### 3.3 GovernedStateTransitionFactV0_1R8

R8 replaces the R7 fact authority/action fields with:

```yaml
GovernedStateTransitionFactV0_1R8:
  transition_fact_id:
  target_kind: BINDING | ASSIGNMENT | DELEGATION | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE
  target_ref:
  target_fingerprint:
  transition: SUSPEND | RESUME | REVOKE | RENOUNCE
  authority_basis: TransitionAuthorityBasisV0_1R8
  authority_basis_fingerprint:
  expected_target_head:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  effective_at_event_sequence:
  reason_codes: []
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.governed-state-transition-fact.v0.1-r8
```

The fact recomputes every body, intent, action, authority, CAS, replay, and
Event field before committing the one Event. Any mismatch rejects the write.

## 4. Total Delegation ancestor cascade

### 4.1 Complete input set

One `DelegationAssessment` must read at one `based_on_event_sequence`:

```text
the exact current target grant head and own transition head
the exact current root Assignment assessment, when present
every exact root-to-parent DelegationAssessment and transition head
target issuance and activation assurance
every ancestor issuance and activation assurance
current Actor identity assessments
scope, lineage, time, and policy
```

The input list is the exact root-to-target lineage and cannot omit or reorder an
ancestor.

### 4.2 Source and ancestor state mapping

Each root source or ancestor maps to the target result from the Event at which
that state became effective:

| Upstream effective state | Descendant mapped state |
|---|---|
| `REVOKED` or `RENOUNCED` | `REVOKED` |
| `SUPERSEDED` | `SUPERSEDED` |
| `SUSPENDED` | `SUSPENDED` |
| `INDETERMINATE`, challenged assurance, or incomplete coverage | `INDETERMINATE` |
| `EXPIRED` | `EXPIRED` |
| `NOT_YET_ACTIVE` | `NOT_YET_ACTIVE` |
| `ACTIVE` | continue |

Historical-action `INVALIDATED` maps to `REVOKED` prospectively from the impact
Event. A valid `RESUME` removes only the suspension introduced by its exact
transition stream; any other suspended ancestor continues to map to
`SUSPENDED`.

### 4.3 Total precedence

After own-target terminal transitions, aggregate the target, root source, and
all ancestors using:

```text
REVOKED
> SUPERSEDED
> SUSPENDED
> INDETERMINATE
> EXPIRED
> NOT_YET_ACTIVE
> ACTIVE
```

Exact reduction order:

```text
own REVOKE or RENOUNCE -> REVOKED
any root/ancestor REVOKED, RENOUNCED, or assurance INVALIDATED -> REVOKED
own head or any required exact ancestor SUPERSEDED -> SUPERSEDED
own or any root/ancestor SUSPENDED -> SUSPENDED
any missing/conflicting/challenged/indeterminate dependency -> INDETERMINATE
own or any root/ancestor EXPIRED -> EXPIRED
own or any root/ancestor NOT_YET_ACTIVE -> NOT_YET_ACTIVE
all exact inputs ACTIVE -> ACTIVE
```

The child state changes at the upstream prospective Event boundary. No child
transition Event is synthesized. Replay at any later Event sequence produces
the same result from the immutable ancestry and transition heads.

## 5. Complete historical-assurance aggregation

### 5.1 CompromiseImpactFactV0_1R8

R8 replaces R7 `CompromiseImpactFactV0_1` provenance and authority fields with
this complete effective schema:

```yaml
CompromiseImpactFactV0_1R8:
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
  authority_basis: TransitionAuthorityBasisV0_1R8
  authority_basis_fingerprint:
  expected_previous_impact_event_sequence: event_sequence | null
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  effective_at_event_sequence:
  reason_codes: []
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag is replaced by:

```text
agents-os.compromise-impact-fact.v0.1-r8
```

The total authority predicate is:

| Impact | Allowed exact basis kinds |
|---|---|
| `CHALLENGE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| `INVALIDATE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION` |
| `CLEAR_CHALLENGE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION` |

The identity steward must be the exact same-or-higher steward for the named
compromised Actor or Principal. Incident policy cannot invalidate or clear.
All R7 stream CAS, complete target-set, terminal invalidation, and
low-disclosure rules remain effective. The fact recomputes body, intent,
action, authority, replay, target-set, and Event fields in one transaction.

### 5.2 HistoricalImpactInputSetV0_1

```yaml
HistoricalImpactInputSetV0_1:
  action_ref:
  action_fingerprint:
  coverage_through_event_sequence:
  current_impact_heads:
    - impact_stream_id:
      impact_revision:
      impact_fact_ref:
      impact_fact_fingerprint:
      effective_at_event_sequence:
      stream_state: CHALLENGED | INVALIDATED | CLEARED
  impact_input_set_fingerprint: CanonicalDigestScalarV0_1
```

Domain tag:

```text
agents-os.historical-impact-input-set.v0.1
```

Rust derives the set from the ledger index of every impact stream whose current
head at or before the coverage watermark names the exact action. It sorts by
`impact_stream_id`, then revision. Caller-supplied refs are ignored. The set
fingerprint is:

```text
SHA-256(JCS([
  "agents-os.historical-impact-input-set.v0.1",
  action_ref,
  action_fingerprint,
  coverage_through_event_sequence,
  [[impact_stream_id, impact_revision, impact_fact_fingerprint,
    effective_at_event_sequence, stream_state], ...]
]))
```

The coverage watermark must equal the `HistoricalActionValidityAssessment`
`based_on_event_sequence`. Missing index coverage, duplicate stream head,
forked stream, target-set mismatch, Event gap, or fingerprint conflict makes
the set incomplete.

### 5.3 Per-stream state

```text
no head -> stream absent
CHALLENGE -> CHALLENGED
CHALLENGE then exact CLEAR_CHALLENGE -> CLEARED
INVALIDATE -> INVALIDATED terminal
CLEAR_CHALLENGE without current CHALLENGED -> reject
```

Clearing one stream never clears another stream. An invalidated stream cannot
be cleared or superseded.

### 5.4 Aggregate current_assurance

The total precedence is:

```text
any verified current impact head is INVALIDATED -> INVALIDATED
else input coverage is incomplete or conflicting -> INDETERMINATE
else complete set contains any CHALLENGED -> CHALLENGED
else -> CONFIRMED
```

`CLEARED` contributes no challenge but remains audit evidence. The
`HistoricalActionValidityAssessmentR8` contains the exact input-set ref and
fingerprint rather than a caller-visible free list:

```yaml
HistoricalActionValidityAssessmentR8Additions:
  impact_input_set_ref:
  impact_input_set_fingerprint:
  impact_coverage_through_event_sequence:
```

## 6. Canonical acyclic synthetic M0 graph

### 6.1 SyntheticM0ControllerSpecV0_1

R8 eliminates a separate synthetic controller subject/current head. The
manifest owns one immutable deterministic verifier spec:

```yaml
SyntheticM0ControllerSpecV0_1:
  controller_contract_version: agents-os.synthetic-m0-controller.v0.1
  controller_id:
  controller_revision: 1
  controller_kind: MANIFEST_OWNED_DETERMINISTIC_VERIFIER
  verifier_id:
  verifier_revision: 1
  supported_mutation_kinds:
    - AUTHENTICATOR_PROFILE_REVISION
    - PRINCIPAL_REVISION
    - GOVERNED_STATE_TRANSITION
  state_model: IMMUTABLE_ACCEPTED_MANIFEST
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.synthetic-m0-controller-spec.v0.1
```

`supported_mutation_kinds` uses the displayed semantic order. The controller is
not an Actor, Principal, credential, service, permission source, or independent
state stream. Its currentness is exactly the manifest activation assessment.

### 6.2 SyntheticM0PrincipalProvisioningManifestV0_1R8

R8 replaces R7 Section 6.5 with:

```yaml
SyntheticM0PrincipalProvisioningManifestV0_1R8:
  manifest_id:
  manifest_revision: 1
  workspace_fixture_id:
  controller_spec: SyntheticM0ControllerSpecV0_1
  controller_spec_fingerprint:
  synthetic_profile_creation_specs: []
  synthetic_principal_creation_specs: []
  permitted_binding_creation_specs: []
  deterministic_credential_handle_refs: []
  manifest_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  manifest_creation_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.synthetic-m0-principal-provisioning-manifest.v0.1-r8
```

The controller spec appears before Profile, Principal, Binding, and credential
spec arrays. Each creation spec has its own domain tag and fingerprint and
contains every proposed subject field except any manifest/acceptance/action ref,
created Event sequence, or final subject fingerprint. Arrays sort by stable
subject ID; duplicates reject.

`manifest_creation_action_ref` must be an immutable Jenn governance decision
that binds the exact manifest mutation intent. An accepted synthetic
test-provisioning action cannot create or accept its own controller manifest.
The manifest body exists before the Jenn decision; the final manifest contains
the later action ref. This follows Section 2.4 and has no cycle.

### 6.3 SyntheticM0ManifestActivationRevisionV0_1

```yaml
SyntheticM0ManifestActivationRevisionV0_1:
  activation_stream_id:
  activation_revision:
  expected_previous_activation_revision: positive_revision | null
  transition: ACCEPT | REVOKE
  manifest_ref:
  manifest_fingerprint:
  Jenn_decision_ref:
  Jenn_decision_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  effective_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.synthetic-m0-manifest-activation-revision.v0.1
```

Revision 1 must be `ACCEPT`; a later contiguous Jenn revision may `REVOKE`.
Revocation is terminal. The deterministic assessment is:

```yaml
SyntheticM0ManifestAssessmentV0_1:
  manifest_ref:
  activation_revision_ref:
  assessment: ACTIVE | REVOKED | INDETERMINATE
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Only `ACTIVE` supports synthetic subjects or controller currentness.

The activation `Jenn_decision_ref/fingerprint` must equal the decision named by
`lifecycle_action_ref.action_ref/action_fingerprint`; its action kind must be
`JENN_GOVERNANCE_DECISION`. The assessment fingerprint domain tag is:

```text
agents-os.synthetic-m0-manifest-assessment.v0.1
```

The assessment reducer is total: a unique contiguous current activation head
of `ACCEPT` produces `ACTIVE`; a unique later current `REVOKE` head produces
`REVOKED`; missing coverage, missing head, fork, CAS gap, decision mismatch, or
fingerprint conflict produces `INDETERMINATE`.

### 6.4 SyntheticManifestDerivedLifecycleRefV0_1

```yaml
SyntheticManifestDerivedLifecycleRefV0_1:
  manifest_ref:
  manifest_fingerprint:
  manifest_assessment_ref:
  manifest_assessment_fingerprint:
  controller_id:
  controller_spec_fingerprint:
  spec_kind: PROFILE | PRINCIPAL | BINDING
  spec_id:
  spec_fingerprint:
  derivation_replay_identity: CanonicalDigestScalarV0_1
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.synthetic-manifest-derived-lifecycle-ref.v0.1
```

Replay identity binds the manifest, active assessment, controller spec, and
exact creation spec. For synthetic `CREATE` only:

```text
Profile lifecycle_action_ref
Principal provisioning_source_ref
Principal transition_action_ref
Binding binding_issuance_source_ref
Binding activation stewardship source
```

are all replaced by the same exact derived lifecycle ref for their own spec.
No distinct synthetic action ref is invented. The created subject recomputes
its spec fingerprint and may contain only fields fixed by that spec plus this
derived ref and the Rust-assigned Event/fingerprint.

All subjects declared by an accepted manifest are materialized atomically as
deterministic results of the one manifest `ACCEPT` Event:

```text
mutation_body_fingerprint = exact subject creation-spec fingerprint
mutation_intent_ref/fingerprint = manifest activation intent ref/fingerprint
lifecycle_action_ref = exact subject SyntheticManifestDerivedLifecycleRefV0_1
mutation_replay_identity = derivation_replay_identity
created_at_event_sequence = manifest activation effective Event sequence
```

The activation intent body binds the manifest fingerprint, which binds every
ordered creation spec. Therefore one group intent authorizes exactly that
closed subject set. No per-subject Event, action, or intent is synthesized.
The transaction rejects if any derived subject already exists with different
bytes, if only part of the set can be materialized, or if a spec/body/fingerprint
does not reproduce exactly.

Profile assessment treats the embedded controller as current only while the
exact manifest assessment is `ACTIVE`. Manifest revocation makes every derived
synthetic Profile, Principal, Binding, and controller dependency safely
non-active at the same Event boundary.

The synthetic Profile's effective `lifecycle_controller_ref` is exactly:

```yaml
SyntheticM0ControllerRefV0_1:
  manifest_ref:
  manifest_fingerprint:
  manifest_assessment_ref:
  manifest_assessment_fingerprint:
  controller_id:
  controller_spec_fingerprint:
  profile_spec_id:
  profile_spec_fingerprint:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.synthetic-m0-controller-ref.v0.1
```

It is derived from the same manifest and Profile creation spec as the Profile's
`SyntheticManifestDerivedLifecycleRefV0_1`. A mismatched manifest, assessment,
controller, or Profile spec rejects Profile creation and assessment. This ref
replaces the ordinary R7 `LifecycleControllerRefV0_1` only for synthetic M0
Profiles created from the accepted manifest.

## 7. Exact ActorIdentityRevision schema and fingerprint

### 7.1 ActorIdentityTransitionAuthorityBasisV0_1R8

```yaml
ActorIdentityTransitionAuthorityBasisV0_1R8:
  authority_basis_id:
  basis_kind: JENN_ROOT_ACTION | JENN_GOVERNANCE_DECISION_BASIS | IDENTITY_STEWARD_ACTION | BOUND_ACTOR_SELF_SUSPEND_ACTION | ACCEPTED_INCIDENT_POLICY_ACTION | ACCEPTED_PROVISIONING_ACTION
  requested_by_actor_ref: optional
  requested_by_actor_identity_assessment_ref: optional
  requested_by_effective_binding_assessment_ref: optional
  Jenn_root_authority_ref: optional
  Jenn_root_authority_fingerprint: optional
  stewardship_relation_ref: optional
  stewardship_relation_fingerprint: optional
  incident_policy_ref: optional
  incident_policy_fingerprint: optional
  incident_controller_ref: optional
  provisioning_component_ref: optional
  provisioning_component_fingerprint: optional
  provisioning_basis_ref: optional
  provisioning_basis_fingerprint: optional
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.actor-identity-transition-authority-basis.v0.1-r8
```

Exact validity:

```text
JENN_ROOT_ACTION -> current ACTIVE Jenn identity and Binding; exact root relation
JENN_GOVERNANCE_DECISION_BASIS -> exact already-effective Jenn root authority; CREATE or recovery bootstrap only; later decision action binds intent; no runtime Binding claim
IDENTITY_STEWARD_ACTION -> current ACTIVE steward identity/Binding and exact R1/R2 target relation
BOUND_ACTOR_SELF_SUSPEND_ACTION -> exact target Actor current ACTIVE identity/Binding; SUSPEND only
ACCEPTED_INCIDENT_POLICY_ACTION -> exact accepted policy/controller; SUSPEND or COMPROMISE only
ACCEPTED_PROVISIONING_ACTION -> System Service/Execution Host CREATE/UPDATE/SUSPEND/COMPROMISE/RETIRE only under exact accepted provisioning basis
```

Actor-based kinds require `AUTHENTICATED_ACTOR_ACTION` and exact current Actor
identity/Binding inputs. `JENN_GOVERNANCE_DECISION_BASIS` requires
`JENN_GOVERNANCE_DECISION` and forbids Actor/Binding assessment fields.
Incident and provisioning kinds require the exact action kind fixed by their
accepted policy/component and forbid Actor/Binding assessment fields. Every
optional field not required by the selected kind is forbidden.

`authority_basis_ref` in the Actor mutation intent equals this immutable
`authority_basis_id`; its fingerprint equals the verified basis fingerprint.

R7 source/target transition matrix still applies. `RESUME`, `RECOVER`, and
ordinary `UPDATE` require Jenn or the exact identity steward; incident policy
cannot perform them.

### 7.2 ActorIdentityRevisionV0_1R8

R8 completely replaces the overlapping R1/R2/R7 Actor revision field lists
with this one effective schema:

```yaml
ActorIdentityRevisionV0_1R8:
  schema_version: agents-os.actor-identity-revision.v0.1-r8
  actor_id:
  actor_identity_revision:
  expected_previous_actor_identity_revision: positive_revision | null
  supersedes_actor_identity_revision: positive_revision | null

  actor_class: JENN_HUMAN_ROOT | RESIDENT_COORDINATOR | DOMAIN_AGENT | TEMPORARY_WORKER | SYSTEM_SERVICE | EXECUTION_HOST
  canonical_name:
  identity_charter_refs: []
  identity_steward_ref:
  parent_actor_ref: optional

  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | COMPROMISE | RECOVER | RETIRE
  source_status: ACTIVE | SUSPENDED | COMPROMISED | null
  status: ACTIVE | SUSPENDED | COMPROMISED | RETIRED
  validity_window: IdentityValidityWindowV0_1 | null
  assignment_binding_ref: optional

  transition_authority_basis: ActorIdentityTransitionAuthorityBasisV0_1R8
  transition_authority_basis_fingerprint:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  recovery_evidence_ref: optional
  change_reason_code:

  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Removed overlapping fields:

```text
R1 identity_provisioning_basis_ref -> represented by transition authority basis
R1 created_by_actor_ref -> represented by typed requested Actor in authority basis
R1 free-form change_reason -> replaced by low-disclosure change_reason_code
R2 stewardship_source and separate steward Actor/Binding/action fields
  -> represented by transition authority basis plus LifecycleActionRefR8
R7 target_status -> the one effective field is status
duplicate R7 identity_steward_ref -> the one R1-position field remains
```

No removed field appears in the fingerprint object, even as null.

### 7.3 Exact Actor fingerprint

The canonical fingerprint is:

```text
SHA-256(JCS([
  "agents-os.actor-identity-revision.v0.1-r8",
  {
    "schema_version": schema_version,
    "actor_id": actor_id,
    "actor_identity_revision": actor_identity_revision,
    "expected_previous_actor_identity_revision": expected_previous_actor_identity_revision_or_null,
    "supersedes_actor_identity_revision": supersedes_actor_identity_revision_or_null,
    "actor_class": actor_class,
    "canonical_name": canonical_name,
    "identity_charter_refs": canonical_identity_charter_refs,
    "identity_steward_ref": identity_steward_ref,
    "parent_actor_ref": parent_actor_ref_or_null,
    "transition_kind": transition_kind,
    "source_status": source_status_or_null,
    "status": status,
    "validity_window": canonical_validity_window_or_null,
    "assignment_binding_ref": assignment_binding_ref_or_null,
    "transition_authority_basis_fingerprint": transition_authority_basis_fingerprint,
    "mutation_body_fingerprint": mutation_body_fingerprint,
    "mutation_intent_fingerprint": mutation_intent_fingerprint,
    "lifecycle_action_ref_fingerprint": lifecycle_action_ref.canonical_fingerprint.digest_lowercase_hex,
    "mutation_replay_identity": mutation_replay_identity,
    "recovery_evidence_ref": recovery_evidence_ref_or_null,
    "change_reason_code": change_reason_code,
    "created_at_event_sequence": created_at_event_sequence
  }
]))
```

`identity_charter_refs` use the effective R1/R4 stable-ref order. Embedded
validity window uses its exact R7 schema object. Referenced authority and action
objects insert their verified digest string, not their full envelopes. Every
numeric value uses the R7 scalar profile.

The subject is accepted only when its body, intent, action, replay identity,
Event sequence, transition matrix, authority basis, CAS, and fingerprint all
match in one Rust transaction.

## 8. Required fixtures and regenerated materialization

### 8.1 Mandatory fixtures

Future authorized tests must include:

```text
same committed action reused with different target/transition/head/body -> reject
same intent with different action or Event -> replay conflict
governance/provisioning record missing exact intent/body/head/Event -> reject
every target/transition/basis allowed tuple -> accept only with exact current refs
every unlisted authority tuple or extra optional basis field -> reject
ancestor revoke/suspend/expire/supersede/challenge combinations -> exact precedence
ancestor resume while another ancestor remains suspended -> descendant suspended
two impact streams: clear one and challenge another -> aggregate challenged
any invalidated stream plus incomplete coverage -> aggregate invalidated
omitted impact stream or watermark gap -> aggregate indeterminate
manifest controller spec mismatch, extra controller, or independent controller head -> reject
manifest accepted then revoked -> all derived synthetic subjects non-active
synthetic Profile/Principal/Binding spec derivation byte identity across writers
every Actor transition and every removed-field reintroduction -> reject
Actor fingerprint byte identity across Rust and JavaScript
```

### 8.2 Materialization regeneration

The R7 materialization remains immutable historical author evidence but is not
implementation-safe. The author must create a new R8 materialization that:

```text
binds R1-R8 hashes
prints every effective R8 schema in full
prints every total reducer and authority table
marks removed R1/R2/R7 Actor fields explicitly
binds every effective rule to exact source subject/hash and section
does not claim closure beyond the fixed subjects
remains non-authoritative and outside the acceptance subject set
```

## 9. Finding disposition

| Finding | R8 disposition |
|---|---|
| `F2-R7-IR-B01` | resolved by Section 2 exact mutation-intent/action/replay binding |
| `F2-R7-IR-B02` | resolved by Section 3 typed basis unions and total predicate |
| `F2-R7-IR-B03` | resolved by Section 4 total ancestor mapping and precedence |
| `F2-R7-IR-B04` | resolved by Section 5 complete ledger-derived impact input and aggregation |
| `F2-R7-IR-B05` | resolved by Section 6 manifest-owned controller and acyclic derivation |
| `F2-R7-IR-B06` | resolved by Section 7 complete schema, removals, tag, and formula |
| `F2-R7-IR-M01` | resolved only by the regenerated Section 8.2 materialization |

## 10. Atomic acceptance and non-authorization

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R8_ATOMIC_BUNDLE
subjects:
  - F2_R1_subject_sha256_639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b
  - F2_R2_amendment_sha256_8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd
  - F2_R3_amendment_sha256_d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db
  - F2_R4_amendment_sha256_a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59
  - F2_R5_amendment_sha256_cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be
  - F2_R6_amendment_sha256_bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932
  - F2_R7_amendment_sha256_343881f2292fbb3c09b0cc572b0d9a9c8f77eef1e4b5957134de31796228187c
  - this_exact_R8_amendment_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
regenerated_effective_materialization_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R8 creates no runtime object, database, service, Profile, Principal, credential,
Binding, Assignment, Delegation, transition, manifest, provider call, permit, or
effect. It does not converge the canonical Prohibited Behavior List, accept F2,
start F3, or authorize implementation or runtime activation.
