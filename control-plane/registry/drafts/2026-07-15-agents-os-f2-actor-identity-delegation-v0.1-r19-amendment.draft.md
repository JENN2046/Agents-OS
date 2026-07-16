# AGENTS OS F2 Actor Identity and Delegation v0.1 R19 Lifecycle Revalidation and Stewardship Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R19_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r19
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

R19 closes only the three subject-level blockers and one low-disclosure minor
from the fresh full R1-R18 and materialization v13 independent review:

```text
Actor validity-window start state was not closed
activation-evidence RESUME revalidation was not canonically bound
Domain Agent stewardship of a non-ACTIVE Worker was recovery-locked
Delegation reason remained unconstrained free text
```

R19 has exact precedence over:

```text
R1 and R7 Actor validity-window reduction
R16 ActorIdentityAssessmentV0_1R16 assessment enum
R8 GovernedStateTransitionFactV0_1R8 and R9 effective overlay
R7 and R8 Binding/Delegation activation-evidence RESUME predicates
R15 IdentityStewardshipAssessmentV0_1R15
R18 post-create Domain Agent stewardship predicate
R3/R4 Delegation issuance-intent projection for reason
the effective Delegation subject field named reason
```

All other R1-R18 rules remain effective. R1-R19 form one indivisible proposed
acceptance unit. Partial acceptance is forbidden. R19 changes no fixed R1-R18
bytes and creates no acceptance, implementation, runtime, provider, database,
service, credential, production-authentication, F3, or permission authority.

## 2. Actor validity-window start closure

### 2.1 Effective Actor assessment enum

R19 replaces only the assessment enum of
`ActorIdentityAssessmentV0_1R16`:

```text
NOT_YET_ACTIVE | ACTIVE | SUSPENDED | COMPROMISED | RETIRED | EXPIRED | SUPERSEDED | INDETERMINATE
```

The schema name and domain remain
`ActorIdentityAssessmentV0_1R16` and
`agents-os.actor-identity-assessment.v0.1-r16`; R19 is part of the complete
effective known-object contract. Existing R17 assurance bindings remain exact.

`NOT_YET_ACTIVE` is a derived time-currentness state. It is not a stored Actor
revision status, transition target, new revision kind, or permission. The
underlying current Actor revision still has `status: ACTIVE` and remains
subject to the existing CAS and lifecycle transition matrix.

### 2.2 Total Actor time reduction

`ActorIdentityEffectiveReducer` applies this exact precedence:

```text
assessed revision is not the unique current head -> SUPERSEDED
current revision status RETIRED -> RETIRED
current revision status COMPROMISED -> COMPROMISED
current revision status SUSPENDED -> SUSPENDED
missing/forked head, invalid transition/action/assurance, unavailable trusted
  time, malformed validity window, or fingerprint conflict -> INDETERMINATE
validity_window is present and trusted now < not_before_utc_ms
  -> NOT_YET_ACTIVE
validity_window is present and trusted now >= expires_at_utc_ms
  -> EXPIRED
all class, lifecycle, assurance, fingerprint, and time dependencies current
  -> ACTIVE
```

`not_before_utc_ms <= trusted now < expires_at_utc_ms` is the only active time
interval. A missing validity window for a Temporary Worker is
`INDETERMINATE`; other classes omit the window unless their accepted profile
requires one.

### 2.3 Downstream projection

Every reducer that consumes an Actor assessment handles `NOT_YET_ACTIVE`
explicitly:

```text
ActorPrincipalBindingAssessment -> NOT_YET_ACTIVE
ResponsibilityAssignmentAssessment -> NOT_YET_ACTIVE
DelegationAssessment when the target/delegate Actor is pre-start
  -> NOT_YET_ACTIVE
TemporaryWorkerResponsibilityBindingAssessment -> NOT_YET_ACTIVE
AuthenticationAssessment or operational-use dependency -> non-authenticated /
  non-active under its existing closed enum; never ACTIVE or AUTHENTICATED
steward Actor or action Actor NOT_YET_ACTIVE -> stewardship/action INVALID or
  INDETERMINATE according to missing-versus-present evidence; never VALID
```

