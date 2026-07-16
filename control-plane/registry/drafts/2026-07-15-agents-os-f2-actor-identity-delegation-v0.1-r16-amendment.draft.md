# AGENTS OS F2 Actor Identity and Delegation v0.1 R16 Stewardship, Assurance Schema and Materialization Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R16_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r16
date: 2026-07-15
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and precedence

R16 closes only the three findings from the fresh R1-R15 full-bundle review:

```text
steward-authorized Actor CREATE precommit circularity
CompromiseImpact assurance binding in affected assessment schemas
complete and internally consistent effective materialization
```

R16 has exact precedence over:

```text
R8 Actor CREATE authority-basis inputs
R15 IdentityStewardshipAssessment use during Actor CREATE
R15 Section 5.3 direct dual assurance-binding prose
the R15 versions of every assessment schema replaced in Section 3
R15 materialization requirements
```

All other R1-R15 rules remain effective. R1-R16 form one indivisible proposed
acceptance unit. Partial acceptance is forbidden.

## 2. Acyclic CREATE-time stewardship

### 2.1 Separate precommit target specification

Post-create transitions continue to use
`IdentityStewardshipAssessmentV0_1R15`. Actor `CREATE` never uses that
assessment because no current target Actor exists yet.

R16 defines this immutable precommit object:

```yaml
ActorCreateStewardshipTargetSpecV0_1R16:
  spec_id:
  intended_actor_id:
  intended_actor_class: RESIDENT_COORDINATOR | DOMAIN_AGENT | TEMPORARY_WORKER
  intended_canonical_name:
  intended_identity_charter_refs: []
  intended_identity_steward_ref:
  intended_parent_actor_ref: optional
  intended_validity_window: IdentityValidityWindowV0_1 | null
  intended_assignment_binding_ref: optional
  expected_actor_head: null
  actor_head_absence_basis_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.actor-create-stewardship-target-spec.v0.1-r16
```

The spec is a content-addressed precommit input, not a ledger subject or state
stream. It contains no authority basis, stewardship assessment, mutation body,
intent, action, replay identity, final Actor fingerprint, or later Event. It is
therefore independent of every object that will bind it. The exact ledger
Actor-head index at `actor_head_absence_basis_event_sequence` must prove that
the intended Actor ID has no current or historical head. An existing head, an
index coverage gap, or a fork rejects the spec.

Class predicates are closed:

```text
RESIDENT_COORDINATOR -> intended steward is exact Jenn
DOMAIN_AGENT -> intended steward is exact Jenn or current Resident Coordinator
TEMPORARY_WORKER -> intended steward is exact Jenn, current Resident Coordinator,
  or current responsible Domain Agent; a Domain Agent route requires exact
  current responsibility evidence containing intended_assignment_binding_ref
```

`JENN_HUMAN_ROOT` creation uses the existing Jenn governance bootstrap path.
`SYSTEM_SERVICE` and `EXECUTION_HOST` creation use the existing accepted
provisioning path. They never use the R16 precommit stewardship path.

### 2.2 CREATE-time derived assessment

```yaml
ActorCreateStewardshipAssessmentV0_1R16:
  target_spec_ref:
  target_spec_fingerprint:
  intended_actor_id:
  intended_actor_class:
  declared_identity_steward_ref:
  steward_actor_identity_ref:
  steward_actor_identity_fingerprint:
  steward_actor_identity_assessment_ref:
  steward_actor_identity_assessment_fingerprint:
  steward_effective_binding_assessment_ref:
  steward_effective_binding_assessment_fingerprint:
  responsibility_evidence_refs: []
  responsibility_evidence_fingerprints: []
  actor_head_absence_basis_event_sequence:
  relation_kind: JENN_STEWARD | NOBAO_STEWARD | RESPONSIBLE_DOMAIN_AGENT_STEWARD
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.actor-create-stewardship-assessment.v0.1-r16
```

