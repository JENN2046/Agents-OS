# AGENTS OS F2 Actor Identity and Delegation v0.1 R10 Binding Issuance Snapshot and Materialization Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R10_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r10
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

R10 closes only `F2-R9-IR-B01`, `F2-R9-IR-M01`, and `F2-R9-IR-M02`.
Fixed R1-R9 hashes remain unchanged. R10 has exact precedence over:

```text
R9 Sections 3.1-3.4 Binding issuance inputs, body, and synthetic derivation
R9 Section 5.1 TransitionAuthorityBasis additions for Binding issuance
R9 Section 6 materialization requirement
R8 Section 6.2 sentence requiring every creation spec to use its own domain tag
  -> only for permitted_binding_creation_specs
  -> Profile and Principal creation-spec domains remain unchanged
```

All other R1-R9 rules remain effective. R1-R10 form one indivisible proposed
acceptance unit. The derived R10 materialization is excluded from acceptance.

## 2. Binding issuance and activation are separate

Binding subject issuance proves that one exact Actor revision, Principal
revision, Authenticator Profile revision, scope, time window, and authority
basis were selected at one ledger watermark. It does not prove that the
Principal currently controls credentials.

```text
Binding subject committed
  -> PENDING_ACTIVATION semantic condition
  -> cannot represent the Actor or authenticate a Command

later PrincipalControlProofAssessment
  + BindingActivationEvidence
  + BindingActivationAssessment
  + ActorPrincipalBindingAssessment
  -> may make the Binding effective for new Commands
```

`PrincipalControlProofAssessment` is required only in that later activation
graph. It is forbidden in the Binding issuance snapshot, mutation body,
authority basis, and creation spec. This preserves the subject-before-evidence
DAG and removes any requirement for a future proof to exist before its Binding.

## 3. Exact issuance snapshot

### 3.1 Schema

R10 adds this immutable object to every Binding revision:

```yaml
BindingIssuanceInputSnapshotV0_1R10:
  snapshot_id:
  actor_identity_ref:
  actor_identity_fingerprint:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  principal_ref:
  principal_fingerprint:
  principal_assessment_ref:
  principal_assessment_fingerprint:
  authenticator_profile_ref:
  authenticator_profile_fingerprint:
  authenticator_profile_assessment_ref:
  authenticator_profile_assessment_fingerprint:
  binding_scope_fingerprint:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  assessed_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.binding-issuance-input-snapshot.v0.1-r10
```

The fingerprint uses the R4 default exact-known-object formula. All references
are exact immutable refs. `assessed_at_event_sequence` equals the mutation
intent `expected_ledger_head_event_sequence` and the authority-basis
`based_on_event_sequence`.

### 3.2 Non-synthetic predicates

For every non-synthetic mode:

```text
Actor assessment = ACTIVE
Principal assessment = ACTIVE
Profile assessment = ACTIVE
all three assessments use the exact snapshot watermark
snapshot semantic refs equal the Binding subject Actor/Principal/Profile refs
snapshot scope fingerprint equals the Binding scope fingerprint
snapshot time window equals the Binding subject time window
authority basis required target/current refs equal the same snapshot refs
PrincipalControlProofAssessment absent
```

Mode-specific authority remains the R9 table. Its corrected required facts are:

| Mode | Exact allowed basis | Additional required current facts |
|---|---|---|
| `JENN_INTERACTIVE_AUTHENTICATION` | `JENN_ROOT_ACTION`; bootstrap may use `JENN_GOVERNANCE_DECISION_BASIS` | exact snapshot Actor, Principal, Profile, scope, window, Jenn basis |
| `RESIDENT_ATTESTED_AGENT_SESSION` | `IDENTITY_STEWARD_ACTION` | exact snapshot plus current steward identity and effective steward Binding |
| `SERVICE_PROVISIONING_ATTESTATION` | `ACCEPTED_PROVISIONING_ACTION` | exact snapshot plus accepted component and provisioning basis |
| `WORKER_ASSIGNMENT_HANDSHAKE` | `DIRECT_DELEGATOR_ACTION` | exact snapshot plus current responsible Actor, effective Binding, and responsibility assessment |
| `SYNTHETIC_M0_FIXTURE` | manifest-derived group intent only | Section 3.3 synthetic rules; no pre-existing assessments |

Every unlisted mode/basis tuple or additional current field rejects.

### 3.3 Synthetic snapshot

Synthetic subjects are created atomically at manifest `ACCEPT`, so they cannot
reference assessments of subjects that do not yet exist. Their snapshot uses:

```yaml
SyntheticBindingIssuanceInputSnapshotV0_1R10:
  snapshot_id:
  manifest_ref:
  manifest_fingerprint:
  manifest_activation_ref:
  manifest_activation_fingerprint:
  controller_spec_ref:
  controller_spec_fingerprint:
  actor_creation_spec_ref:
  actor_creation_spec_fingerprint:
  principal_creation_spec_ref:
  principal_creation_spec_fingerprint:
  authenticator_profile_creation_spec_ref:
  authenticator_profile_creation_spec_fingerprint:
  binding_creation_spec_ref:
  binding_creation_spec_fingerprint:
  binding_scope_fingerprint:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  effective_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag is
`agents-os.synthetic-binding-issuance-input-snapshot.v0.1-r10`. Every spec is
an exact member of the accepted manifest; the activation is `ACTIVE`; all
derived subjects commit at `effective_at_event_sequence`; and all subject
fields equal their creation specs. No current assessment or control proof is
allowed in this synthetic snapshot.

## 4. Complete Binding revision replacement

R10 replaces R9 Section 3.2 only by adding:

```yaml
ActorPrincipalBindingRevisionR10Additions:
  issuance_input_snapshot: BindingIssuanceInputSnapshotV0_1R10 | SyntheticBindingIssuanceInputSnapshotV0_1R10
  issuance_input_snapshot_fingerprint:
```

These fields appear immediately before `authority_basis`. They are included in
the `BINDING_REVISION` mutation body and final Binding fingerprint. The body
still excludes only the R9 derived action, intent, replay, Event, and final
fingerprint fields. A missing, wrong-kind, stale, mismatched, proof-bearing, or
extra-field snapshot rejects.

`TransitionAuthorityBasisV0_1R9` remains the schema name and fingerprint domain.
For Binding issuance, its existing exact actor, binding, responsibility,
Profile, controller, component, provisioning, scope, and relation fields must
equal the required R10 snapshot and mode row. R10 adds no proof field and no
second authority-basis domain.

## 5. Binding creation-spec canonicalization

R10 explicitly replaces the conflicting R8 Section 6.2 rule only for
`permitted_binding_creation_specs`:

```text
Binding creation spec
  -> uses the BINDING_REVISION mutation-body known-object shape
  -> includes the SyntheticBindingIssuanceInputSnapshot creation values
  -> creation-spec fingerprint equals the created Binding mutation_body_fingerprint
  -> has no second creation-spec domain digest

Profile and Principal creation specs
  -> retain their R8 own-domain tags and fingerprints
```

The manifest contains the exact Binding body fingerprint before activation.
At atomic materialization the derived activation/action fields are added only
to the final subject; the precommitted body and spec fingerprint remain
byte-identical.

## 6. Required complete materialization

The R10 derived materialization must print, rather than cross-reference:

```text
all complete effective lifecycle subject schemas
all exact Actor/Profile/Principal/Binding/transition/impact authority tables
required current facts and forbidden field combinations
source/target/additional transition predicates
the full Binding effective-current reducer
the full Delegation descendant reducer
the full historical-impact reducer
the synthetic graph and exact action order
source subject/hash/section for every block
```

It remains non-authoritative and excluded from acceptance.

## 7. Required future fixtures

```text
Binding issuance snapshot omits one exact assessment -> reject
Binding issuance snapshot watermark differs from intent by one Event -> reject
non-synthetic issuance snapshot contains control proof -> reject
synthetic snapshot contains current assessment -> reject
Binding subject used before activation/effective assessment -> reject
Binding spec uses R8 own-domain digest -> reject
Profile or Principal spec incorrectly uses Binding body domain -> reject
snapshot/authority semantic ref mismatch -> reject
valid later proof and activation graph -> Binding may become effective
```

## 8. Finding disposition and non-authorization

| Finding | R10 disposition |
|---|---|
| `F2-R9-IR-B01` | resolved by Sections 2-4: exact issuance snapshot; proof remains later activation-only |
| `F2-R9-IR-M01` | resolved by Sections 1 and 5 explicit R8 Section 6.2 override |
| `F2-R9-IR-M02` | resolved only by the regenerated complete R10 materialization |

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R10_ATOMIC_BUNDLE
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R10 creates no runtime object, database, service, credential, Binding, proof,
provider call, permit, or effect. It does not accept F2, start F3, converge the
canonical Prohibited List, or authorize implementation or runtime activation.
