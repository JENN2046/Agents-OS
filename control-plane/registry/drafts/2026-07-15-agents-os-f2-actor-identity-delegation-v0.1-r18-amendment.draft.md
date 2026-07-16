# AGENTS OS F2 Actor Identity and Delegation v0.1 R18 Temporary Worker Binding and Activation Assurance Projection Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R18_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r18
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

R18 closes only the remaining subject-level findings from the external full
R1-R17 and materialization v8 review:

```text
Temporary Worker assignment binding was opaque and not computable
Binding and Delegation activation assurance did not name exact source fields
```

R18 also requires the next derived materialization to remove two fields that
v8 printed without a source subject. R18 does not add those fields to the
contract.

R18 has exact precedence over:

```text
R1 ActorIdentityRevision.assignment_binding_ref and its status-reducer use
R8 effective Actor identity schema and fingerprint projection for that field
R16 ActorIdentityAssessment.assignment_assessment_ref
R15 and R16 stewardship predicates that use assignment_binding_ref
R16 CREATE-time intended_assignment_binding_ref
R17 generic Binding/Delegation "creation/activation action" rows
R17 generic activation complete-set wording
```

All other R1-R17 rules remain effective. R1-R18 form one indivisible proposed
acceptance unit. Partial acceptance is forbidden.

## 2. Identity and responsibility remain separate

### 2.1 Remove assignment binding from Actor identity

The effective `ActorIdentityRevisionV0_1R8` and its mutation body no longer
contain `assignment_binding_ref`. The field is forbidden for every Actor class.
It is removed from the Actor subject fingerprint projection.

The effective `ActorIdentityAssessmentV0_1R16` no longer contains
`assignment_assessment_ref`. That field is forbidden and removed from the
assessment fingerprint projection. Responsibility currentness is represented
only by the Section 3 assessment.

For `TEMPORARY_WORKER`:

```text
validity_window remains required
assignment_binding_ref is forbidden
identity currentness depends on identity lifecycle and validity time
identity ACTIVE does not mean the Worker may accept or execute work
```

R1 Actor identity status reduction is replaced only for the removed dependency:

```text
trusted now >= validity_window.expires_at_utc_ms
  -> EXPIRED

missing, forked, or uncertain required identity/time input
  -> INDETERMINATE

missing, inactive, or indeterminate work responsibility
  -> does not change Actor identity state
  -> prevents operational use through Section 3 instead
```

This preserves the established distinction:

```text
identity answers who exists and acts
responsibility answers what work that Actor currently owns
```

It also removes the cycle in which an Actor identity required an Assignment
whose own effective assessment required that same Actor identity.

### 2.2 CREATE-time stewardship input

R16
`ActorCreateStewardshipTargetSpecV0_1R16.intended_assignment_binding_ref` is
replaced by:

```yaml
intended_initial_resource_ref: ResponsibilityResourceRefV0_1 | null
```

For a `TEMPORARY_WORKER` created through a responsible Domain Agent, the value
is required and its `resource_kind` is exactly `TASK` or `RUN`. The Domain
Agent's exact current ACTIVE responsibility evidence must contain the same
resource tuple. Jenn or Nobao stewardship does not require an initial resource.

The field is CREATE-time evidence only. It does not assign responsibility,
does not enter `ActorIdentityRevision`, and cannot authorize a Command.

R15 `IdentityStewardshipAssessmentV0_1R15` is corrected as follows:

```text
TEMPORARY_WORKER with Jenn or Nobao steward
  -> use the existing exact Actor and stewardship predicates

TEMPORARY_WORKER with Domain Agent steward during CREATE
  -> require intended_initial_resource_ref
  -> require one current ACTIVE Assignment/Delegation of the Domain Agent
     whose exact scope contains that resource

TEMPORARY_WORKER with Domain Agent steward after CREATE
  -> require current ACTIVE TemporaryWorkerResponsibilityBindingAssessment
  -> require one current ACTIVE Assignment/Delegation of the Domain Agent
     whose exact scope contains the same bound resource
```

No stewardship relation ledger, permission level, or ambient domain authority
is created.

## 3. Derived Temporary Worker responsibility binding

### 3.1 Exact binding reference

R18 introduces one embedded value, not a ledger stream:

```yaml
TemporaryWorkerResponsibilityBindingRefV0_1R18:
  worker_actor_id:
  source_kind: RESPONSIBILITY_ASSIGNMENT | DELEGATION
  source_subject_ref:
  source_subject_fingerprint:
  bound_resource_ref: ResponsibilityResourceRefV0_1
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.temporary-worker-responsibility-binding-ref.v0.1-r18
```

`bound_resource_ref.resource_kind` is exactly `TASK` or `RUN`. The resource
tuple must occur byte-identically in the source subject's exact
`ResponsibilityScopeV0_1R7.resource_refs`. `DOMAIN`, `GOAL`,
`ARTIFACT_METADATA`, wildcard, subtree, narrative, and future-resource binding
are rejected.