All refs and fingerprints are exact. Both Event watermarks equal
`based_on_event_sequence`. The target spec's absence-basis watermark equals
that watermark and the Actor-head index must prove absence through it. Steward
Actor and Binding must be exact current `ACTIVE` facts at the same watermark.
Responsibility refs and fingerprints are parallel,
same-length arrays sorted by stable ref and duplicate-free.

Missing coverage or an indeterminate dependency yields `INDETERMINATE`; an
explicit class, steward, scope, or target mismatch yields `INVALID`; only the
closed predicate with all exact inputs yields `VALID`.

This is a derived assessment, not a relation subject, current pointer, stream,
table, permission object, or second ledger.

### 2.3 Actor CREATE authority basis and mutation binding

R16 replaces the CREATE use of R8/R15 `IDENTITY_STEWARD_ACTION` authority
basis with these exact fields:

```yaml
ActorCreateStewardAuthorityBasisV0_1R16:
  authority_basis_id:
  basis_kind: IDENTITY_STEWARD_ACTION
  requested_by_actor_ref:
  requested_by_actor_identity_assessment_ref:
  requested_by_effective_binding_assessment_ref:
  create_target_spec_ref:
  create_target_spec_fingerprint:
  create_stewardship_assessment_ref:
  create_stewardship_assessment_fingerprint:
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.actor-create-steward-authority-basis.v0.1-r16
```

The other Actor authority routes use this complete R8/R15 replacement:

```yaml
ActorGeneralTransitionAuthorityBasisV0_1R16:
  authority_basis_id:
  basis_kind: JENN_ROOT_ACTION | JENN_GOVERNANCE_DECISION_BASIS | IDENTITY_STEWARD_ACTION | BOUND_ACTOR_SELF_SUSPEND_ACTION | ACCEPTED_INCIDENT_POLICY_ACTION | ACCEPTED_PROVISIONING_ACTION
  requested_by_actor_ref: optional
  requested_by_actor_identity_assessment_ref: optional
  requested_by_effective_binding_assessment_ref: optional
  Jenn_root_authority_ref: optional
  Jenn_root_authority_fingerprint: optional
  identity_stewardship_assessment_ref: optional
  identity_stewardship_assessment_fingerprint: optional
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
agents-os.actor-general-transition-authority-basis.v0.1-r16
```

Its optional-field matrix remains R8 Section 7.1, except the superseded
stewardship relation fields are replaced by the exact current-target
`IdentityStewardshipAssessmentV0_1R15` ref/fingerprint. An
`IDENTITY_STEWARD_ACTION` in this general basis is forbidden for CREATE.

The effective Actor revision field type is:

```text
transition_authority_basis:
  ActorCreateStewardAuthorityBasisV0_1R16
  | ActorGeneralTransitionAuthorityBasisV0_1R16
```

The requested Actor equals the steward in the `VALID` assessment. The basis,
assessment, and target spec use the same watermark. The later Actor mutation
body includes the exact target-spec and assessment refs/fingerprints through
this authority basis. Its stable identity fields must be byte-equal to the
target spec. The normal R8 order then remains acyclic:

```text
target spec
-> CREATE-time stewardship assessment
-> CREATE authority basis
-> Actor mutation body
-> mutation intent
-> authenticated steward action
-> LifecycleActionRef
-> final Actor revision and Event
```

For `UPDATE`, `SUSPEND`, `RESUME`, `COMPROMISE`, `RECOVER`, and `RETIRE`, the
R15 current-target `IdentityStewardshipAssessmentV0_1R15` remains mandatory for
`IDENTITY_STEWARD_ACTION`. A CREATE-time assessment is invalid for any
post-create transition, and a current-target assessment is invalid for CREATE.

## 3. Canonical assurance binding closure

### 3.1 One transitive assurance binding

R16 replaces R15 Section 5.3's requirement to repeat both the historical
assessment and input-set refs directly in every object. Each directly affected
assessment instead contains one closed array of this embedded known object:

```yaml
ActionAssuranceBindingV0_1R16:
  action_role:
  action_ref:
  action_fingerprint:
  historical_action_validity_assessment_ref:
  historical_action_validity_assessment_fingerprint:
```

The embedded-object domain tag is:

```text
agents-os.action-assurance-binding.v0.1-r16
```

