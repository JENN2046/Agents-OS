# AGENTS OS F2 Actor Identity and Delegation v0.1 R20 Final Freeze Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R20_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r20
date: 2026-07-16
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
scope_locked: true
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope, precedence, and final-closure boundary

R20 closes only these four unresolved F2 subject issues:

```text
synthetic Profile and Principal creation specs were not reproducible
three authoritative CanonicalDigestScalar values lacked owning formulas
IDENTITY_STEWARD_ACTION retained an untyped target relation
nullable Binding and Assignment expiry lacked total comparison semantics
```

R20 has exact precedence only over:

```text
R8 Section 6.2 and R10 Section 5 for synthetic Profile and Principal
  creation-spec schemas, domains, fingerprints, and final-subject projection
R8 Section 6.4 for derivation_replay_identity
R7 Section 9.2 and R8 Section 5.1 for complete_target_set_fingerprint
R2 Section 7.2 for complete_affected_binding_set_fingerprint
R8 Sections 2.1, 3.1, and 5.1 for IDENTITY_STEWARD_ACTION target typing
R7 Section 2.3, R9 Section 3.2, and R15 Section 3.2 for nullable expiry
```

All other R1-R19 semantics remain effective. R1-R20 form one indivisible
proposed acceptance unit. Partial acceptance is forbidden.

This amendment adds no Actor class, Principal class, Binding mode,
responsibility kind, delegation edge, authority basis kind, transition,
permission, F3 wire field, F4 effect protocol, production authentication
profile, persistence design, runtime component, or implementation authority.

## 2. F2 closure and downstream boundary

The final F2 review uses this stopping rule:

```yaml
F2_FREEZE_RULE_V0_1:
  freeze_when:
    - no identity spoofing path
    - no responsibility expansion path
    - delegation always attenuates
    - revocation and compromise fail closed
    - currentness reducers are total
    - one canonical writer per fact class
    - F3 and F4 dependency properties are explicit
    - atomic subject set is internally consistent
    - independent review has no BLOCKING_F2 finding
  do_not_wait_for:
    - production authentication
    - final cryptographic profile
    - database schema
    - Rust implementation
    - final F3 wire format
    - F4 host protocol
    - performance evidence
  reopen_only_on:
    - safety contradiction
    - authority contradiction
    - implementation impossibility
    - verified cross-writer divergence
```

An independent review may classify a finding as BLOCKING_F2 only when it has
normative F2 evidence, an exact reachable counterexample or impossible M0
witness, unresolved precedence, and one of these effects:

```text
IDENTITY_SPOOFING
AUTHORITY_EXPANSION
REVOCATION_COMPROMISE_BYPASS
FAIL_OPEN
DUAL_WRITER
CIRCULAR_PROOF
M0_IMPOSSIBILITY
INTERNAL_CONTRADICTION
```

Every other open issue is classified as DOWNSTREAM_F3_OR_F4 or
IMPLEMENTATION_PROFILE. A materialization-only error may prevent that
materialization from being the accepted effective view, but it cannot create a
new acceptance-subject amendment unless the authoritative subjects themselves
meet the BLOCKING_F2 test.

F2 requires F3 to provide an immutable authenticated action ref that binds the
exact Actor, Principal, Binding, responsibility source, action payload, and
committed intake Event required by the F2 interface. F2 does not freeze the
final CommandEnvelope fields, nonce storage, replay index, or transaction
layout.

F2 requires F4 to admit an effect only against exact current identity,
responsibility, permit, host, and fence evidence supplied by the owning
contracts. F2 does not freeze key algorithms, host transport, module layout, or
effect implementation.

## 3. Deterministic synthetic M0 Profile and Principal creation specs

### 3.1 Profile creation spec

R20 replaces the anonymous element type of
synthetic_profile_creation_specs with:

```yaml
SyntheticM0AuthenticatorProfileCreationSpecV0_1R20:
  profile_id:
  profile_revision: 1
  expected_previous_profile_revision: null
  supersedes_profile_revision: null
  transition_kind: CREATE
  source_status: null
  status: ACTIVE
  proof_kind: SYNTHETIC_FIXTURE
  supported_principal_classes:
    - SYNTHETIC_TEST_PRINCIPAL
  supported_environments:
    - SYNTHETIC_TEST
  verifier_id:
  verifier_revision: 1
  trust_anchor_refs: []
  assertion_max_age_ms: duration_milliseconds
  clock_policy_ref:
  replay_policy_ref:
  canonical_fingerprint: R4FingerprintEnvelope
```

The domain tag is:

```text
agents-os.synthetic-m0-authenticator-profile-creation-spec.v0.1-r20
```

The fingerprint is:

```text
synthetic_profile_creation_spec_fingerprint = SHA-256(JCS([
  "agents-os.synthetic-m0-authenticator-profile-creation-spec.v0.1-r20",
  {
    "profile_id": profile_id,
    "profile_revision": 1,
    "expected_previous_profile_revision": null,
    "supersedes_profile_revision": null,
    "transition_kind": "CREATE",
    "source_status": null,
    "status": "ACTIVE",
    "proof_kind": "SYNTHETIC_FIXTURE",
    "supported_principal_classes": ["SYNTHETIC_TEST_PRINCIPAL"],
    "supported_environments": ["SYNTHETIC_TEST"],
    "verifier_id": verifier_id,
    "verifier_revision": 1,
    "trust_anchor_refs": canonical_trust_anchor_refs,
    "assertion_max_age_ms": assertion_max_age_ms,
    "clock_policy_ref": clock_policy_ref,
    "replay_policy_ref": replay_policy_ref
  }
]))
```

The two singleton arrays use exactly the displayed semantic order.
trust_anchor_refs sort by exact normalized stable ref and reject duplicates.
The spec array sorts by profile_id normalized UTF-8 bytes and rejects duplicate
profile_id values.

verifier_id and verifier_revision equal the enclosing
SyntheticM0ControllerSpecV0_1 values byte-for-byte.

The creation spec intentionally excludes lifecycle_controller_ref and
credential_status_provider_ref and profile_steward_ref because all three are
exact manifest-derived refs, and excludes all mutation body, intent, action,
replay, Event, and final-subject fingerprint fields. No excluded value is
caller chosen.

At atomic ACCEPT, the final Profile is derived as follows:

```text
every field present in the creation spec = byte-identical spec value
lifecycle_controller_ref = exact same-manifest SyntheticM0ControllerRefV0_1
credential_status_provider_ref = exact stable ref of that same controller
profile_steward_ref = exact same-manifest SYNTHETIC_M0_STEWARD ref
mutation_body_fingerprint = exact creation-spec fingerprint
mutation_intent_ref/fingerprint = exact manifest activation intent
lifecycle_action_ref = exact same-spec SyntheticManifestDerivedLifecycleRefV0_1
mutation_replay_identity = that derived ref derivation_replay_identity
created_at_event_sequence = manifest ACCEPT Event
canonical_fingerprint = effective Profile subject formula
```

Any extra spec field, non-fixed enum, external controller/steward ref, missing
same-manifest derivation, or field mismatch rejects the whole atomic
materialization.

### 3.2 Principal creation spec

R20 replaces the anonymous element type of
synthetic_principal_creation_specs with:

```yaml
SyntheticM0PrincipalCreationSpecV0_1R20:
  principal_id:
  principal_revision: 1
  expected_previous_principal_revision: null
  supersedes_principal_revision: null
  transition_kind: CREATE
  source_status: null
  principal_class: SYNTHETIC_TEST_PRINCIPAL
  environment: SYNTHETIC_TEST
  authenticator_profile_creation_spec_ref:
  authenticator_profile_creation_spec_fingerprint:
  credential_handle_refs: []
  status: ACTIVE
  canonical_fingerprint: R4FingerprintEnvelope
```

The domain tag is:

```text
agents-os.synthetic-m0-principal-creation-spec.v0.1-r20
```

The fingerprint is:

```text
synthetic_principal_creation_spec_fingerprint = SHA-256(JCS([
  "agents-os.synthetic-m0-principal-creation-spec.v0.1-r20",
  {
    "principal_id": principal_id,
    "principal_revision": 1,
    "expected_previous_principal_revision": null,
    "supersedes_principal_revision": null,
    "transition_kind": "CREATE",
    "source_status": null,
    "principal_class": "SYNTHETIC_TEST_PRINCIPAL",
    "environment": "SYNTHETIC_TEST",
    "authenticator_profile_creation_spec_ref": authenticator_profile_creation_spec_ref,
    "authenticator_profile_creation_spec_fingerprint": authenticator_profile_creation_spec_fingerprint,
    "credential_handle_refs": canonical_credential_handle_refs,
    "status": "ACTIVE"
  }
]))
```

authenticator_profile_creation_spec_ref and fingerprint name one exact
same-manifest SyntheticM0AuthenticatorProfileCreationSpecV0_1R20. They cannot
name an external Profile. credential_handle_refs are exact opaque non-secret
refs, sort by normalized UTF-8 bytes, reject duplicates, and have exact set
equality with the handles used by this Principal from
deterministic_credential_handle_refs.