The time-derived state does not synthesize a transition fact and does not
prevent Jenn or a valid current steward from committing an otherwise admitted
safe lifecycle transition against the current underlying revision.

## 3. Canonical activation-evidence RESUME revalidation

### 3.1 Closed derived assessment

R19 introduces one derived assessment, not a ledger or writer:

```yaml
ActivationEvidenceResumeRevalidationAssessmentV0_1R19:
  revalidation_assessment_id:
  target_kind: BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE
  target_activation_evidence_ref:
  target_activation_evidence_fingerprint:
  current_transition_head_ref:
  current_transition_head_fingerprint:
  target_subject_ref:
  target_subject_fingerprint:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  principal_assessment_ref: optional
  principal_assessment_fingerprint: optional
  authenticator_profile_assessment_ref: optional
  authenticator_profile_assessment_fingerprint: optional
  credential_status_assessment_refs: []
  credential_status_assessment_fingerprints: []
  principal_control_proof_assessment_ref: optional
  principal_control_proof_assessment_fingerprint: optional
  delegation_activation_acknowledgement_ref: optional
  delegation_activation_acknowledgement_fingerprint: optional
  acknowledging_principal_binding_assessment_ref: optional
  acknowledging_principal_binding_assessment_fingerprint: optional
  acknowledgement_action_validity_assessment_ref: optional
  acknowledgement_action_validity_assessment_fingerprint: optional
  source_responsibility_assessment_ref: optional
  source_responsibility_assessment_fingerprint: optional
  ancestor_delegation_assessment_refs: []
  ancestor_delegation_assessment_fingerprints: []
  time_authority_ref:
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.activation-evidence-resume-revalidation-assessment.v0.1-r19
```

Canonical fingerprint:

```text
SHA-256(JCS([
  "agents-os.activation-evidence-resume-revalidation-assessment.v0.1-r19",
  complete_Section_3_1_known_object_without_canonical_fingerprint
]))
```

The assessment uses the R15 canonical derived-record profile. Arrays are
parallel, sorted by stable ref, and duplicate-free. Every dependency and the
assessment itself has exactly the same `based_on_event_sequence` watermark.
Unknown fields, mixed conditional branches, stale watermarks, missing
fingerprints, or normalized-key collisions reject.

### 3.2 Conditional branches and reducer

`ActivationEvidenceResumeRevalidationReducerV0_1R19` is total.

Common rules:

```text
target evidence/ref/fingerprint does not name the unique current suspended
  activation-evidence stream -> INVALID
current transition head is not the accepted SUSPEND head named by the RESUME
  expected_target_head -> INVALID
fork, CAS gap, missing coverage, stale watermark, time uncertainty, action
  assurance failure, or any ref/fingerprint mismatch -> INDETERMINATE
actor identity not ACTIVE, or trusted time outside every required current
  validity window -> INVALID when proven, otherwise INDETERMINATE
```

For `BINDING_ACTIVATION_EVIDENCE`:

```text
principal, Profile, and every credential assessment field is required
principal-control proof assessment ref/fingerprint is required
Delegation-only fields and arrays are null/empty
proof assessment is VERIFIED, was assessed after the effective SUSPEND Event,
  is current at the common watermark, and binds the exact target Binding,
  Actor, Principal, Profile, verifier revision, and challenge fingerprint
all exact dependencies current and ACTIVE -> VALID
```

For `DELEGATION_ACTIVATION_EVIDENCE`:

```text
exact immutable activation acknowledgement and its fingerprint are required
acknowledging Principal Binding assessment is required and ACTIVE
exact historical action-validity assessment for the acknowledgement command
  envelope is required and its current_assurance is CONFIRMED
source responsibility and complete ancestor arrays are required as applicable
Binding-only Profile/credential/proof fields are null/empty
acknowledgement names the exact current Delegation subject, delegate Actor,
  committed command envelope, activation mode, and replay identity
delegate identity, acknowledging Binding, source responsibility, and every
  ancestor are current at the common watermark -> VALID
```

A routine session end, Principal Binding expiry or replacement, or credential
rotation does not retroactively invalidate an accepted acknowledgement. Only
the bound historical action-validity assessment and its CompromiseImpact
projection can make that acknowledgement `CHALLENGED`, `INVALIDATED`, or
`INDETERMINATE` for this reducer.