The referenced complete historical assessment is:

```yaml
HistoricalActionValidityAssessmentV0_1R16:
  action_ref:
  action_fingerprint:
  actor_ref_at_commit: optional
  principal_ref_at_commit: optional
  binding_ref_at_commit: optional
  authentication_assessment_ref_at_commit: optional
  authentication_assessment_fingerprint_at_commit: optional
  committed_event_sequence:
  validity_at_commit: VALID | INVALID | INDETERMINATE
  impact_input_set_ref:
  impact_input_set_fingerprint:
  impact_coverage_through_event_sequence:
  current_assurance: CONFIRMED | CHALLENGED | INVALIDATED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.historical-action-validity-assessment.v0.1-r16
```

Authenticated Actor actions require all five commit-identity/authentication
fields. Jenn governance decisions and accepted provisioning actions require
all five to be null and instead prove their exact immutable action kind through
the referenced action fingerprint. Mixed or partially populated commit fields
yield `INDETERMINATE`.

The binding action ref/fingerprint equals the historical assessment action
ref/fingerprint. Its input-set ref/fingerprint resolves to the complete
`HistoricalImpactInputSetV0_1`. Both
`impact_coverage_through_event_sequence` and the historical assessment
`based_on_event_sequence` equal the containing effective assessment watermark.
Thus one fingerprinted transitive edge binds the exact input set without
duplicating fields that could disagree.

R16 replaces the corresponding R15 domain-registry entries with every R16
domain printed in Sections 2 and 3. It adds no implicit namespace: the CREATE
target spec, both CREATE/general Actor authority bases, CREATE stewardship
assessment, action assurance binding, historical assessment, and all R16
replacement assessments are the complete closed additions. Their domain tags
and complete known objects are mandatory; their R15/R7 predecessor domains are
historical only for new R16 assessments.

`action_assurance_bindings` is sorted by `action_role`, then `action_ref`, and
is duplicate-free. Each schema below has a closed allowed-role set. Missing,
extra, duplicated, stale, or mismatched bindings yield `INDETERMINATE` and deny
new use. Unknown action roles or action classes are rejected.

### 3.2 Complete directly affected assessment schemas

R16 completely replaces the following assessment schemas. Every optional
field is present as JSON null. All use the R15 canonical profile with the R16
domain tag printed below each schema.

```yaml
ActorIdentityAssessmentV0_1R16:
  actor_identity_ref:
  actor_identity_fingerprint:
  current_head_ref:
  current_head_fingerprint:
  assignment_assessment_ref: optional
  time_authority_ref:
  action_assurance_bindings: []
  assessment: ACTIVE | SUSPENDED | COMPROMISED | RETIRED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.actor-identity-assessment.v0.1-r16`.
Allowed roles: `CURRENT_ACTOR_REVISION`, followed by every effective Actor
state-transition action through the watermark.

```yaml
AuthenticatorProfileAssessmentV0_1R16:
  profile_ref:
  profile_subject_fingerprint:
  current_profile_head_ref:
  lifecycle_controller_ref:
  action_assurance_bindings: []
  assessment: ACTIVE | SUSPENDED | RETIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.authenticator-profile-assessment.v0.1-r16`.
Allowed roles: `CURRENT_PROFILE_REVISION`, followed by effective Profile
state-transition actions.

```yaml
PrincipalAssessmentV0_1R16:
  principal_ref:
  principal_subject_fingerprint:
  current_principal_head_ref:
  authenticator_profile_assessment_ref:
  authenticator_profile_assessment_fingerprint:
  credential_status_assessment_refs: []
  credential_status_assessment_fingerprints: []
  action_assurance_bindings: []
  assessment: ACTIVE | SUSPENDED | REVOKED | RETIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.principal-assessment.v0.1-r16`.
Allowed roles: `CURRENT_PRINCIPAL_REVISION`, followed by effective Principal
state-transition actions. Credential arrays are parallel and sorted by
credential-handle stable ref.