The spec array sorts by principal_id normalized UTF-8 bytes and rejects
duplicate principal_id values.

The creation spec intentionally excludes authenticator_profile_ref,
provisioning_source_ref, lifecycle_controller_ref, and lifecycle_action_ref
because they are exact same-manifest derived refs, and excludes all mutation
body, intent, replay, Event, and final-subject fingerprint fields. No excluded
value is caller chosen.

At atomic ACCEPT, the final Principal is derived as follows:

```text
every field present in the creation spec = byte-identical spec value
authenticator_profile_ref = exact revision-1 Profile materialized from the
  named same-manifest Profile creation spec
provisioning_source_ref = exact same-spec SyntheticManifestDerivedLifecycleRef
lifecycle_controller_ref = exact controller ref of that materialized Profile
mutation_body_fingerprint = exact creation-spec fingerprint
mutation_intent_ref/fingerprint = exact manifest activation intent
lifecycle_action_ref = exact same-spec SyntheticManifestDerivedLifecycleRef
mutation_replay_identity = that derived ref derivation_replay_identity
created_at_event_sequence = manifest ACCEPT Event
canonical_fingerprint = effective Principal subject formula
```

The final Principal and referenced Profile must be created in the same atomic
manifest ACCEPT. An absent, external, duplicated, mismatched, partially
materialized, or differently ordered spec rejects.

### 3.3 Manifest array and subject-set closure

The effective manifest fields are typed as:

```yaml
synthetic_profile_creation_specs:
  - SyntheticM0AuthenticatorProfileCreationSpecV0_1R20
synthetic_principal_creation_specs:
  - SyntheticM0PrincipalCreationSpecV0_1R20
```

Both arrays are non-empty. Every Principal names exactly one Profile in the
Profile spec array. Every permitted synthetic Binding names exactly one
Principal and Profile in these arrays and the exact pre-existing eligible
Actor required by R12-R14. The manifest body includes the complete spec
objects, including their canonical fingerprints, in the R7 M0 creation-spec
order. No anonymous creation-spec shape remains effective.

## 4. Owning formulas for the three local canonical digests

All three values below are CanonicalDigestScalarV0_1 values. They persist the
raw SHA-256 result as exactly 64 lowercase hexadecimal ASCII characters.

### 4.1 Synthetic derivation replay identity

R20 defines:

```text
derivation_replay_identity = SHA-256(JCS([
  "agents-os.synthetic-manifest-derived-lifecycle-replay.v0.1-r20",
  manifest_ref,
  manifest_fingerprint.digest_lowercase_hex,
  manifest_assessment_ref,
  manifest_assessment_fingerprint.digest_lowercase_hex,
  controller_id,
  controller_spec_fingerprint.digest_lowercase_hex,
  spec_kind,
  spec_id,
  spec_fingerprint.digest_lowercase_hex
]))
```

The tuple fields are the corresponding fields of
SyntheticManifestDerivedLifecycleRefV0_1 in displayed order. The digest,
derived-ref final fingerprint, final subject fingerprint, and manifest ACCEPT
Event are excluded. One exact manifest assessment, controller spec, and
creation spec therefore produce one replay identity without a self-edge.
Every fingerprint input contributes its verified digest_lowercase_hex string,
not a FingerprintEnvelope object.

### 4.2 Compromise complete target set

Each complete_target_action_refs element is an exact verified
LifecycleActionRefV0_1R8. The canonical element projection is:

```text
[action_ref, action_fingerprint.digest_lowercase_hex]
```

Elements sort by action_ref normalized UTF-8 bytes and then
action_fingerprint lowercase ASCII bytes. Duplicate action_ref values reject.

R20 defines:

```text
complete_target_set_fingerprint = SHA-256(JCS([
  "agents-os.compromise-complete-target-action-set.v0.1-r20",
  compromised_actor_or_principal_ref,
  selection_basis_event_sequence,
  [[action_ref, action_fingerprint.digest_lowercase_hex],
   ... canonical action-ref order]
]))
```

The set is exactly the complete closed action set selected at the named Event
watermark. Missing index coverage, extra or omitted actions, duplicate refs,
unverified action fingerprints, or non-canonical order rejects before the
outer CompromiseImpact body is fingerprinted.

### 4.3 Recovery complete affected Binding set

Each complete_affected_binding_refs element is the exact immutable Binding
revision ref already required by R2. Elements sort by binding_id and then
binding_revision; duplicate stable revision keys reject.

R20 defines:

```text
complete_affected_binding_set_fingerprint = SHA-256(JCS([
  "agents-os.identity-recovery-complete-affected-binding-set.v0.1-r20",
  actor_id,
  compromised_actor_identity_revision,
  affected_binding_set_basis_event_sequence,
  [binding_ref, ... canonical Binding-ref order]
]))
```

The ref value inserted into JCS is the exact verified F2 Binding revision ref,
not a caller label or database key. The set has exact equality with the
binding_ref values in binding_dispositions. Missing coverage, extra or omitted
Bindings, a current Binding not represented, duplicate refs, unresolved ref
bytes, or non-canonical order yields INDETERMINATE and cannot activate
recovery.

## 5. Typed IDENTITY_STEWARD_ACTION target derivation

### 5.1 One allowed relation type

For TransitionAuthorityBasisV0_1R9 with
basis_kind IDENTITY_STEWARD_ACTION:

```text
target_relation_ref =
  exact IdentityStewardshipAssessmentV0_1R19 ref
target_relation_fingerprint =
  that assessment canonical fingerprint
assessment = VALID
assessment based_on_event_sequence = authority basis watermark
steward Actor ref = requested_by_actor_ref
steward identity and effective Binding assessments = ACTIVE
relation_kind is JENN_ROOT_STEWARD, JENN_STEWARD, NOBAO_STEWARD, or
  RESPONSIBLE_DOMAIN_AGENT_STEWARD
```

No relation subject, caller assertion, Assignment, Delegation, responsibility
assessment, Principal ref, free-form target, or implementation lookup may
satisfy these two fields.

The target Actor is derived only by this closed matrix:

| Use | Exact target Actor |
|---|---|
| RESIDENT_ATTESTED_AGENT_SESSION Binding issuance | proposed Binding actor_id and actor_identity_revision |
| Binding SUSPEND, RESUME, or REVOKE | exact target Binding Actor revision |
| Binding activation-evidence SUSPEND, RESUME, or REVOKE | exact target Binding named by the evidence |
| Actor-target CompromiseImpact | exact compromised Actor revision |

The stewardship assessment target ref/fingerprint must equal that exact Actor
revision. Missing, stale, non-VALID, different-Actor, different-steward,
wrong-watermark, forked, or fingerprint-conflicting assessment rejects.

Every target kind or use not listed in this matrix forbids
IDENTITY_STEWARD_ACTION in TransitionAuthorityBasisV0_1R9.
Actor lifecycle transitions continue to use the separately typed R16/R19
Actor authority bases and do not use this generic target_relation branch.

### 5.2 Principal compromise closes fail-safe

For CompromiseImpact targeting a Principal,
IDENTITY_STEWARD_ACTION is forbidden. R20 replaces the conflicting R8
mutation-kind and impact tables with:

| Compromised target | Impact | Exact allowed basis kinds |
|---|---|---|
| Actor | CHALLENGE | JENN_ROOT_ACTION, IDENTITY_STEWARD_ACTION, ACCEPTED_INCIDENT_POLICY_ACTION |
| Actor | INVALIDATE | JENN_ROOT_ACTION, IDENTITY_STEWARD_ACTION |
| Actor | CLEAR_CHALLENGE | JENN_ROOT_ACTION, IDENTITY_STEWARD_ACTION |
| Principal | CHALLENGE | JENN_ROOT_ACTION, ACCEPTED_INCIDENT_POLICY_ACTION |
| Principal | INVALIDATE | JENN_ROOT_ACTION |
| Principal | CLEAR_CHALLENGE | JENN_ROOT_ACTION |

An incident policy cannot invalidate or clear. Principal stewardship is not
inferred from a historical, suspended, revoked, superseded, missing, or
multiple Binding. A future typed Principal stewardship capability would
require a post-freeze F2 amendment justified by the reopen rule; no verifier
may invent it.

## 6. Total nullable-expiry semantics

### 6.1 Meaning and admission

For Binding and Responsibility Assignment expiry only:

```text
expires_at_utc_ms = null means unbounded future expiry, conceptually +infinity
null is a known valid value, not missing, unknown, indeterminate, or expired
```

The exact admission rules are:

| not_before | expires | Result |
|---|---|---|
| valid utc_milliseconds | null | valid unbounded window |
| valid utc_milliseconds | valid utc_milliseconds greater than not_before | valid finite window |
| valid utc_milliseconds | finite value equal to or less than not_before | reject |
| missing, malformed, unsafe, or time-uncertain | any | reject or INDETERMINATE under the owning reducer; never ACTIVE |

R7 Section 2.3 not_before_utc_ms < expires_at_utc_ms applies only when expiry
is non-null. Any issued-at versus expiry comparison likewise applies only when
expiry is non-null.