No branch references the effective Binding or effective Delegation assessment
whose activation result it helps resume. This prevents a revalidation cycle.
`INVALID` and `INDETERMINATE` both reject RESUME.

### 3.3 Transition body and fact overlay

R19 adds these fields to the effective governed transition fact:

```yaml
GovernedStateTransitionFactV0_1R19Additions:
  resume_revalidation_assessment_ref: optional
  resume_revalidation_assessment_fingerprint: optional
```

They occur immediately after `expected_target_head` in the known-object field
order. For `RESUME` targeting Binding or Delegation activation evidence, both
are required and must name an exact `VALID` Section 3.1 assessment. For every
other target/transition tuple both are JSON null. Extra, missing, substituted,
or non-null values reject.

The `GOVERNED_STATE_TRANSITION` mutation body includes the two fields in the
same position. MutationIntent, body fingerprint, LifecycleActionRef, replay
identity, final fact fingerprint, recovery, and current-head CAS therefore
bind the exact revalidation assessment. The existing R8/R9 fact domain remains
`agents-os.governed-state-transition-fact.v0.1-r8`; R19 changes the complete
effective known object and no earlier fact bytes are rewritten.

RESUME acceptance is:

```text
current exact SUSPEND head + exact VALID R19 revalidation assessment
-> body -> body fingerprint -> intent -> committed action
-> LifecycleActionRef -> replay identity -> final transition fact/Event/CAS
```

The R17 `BINDING_ACTIVATION_TRANSITION_RESUME` and
`DELEGATION_ACTIVATION_TRANSITION_RESUME` roles remain exact; R19 creates no
new assurance role.

## 4. Non-circular Domain Agent Worker stewardship

### 4.1 Target-state-independent scope assessment

R19 introduces this derived assessment:

```yaml
TemporaryWorkerStewardshipScopeAssessmentV0_1R19:
  target_worker_identity_ref:
  target_worker_identity_fingerprint:
  worker_actor_id:
  declared_domain_agent_steward_ref:
  domain_agent_identity_assessment_ref:
  domain_agent_identity_assessment_fingerprint:
  domain_agent_responsibility_assessment_ref:
  domain_agent_responsibility_assessment_fingerprint:
  worker_responsibility_binding_ref: TemporaryWorkerResponsibilityBindingRefV0_1R18
  worker_responsibility_binding_fingerprint:
  source_subject_ref:
  source_subject_fingerprint:
  source_current_head_ref:
  source_current_head_fingerprint:
  source_transition_fact_refs: []
  source_transition_fact_fingerprints: []
  source_action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  source_responsibility_scope_fingerprint:
  bound_resource_ref: ResponsibilityResourceRefV0_1
  domain_agent_responsibility_scope_fingerprint:
  time_authority_ref:
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.temporary-worker-stewardship-scope-assessment.v0.1-r19
```

It uses the R15 canonical derived-record profile and the complete known object
excluding only `canonical_fingerprint`. Arrays are sorted, parallel where
paired, and duplicate-free.

### 4.2 Scope reducer

`TemporaryWorkerStewardshipScopeReducerV0_1R19` verifies:

```text
target stable Actor is exactly TEMPORARY_WORKER and its current-head identity
  bytes match worker_actor_id; target assessment state is deliberately not an
  input to this scope-only projection
declared steward is the exact current ACTIVE Domain Agent
Domain Agent responsibility assessment is ACTIVE and its exact scope contains
  bound_resource_ref
target worker_actor_id is absent from every Actor position in the Domain Agent
  responsibility root and Delegation lineage
Domain Agent responsibility is not issued, delegated, controlled, or made
  current by target Worker or by any lineage deriving from target Worker
Worker binding ref/fingerprint names the same Worker, source subject,
  source fingerprint, and exact TASK or RUN resource
source Assignment recipient or Delegation delegate equals worker_actor_id
source subject is the unique current head with valid CAS, issuance, lineage,
  activation when Delegation, transition coverage, assurance, time, scope, and
  fingerprints, after excluding only the target Worker's own derived identity
  state from the source's operational-use projection
source is not suspended, revoked, renounced, expired, superseded, challenged,
  invalidated, or indeterminate
source scope and Domain Agent scope both contain the exact bound resource
all inputs use one exact watermark -> VALID
```