```yaml
BindingActivationAssessmentV0_1R16:
  binding_ref:
  binding_subject_fingerprint:
  activation_evidence_ref:
  activation_evidence_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  action_assurance_bindings: []
  assessment: ACTIVATED | NOT_ACTIVATED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.binding-activation-assessment.v0.1-r16`.
Allowed roles: `BINDING_ACTIVATION`, followed by effective activation-evidence
state-transition actions.

```yaml
ActorPrincipalBindingAssessmentV0_1R16:
  binding_ref:
  binding_subject_fingerprint:
  current_binding_head_ref:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  principal_assessment_ref:
  principal_assessment_fingerprint:
  authenticator_profile_assessment_ref:
  authenticator_profile_assessment_fingerprint:
  credential_status_assessment_refs: []
  credential_status_assessment_fingerprints: []
  binding_activation_assessment_ref:
  binding_activation_assessment_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  time_authority_ref:
  action_assurance_bindings: []
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.actor-principal-binding-assessment.v0.1-r16`.
Allowed roles: `BINDING_ISSUANCE`, followed by effective Binding
state-transition actions. Activation assurance is bound by the referenced
activation assessment and is not duplicated.

```yaml
ResponsibilityAssignmentAssessmentV0_1R16:
  assignment_ref:
  assignment_subject_fingerprint:
  current_assignment_head_ref:
  recipient_actor_identity_assessment_ref:
  recipient_actor_identity_assessment_fingerprint:
  source_direction_ref:
  source_direction_fingerprint:
  responsibility_scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  time_authority_ref:
  action_assurance_bindings: []
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.responsibility-assignment-assessment.v0.1-r16`.
Allowed roles: `ASSIGNMENT_ISSUANCE`, followed by effective Assignment
state-transition actions.

```yaml
DelegationActivationAssessmentV0_1R16:
  delegation_ref:
  delegation_subject_fingerprint:
  activation_acknowledgement_ref:
  activation_evidence_ref:
  activation_evidence_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  action_assurance_bindings: []
  assessment: ACTIVATED | NOT_ACTIVATED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.delegation-activation-assessment.v0.1-r16`.
Allowed roles: `DELEGATION_ACTIVATION`, followed by effective
activation-evidence state-transition actions.

```yaml
DelegationAssessmentV0_1R16:
  delegation_ref:
  delegation_subject_fingerprint:
  current_delegation_head_ref:
  source_assignment_assessment_ref: optional
  source_assignment_assessment_fingerprint: optional
  ancestor_delegation_assessment_refs: []
  ancestor_delegation_assessment_fingerprints: []
  delegator_actor_identity_assessment_ref:
  delegator_actor_identity_assessment_fingerprint:
  delegate_actor_identity_assessment_ref:
  delegate_actor_identity_assessment_fingerprint:
  activation_assessment_ref:
  activation_assessment_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
  time_authority_ref:
  action_assurance_bindings: []
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | RENOUNCED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.delegation-assessment.v0.1-r16`.
Allowed roles: `DELEGATION_ISSUANCE`, followed by effective Delegation
state-transition actions. Activation assurance and ancestor assurance are
bound transitively by their exact fingerprinted assessments.