The reference is derived from existing immutable subjects. It has no revision,
current-head pointer, mutation command, transition fact, or independent writer.
It cannot become a second responsibility ledger.

Canonical fingerprint:

```text
SHA-256(JCS([
  "agents-os.temporary-worker-responsibility-binding-ref.v0.1-r18",
  worker_actor_id,
  source_kind,
  source_subject_ref,
  source_subject_fingerprint,
  bound_resource_ref
]))
```

All strings use the F2 NFC rules. `bound_resource_ref` uses its R7 normalized
known-object projection. Unknown fields, normalized-key collisions, a mismatched
source kind, or a resource not contained by the source scope reject.

### 3.2 Effective assessment

```yaml
TemporaryWorkerResponsibilityBindingAssessmentV0_1R18:
  binding_ref: TemporaryWorkerResponsibilityBindingRefV0_1R18
  binding_fingerprint:
  worker_actor_identity_assessment_ref:
  worker_actor_identity_assessment_fingerprint:
  source_subject_ref:
  source_subject_fingerprint:
  source_current_head_ref:
  source_effective_assessment_ref:
  source_effective_assessment_fingerprint:
  responsibility_scope_fingerprint:
  bound_resource_ref: ResponsibilityResourceRefV0_1
  time_authority_ref:
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | RENOUNCED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:

```text
agents-os.temporary-worker-responsibility-binding-assessment.v0.1-r18
```

`reason_codes` is sorted by NFC UTF-8 bytes and duplicate-free. The assessment
uses the R15 canonical assessment profile. Every ref/fingerprint pair is exact
and all current inputs use one watermark.

### 3.3 Total reducer

`TemporaryWorkerResponsibilityBindingReducerV0_1R18` is the only reducer for
this derived projection:

```text
worker Actor class is not TEMPORARY_WORKER -> reject
worker Actor stable ID differs from binding.worker_actor_id -> reject
worker Actor identity RETIRED or COMPROMISED -> INDETERMINATE; deny new use
worker Actor identity SUSPENDED -> SUSPENDED
worker Actor identity EXPIRED -> EXPIRED
worker Actor identity INDETERMINATE -> INDETERMINATE

source_kind RESPONSIBILITY_ASSIGNMENT:
  source subject actor_id must equal worker_actor_id
  use exact ResponsibilityAssignmentAssessmentV0_1R16

source_kind DELEGATION:
  source subject delegate_actor_id must equal worker_actor_id
  use exact DelegationAssessmentV0_1R16

source subject/ref/fingerprint/head/scope mismatch -> INDETERMINATE
bound resource absent from exact source scope -> INDETERMINATE
source NOT_YET_ACTIVE -> NOT_YET_ACTIVE
source SUSPENDED -> SUSPENDED
source REVOKED -> REVOKED
source RENOUNCED -> RENOUNCED
source EXPIRED -> EXPIRED
source SUPERSEDED -> SUPERSEDED
source INDETERMINATE -> INDETERMINATE
worker identity ACTIVE and source assessment ACTIVE -> ACTIVE
```

The Assignment or Delegation remains the sole canonical responsibility fact.
The new assessment only answers whether that existing responsibility currently
binds one Temporary Worker to one exact Task or Run.

F3 must require `ACTIVE` for a Temporary Worker Command. Actor identity ACTIVE,
a binding reference, a historical source subject, or a matching resource alone
is insufficient. This is an F3 interface requirement only; R18 does not start
F3 or define its Command schema.

## 4. Exact activation-assurance projection

### 4.1 Projection rule

R18 replaces R17's generic activation rows and complete-set phrase with the
following exact projection. Callers never provide these bindings. Rust derives
them from the committed evidence and closed ledger indexes.

| Effective object | Exact mode/source | `action_ref` | `action_fingerprint` | Role |
|---|---|---|---|---|
| Binding activation | `JENN_ROOT_BOOTSTRAP_DECISION` | `stewardship_source.source_ref` | canonical fingerprint resolved for that exact accepted governance decision | `BINDING_ACTIVATION` |
| Binding activation | `AUTHENTICATED_STEWARD_ACTION` | `steward_action_ref.action_ref_id` | `steward_action_ref.canonical_action_ref_fingerprint` | `BINDING_ACTIVATION` |
| Binding activation | `SYNTHETIC_M0_FIXTURE` | no separate activation binding | no separate activation binding | use the required manifest `SYNTHETIC_MANIFEST_ACCEPT` assurance transitively |
| Delegation activation | `EXPLICIT_ACK` | `acknowledgement_ref.command_envelope_ref` | `acknowledgement_ref.command_envelope_fingerprint` | `DELEGATION_ACTIVATION` |
| Delegation activation | `WORKER_ASSIGNMENT_HANDSHAKE` | `acknowledgement_ref.command_envelope_ref` | `acknowledgement_ref.command_envelope_fingerprint` | `DELEGATION_ACTIVATION` |

The bootstrap governance decision is an assurance-bearing committed governance
action for this row only. It must be accepted, immutable, hash-addressed, and
within the exact bootstrap path. An unavailable canonical decision fingerprint
is `INDETERMINATE`, never an empty binding.

For authenticated Binding activation, the evidence's exact `steward_action_ref`
is mandatory. `stewardship_source.source_ref`, the steward Binding, replay ID,
or evidence fingerprint cannot substitute for the action ref.

For Delegation activation, the exact F3 committed command envelope named by
the R3 acknowledgement is the assurance action. The acknowledgement object,
acknowledgement ID, Principal Binding, authentication assertion, replay ID, and
activation-evidence fingerprint cannot substitute for the command envelope.

For `WORKER_ASSIGNMENT_HANDSHAKE`, the R3 acknowledgement must additionally be
accepted with that exact activation mode by the future F3 closed payload. Until
F3 closes and supplies that mode binding, the assessment is `INDETERMINATE`.

### 4.2 Conditional complete sets

R17 Section 2.3 is replaced only for activation objects:

```text
ordinary Binding activation:
  exactly one Section 4.1 BINDING_ACTIVATION binding
  plus every accepted activation-evidence transition through watermark

