# AGENTS OS F2 Actor Identity and Delegation v0.1 R21 Verified Core Constructibility Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R21_ATOMIC_BUNDLE
version: v0.1-r21
date: 2026-07-16
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
scope_locked: true
blockers_closed:
  - M0_ACTOR_ELIGIBILITY_EMPTY_INTERSECTION
  - SYNTHETIC_BINDING_ACTIVATION_REPLAY_UNDEFINED
  - COMPROMISE_TARGET_ACTION_TYPE_EXCLUSION
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and precedence

R21 is permitted by `F2_FREEZE_RULE_V0_1` only because the fresh R1-R20 full
atomic review produced exact `M0_IMPOSSIBILITY`, `INTERNAL_CONTRADICTION`, and
`REVOCATION_COMPROMISE_BYPASS` witnesses.

R21 replaces only:

```text
1. the R2/R16 Actor CREATE class matrix for the exact R13-R14 synthetic M0
   bootstrap branch whose otherwise-required class/basis intersection was empty;

2. the R4/R5 BindingActivationEvidence.replay_identity derivation for the
   R8/R15 SYNTHETIC_M0_FIXTURE stewardship-source shape;

3. the R20 complete_target_action_refs element type, canonical order, and
   complete_target_set_fingerprint formula so every exact R15/R17/R18
   assurance action remains challengeable and invalidatable.
```

R21 does not replace any ordinary Actor CREATE route, post-create authority,
Actor class, Principal or Binding rule, responsibility source, Delegation
rule, permit, Prohibited Boundary rule, F3 message, F4 effect protocol,
production authenticator, cryptographic profile, storage schema, Rust layout,
or performance requirement. Every R1-R20 rule not expressly replaced below
remains effective. The narrower R21 rule governs any broader or conflicting
older sentence.

R1-R21 form one indivisible proposed acceptance unit. Partial acceptance is
forbidden. The derived R21-v16 materialization is excluded from that unit and
creates no authority.

## 2. Non-empty synthetic M0 Actor eligibility intersection

### 2.1 Exact synthetic bootstrap CREATE branch

R21 preserves the R13-R14 eligibility predicate and restores the one CREATE
branch that predicate already requires. In addition to the ordinary R16
class-specific routes, an Actor revision-1 `CREATE` is admitted by the exact
synthetic M0 bootstrap branch only when every predicate below is true:

```text
actor_class = DOMAIN_AGENT
identity_steward_ref names exact Jenn

actor_identity_revision = 1
expected_previous_actor_identity_revision = null
supersedes_actor_identity_revision = null
source_status = null
status = ACTIVE
no current or historical Actor head exists for actor_id

transition_authority_basis is ActorGeneralTransitionAuthorityBasisV0_1R16
basis_kind = JENN_GOVERNANCE_DECISION_BASIS
Jenn_root_authority_ref/fingerprint are both present and exact
the referenced JennRootGovernanceAuthorityRefV0_1R8 has:
  environment = SYNTHETIC_TEST
  permitted_basis_uses containing IDENTITY_BOOTSTRAP

requested Actor/Binding fields, stewardship fields, incident fields, and
provisioning fields in the general basis are JSON null and semantically forbidden

the mutation body, intent, Jenn governance decision, LifecycleActionRef,
replay identity, Event, Actor revision, and all fingerprints verify under the
existing R8 order with no substituted authenticated Actor or provisioning action
```

This is the sole exception to the R2/R16 class-exclusive ordinary CREATE
matrix. It uses the already-defined R16 general basis and the already-defined
R8 Jenn governance decision path; it adds no basis kind, authority object,
Actor class, action kind, or writer.

The branch is forbidden for every class other than `DOMAIN_AGENT`, every
post-create transition, every Actor revision greater than 1, every non-
`SYNTHETIC_TEST` root authority, and every root authority that does not permit
`IDENTITY_BOOTSTRAP`. Missing, stale, forked, mismatched, or indeterminate
authority evidence rejects. R13-R14 may retain their wider eligibility class
allowlist, but only the exact `DOMAIN_AGENT` intersection restored here is
constructible through this exception.

### 2.2 Eligibility binding and constructive witness

For `SyntheticM0ActorEligibilityAssessmentV0_1R13`, the exact
`root_create_authority_basis_ref/fingerprint` names the Section 2.1 general
basis, and `root_Jenn_governance_authority_ref/fingerprint` equals its exact
Jenn-root authority pair. R14's closed positive inputs and class allowlist are
otherwise unchanged.

One constructive class/basis intersection therefore exists:

```text
DOMAIN_AGENT revision-1 CREATE
-> exact Section 2.1 JENN_GOVERNANCE_DECISION_BASIS
-> exact SYNTHETIC_TEST Jenn root authority permitting IDENTITY_BOOTSTRAP
-> current Actor assessment ACTIVE at manifest ACCEPT
-> SyntheticM0ActorEligibilityAssessment = ELIGIBLE
-> same Actor may be the exact pre-existing Actor in one synthetic Binding spec
```

The Actor exists before the manifest. The eligibility assessment is derived
only at manifest `ACCEPT` and has no writer-owned head. Neither object depends
on the later synthetic Binding, Profile, Principal, activation evidence, or
final subject fingerprints. This branch therefore restores constructibility
without a proof cycle.

The Actor identity alone grants no permission or responsibility. Operational
use still requires an exact current Principal Binding, responsibility source,
F3 attribution, Prohibited Boundary result, TaskPermit, and F4 admission under
their owning contracts.

## 3. Synthetic Binding activation replay derivation

### 3.1 Ordinary branches remain byte-identical

For `JENN_ROOT_BOOTSTRAP_DECISION` and `AUTHENTICATED_STEWARD_ACTION`, the R4
`binding_activation_evidence_replay_identity` formula and domain remain
byte-identical. Their `stewardship_source` is the R2 inline object with exact
`kind` and `source_ref` fields. R21 does not change existing ordinary replay
identities.

### 3.2 Synthetic branch exact source projection

For `activation_mode = SYNTHETIC_M0_FIXTURE` only, `stewardship_source` is the
complete exact `SyntheticManifestDerivedLifecycleRefV0_1` required by R8 and
R15. It has `spec_kind = BINDING` and names the exact Binding creation spec.
It is not treated as the R2 inline object and is never read through nonexistent
`.kind` or `.source_ref` fields.

The canonical source projection is this displayed array:

```text
[
  "SYNTHETIC_MANIFEST_DERIVED_LIFECYCLE_REF",
  stewardship_source.manifest_ref,
  stewardship_source.manifest_fingerprint.digest_lowercase_hex,
  stewardship_source.manifest_assessment_ref,
  stewardship_source.manifest_assessment_fingerprint.digest_lowercase_hex,
  stewardship_source.controller_id,
  stewardship_source.controller_spec_fingerprint.digest_lowercase_hex,
  "BINDING",
  stewardship_source.spec_id,
  stewardship_source.spec_fingerprint.digest_lowercase_hex,
  stewardship_source.derivation_replay_identity,
  stewardship_source.canonical_fingerprint.digest_lowercase_hex
]
```

Every fingerprint and digest is verified before projection. The manifest
assessment is exact and `ACTIVE`; controller and Binding spec membership are
exact; unresolved, cross-manifest, wrong-kind, mismatched, or extra source
values reject.

### 3.3 Synthetic replay formula

R21 replaces the R4/R5 replay derivation only for the synthetic branch with:

```text
binding_activation_evidence_replay_identity = SHA-256(JCS([
  "agents-os.binding-activation-evidence-replay.synthetic-m0.v0.1-r21",
  evidence_id,
  target_binding_ref,
  binding_subject_fingerprint.digest_lowercase_hex,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  "SYNTHETIC_TEST_PRINCIPAL",
  "SYNTHETIC_TEST",
  authenticator_profile_ref,
  verifier_revision,
  principal_control_proof_assessment_ref_fingerprint.digest_lowercase_hex,
  "SYNTHETIC_M0_FIXTURE",
  canonical_synthetic_stewardship_source_projection,
  null,
  null,
  null,
  null,
  not_before_utc_ms,
  expires_at_utc_ms
]))
```

The result is `CanonicalDigestScalarV0_1`. The four null positions are the
schema-known steward Actor, steward identity revision, steward Binding, and
steward action fingerprint positions. They are present as JSON null. Evidence
revision, status, Event, replay result, and evidence final fingerprint remain
excluded exactly as in R4.

R15's complete-known-object fingerprint using domain
`agents-os.binding-activation-evidence.v0.1-r15` remains authoritative for the
outer evidence. It includes the exact selected union value and the R21 replay
identity. R21 creates neither a second evidence schema nor a second writer.

## 4. Complete compromise target action universe

### 4.1 Typed member projection

R21 replaces the R20 statement that every complete target element is a
`LifecycleActionRefV0_1R8`. Every element instead uses:

```yaml
CompleteCompromiseTargetActionMemberV0_1R21:
  action_role: ActionAssuranceRoleV0_1R17
  action_ref:
  action_fingerprint: R4FingerprintEnvelope
```

`action_role`, `action_ref`, and `action_fingerprint` are derived from the
exact R15/R17/R18 action-assurance indexes; they are not caller labels.
The owning action class determines the exact ref type and verification rule:

```text
R8 lifecycle actions
  -> exact LifecycleActionRefV0_1R8 action and fingerprint

Binding or Delegation issuance using an authenticated Actor action
  -> exact AuthenticatedActorActionRefR4Effective action_ref_id and
     canonical_action_ref_fingerprint

ordinary Binding activation
  -> the exact R18 bootstrap governance decision or authenticated steward
     action projection

Delegation activation
  -> the exact immutable F3 command_envelope_ref/fingerprint selected by R18

synthetic Binding activation
  -> no invented BINDING_ACTIVATION member; the exact manifest create/accept
     assurances remain the transitive target actions
```

Every other R15 action class follows its exact R17 action-to-role row and
owning immutable ref. Role/ref mismatch, unavailable canonical fingerprint,
substituted evidence or acknowledgement ref, unknown action class, action
targeting another CompromiseImpact action, or a non-F2 action rejects. Missing
or conflicting index coverage is `INDETERMINATE` and cannot support new use.

### 4.2 Canonical order and formula

Members sort by R17 `ActionAssuranceRoleV0_1R17` enum ordinal, then normalized
action_ref UTF-8 bytes, then verified lowercase fingerprint ASCII bytes.
Duplicate action_ref values, duplicate member tuples, or one ref carrying two
roles or fingerprints reject.

R21 replaces the R20 target-set formula with:

```text
complete_target_set_fingerprint = SHA-256(JCS([
  "agents-os.compromise-complete-target-action-set.v0.1-r21",
  compromised_actor_or_principal_ref,
  selection_basis_event_sequence,
  [[action_role, action_ref, action_fingerprint.digest_lowercase_hex],
   ... canonical R17 role/action-ref order]
]))
```

The result remains `CanonicalDigestScalarV0_1`. The set is exactly the closed
target action set selected at the named watermark. It includes every eligible
R15 action regardless of which exact immutable action-ref interface owns that
action. Missing, extra, omitted, unverified, duplicated, or differently
ordered members reject before the outer CompromiseImpact body is accepted.

`HistoricalActionAssuranceReducer` continues to consume the resulting exact
impact streams. `CHALLENGE` and `INVALIDATE` therefore reach issuance and
activation assurance actions instead of silently excluding them by ref type.

## 5. Downstream boundary

R21 requires F3 only to supply the already-required immutable, authenticated,
hash-addressed command/action reference and fingerprint properties used by the
R18 projection. It does not define the final CommandEnvelope fields, nonce
database, replay index implementation, transaction schema, or handshake wire
format.

R21 adds no F4 field. F4 still admits effects only against exact current
identity, responsibility, permit, host, and fence evidence. Missing, stale,
conflicting, challenged, invalidated, or indeterminate F2 evidence cannot be
converted into effect admission.

## 6. Corrected complete materialization requirements

The next complete materialization must:

```text
apply Sections 2-4 without broadening any ordinary authority route
print the synthetic Actor bootstrap exception beside the ordinary class matrix
print both ordinary and synthetic Binding activation replay branches
replace the R20 LifecycleActionRef-only compromise member and formula
add CompleteCompromiseTargetActionMemberV0_1R21 to the exact schema index
add Actor SUPERSEDED branches to Binding and Assignment currentness
add Delegation activation NOT_ACTIVATED -> NOT_YET_ACTIVE
leave proven pre-start authentication non-AUTHENTICATED without inventing an
  exact REJECTED-versus-INDETERMINATE rule beyond the owning predicates
print the complete R1/R7 fail-closed startup and recovery boundary
update exact hashes, domains, source refs, formula catalogue, and counts
create no new semantic field, writer, authority, or downstream protocol
```

The materialization remains a non-authoritative resolved reading surface. It
may not repair R1-R21 by interpretation.

## 7. Review gate and non-authorization

The corrected R1-R21 unit and its complete materialization require a targeted
consistency review followed by a fresh full atomic review under
`F2_FREEZE_RULE_V0_1`. `PASS_NO_BLOCKER` makes the unit eligible only for
Jenn's atomic freeze decision.

R21 does not accept, freeze, implement, activate, commit, push, deploy, or
start F3. It authorizes no runtime, provider, credential, production
authentication, database, service, host effect, or external write.