A proven mismatch is `INVALID`; missing, forked, stale, uncertain, or
fingerprint-conflicting evidence is `INDETERMINATE`. This assessment cannot
assign responsibility, activate the Worker, authorize a Command, replace the
R18 operational Worker binding assessment, or create a second ledger. It only
answers whether the declared Domain Agent still owns the exact scope needed to
steward the named Worker lifecycle.

The target Worker identity assessment, the R18 operational Worker binding
assessment, and any Domain Agent responsibility lineage containing or deriving
from the target Worker are forbidden inputs. A `VALID` scope assessment is
allowlisted only as responsibility evidence for
`IdentityStewardshipAssessmentV0_1R19`; no other consumer may treat it as
operational authority.

### 4.3 Post-create stewardship overlay

R19 replaces `IdentityStewardshipAssessmentV0_1R15` with:

```yaml
IdentityStewardshipAssessmentV0_1R19:
  target_actor_identity_ref:
  target_actor_identity_fingerprint:
  target_actor_identity_assessment_ref:
  target_actor_class:
  declared_identity_steward_ref:
  steward_actor_identity_ref: optional
  steward_actor_identity_assessment_ref: optional
  provisioning_authority_ref: optional
  provisioning_authority_fingerprint: optional
  responsibility_evidence_refs: []
  responsibility_evidence_fingerprints: []
  relation_kind: JENN_ROOT_STEWARD | JENN_STEWARD | NOBAO_STEWARD | RESPONSIBLE_DOMAIN_AGENT_STEWARD | PROVISIONING_STEWARD | NOT_APPLICABLE
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.identity-stewardship-assessment.v0.1-r19
```

The R15 domain and schema are historical for new post-create assessments.
For a responsible Domain Agent steward, the responsibility evidence arrays
contain exactly one matching `TemporaryWorkerStewardshipScopeAssessmentV0_1R19`
ref/fingerprint with result `VALID`. The R18 requirement for an operational
Worker binding assessment to be `ACTIVE` is replaced only in this stewardship
branch. Jenn, Nobao, provisioning, and non-Worker derivations remain otherwise
unchanged.

The target Actor assessment is still fingerprinted evidence but its non-ACTIVE
state does not make a proven scope relation invalid. The Actor transition
matrix separately decides whether `UPDATE`, `RESUME`, `RECOVER`, or `RETIRE`
is valid for that target state. This separation removes the recovery lock.

## 5. Closed Delegation reason profile

### 5.1 Field replacement

The effective Delegation subject replaces free-text `reason` with:

```yaml
DelegationReasonV0_1R19:
  reason_code: TASK_HANDOFF | RUN_EXECUTION | DOMAIN_OPERATION | INCIDENT_RESPONSE | MAINTENANCE
  reason_artifact_ref: ResponsibilityResourceRefV0_1 | null
```

`reason_artifact_ref`, when non-null, has `resource_kind: ARTIFACT_METADATA` and
names an immutable low-disclosure artifact reference. It cannot contain inline
narrative, secrets, credentials, provider output, private memory, wildcard,
subtree, future-resource notation, or authority. The value is embedded and
`NOT_STANDALONE`; no independent writer or fingerprint domain is created.

The old `reason` field is forbidden, including as null or an unknown field.
Reason codes are exact ASCII values; aliases, localization, case folding,
extensions, and free text reject.

### 5.2 Updated issuance intent and subject fingerprint

The R3/R4 Delegation issuance-intent projection remains exact except its
`reason` position is replaced by these two positions:

```text
reason_code
reason_artifact_ref_or_null
```

The updated exact formula is:

```text
SHA-256(JCS([
  "agents-os.delegation-issuance-intent.v0.1-r19",
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
  reason_code,
  reason_artifact_ref_or_null,
  status
]))
```

The final subject fingerprint remains the R4 acyclic formula except it uses
the R19 intent fingerprint:

```text
delegation_subject_fingerprint = SHA-256(JCS([
  "agents-os.delegation-grant-subject.v0.1-r4",
  delegation_issuance_intent_fingerprint,
  issuance_action_ref.F3_contract_version,
  issuance_action_ref.canonical_action_ref_fingerprint,
  created_at_event_sequence
]))
```

Existing historical Delegation subjects retain their original bytes and
fingerprints. A new successor using R19 preserves stable lineage fields and
uses the R19 intent domain and reason value. Recovery never silently rewrites
old free text.

## 6. Corrected materialization requirements

The next derived materialization is:

```text
F2 Effective Contract Materialization v0.1-r19-v14
```

It is not an acceptance subject. In addition to every R1-R19 requirement, it
must close all materialization findings from the blocking R18-v13 full review:

```text
restore the exact R6 parsed-binary64 admission rule and rounded-token examples
print every still-effective special fingerprint, intent, replay, evidence-ID,
  lineage, and derived-digest formula in full
print every effective closed set and invariant, including Assignment
  self-issuance rejection, non-transferable responsibility, BindingScope and
  context scalar rules, and Jenn permitted_basis_uses
split Actor CREATE authority by exact Actor class
distinguish ACTIVE-only evidence creation from derived SUSPENDED, REVOKED, and
  SUPERSEDED activation-evidence states
use exact subject sections and valid cross-references throughout the source map
print every effective schema and reducer exactly once
apply every R19 schema, reducer, domain, fingerprint, and downstream state rule
create no new authority or semantics beyond fixed R1-R19
```

The exhaustive surface and reducer indexes must include the R19 additions and
must be validated for both row-set equality and source-predicate/formula
completeness. Structural equality alone is insufficient.

## 7. Required future fixtures

```text
Temporary Worker before not_before -> NOT_YET_ACTIVE
Temporary Worker at not_before -> ACTIVE when every other dependency is valid
Temporary Worker at expiry -> EXPIRED
pre-start Actor cannot authenticate or support operational use
activation RESUME without revalidation ref/fingerprint -> reject
Binding activation RESUME with proof assessed before SUSPEND -> reject
Binding activation RESUME with exact fresh current proof -> admit
Delegation activation RESUME with substituted acknowledgement -> reject
Delegation activation RESUME with stale principal Binding -> reject
non-RESUME transition with non-null revalidation fields -> reject
Domain Agent steward resumes a suspended Worker with VALID scope assessment
Domain Agent steward recovers a compromised Worker with VALID scope assessment
Domain Agent responsibility lineage contains or derives from target Worker -> reject
scope assessment cannot make Worker operationally ACTIVE
source responsibility suspended/revoked/expired -> stewardship scope non-valid
free-text Delegation reason field -> reject
unknown Delegation reason code -> reject
reason artifact not ARTIFACT_METADATA -> reject
historical Delegation fingerprint remains unchanged
```

## 8. Finding disposition and non-authorization

| Prior finding | R19 disposition |
|---|---|
| `F2-R18-V13-FULL-IR-B01` | Sections 2.1-2.3 close pre-start Actor state and every downstream projection |
| `F2-R18-V13-FULL-IR-B02` | Sections 3.1-3.3 bind exact RESUME revalidation into body, intent, action, replay, fact, Event, and CAS |
| `F2-R18-V13-FULL-IR-B03` | Sections 4.1-4.3 separate stewardship scope validity from target Worker state |
| `F2-R18-V13-FULL-IR-m01` | Section 5 replaces free text with a closed low-disclosure reason value |
| Materialization `B04-B06`, `M01-M03` | Section 6 requires complete correction in derived v14; no subject semantics are invented for those materialization-only findings |

R19 does not accept F2, authorize implementation, start F3, define F3 Command
payloads, modify the single Prohibited Boundary, create a permission taxonomy,
activate runtime, authorize authentication, create a database or service,
call a provider, access secrets or private memory, modify R1-R18, or authorize
commit/push/release/deploy. Only a later fresh full hash-bound independent
review of fixed R1-R19 and corrected v14 may place the atomic bundle on Jenn's
acceptance surface.