### 6.2 Currentness

The time branches are total:

```text
trusted now < not_before_utc_ms -> NOT_YET_ACTIVE
expires_at_utc_ms is non-null and trusted now >= expires_at_utc_ms -> EXPIRED
expires_at_utc_ms is null -> no expiry branch
missing or uncertain trusted time -> INDETERMINATE
```

No null value may be coerced to zero, omitted, compared as a string, replaced
by a platform maximum, or treated as permission to skip other currentness
checks.

### 6.3 Narrowing and containment

For successor Binding or Assignment windows and every source-to-child
containment check, null orders as +infinity:

| Source expiry | Candidate expiry | Narrowing result |
|---|---|---|
| null | null | equal; allowed if every other predicate passes |
| null | finite | shorter; allowed |
| finite S | finite C where C <= S | equal or shorter; allowed |
| finite S | finite C where C > S | wider; reject |
| finite | null | wider; reject |

The candidate not_before_utc_ms must be greater than or equal to the source
not_before_utc_ms. Scope, responsibility, delegation depth, redelegation,
Actor/Principal identity, CAS, action assurance, and all other attenuation
rules still apply independently.

Synthetic Binding precommit inputs, Binding issuance snapshots, and Binding
creation specs inherit the exact Binding value and truth table. They cannot
reinterpret null.

## 7. Corrected final materialization requirements

The next derived reading surface is:

```text
F2 Effective Contract Materialization v0.1-r20-v15
```

It is not an acceptance subject and must not invent semantics. It must:

```text
apply the four R20 closures exactly
restore Actor provisioning UPDATE and the complete Actor basis matrix
print authoritative numeric, MutationIntent, Event, and CAS predicates
print array ordering required for authoritative fingerprints and reducers
restore Binding uniqueness and Principal/Actor compatibility
restore lifecycle successor immutability and attenuation
restore exact Delegation root, Assignment, and child issuance branches
make DelegationEffectiveCurrentReducer total over Actor states
inline the existing recovery binding_dispositions element contract
encode schema-known bootstrap stewardship fields as JSON null
restore CompromiseImpact authoritative field order
repair exact source provenance without treating citation polish as F2 semantics
```

The materialization may record DOWNSTREAM_F3_OR_F4 and
IMPLEMENTATION_PROFILE gaps, but they cannot become new F2 semantics or an
automatic requirement for R21.

## 8. Required final fixtures

```text
same Profile creation spec -> identical spec fingerprint across two writers
same Principal creation spec -> identical spec fingerprint across two writers
anonymous or extra creation-spec field -> reject
Principal names external Profile spec -> reject
derived replay identity changes when any exact manifest/spec input changes
derived replay identity has no self or final-subject input
complete target set reordered -> canonical digest remains identical
complete target set omitted or duplicated action -> reject
affected Binding set omitted or duplicated Binding -> recovery INDETERMINATE
generic caller target relation used for stewardship -> reject
Principal-target CompromiseImpact by identity steward -> reject
Actor-target impact with exact VALID stewardship assessment -> deterministic
null Binding expiry remains current only while all non-time inputs validate
finite-to-null Binding successor -> reject as widening
null-to-finite Assignment successor -> admit as time narrowing
missing or uncertain trusted time -> INDETERMINATE
```

## 9. Finding disposition and non-authorization

| Prior finding | R20 disposition |
|---|---|
| F2-R19-V14-FULL-IR-B01 | Section 3 freezes both creation-spec schemas, domains, formulas, ordering, and final-subject projection |
| F2-R19-V14-FULL-IR-B02 | Section 4 freezes all three owning domain-tagged digest formulas |
| F2-R19-V14-FULL-IR-B03 | Section 5 types every permitted generic stewardship target and forbids the unresolved Principal path |
| F2-R19-V14-FULL-IR-M01 | Section 6 defines null as unbounded expiry and closes admission, reducer, and narrowing truth tables |
| Materialization findings | Section 7 requires faithful v15 correction without subject expansion |

R20 does not accept or freeze F2. It does not authorize implementation, start
F3, complete F3 or F4, define a production authentication profile, activate
runtime, create or modify a database or service, call a provider, access
secrets or private memory, or authorize commit, push, merge, release, deploy,
or package publication.

Only a later fresh hash-bound full atomic review of fixed R1-R20 plus corrected
v15 may return PASS_NO_BLOCKER under F2_FREEZE_RULE_V0_1 and place the atomic
bundle on Jenn's freeze decision surface. A PASS does not claim semantic
perfection or implementation readiness.