```yaml
SyntheticM0ManifestAssessmentV0_1R16:
  manifest_ref:
  manifest_fingerprint:
  current_activation_revision_ref:
  current_activation_revision_fingerprint:
  action_assurance_bindings: []
  assessment: ACTIVE | REVOKED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain: `agents-os.synthetic-m0-manifest-assessment.v0.1-r16`.
Allowed roles: `MANIFEST_CREATE`, `MANIFEST_ACCEPT`, followed by an effective
`MANIFEST_REVOKE` action when present.

### 3.3 Dependent assessments do not duplicate direct assurance

`AuthenticationAssessmentV0_1R15`, synthetic eligibility, stewardship, and
recovery evidence depend on the exact R16 assessments above. They do not add a
second copy of the same action assurance. Their watermark must equal every
referenced effective assessment watermark. If a referenced assessment is
`INDETERMINATE`, non-active, stale, or fingerprint-mismatched, the dependent
assessment fails closed under its existing reducer.

Credential status and principal-control proof assessments remain owned by
their authenticator/controller contracts. F2 references their exact
fingerprints; CompromiseImpact targets the F2 Principal or Profile action, not
secret-bearing credential/proof bytes.

### 3.4 Total CompromiseImpact integration

For each directly affected schema, reducer order is:

```text
1. verify complete required action-role set and every transitive assurance edge
2. apply R15 action-class mapping to current_assurance
3. preserve safer transition effects and prohibit automatic restore
4. apply object-specific terminal/currentness/dependency rules
5. allow ACTIVE or ACTIVATED only when every required assurance is CONFIRMED
```

Safety transition bindings remain present even if their assurance becomes
`CHALLENGED` or `INVALIDATED`. The safer state remains effective and the
binding exposes non-confirmed assurance plus a reason code without returning
the object to a less safe state. The object assessment remains the applicable
safe state (`SUSPENDED`, `REVOKED`, `COMPROMISED`, or `RETIRED`); only a new
explicit valid compensation action can change it. Where an object's assessment
enum has no applicable safe terminal value, it returns `INDETERMINATE` and
denies new use.

An enabling action that becomes challenged or invalidated never reactivates a
target. The target stays non-active or `INDETERMINATE` until a new explicit
valid enabling action is committed.

## 4. Materialization v4 requirements

The author must create:

```text
F2 Effective Contract Materialization v0.1-r16-v4
```

It is derived-only and not an acceptance subject. It must provide one complete
resolved implementation reading surface and include, in full:

```text
all R1-R16 acceptance-subject hashes and override precedence
canonical scalar, JCS, reference, domain, and fingerprint rules
every effective Actor/Profile/Principal/Binding/Assignment/Delegation schema
every activation evidence and assessment schema
every authentication, action, mutation, replay, transition, recovery,
  historical assurance, CompromiseImpact, and synthetic M0 schema
CREATE-time and post-create stewardship schemas and authority predicates
all reducer precedence and currentness/watermark rules
the exact mutation-kind list including RESPONSIBILITY_ASSIGNMENT_REVISION
the single Prohibited Boundary and all non-authorization limits
an object-to-source map for every printed schema and reducer
```

It must not refer readers back to a superseded schema for required fields. A
schema may reference another schema printed in full in v4. No required object
may appear only as prose, a domain-table row, or an undefined alias.

## 5. Required future fixtures

```text
CREATE stewardship assessment points to current target Actor -> reject
CREATE target spec contains assessment, authority, body, intent, or action -> reject
Actor head appears before CREATE assessment watermark -> reject
CREATE body stable identity differs from target spec -> reject
post-create transition uses CREATE assessment -> reject
directly affected assessment omits required action role -> INDETERMINATE
historical assessment watermark differs from containing assessment -> INDETERMINATE
historical assessment input-set fingerprint mismatch -> INDETERMINATE
safety transition assurance INVALIDATED -> no automatic restore
enabling transition assurance INVALIDATED -> target remains non-active
materialization mutation-kind list omits Assignment -> validation failure
materialization schema catalogue has unresolved alias -> validation failure
```

## 6. Finding disposition

| Finding | R16 disposition |
|---|---|
| `F2-R15-FULL-IR-B01` | Sections 2.1-2.3 introduce an exact precommit spec and CREATE-only assessment; current-target assessment remains post-create only |
| `F2-R15-FULL-IR-M01` | Sections 3.1-3.4 define one transitive assurance binding and complete replacement schemas for every directly affected F2 assessment |
| `F2-R15-FULL-IR-M02` | Section 4 requires a complete v4 resolved reading surface and exact mutation list |

## 7. Non-authorization

R16 does not:

```text
accept F2
authorize implementation or database changes
start F3
authorize runtime activation or production authentication
create a second relation or task ledger
create a new permission taxonomy
change the single Prohibited Boundary
modify R1-R15 or prior review bytes
```

The next gate after author closeout is a fresh hash-bound independent review of
R1-R16 and materialization v4. Only a clean review may place the atomic bundle
before Jenn for an acceptance decision.