synthetic M0 Binding activation:
  no invented BINDING_ACTIVATION action
  exact transitive manifest-create and manifest-accept assurances
  plus every accepted activation-evidence transition through watermark

Delegation activation:
  exactly one Section 4.1 DELEGATION_ACTIVATION binding
  plus every accepted activation-evidence transition through watermark
```

Missing, extra, duplicated, mode-mismatched, or substituted bindings produce
`INDETERMINATE` and deny new use. A single committed action cannot receive two
roles in the same assessment. R17 ordering remains effective.

### 4.3 Evidence creation status

New `BindingActivationEvidenceR15Effective` and
`DelegationActivationEvidenceR15Effective` streams may be created only with:

```yaml
status: ACTIVE
```

`REVOKED` and `SUPERSEDED` are effective later states produced only by the
accepted transition/current-head rules. An implementation must not create a
new evidence stream directly in either state.

## 5. Materialization v9 requirements

The next derived materialization must be named:

```text
F2 Effective Contract Materialization v0.1-r18-v9
```

It is not an acceptance subject and must:

```text
apply the R18 effective Actor identity and CREATE-target corrections
print both R18 Temporary Worker binding schemas and the sole reducer
print the exact activation projection and conditional complete-set rules
show activation evidence creation_status = ACTIVE_ONLY as a rule, not a field
remove compromised_subject_action_set_ref
remove compromised_subject_action_set_fingerprint
retain only complete_target_action_refs and complete_target_set_fingerprint
represent CanonicalCommand, CommandTypeDefinition, and
  AuthenticatedCommandContext as F3-owned placeholders, not complete F2 schemas
recompute the exhaustive schema and reducer indexes
create no field, enum, role, reducer, or authority absent from R1-R18
```

Removing a field from the materialization is not a subject amendment when the
field never existed in R1-R18.

## 6. Required future fixtures

```text
Temporary Worker identity ACTIVE without responsibility -> no Command use
opaque or old assignment_binding_ref field -> reject
Worker binding to GOAL, DOMAIN, or ARTIFACT_METADATA -> reject
source scope does not contain exact Task/Run -> INDETERMINATE
source Assignment recipient differs from Worker -> reject
source Delegation delegate differs from Worker -> reject
source expires or is revoked -> Worker responsibility binding follows exactly
Domain Agent steward scope lacks bound resource -> stewardship INVALID
bootstrap decision lacks canonical fingerprint -> activation INDETERMINATE
ordinary Binding substitutes stewardship source for steward action -> reject
Delegation substitutes acknowledgement ID for command envelope -> reject
synthetic Binding invents BINDING_ACTIVATION action -> reject
new activation evidence created REVOKED or SUPERSEDED -> reject
materialization contains either invented compromise-subject field -> fail
```

## 7. Finding disposition

| Finding | R18 disposition |
|---|---|
| External `B01` | Sections 2-3 remove identity/responsibility circularity and define one exact derived Worker responsibility binding without a second ledger |
| External `B02` | Section 4 freezes exact per-mode action-ref and fingerprint sources and conditional complete sets |
| External `M-B01` | Section 5 requires deletion of the two v8-only fields; R18 does not adopt them |
| External command-interface major | Section 5 requires F3-owned placeholders rather than complete F2 Command schemas |
| External activation-creation major | Section 4.3 makes ACTIVE-only creation explicit |

The free-text Delegation `reason` low-disclosure observation is recorded as a
non-blocking future amendment candidate. R18 does not change Delegation content
semantics.

## 8. Non-authorization

R18 does not accept F2, create a permission taxonomy, modify the single
Prohibited Boundary, create a second responsibility ledger, authorize
implementation, start F3, activate runtime, authorize production
authentication, or modify R1-R17/prior-review bytes.

After author closeout, the next gate is source-exact materialization v9. Only a
later fresh hash-bound independent full review of fixed R1-R18 and v9 may place
the bundle on Jenn's atomic acceptance surface.
