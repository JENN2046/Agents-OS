# AGENTS OS F4 TaskPermit / Host Authentication / Effect Admission v0.1 R1

Status: author draft for fresh hash-bound independent review  
Date: 2026-07-16  
Owner: Jenn  
Agent steward: Nobao

## 0. Authority, acceptance, and fixed inputs

This document is the first F4 author surface authorized by Jenn's explicit
`启动 F4` instruction and the immutable start decision:

```text
control-plane/registry/decisions/2026-07-16-agents-os-f4-taskpermit-host-authentication-effect-admission-start-decision-v0.1.yaml
SHA-256 00a1a1fe86c6e550a52f85b7638e6d4c39392f731486ddd4d20306e771ba33d8
```

The effective contract literal is exactly:

```text
F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R1_ATOMIC_BUNDLE
```

This draft has no authority before a fresh full hash-bound independent review
and a later explicit Jenn atomic acceptance decision. Partial acceptance is
forbidden.

Fixed prerequisites:

| Input | Path | SHA-256 |
|---|---|---|
| F1 acceptance | `control-plane/registry/decisions/2026-07-14-agents-os-f1-goal-spec-plan-membership-acceptance-decision-v0.1.yaml` | `e49e572055b8e367d38cc70297f5ee144482f4023c62aa46e74de35d999977b2` |
| F2 freeze | `control-plane/registry/decisions/2026-07-16-agents-os-f2-actor-identity-delegation-r22-atomic-freeze-decision-v0.1.yaml` | `bf0fa804d8fd58ac6dfd4e5bb775d3b831ccc5b91443d6dbeac50c5414de97a1` |
| F3 freeze | `control-plane/registry/decisions/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-r4-atomic-freeze-decision-v0.1.yaml` | `f692ef1a1af8ac15f40c8af696f486240b73a3ddf391633078e31f17eaf62529` |
| High-privilege direction | `control-plane/registry/decisions/2026-07-12-agents-os-vcp-high-privilege-architecture-v0.1.md` | `9b3a8ecf80ab1a8c7cba120f46d0ec70bab437040dda3c7a468cbe5623875a71` |
| Readiness graph | `control-plane/registry/reviews/2026-07-14-yellow-agents-os-construction-readiness-review-v0.1.md` | `8159c32d359243b81250f639c7e267619e59176a682cad2afee9bd28ed74d670` |

Nothing in F4 edits, replaces, weakens, or reinterprets the accepted F1, F2,
or F3 subject bytes. F4 consumes their canonical refs and current assessments.

## 1. Scope and explicit exclusions

F4 closes exactly the semantic boundary between a committed F3
`EFFECT_INTENT` Command and one identity-bound, fence-bound host start
admission.

In scope:

```text
TaskPermit immutable schema and canonical identity
permit issuance, currentness, expiry, revocation, supersession and consumption
current Task / commitment / dependency authority binding
current Actor / Principal / Binding / Delegation / Authentication binding
current Resident identity / writer epoch / continuity / Command binding
Host identity, Host authentication and Host capability assessment
host fence, effect fence and execution epoch currentness
one-time HostWorkAcceptanceFact per invocation before effect handoff
host-side fail-closed verification immediately before effect handoff
idempotency, replay, crash ambiguity and UNKNOWN_AFTER_CRASH
synthetic M0-A constructibility without real secrets, providers or effects
```

Out of scope:

```text
F5 Outbox claim, dispatch, delivery, retry, dead-letter and reconciliation
F6 Validation current decision and Task completion eligibility
real host enrollment, real credentials, keys, cryptography or attestation profile
Rust, JavaScript, N-API implementation, database, index, cache or service
Resident, worker, host, provider, executor or external-effect execution
production authentication, provider configuration, public API or MCP expansion
secret values, private raw Memory, raw provider response or raw runtime logs
commit, push, PR, merge, tag, release, deploy or publish
```

F4 authorizes no effect. It defines the evidence that a future implementation
must possess before one host may accept one bounded start authority.

## 2. Separation of facts

The following objects are never interchangeable:

| Object | Proves | Does not prove |
|---|---|---|
| F3 `CommandEnvelope` | one Command was committed under exact identity/currentness evidence | Task authority, host identity, permit validity or effect occurrence |
| `TaskPermitV0_1` | immutable bounded authorization was issued from one exact current snapshot | current validity, host acceptance, physical start or effect result |
| `TaskPermitCurrentnessAssessmentV0_1` | permit and every bound authority are current at one ledger watermark | host-side state at the later F5 handoff boundary |
| `HostLocalAdmissionDecisionV0_1` | a pure evaluator found the exact snapshot admissible | committed acceptance, physical start or external effect |
| `HostWorkAcceptanceFactV0_1` | Rust committed one one-time start authority for the exact invocation before the deadline/fence | physical start or external effect |
| `HostWorkStartDispositionFactV0_1` | authenticated host evidence says authority was current at the F5 handoff boundary, or says no handoff was authorized | physical start or effect result |
| F5 delivery/recovery facts | future transport and reconciliation state | authority to mint or widen a permit |

Prompt compliance, model intent, session continuity, process possession,
hostname, IPC origin, network location, bearer-token possession, UI state,
Outbox presence, or a callback response cannot substitute for any row.

## 3. Canonical value profile

Every F4 field named `canonical_fingerprint`, `assessment_fingerprint`,
`decision_fingerprint`, or `fact_fingerprint` is:

```text
SHA-256(JCS([
  "agents-os.f4-fingerprint.v0.1:" + exact_schema_name,
  field_1_value,
  ...,
  last_value_before_the_fingerprint
]))
```

`exact_schema_name` is the case-sensitive schema heading in this contract.
Fields occur in displayed order; the fingerprint field itself is excluded.
This rule also applies when a paragraph says “covers every preceding field.”
It removes object-key-order ambiguity and self-digest cycles. Strings are NFC
UTF-8, hashes are 64 lowercase hexadecimal characters, timestamps are UTC
integer milliseconds, and integers are non-negative safe integers unless
declared positive.

```yaml
stable_ref:
  type: string
  min_utf8_bytes: 1
  max_utf8_bytes: 512
  forbidden: [NUL, leading_or_trailing_whitespace, non_NFC]

closed_string_set:
  order: bytewise_ASCII
  duplicates: reject
  unknown_values: reject

low_disclosure_ref:
  carries_raw_secret: false
  carries_raw_private_content: false
  carries_provider_response: false
```

Unknown fields, enum values, algorithms, schema revisions, digest profiles,
or additional array members reject. Missing authority never becomes `false`
or `not required`; it becomes `INDETERMINATE` and cannot admit work.

## 4. Exact upstream authority bindings

### 4.1 `F4TaskAuthorityBindingV0_1`

```yaml
F4TaskAuthorityBindingV0_1:
  interface_version: agents-os.f4-task-authority-binding.v0.1
  task_id: stable_ref
  task_lifecycle_generation: positive_safe_integer
  task_completion_epoch: non_negative_safe_integer
  task_state_revision: positive_safe_integer
  task_state_fingerprint: lowercase_sha256
  goal_id: stable_ref
  goal_spec_revision: positive_safe_integer
  goal_spec_fingerprint: lowercase_sha256
  goal_plan_membership_revision: positive_safe_integer
  goal_plan_membership_fingerprint: lowercase_sha256
  task_commitment_snapshot_id: stable_ref
  task_commitment_snapshot_fingerprint: lowercase_sha256
  dependency_closure_snapshot_id: stable_ref
  dependency_closure_fingerprint: lowercase_sha256
  task_completion_refs:
    type: sorted_unique_array
    item: [task_id, completion_epoch, completion_ref_id]
  completion_assurance_versions:
    type: sorted_unique_array
    item: [completion_ref_id, assurance_version, fence_generation]
  previous_execution_epoch: non_negative_safe_integer
  execution_epoch_head_fingerprint: lowercase_sha256
  currentness_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

The fingerprint is SHA-256 JCS over every preceding field in order. The
binding is a read-only F4 snapshot. It creates no Goal, Task, Run, membership,
commitment, dependency, completion, or scheduling fact.

`previous_execution_epoch` and its head fingerprint bind the current F4 epoch
head observed before issuance. Epoch 0 is the only valid pre-issuance value for
the first permit in a Task lineage.

A permit can issue only when the Task is current and eligible for a new
execution admission under its owning contracts; its completion epoch is not
terminally closed; the commitment snapshot and complete dependency closure
are current; and every completion assurance tuple is current. A later change
to any bound revision or fingerprint invalidates the permit.

### 4.2 `F4ActorAuthorityBindingV0_1`

```yaml
F4ActorAuthorityBindingV0_1:
  interface_version: agents-os.f4-actor-authority-binding.v0.1
  actor_id: stable_ref
  actor_identity_revision: positive_safe_integer
  actor_identity_assessment_ref: stable_ref
  actor_identity_assessment_fingerprint: lowercase_sha256
  principal_id: stable_ref
  principal_binding_revision: positive_safe_integer
  principal_binding_assessment_ref: stable_ref
  principal_binding_assessment_fingerprint: lowercase_sha256
  authentication_assessment_ref: stable_ref
  authentication_assessment_fingerprint: lowercase_sha256
  authentication_result: literal:AUTHENTICATED
  responsibility_source_kind: JENN_ROOT | ASSIGNMENT | DELEGATION
  responsibility_source_ref: stable_ref
  responsibility_source_fingerprint: lowercase_sha256
  delegation_chain_fingerprint: lowercase_sha256 | null
  bound_resource_ref: stable_ref
  action_ref: stable_ref
  action_fingerprint: lowercase_sha256
  prohibited_behavior_list_revision: positive_safe_integer
  prohibited_boundary_evidence_ref: stable_ref
  prohibited_boundary_evidence_fingerprint: lowercase_sha256
  authority_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Every F2 assessment is recomputed at the same issuance watermark. Jenn root
uses the exact frozen root semantics; it does not omit responsibility or
prohibited-boundary evidence. Assignment and Delegation sources require their
complete current F2 activation/currentness chain. A stale, suspended, revoked,
renounced, superseded, compromised, unauthenticated, indeterminate, scope-
mismatched, or over-depth lineage cannot issue or use a permit.

### 4.3 `F4ResidentCommandBindingV0_1`

```yaml
F4ResidentCommandBindingV0_1:
  interface_version: agents-os.f4-resident-command-binding.v0.1
  resident_identity_ref: stable_ref
  resident_identity_revision: positive_safe_integer
  resident_incarnation_id: stable_ref
  resident_epoch: positive_safe_integer
  resident_continuity_assessment_ref: stable_ref
  resident_continuity_assessment_fingerprint: lowercase_sha256
  resident_continuity_result: literal:CONTINUOUS
  command_id: stable_ref
  command_fingerprint: lowercase_sha256
  command_type_id: stable_ref
  command_type_version: positive_safe_integer
  command_definition_fingerprint: lowercase_sha256
  command_envelope_ref: stable_ref
  command_envelope_fingerprint: lowercase_sha256
  authenticated_context_ref: stable_ref
  authenticated_context_fingerprint: lowercase_sha256
  authenticated_action_ref: stable_ref
  authenticated_action_fingerprint: lowercase_sha256
  F3_contract_version: literal:F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
  writer_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Issuance requires the exact current F3 writer to be `READY` and `CONTINUOUS`
both before intake and immediately before the atomic commit. A stale process,
old epoch, alternate connection, copied envelope, changed Command, or
non-current continuity proof rejects.

## 5. Host identity and authentication

### 5.1 `HostIdentityRevisionV0_1`

```yaml
HostIdentityRevisionV0_1:
  interface_version: agents-os.host-identity-revision.v0.1
  host_id: stable_ref
  revision: positive_safe_integer
  previous_revision_ref: stable_ref | null
  previous_revision_fingerprint: lowercase_sha256 | null
  host_kind: VCPTOOLBOX | VCPCHAT | VCPMOBILE | LOCAL_EXECUTOR | SYNTHETIC_M0_HOST
  controller_actor_id: stable_ref
  controller_actor_identity_revision: positive_safe_integer
  authenticator_profile_ref: stable_ref
  authenticator_profile_revision: positive_safe_integer
  authenticator_profile_fingerprint: lowercase_sha256
  credential_binding_ref: low_disclosure_ref
  credential_binding_fingerprint: lowercase_sha256
  lifecycle_state: PRESTART | ACTIVE | SUSPENDED | REVOKED | COMPROMISED | RETIRED
  validity_start_utc_ms: non_negative_safe_integer
  validity_end_utc_ms: positive_safe_integer | null
  issued_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

The revision fingerprint covers every preceding field in order. Revision 1
requires both previous fields null; later revisions require both and one
unique current predecessor. State transitions are append-only. `REVOKED`,
`COMPROMISED`, and `RETIRED` are terminal. A credential value is never stored
in this subject.

### 5.2 `HostAuthenticationAssessmentV0_1`

```yaml
HostAuthenticationAssessmentV0_1:
  interface_version: agents-os.host-authentication-assessment.v0.1
  host_identity_ref: stable_ref
  host_identity_fingerprint: lowercase_sha256
  authenticator_profile_ref: stable_ref
  authenticator_profile_fingerprint: lowercase_sha256
  challenge_ref: low_disclosure_ref
  challenge_fingerprint: lowercase_sha256
  verifier_identity_ref: stable_ref
  verifier_profile_ref: stable_ref
  verification_evidence_ref: low_disclosure_ref
  verification_evidence_fingerprint: lowercase_sha256
  host_authentication_epoch: positive_safe_integer
  trusted_time_utc_ms: non_negative_safe_integer
  valid_until_utc_ms: non_negative_safe_integer
  host_revocation_event_sequence: non_negative_safe_integer
  result: AUTHENTICATED | REJECTED | INDETERMINATE
  reason: MATCH | EXPIRED | NOT_YET_VALID | SUSPENDED | REVOKED | COMPROMISED | RETIRED | PROFILE_MISMATCH | CHALLENGE_MISMATCH | VERIFIER_UNAVAILABLE | REVOCATION_UNAVAILABLE | INTEGRITY_FAILURE | UNKNOWN
  assessment_fingerprint: lowercase_sha256
```

The assessment fingerprint covers every preceding field in order. Result
`AUTHENTICATED` requires reason `MATCH`, an ACTIVE unique current Host
revision, exact profile and challenge match, trusted time inside both windows,
and readable current revocation state. Any proven negative is `REJECTED`; an
unavailable or non-reproducible input is `INDETERMINATE`. Neither negative
result admits work.

The authentication epoch is allocated monotonically per Host identity by the
canonical verifier and is never supplied by JavaScript. Re-authentication
creates a higher epoch; expiry, revocation, compromise, profile change, or
challenge invalidation makes all earlier epochs non-current.

The cryptographic algorithm, key custody, device enrollment, rotation,
transport, and production verifier implementation remain a separate profile.
F4 requires their future accepted outputs; it does not invent or activate
them.

## 6. Canonical TaskPermit

### 6.1 Supporting closed values

```yaml
SideEffectClassV0_1: GREEN | YELLOW | RED
PermitLifecycleStateV0_1: ISSUED | ACTIVE | CONSUMED | REVOKED | EXPIRED | SUPERSEDED
PermitCurrentnessResultV0_1: VALID | REJECTED | INDETERMINATE
EffectOutcomeClassV0_1: NOT_EXECUTED | SUCCEEDED | FAILED | UNKNOWN_AFTER_CRASH

CapabilityGrantV0_1:
  capability_id: stable_ref
  capability_revision: positive_safe_integer
  operation_set: sorted_unique_closed_strings
  constraint_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256

ResourceGrantV0_1:
  resource_kind: FILE | DIRECTORY | PROCESS | NETWORK_ENDPOINT | DEVICE | UI_SURFACE | PROVIDER_OPERATION | SYNTHETIC_M0_RESOURCE
  resource_ref: low_disclosure_ref
  resource_subject_fingerprint: lowercase_sha256
  operation_set: sorted_unique_closed_strings
  selector_constraint_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256

SecretHandleBindingV0_1:
  handle_ref: low_disclosure_ref
  handle_revision: positive_safe_integer
  handle_binding_fingerprint: lowercase_sha256
  owner_host_id: stable_ref
  permitted_use_fingerprint: lowercase_sha256
  revocation_head_fingerprint: lowercase_sha256
  raw_value_present: literal:false
  canonical_fingerprint: lowercase_sha256
```

A capability or resource not named exactly is denied. Wildcard resources,
implicit descendants, ambient environment authority, arbitrary shell text,
provider-wide authority, bearer-secret values, and unknown selector syntax
reject.

Each supporting object fingerprint follows Section 3. Supporting-object arrays
are sorted bytewise by canonical fingerprint, reject duplicate fingerprints,
and also reject two entries that reuse one capability ID, resource
`(resource_kind, resource_ref)`, or secret handle ref with different bytes.
Their set fingerprints are exactly:

```text
SHA256(JCS(["agents-os.f4-capability-set.v0.1", sorted_capability_fingerprints]))
SHA256(JCS(["agents-os.f4-resource-set.v0.1", sorted_resource_fingerprints]))
SHA256(JCS(["agents-os.f4-secret-handle-set.v0.1", sorted_secret_handle_fingerprints]))
```

Secret-handle metadata is current authority, not a bearer value. Issuance,
acceptance, and handoff require the exact revision, binding, owner Host,
permitted use, and revocation head to remain current without resolving the raw
secret.

### 6.2 `EffectIntentBindingV0_1`

```yaml
EffectIntentBindingV0_1:
  interface_version: agents-os.effect-intent-binding.v0.1
  effect_intent_id: stable_ref
  operation_kind: stable_ref
  target_resource_refs: sorted_unique_low_disclosure_refs
  payload_fingerprint: lowercase_sha256
  capability_set_fingerprint: lowercase_sha256
  resource_set_fingerprint: lowercase_sha256
  expected_result_contract_ref: stable_ref
  expected_result_contract_fingerprint: lowercase_sha256
  idempotency_key: stable_ref
  side_effect_class: GREEN | YELLOW | RED
  external_effect_requested: true
  raw_payload_present: false
  canonical_fingerprint: lowercase_sha256
```

The fingerprint covers every preceding field. The binding is an intent, not a
dispatch, Outbox item, provider request, host call, or effect result.

### 6.3 `JennAuthorizationBindingV0_1`

```yaml
JennAuthorizationBindingV0_1:
  mode: NOT_REQUIRED | EXACT_CURRENT_P3A_AUTHORIZATION
  authorization_event_ref: stable_ref | null
  authorization_event_fingerprint: lowercase_sha256 | null
  Jenn_actor_identity_ref: stable_ref | null
  authorized_scope_fingerprint: lowercase_sha256 | null
  authorized_side_effect_class: RED | null
  policy_bundle_revision: positive_safe_integer | null
  prohibited_behavior_list_revision: positive_safe_integer | null
  issued_at_utc_ms: non_negative_safe_integer | null
  expires_at_utc_ms: positive_safe_integer | null
  revocation_event_sequence: non_negative_safe_integer | null
  currentness_result: NOT_APPLICABLE | CURRENT | REJECTED | INDETERMINATE
  canonical_fingerprint: lowercase_sha256
```

GREEN and YELLOW require `NOT_REQUIRED`, every nullable field null, and
`NOT_APPLICABLE`. RED requires the exact current P3a authorization and every
field non-null with `CURRENT`. P3b behavior, permission bypass, confirmation
bypass, secret exposure, private raw Memory access, raw-log disclosure,
browser-login mutation, or review/branch-protection bypass can never form an
issuable binding, even if a purported Jenn Event exists.

### 6.3.1 `HumanPresenceBindingV0_1`

```yaml
HumanPresenceBindingV0_1:
  mode: NOT_REQUIRED | EXACT_CURRENT_PRESENCE
  presence_event_ref: stable_ref | null
  presence_event_fingerprint: lowercase_sha256 | null
  present_actor_id: stable_ref | null
  present_actor_identity_revision: positive_safe_integer | null
  authorized_scope_fingerprint: lowercase_sha256 | null
  observer_host_id: stable_ref | null
  observed_at_utc_ms: non_negative_safe_integer | null
  valid_until_utc_ms: positive_safe_integer | null
  revocation_event_sequence: non_negative_safe_integer | null
  currentness_result: NOT_APPLICABLE | CURRENT | REJECTED | INDETERMINATE
  canonical_fingerprint: lowercase_sha256
```

When `requires_human_presence` is false, mode is `NOT_REQUIRED`, all nullable
fields are null, and currentness is `NOT_APPLICABLE`. When true, mode is
`EXACT_CURRENT_PRESENCE`, every field is non-null, the actor/Host/scope exactly
match the permit, trusted time is before `valid_until`, and currentness is
`CURRENT`. UI focus, session activity, a recent prompt, process possession,
or an unbound click is not human-presence evidence.

### 6.4 `TaskPermitV0_1`

```yaml
TaskPermitV0_1:
  interface_version: agents-os.task-permit.v0.1
  F4_contract_version: literal:F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R1_ATOMIC_BUNDLE
  permit_id: stable_ref
  permit_revision: literal:1
  issuance_event_sequence: non_negative_safe_integer
  task_authority_binding: F4TaskAuthorityBindingV0_1
  actor_authority_binding: F4ActorAuthorityBindingV0_1
  resident_command_binding: F4ResidentCommandBindingV0_1
  host_identity_ref: stable_ref
  host_identity_fingerprint: lowercase_sha256
  host_authenticator_profile_ref: stable_ref
  host_authenticator_profile_fingerprint: lowercase_sha256
  host_authentication_assessment_ref: stable_ref
  host_authentication_assessment_fingerprint: lowercase_sha256
  host_authentication_epoch: positive_safe_integer
  issuer_resident_identity_ref: stable_ref
  issuer_resident_epoch: positive_safe_integer
  policy_bundle_revision: positive_safe_integer
  policy_bundle_fingerprint: lowercase_sha256
  prohibited_behavior_list_revision: positive_safe_integer
  prohibited_boundary_evidence_ref: stable_ref
  prohibited_boundary_evidence_fingerprint: lowercase_sha256
  capability_grants: sorted_unique_CapabilityGrantV0_1
  resource_grants: sorted_unique_ResourceGrantV0_1
  effect_intent_binding: EffectIntentBindingV0_1
  execution_epoch: positive_safe_integer
  host_fence_generation: positive_safe_integer
  effect_fence_generation: positive_safe_integer
  task_fence_generation: positive_safe_integer
  issued_at_utc_ms: non_negative_safe_integer
  not_before_utc_ms: non_negative_safe_integer
  expires_at_utc_ms: positive_safe_integer
  start_authority_commit_before_utc_ms: positive_safe_integer
  max_invocations: positive_safe_integer
  idempotency_key: stable_ref
  requires_human_presence: boolean
  human_presence_binding: HumanPresenceBindingV0_1
  Jenn_authorization_binding: JennAuthorizationBindingV0_1
  secret_handle_bindings: sorted_unique_SecretHandleBindingV0_1
  permit_attestation_profile_ref: stable_ref
  permit_attestation_profile_fingerprint: lowercase_sha256
  permit_attestation_evidence_ref: low_disclosure_ref
  permit_attestation_evidence_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

The permit fingerprint is SHA-256 JCS over every preceding field in order.
`permit_id` is:

```text
SHA-256(JCS([
  "agents-os.task-permit-id.v0.1",
  task_authority_binding.task_id,
  task_authority_binding.task_lifecycle_generation,
  execution_epoch,
  resident_command_binding.command_id,
  host_identity_ref,
  effect_intent_binding.idempotency_key,
  issuance_event_sequence
]))
```

`execution_epoch` must be new for a newly issued effect intent. It equals
`task_authority_binding.previous_execution_epoch + 1`; the issuance
transaction installs it as the new execution-epoch head. All three fence
generations are exact current positive integers at issuance.
`not_before <= issued_at < expires_at`,
`issued_at <= start_authority_commit_before <= expires_at`, and the maximum
duration cannot exceed the exact current Command type definition.
When RED authorization or human presence is required, permit and start-
authority deadlines cannot exceed the bound authorization/presence deadline.

The capability, resource, target, payload, idempotency, side-effect class,
host, actor, Task, Command, policy, authorization, attestation, validity,
invocation, and fence fields are immutable. There is no permit amendment.
Changed authority requires a new permit ID and higher execution epoch.

A permit never carries a raw secret, credential, cookie, private content,
provider response, executable callback, SQL, shell command, or arbitrary
metadata. A secret handle grants only the exact named use on the exact owner
host; it does not reveal or transfer the secret.

## 7. Permit state and currentness

### 7.1 Append-only facts

```yaml
TaskPermitIssuanceFactV0_1:
  permit_ref: stable_ref
  permit_fingerprint: lowercase_sha256
  issuance_command_envelope_ref: stable_ref
  issuance_command_envelope_fingerprint: lowercase_sha256
  issuance_event_sequence: non_negative_safe_integer
  fact_fingerprint: lowercase_sha256

TaskPermitTransitionFactV0_1:
  permit_ref: stable_ref
  permit_fingerprint: lowercase_sha256
  transition_kind: ACTIVATE | CONSUME | REVOKE | EXPIRE | SUPERSEDE
  expected_previous_state: ISSUED | ACTIVE
  resulting_state: ACTIVE | CONSUMED | REVOKED | EXPIRED | SUPERSEDED
  reason: HOST_ACCEPTANCE | INVOCATIONS_EXHAUSTED | EXPLICIT_REVOCATION | ACTOR_REVOKED | HOST_REVOKED | HOST_COMPROMISED | POLICY_CHANGED | PROHIBITED_BOUNDARY_CHANGED | TASK_CHANGED | COMMAND_CHANGED | FENCE_ADVANCED | TIME_EXPIRED | REPLACED
  transition_action_ref: stable_ref
  transition_action_fingerprint: lowercase_sha256
  event_sequence: non_negative_safe_integer
  fact_fingerprint: lowercase_sha256
```

The unique state path is:

```text
ISSUED -> ACTIVE -> CONSUMED
ISSUED -> REVOKED | EXPIRED | SUPERSEDED
ACTIVE -> REVOKED | EXPIRED | SUPERSEDED
```

Terminal states never transition. `ACTIVATE` occurs only with the first
committed HostWorkAcceptanceFact. `CONSUME` occurs when all invocation
ordinals are terminally accounted. Revocation does not erase prior acceptance
or physical-start evidence.

### 7.2 `TaskPermitCurrentnessAssessmentV0_1`

```yaml
TaskPermitCurrentnessAssessmentV0_1:
  interface_version: agents-os.task-permit-currentness-assessment.v0.1
  permit_ref: stable_ref
  permit_fingerprint: lowercase_sha256
  lifecycle_state: ISSUED | ACTIVE | CONSUMED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  trusted_time_utc_ms: non_negative_safe_integer
  task_binding_current: PASS | REJECTED | INDETERMINATE
  actor_binding_current: PASS | REJECTED | INDETERMINATE
  resident_command_binding_current: PASS | REJECTED | INDETERMINATE
  host_identity_current: PASS | REJECTED | INDETERMINATE
  host_authentication_current: PASS | REJECTED | INDETERMINATE
  policy_current: PASS | REJECTED | INDETERMINATE
  prohibited_boundary_current: PASS | REJECTED | INDETERMINATE
  capability_grants_current: PASS | REJECTED | INDETERMINATE
  resource_grants_current: PASS | REJECTED | INDETERMINATE
  secret_handle_bindings_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  permit_attestation_current: PASS | REJECTED | INDETERMINATE
  human_presence_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  Jenn_authorization_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  time_window_current: PASS | REJECTED | INDETERMINATE
  invocation_available: PASS | REJECTED | INDETERMINATE
  execution_epoch_current: PASS | REJECTED | INDETERMINATE
  host_fence_current: PASS | REJECTED | INDETERMINATE
  effect_fence_current: PASS | REJECTED | INDETERMINATE
  task_fence_current: PASS | REJECTED | INDETERMINATE
  result: VALID | REJECTED | INDETERMINATE
  reason: ALL_CURRENT | TERMINAL | NOT_YET_VALID | EXPIRED | INVOCATIONS_EXHAUSTED | TASK_STALE | ACTOR_STALE | COMMAND_STALE | HOST_STALE | AUTH_STALE | POLICY_STALE | PROHIBITED | AUTHORIZATION_STALE | EPOCH_STALE | FENCE_STALE | UNAVAILABLE | INTEGRITY_FAILURE
  assessment_event_sequence: non_negative_safe_integer
  assessment_fingerprint: lowercase_sha256
```

The fingerprint covers every preceding field. `VALID` requires state ISSUED or
ACTIVE, reason `ALL_CURRENT`, every applicable check PASS, GREEN/YELLOW Jenn
authorization `NOT_APPLICABLE`, RED Jenn authorization PASS, and all inputs
read at one reproducible current watermark. Any proven negative is
`REJECTED`; any missing, conflicting, unreadable, or non-reproducible input is
`INDETERMINATE`. Only `VALID` can enter host acceptance.

## 8. Fences and invocation identity

### 8.1 `F4FenceStateV0_1`

```yaml
F4FenceStateV0_1:
  interface_version: agents-os.f4-fence-state.v0.1
  task_id: stable_ref
  task_lifecycle_generation: positive_safe_integer
  host_id: stable_ref
  execution_epoch: positive_safe_integer
  task_fence_generation: positive_safe_integer
  host_fence_generation: positive_safe_integer
  effect_fence_generation: positive_safe_integer
  fence_reason: GENESIS | NEW_EXECUTION | TASK_CHANGED | HOST_REVOKED | HOST_COMPROMISED | POLICY_CHANGED | PROHIBITED_BOUNDARY_CHANGED | PERMIT_REVOKED | EFFECT_UNKNOWN | INCIDENT | JENN_KILL_SWITCH
  source_event_ref: stable_ref
  source_event_fingerprint: lowercase_sha256
  event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

There is one current append-only head for each `(task_id, generation)`, each
host, and each effect-intent lineage. A generation may increase only by
exactly one through the Rust canonical writer. Decrease, reuse, duplicate
current heads, skipped generations, or an unbound reason is an integrity
failure and fences all affected work.

A permit remains usable only when all three current generations equal the
permit exactly. No later recovery, projection rebuild, `PRESERVED` state,
clock change, process restart, restored database, or replay can make an old
generation current again.

### 8.2 Invocation identity

```yaml
PermitInvocationIdentityV0_1:
  permit_id: stable_ref
  permit_fingerprint: lowercase_sha256
  invocation_ordinal: positive_safe_integer
  idempotency_key: stable_ref
  execution_epoch: positive_safe_integer
  host_id: stable_ref
  effect_intent_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

The ordinal is contiguous from 1 through `max_invocations`. At most one
nonterminal acceptance exists per identity. An identical replay returns the
same facts; changed bytes under the same identity are a protocol conflict.

## 9. Host-local effect admission

Admission is a two-boundary protocol. The first boundary is a pure decision
over a reproducible snapshot. The second boundary is the Rust canonical
writer's atomic acceptance commit. Neither boundary is evidence that an
external effect physically started or completed.

### 9.1 `HostLocalAdmissionRequestV0_1`

```yaml
HostLocalAdmissionRequestV0_1:
  interface_version: agents-os.host-local-admission-request.v0.1
  invocation_identity: PermitInvocationIdentityV0_1
  task_permit_ref: stable_ref
  task_permit_fingerprint: lowercase_sha256
  effect_intent_ref: stable_ref
  effect_intent_fingerprint: lowercase_sha256
  resident_command_envelope_ref: stable_ref
  resident_command_envelope_fingerprint: lowercase_sha256
  target_host_id: stable_ref
  target_host_identity_revision: positive_safe_integer
  requested_at_utc_ms: non_negative_safe_integer
  request_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

The request contains references and canonical fingerprints only. It cannot
contain a raw secret, raw credential, arbitrary executable material, provider
response, private memory, or an authority-bearing callback. Its target host
must equal the permit owner host.

### 9.2 `HostLocalAdmissionDecisionV0_1`

```yaml
HostLocalAdmissionDecisionV0_1:
  interface_version: agents-os.host-local-admission-decision.v0.1
  invocation_identity_fingerprint: lowercase_sha256
  request_ref: stable_ref
  request_fingerprint: lowercase_sha256
  permit_currentness_assessment_ref: stable_ref
  permit_currentness_assessment_fingerprint: lowercase_sha256
  host_authentication_assessment_ref: stable_ref
  host_authentication_assessment_fingerprint: lowercase_sha256
  fence_state_ref: stable_ref
  fence_state_fingerprint: lowercase_sha256
  current_watermark_event_sequence: non_negative_safe_integer
  request_integrity: PASS | REJECTED | INDETERMINATE
  permit_currentness: PASS | REJECTED | INDETERMINATE
  host_authentication: PASS | REJECTED | INDETERMINATE
  host_ownership: PASS | REJECTED | INDETERMINATE
  task_fence_match: PASS | REJECTED | INDETERMINATE
  host_fence_match: PASS | REJECTED | INDETERMINATE
  effect_fence_match: PASS | REJECTED | INDETERMINATE
  execution_epoch_match: PASS | REJECTED | INDETERMINATE
  capability_subset: PASS | REJECTED | INDETERMINATE
  resource_subset: PASS | REJECTED | INDETERMINATE
  secret_handle_scope: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  permit_attestation: PASS | REJECTED | INDETERMINATE
  human_presence: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  effect_intent_exact_match: PASS | REJECTED | INDETERMINATE
  idempotency_identity_match: PASS | REJECTED | INDETERMINATE
  invocation_slot_available: PASS | REJECTED | INDETERMINATE
  prohibited_boundary: PASS | REJECTED | INDETERMINATE
  Jenn_authorization: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  decision: ADMITTED | REJECTED | INDETERMINATE
  reason: ALL_CHECKS_PASS | INVALID_REQUEST | PERMIT_INVALID | HOST_UNAUTHENTICATED | HOST_NOT_OWNER | STALE_FENCE | STALE_EPOCH | CAPABILITY_DENIED | RESOURCE_DENIED | SECRET_HANDLE_DENIED | ATTESTATION_INVALID | HUMAN_PRESENCE_MISSING | EFFECT_MISMATCH | IDEMPOTENCY_CONFLICT | INVOCATION_UNAVAILABLE | PROHIBITED | AUTHORIZATION_MISSING | CURRENTNESS_UNAVAILABLE | INTEGRITY_FAILURE
  decided_at_utc_ms: non_negative_safe_integer
  decision_fingerprint: lowercase_sha256
```

`ADMITTED` requires `ALL_CHECKS_PASS`, every applicable check PASS,
GREEN/YELLOW Jenn authorization `NOT_APPLICABLE`, RED Jenn authorization PASS,
and one reproducible watermark. A proven negative is `REJECTED`. Missing,
conflicting, unreadable, stale, or non-reproducible evidence is
`INDETERMINATE`. Both non-ADMITTED values fail closed.

The decision is advisory input to the canonical reducer. It grants no start
authority and expires as soon as any bound head changes.

### 9.3 `HostWorkAcceptanceFactV0_1`

```yaml
HostWorkAcceptanceFactV0_1:
  interface_version: agents-os.host-work-acceptance-fact.v0.1
  acceptance_id: stable_ref
  invocation_identity: PermitInvocationIdentityV0_1
  admission_request_ref: stable_ref
  admission_request_fingerprint: lowercase_sha256
  admission_decision_ref: stable_ref
  admission_decision_fingerprint: lowercase_sha256
  permit_currentness_assessment_ref: stable_ref
  permit_currentness_assessment_fingerprint: lowercase_sha256
  host_authentication_assessment_ref: stable_ref
  host_authentication_assessment_fingerprint: lowercase_sha256
  accepted_host_id: stable_ref
  accepted_host_identity_revision: positive_safe_integer
  accepted_host_authentication_epoch: positive_safe_integer
  accepted_task_fence_generation: positive_safe_integer
  accepted_host_fence_generation: positive_safe_integer
  accepted_effect_fence_generation: positive_safe_integer
  accepted_execution_epoch: positive_safe_integer
  accepted_watermark_event_sequence: non_negative_safe_integer
  accepted_at_utc_ms: non_negative_safe_integer
  start_authority_expires_at_utc_ms: positive_safe_integer
  host_acceptance_attestation_ref: stable_ref
  host_acceptance_attestation_fingerprint: lowercase_sha256
  fact_fingerprint: lowercase_sha256
```

`acceptance_id =
SHA256(JCS(["agents-os.host-work-acceptance-id.v0.1",
invocation_identity.canonical_fingerprint]))`.

The Rust canonical writer commits this fact only after re-reading the permit,
host identity, authentication, fences, task, actor, Command, policy,
authorization, invocation ledger, and prohibited boundary at one current
watermark. It must reproduce the advisory decision exactly. The accepted
generations and epoch equal both permit and current heads. The start-authority
expiry is no later than permit, Host-authentication, Jenn-authorization, and
applicable human-presence expiry, and may be shorter under host policy.

There is exactly one accepted fact per invocation identity. Identical replay
returns it; changed bytes are an integrity failure. Commitment occurs before
any physical effect start. An effect-work database row, dispatch queue item,
JavaScript promise, network request, provider request, shell process, file
mutation, or actuator call created before this fact commits is unauthorized
work.

### 9.4 `HostWorkStartDispositionFactV0_1`

```yaml
HostWorkStartDispositionFactV0_1:
  interface_version: agents-os.host-work-start-disposition-fact.v0.1
  observation_id: stable_ref
  observation_attempt: positive_safe_integer
  acceptance_ref: stable_ref
  acceptance_fingerprint: lowercase_sha256
  invocation_identity_fingerprint: lowercase_sha256
  observed_host_id: stable_ref
  observed_host_identity_revision: positive_safe_integer
  observed_host_authentication_epoch: positive_safe_integer
  rechecked_task_fence_generation: positive_safe_integer
  rechecked_host_fence_generation: positive_safe_integer
  rechecked_effect_fence_generation: positive_safe_integer
  rechecked_execution_epoch: positive_safe_integer
  rechecked_secret_handle_set_fingerprint: lowercase_sha256
  rechecked_permit_attestation_fingerprint: lowercase_sha256
  rechecked_human_presence_binding_fingerprint: lowercase_sha256
  secret_handles_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  permit_attestation_current: PASS | REJECTED | INDETERMINATE
  human_presence_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  disposition: START_AUTHORITY_CURRENT | NOT_STARTED | INDETERMINATE
  reason: ALL_RECHECKS_PASS | EXPIRED | FENCED | HOST_UNAUTHENTICATED | EPOCH_STALE | ACCEPTANCE_MISSING | INTEGRITY_FAILURE | OBSERVATION_UNAVAILABLE
  observed_at_utc_ms: non_negative_safe_integer
  observation_event_sequence: non_negative_safe_integer
  host_observation_attestation_ref: stable_ref
  host_observation_attestation_fingerprint: lowercase_sha256
  fact_fingerprint: lowercase_sha256
```

Immediately before handing accepted work to the future F5 effect executor, the
authenticated owner host rechecks acceptance, expiry, identity revision,
authentication epoch, all three fences, and execution epoch. Only
`START_AUTHORITY_CURRENT / ALL_RECHECKS_PASS` may cross that handoff. This
fact says that authority was current at the handoff boundary. It does **not**
say that the external effect started, succeeded, failed, or did not execute.
Those are F5 facts.

The result/reason mapping is closed: `START_AUTHORITY_CURRENT` requires
`ALL_RECHECKS_PASS`; `NOT_STARTED` requires one proven negative reason;
`INDETERMINATE` requires `OBSERVATION_UNAVAILABLE` or an unreproducible
integrity state. No other pairing is valid.

The canonical writer commits a successful `START_AUTHORITY_CURRENT`
disposition and the corresponding `F4AcceptedEffectHandoffV0_1` in one
serializable transaction after the final recheck. There is no authority gap
between them. Revocation/fence ordering first rejects the transaction;
handoff ordering first preserves the historical handoff and routes later
outcome uncertainty to F5. A `NOT_STARTED` fact may commit only while the
unique handoff key is absent.

`observation_id =
SHA256(JCS(["agents-os.host-work-start-observation-id.v0.1",
acceptance_fingerprint, observation_attempt]))`. Attempts are contiguous from
1. There may be multiple `INDETERMINATE` observations before expiry, but at
most one `START_AUTHORITY_CURRENT` observation per acceptance. After
`START_AUTHORITY_CURRENT` or `NOT_STARTED`, no later observation is permitted.
Identical replay returns the same fact; changed bytes under one observation ID
are an integrity failure.

## 10. Atomic reducers and crash semantics

### 10.1 `TaskPermitIssuanceReducerV0_1`

For one committed F3 `EFFECT_INTENT` Command envelope, the Rust canonical
writer performs one serializable transaction:

1. verify the Command envelope and its accepted type definition;
2. re-read Task, actor, delegation, Resident, policy, prohibited-boundary,
   host, authorization, fence, commitment, and dependency heads;
3. prove the requested capabilities/resources/effect are exact subsets of all
   current upstream authority;
4. reject P3b and require exact current Jenn authorization for P3a;
5. allocate `previous_execution_epoch + 1`, install that new epoch head, and
   bind exact current fence generations; a later permit for the same effect
   lineage also advances its effect fence and supersedes the earlier permit;
6. derive the permit ID and full fingerprint;
7. insert the immutable permit and issuance fact; and
8. append the new permit head and issuance receipt at one event sequence.

The unique key is the issuance Command envelope fingerprint. Identical replay
returns the same permit. A different requested permit under the same envelope
is a protocol conflict. Failure before commit leaves no permit; ambiguous
commit observation is resolved by lookup on the unique key, never by blind
reissuance.

### 10.2 `HostWorkAcceptanceReducerV0_1`

For one invocation identity, the Rust canonical writer performs one
serializable transaction:

1. validate the request and reproduce the local decision;
2. lock or compare-and-swap the permit, invocation, host, and fence heads;
3. re-run every currentness, authentication, ownership, scope, authorization,
   idempotency, and prohibited-boundary check;
4. reject any changed watermark or non-PASS value;
5. insert the unique `HostWorkAcceptanceFactV0_1`;
6. append `ACTIVATE` on first acceptance when the permit is `ISSUED`;
7. reserve exactly the invocation ordinal; and
8. append the acceptance receipt at one event sequence.

Nothing outside that transaction is permitted to infer acceptance from an
advisory decision. Commit conflict, timeout, unavailable currentness, or an
unknown transaction outcome produces no new physical attempt. Recovery first
looks up the unique acceptance ID and compares fingerprints.

### 10.3 Crash matrix

| Crash point | Durable truth | Permitted recovery |
|---|---|---|
| before permit commit | no permit | re-evaluate issuance from current heads |
| permit commit, reply lost | unique permit may exist | look up by issuance envelope; never mint a second epoch blindly |
| before acceptance commit | no start authority | re-evaluate admission from current heads |
| acceptance commit, reply lost | unique acceptance may exist | look up by invocation identity and compare fingerprints |
| after acceptance, before F5 handoff | accepted but not proven started | recheck all fences and expiry; F5 policy decides whether a first handoff is safe |
| during or after F5 handoff | external start may be unknown | F5 outcome/recovery protocol; never infer success or safe retry from F4 |
| revocation races acceptance | serialization order is authoritative | earlier acceptance remains historical; later fence blocks a not-yet-started handoff |

No F4 state converts an unknown external outcome into `NOT_EXECUTED`, and no
retry permission follows merely from idempotency-key equality.

## 11. F3 Command seam without a self-hash cycle

F4 consumes an already committed F3 Command envelope whose accepted
`CommandTypeDefinitionV0_1.effect_class` is `EFFECT_INTENT`. It does not amend
the frozen F3 registry, reinterpret `LEDGER_ONLY` as physical authority, or
create a F4-owned production Command definition inside this subject.

The production type definition is supplied by the accepted owning domain or
control-plane contract and is independently bound into the F3 registry. Its
`owner_contract_sha256` is therefore an upstream fixed subject digest, not the
digest of this F4 file. This removes a same-subject digest cycle. F4 refuses:

- an unregistered, inactive, stale, or fingerprint-mismatched type definition;
- a definition whose owner contract is not accepted;
- any `LEDGER_ONLY`, `READ_ONLY`, or `CONTROL_TRANSITION` Command presented as
  an effect intent;
- a payload whose canonical fingerprint differs from the envelope; and
- a Command that bypasses F3 commitment, authenticated context, or immutable
  action provenance.

M0 fixtures may use a manifest-bound synthetic `EFFECT_INTENT` definition, but
that definition is test evidence only. It cannot enter the production registry
or authorize real work.

## 12. Revocation, compromise, and fence propagation

Revocation is an append-only authority loss. It never deletes or edits the
permit, acceptance, start-authority, or future outcome history.

```yaml
F4RevocationPropagationFactV0_1:
  interface_version: agents-os.f4-revocation-propagation-fact.v0.1
  propagation_id: stable_ref
  source_kind: TASK_CHANGE | ACTOR_REVOCATION | DELEGATION_REVOCATION | HOST_SUSPENSION | HOST_REVOCATION | HOST_COMPROMISE | PERMIT_REVOCATION | AUTHORIZATION_REVOCATION | POLICY_CHANGE | PROHIBITED_BOUNDARY_CHANGE | INCIDENT | JENN_KILL_SWITCH
  source_event_ref: stable_ref
  source_event_fingerprint: lowercase_sha256
  affected_task_id: stable_ref
  affected_task_lifecycle_generation: positive_safe_integer
  affected_host_id: stable_ref
  affected_effect_intent_ref: stable_ref
  advanced_fence_kind: TASK | HOST | EFFECT
  previous_generation: positive_safe_integer
  resulting_generation: positive_safe_integer
  resulting_fence_state_ref: stable_ref
  resulting_fence_state_fingerprint: lowercase_sha256
  propagation_result: APPLIED | IDEMPOTENT_REPLAY | INDETERMINATE
  event_sequence: non_negative_safe_integer
  fact_fingerprint: lowercase_sha256
```

For `APPLIED`, `resulting_generation = previous_generation + 1`. An identical
source event and affected scope is idempotent and returns the same resulting
head. Changed scope under the same propagation ID is an integrity failure.
`INDETERMINATE` disables affected admission until current projection is
reconstructed; it never means the old generation remains safely usable.

Minimum propagation is closed as follows:

| Source | Required immediate action |
|---|---|
| Task revision, completion, cancellation, commitment or dependency change | advance affected Task fence; supersede current permits |
| Actor, Principal, Binding, Assignment or Delegation authority loss | advance every affected effect fence; revoke affected permits |
| Host suspension, revocation or compromise | advance Host fence before later acceptance; reject Host authentication |
| Permit revocation | advance its effect fence; transition permit to REVOKED |
| Jenn authorization revocation/expiry | advance affected effect fence; revoke RED permits |
| Policy or Prohibited Behavior List change | advance every affected effect fence; require current policy re-evaluation |
| Incident or Jenn kill switch | advance the narrowest complete Task, Host and/or effect fences covering the stop scope |

If an affected-set query is unavailable, incomplete, or inconsistent, the
canonical writer places the containing admission domain in fail-closed
`INDETERMINATE` state before acknowledging propagation. A best-effort scan is
not a revocation guarantee.

Host compromise is stronger than session logout. The Host identity becomes
terminal `COMPROMISED`, its Host fence advances, every outstanding challenge
and authentication assessment becomes unusable, and no restart or credential
rotation revives the identity. Recovery requires a new Host identity lineage.

Revocation racing physical work cannot reverse an effect. If acceptance is
committed but no F5 handoff has occurred, the next host recheck returns
`NOT_STARTED / FENCED`. If a handoff may already have occurred, F4 records the
authority change and F5 determines `SUCCEEDED`, `FAILED`, or
`UNKNOWN_AFTER_CRASH`; F4 never relabels it `NOT_EXECUTED` from silence.

## 13. Exact F5 handoff and outcome boundary

F4 exports one sealed, read-only handoff object:

```yaml
F4AcceptedEffectHandoffV0_1:
  interface_version: agents-os.f4-accepted-effect-handoff.v0.1
  handoff_id: stable_ref
  acceptance_ref: stable_ref
  acceptance_fingerprint: lowercase_sha256
  start_disposition_ref: stable_ref
  start_disposition_fingerprint: lowercase_sha256
  invocation_identity: PermitInvocationIdentityV0_1
  task_permit_ref: stable_ref
  task_permit_fingerprint: lowercase_sha256
  effect_intent_ref: stable_ref
  effect_intent_fingerprint: lowercase_sha256
  owner_host_id: stable_ref
  owner_host_identity_revision: positive_safe_integer
  owner_host_authentication_epoch: positive_safe_integer
  execution_epoch: positive_safe_integer
  task_fence_generation: positive_safe_integer
  host_fence_generation: positive_safe_integer
  effect_fence_generation: positive_safe_integer
  start_authority_expires_at_utc_ms: positive_safe_integer
  capability_set_fingerprint: lowercase_sha256
  resource_set_fingerprint: lowercase_sha256
  secret_handle_set_fingerprint: lowercase_sha256
  permit_attestation_evidence_fingerprint: lowercase_sha256
  human_presence_binding_fingerprint: lowercase_sha256
  Jenn_authorization_binding_fingerprint: lowercase_sha256
  expected_result_contract_ref: stable_ref
  expected_result_contract_fingerprint: lowercase_sha256
  handoff_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256
```

The object may be emitted only for a `START_AUTHORITY_CURRENT` disposition and
before its expiry, in the same canonical transaction as that disposition.
Every field must equal the accepted permit and the transaction must reproduce
all current Host/epoch/fence, secret-handle, attestation, and applicable human-
presence checks. It contains no
raw payload, secret, provider response, callback, database handle, file
descriptor, process handle, or retry instruction.

`handoff_id =
SHA256(JCS(["agents-os.f4-accepted-effect-handoff-id.v0.1",
invocation_identity.canonical_fingerprint]))`. Exactly one handoff fingerprint
may exist per invocation identity. Identical replay returns it; changed bytes
under the same handoff ID are an integrity failure.

F5 may claim, dispatch, reconcile, and terminally account only this exact
invocation. It cannot change host, target, payload, capability, resource,
secret handle, epoch, fence, idempotency identity, expiry, or invocation
ordinal. A changed handoff fingerprint is a new unauthorized object, not an
amendment.

F5 returns a future immutable terminal accounting fact bound to the invocation
identity and one of:

```text
NOT_EXECUTED       positive evidence that no physical effect crossed the boundary
SUCCEEDED          result contract satisfied by current evidence
FAILED             physical attempt terminated without satisfying the result contract
UNKNOWN_AFTER_CRASH physical start or result cannot be ruled in or out
```

Absence of evidence, timeout, process death, lost response, transport
disconnect, provider ambiguity, or a committed start-authority fact cannot
produce `NOT_EXECUTED`. Only F5 terminal accounting may release the invocation
reservation. F4 transitions a permit to `CONSUMED` only when F5 has terminally
accounted every ordinal; `UNKNOWN_AFTER_CRASH` is terminal for automatic retry
purposes unless a later separately authorized recovery contract proves a safe
continuation.

## 14. Future N-API boundary

The future JavaScript surface is transport only. Rust remains the sole
authority evaluator and canonical writer. The closed method set is:

```yaml
F4NapiSurfaceV0_1:
  assessHostAuthentication:
    input: canonical HostAuthenticationAssessment request refs
    output: HostAuthenticationAssessmentV0_1
    writes: none
  prepareTaskPermitIssuance:
    input: committed F3 CommandEnvelope ref
    output: immutable issuance candidate or fail-closed decision
    writes: none
  commitTaskPermitIssuance:
    input: issuance candidate fingerprint
    output: TaskPermitIssuanceFactV0_1 or fail-closed decision
    writes: Rust canonical transaction only
  assessTaskPermitCurrentness:
    input: TaskPermit ref and trusted-time input
    output: TaskPermitCurrentnessAssessmentV0_1
    writes: none
  decideHostLocalAdmission:
    input: HostLocalAdmissionRequestV0_1
    output: HostLocalAdmissionDecisionV0_1
    writes: none
  commitHostWorkAcceptance:
    input: admission decision fingerprint
    output: HostWorkAcceptanceFactV0_1 or fail-closed decision
    writes: Rust canonical transaction only
  observeStartAuthority:
    input: HostWorkAcceptanceFact ref
    output: HostWorkStartDispositionFactV0_1 and, only on START_AUTHORITY_CURRENT, F4AcceptedEffectHandoffV0_1
    writes: one append-only Rust disposition/handoff transaction
  getAcceptedEffectHandoff:
    input: HostWorkStartDispositionFact ref
    output: already-committed F4AcceptedEffectHandoffV0_1 or fail-closed decision
    writes: none
```

Every input is canonical parsed data or a stable reference, never an SQL
fragment, filesystem path with ambient authority, executable callback, raw
credential, raw secret, provider client, database connection, or arbitrary
native handle. JavaScript cannot provide a claimed currentness result, override
a fence, select a writer, supply an event sequence, mark a permit consumed, or
convert an error into admission.

The implementation must use the frozen F3 singleton Resident connection and
writer identity. Opening an F4 side connection, secondary writer, direct table
write, alternate native addon, or JavaScript-maintained authority cache is a
dual-writer violation.

This section freezes an interface boundary only. It does not authorize or
claim an N-API, Rust, database, service, host, provider, or runtime
implementation.

## 15. Proof DAG and constructive M0-A witness

### 15.1 Acyclic authority graph

```text
F1 Task / commitment / dependency heads -------------------+
F2 Actor / identity / responsibility / delegation heads ---+
F3 Resident / Command / authenticated context heads -------+
Host identity / authentication / revocation heads ---------+--> TaskPermit
Policy / PBL / Jenn authorization / current fences --------+

TaskPermit + all current heads --> CurrentnessAssessment
CurrentnessAssessment + exact request --> LocalAdmissionDecision
LocalAdmissionDecision + atomic re-read --> HostWorkAcceptanceFact
Acceptance + host-local recheck --> StartDisposition
StartDisposition + immutable accepted scope --> F5 handoff
F5 terminal evidence --> invocation accounting --> permit consumption
```

No downstream node proves an upstream node. In particular:

- a permit does not prove current Task, Actor, Resident, Host, policy, or fence;
- an admission decision does not prove acceptance;
- acceptance does not prove physical start;
- a start-authority disposition does not prove effect outcome;
- an Outbox item or provider response does not prove authority; and
- Task completion never retroactively proves effect validity.

Fingerprints bind already-materialized canonical bytes or upstream fixed
digests. No subject includes its own digest, no definition fingerprint depends
on the manifest that contains it, and no review result is an input to the
subject it reviews.

### 15.2 M0-A witness constraints

The required witness uses only synthetic, non-secret, non-provider objects:

```yaml
M0A_F4_WITNESS_V0_1:
  task_id: task:m0-a:f4:001
  task_lifecycle_generation: 1
  task_completion_epoch: 0
  execution_epoch: 1
  actor_id: actor:m0-a:synthetic
  principal_id: principal:m0-a:synthetic
  resident_identity_ref: resident:m0-a:synthetic
  resident_epoch: 1
  command_id: command:m0-a:effect-intent:001
  command_effect_class: EFFECT_INTENT
  host_id: host:m0-a:synthetic
  host_kind: SYNTHETIC_M0_HOST
  host_identity_revision: 1
  host_authentication_epoch: 1
  task_fence_generation: 1
  host_fence_generation: 1
  effect_fence_generation: 1
  invocation_ordinal: 1
  max_invocations: 1
  side_effect_class: GREEN
  Jenn_authorization_mode: NOT_REQUIRED
  requires_human_presence: false
  human_presence_mode: NOT_REQUIRED
  secret_handle_bindings: []
  resource_kind: SYNTHETIC_M0_RESOURCE
  external_effect_execution: false
  expected_terminal_outcome: NOT_EXECUTED
```

The witness must materialize and hash, in topological order:

1. current F1 Task authority, commitment, dependency, and assurance fixtures;
2. current F2 Actor authority and synthetic authentication fixtures;
3. current F3 Resident continuity, synthetic `EFFECT_INTENT` definition,
   Command, authenticated context, immutable action, and envelope fixtures;
4. ACTIVE synthetic Host identity and MATCH authentication assessment;
5. genesis Task, Host, and effect fence heads;
6. GREEN synthetic effect intent, exact capability, and exact resource grant;
7. immutable one-invocation TaskPermit and issuance fact;
8. VALID currentness assessment at one watermark;
9. exact admission request and ADMITTED decision;
10. unique committed Host work acceptance;
11. `START_AUTHORITY_CURRENT` host disposition;
12. the exact immutable accepted-effect handoff; and
13. a synthetic F5 boundary stub that performs no effect and positively
    returns `NOT_EXECUTED` for fixture validation only.

The machine fixture and its validator are subjects of the R1 atomic review
bundle. A witness passes only when every declared SHA-256 recomputes from
canonical bytes, every edge points to an earlier node, all exact bindings
match, every generation/epoch is current, one acceptance exists, and the
external-effect counter remains exactly zero. A prose assertion is not a
constructive witness.

## 16. Required adversarial decisions

Every conforming implementation and independent review must produce the
following exact fail-closed decisions. “Reject” includes a durable integrity
incident where the input conflicts with an already committed identity.

| # | Adversarial case | Required decision |
|---:|---|---|
| 1 | Prompt claims Jenn approved an effect but no current authorization fact exists | reject RED; prompt has no authority |
| 2 | P3b behavior appears with a purported signed approval | reject permanently; no permit is issuable |
| 3 | Current Task state cannot be read | `INDETERMINATE`; no issuance or acceptance |
| 4 | Commitment or dependency snapshot changed after issuance | currentness `REJECTED`; advance/satisfy Task fence policy |
| 5 | Completion assurance version changed | currentness `REJECTED`; old permit cannot revive |
| 6 | Actor identity is copied with a different revision | reject identity/fingerprint mismatch |
| 7 | Delegation is expired, revoked, over-depth, or scope-mismatched | reject authority binding |
| 8 | Actor authentication exists but Host authentication does not | reject Host admission |
| 9 | Host authentication exists but Actor authority is stale | reject permit/currentness |
| 10 | Host presents an old challenge response | authentication `REJECTED` |
| 11 | Host revocation projection is unavailable | authentication/currentness `INDETERMINATE` |
| 12 | Host is ACTIVE but credential profile fingerprint changed | authentication `REJECTED` |
| 13 | Host is COMPROMISED then restarts with the same identity | reject; terminal identity cannot revive |
| 14 | Permit target host differs from accepting host | admission `REJECTED` |
| 15 | JavaScript claims a different Host ID for the same native connection | reject; Rust-bound identity wins |
| 16 | Permit capability omits requested operation | admission `REJECTED` |
| 17 | Resource uses wildcard, implicit child, or ambient environment authority | reject issuance/admission |
| 18 | Effect payload bytes differ while payload fingerprint is reused | reject integrity conflict |
| 19 | Command definition effect class is `LEDGER_ONLY` | reject as non-effect-intent |
| 20 | Command owner contract or registry revision is stale | reject issuance |
| 21 | Resident epoch changes between Command intake and permit commit | reject issuance |
| 22 | Resident epoch changes between permit and acceptance | currentness/admission `REJECTED` |
| 23 | Any Task, Host, or effect fence is lower or higher than the permit | currentness/admission `REJECTED` |
| 24 | Fence head cannot be reproduced at one watermark | `INDETERMINATE`; no acceptance |
| 25 | Clock is unavailable, rolls back, or is outside the trusted profile | `INDETERMINATE` or `REJECTED`; never extend validity |
| 26 | Permit is before `not_before` or at/after expiry | `REJECTED` |
| 27 | Acceptance occurs after `start_authority_commit_before` | reject acceptance |
| 28 | Start recheck occurs at/after start-authority expiry | `NOT_STARTED / EXPIRED` |
| 29 | Same invocation identity is replayed byte-for-byte | return the same committed facts |
| 30 | Same invocation identity carries changed bytes | reject protocol conflict |
| 31 | Two hosts race one invocation | at most the exact owner Host can commit; unique acceptance wins |
| 32 | Two writer connections race acceptance | dual-writer/integrity failure; no second acceptance |
| 33 | Acceptance transaction outcome is unknown | look up unique ID; do not start or blindly retry |
| 34 | Crash occurs after acceptance but before F5 handoff | accepted, not proven started; recheck current authority |
| 35 | Crash occurs during F5 handoff | F5 `UNKNOWN_AFTER_CRASH` unless positive terminal evidence exists |
| 36 | Provider reports success without matching accepted handoff | no authority and no F4 outcome proof |
| 37 | Outbox item exists without F4 acceptance | no authority to dispatch |
| 38 | Revocation races acceptance and orders first | acceptance rejects |
| 39 | Acceptance orders first and revocation follows before handoff | historical acceptance remains; host recheck is fenced |
| 40 | Revocation propagation cannot enumerate all affected permits | containing domain fails closed |
| 41 | Database restore exposes an older fence generation | reject stale head; no resurrection |
| 42 | Permit fingerprint verifies but attestation evidence is missing | reject or `INDETERMINATE`; fingerprint alone is insufficient |
| 43 | Secret value is embedded instead of a bound handle | reject and do not persist/expose it |
| 44 | Secret handle owner differs from accepted Host | reject scope mismatch |
| 45 | UI, network origin, IPC possession, or process identity is offered as proof | reject substitute evidence |
| 46 | Unknown enum, schema revision, digest profile, or extra field appears | reject canonical input |
| 47 | A later F5 result attempts to widen permit scope | reject; downstream evidence cannot amend authority |
| 48 | M0 fixture attempts a real file, process, network, device, provider, or secret effect | fixture fails; external-effect count must remain zero |
| 49 | Human presence is required but only UI focus, session activity, a prompt, or stale presence evidence exists | admission/handoff rejects or is `INDETERMINATE` |

## 17. Normative invariants

The following 64 invariants are independently countable acceptance criteria.

### 17.1 Authority and provenance (I01-I08)

1. **I01** Every permit binds one exact current F1 Task authority snapshot.
2. **I02** Every permit binds one exact current F2 Actor authority snapshot.
3. **I03** Every permit binds one exact current F3 Resident and Command snapshot.
4. **I04** Every permit binds one exact Host identity revision and authenticator profile.
5. **I05** Every effect intent is an accepted F3 `EFFECT_INTENT` Command, never a prompt or callback.
6. **I06** Responsibility, action provenance, and prohibited-boundary evidence remain explicit.
7. **I07** P3a requires exact current Jenn authorization bound to the exact effect scope.
8. **I08** P3b can never be represented as issuable authority.

### 17.2 Canonical identity and immutability (I09-I16)

9. **I09** Every identity and fingerprint uses the closed canonical value profile.
10. **I10** Unknown fields, enum values, algorithms, or revisions reject.
11. **I11** Permit ID is derived from the declared immutable identity tuple under its domain separator; the full permit fingerprint detects any changed non-identity field.
12. **I12** A permit has revision 1 only and is never amended.
13. **I13** Changed authority, target, payload, or constraints require a new permit and execution epoch.
14. **I14** One issuance Command envelope maps to at most one permit fingerprint.
15. **I15** One invocation identity maps to at most one acceptance fingerprint.
16. **I16** Downstream evidence cannot rewrite or broaden upstream authority.

### 17.3 Currentness and time (I17-I24)

17. **I17** Issuance and acceptance re-read all authority at one reproducible watermark.
18. **I18** `VALID` and `ADMITTED` require every applicable check PASS.
19. **I19** Missing, conflicting, stale, or unavailable currentness is fail-closed `INDETERMINATE`.
20. **I20** A proven negative is `REJECTED`, not `INDETERMINATE` or PASS.
21. **I21** Permit validity is bounded by trusted time and never extended by clock rollback.
22. **I22** Acceptance commits before its deadline and before permit expiry.
23. **I23** Start authority is rechecked before handoff and may have a shorter expiry.
24. **I24** Expiry cannot be undone by restart, replay, restore, or projection rebuild.

### 17.4 Host identity and authentication (I25-I32)

25. **I25** Actor authentication and Host authentication are separate required facts.
26. **I26** Only the exact ACTIVE owner Host identity may accept a permit.
27. **I27** Host authentication binds identity, revision, profile, challenge, verifier, time, and revocation head.
28. **I28** Suspended, revoked, compromised, retired, expired, or indeterminate Hosts cannot accept.
29. **I29** Compromised and retired Host identities are terminal and never revived.
30. **I30** A new Host identity lineage is required after compromise.
31. **I31** Host attestations carry references/fingerprints, never credential values.
32. **I32** IPC, hostname, session, process, network, or UI possession is not Host authentication.

### 17.5 Capability and resource bounds (I33-I40)

33. **I33** Capabilities are exact named operation subsets; ambient authority is denied.
34. **I34** Resources are exact named subjects with exact selectors and operations.
35. **I35** Wildcards, implicit descendants, arbitrary shell text, and provider-wide grants reject.
36. **I36** Effect target, payload, result contract, idempotency identity, and side-effect class are immutable.
37. **I37** Secret bindings are opaque current handles owned by the exact Host and exact permitted use, with exact revision and revocation head.
38. **I38** Raw secrets, credentials, cookies, private content, or provider responses never enter F4 subjects.
39. **I39** Required human presence is exact, scope-bound, current, time-bounded evidence and is rechecked at handoff.
40. **I40** Permit scope is the intersection of all upstream authority and can never exceed any input.

### 17.6 Admission and single-writer commitment (I41-I48)

41. **I41** Local admission decision is pure advisory evidence and grants no start authority.
42. **I42** Only the Rust canonical writer may commit Host work acceptance.
43. **I43** Acceptance atomically rechecks currentness and reserves one exact invocation.
44. **I44** No external work object or physical effect may exist before acceptance commits.
45. **I45** First acceptance activates an ISSUED permit in the same authoritative ordering.
46. **I46** Physical handoff requires a current authenticated Host recheck after acceptance.
47. **I47** `START_AUTHORITY_CURRENT` proves current authority at handoff, not physical effect or result.
48. **I48** JavaScript cannot choose writer identity, event sequence, currentness, fence, or admission result.

### 17.7 Fences and revocation (I49-I56)

49. **I49** Task, Host, and effect fences are monotonic append-only positive generations.
50. **I50** Each fence advance is exactly one generation through the canonical writer.
51. **I51** Permit generations must equal all current fence heads at issuance, acceptance, and handoff.
52. **I52** An old generation never becomes current again.
53. **I53** Revocation preserves historical facts and removes only future authority.
54. **I54** Host compromise immediately rejects authentication and advances the Host fence.
55. **I55** Incomplete revocation propagation fails the containing admission domain closed.
56. **I56** A revocation after possible physical start cannot relabel the outcome `NOT_EXECUTED`.

### 17.8 Replay, crash, outcome, and phase boundary (I57-I64)

57. **I57** Identical issuance and acceptance replays return the same facts.
58. **I58** Changed bytes under a committed identity are protocol conflicts.
59. **I59** Unknown transaction outcomes are resolved by unique-key lookup before any retry.
60. **I60** Acceptance alone never proves physical start, success, failure, or non-execution.
61. **I61** Absence, timeout, disconnect, or crash never proves `NOT_EXECUTED`.
62. **I62** F5 may account only the exact immutable accepted handoff and cannot mint authority.
63. **I63** `UNKNOWN_AFTER_CRASH` grants no automatic retry authority.
64. **I64** F4 acceptance authorizes no implementation, database, service, runtime activation, provider call, production authentication, F5, or F6.

## 18. Review gate, acceptance unit, and stop condition

The R1 atomic subject set is exactly:

```text
1. this F4 R1 contract
2. one canonical synthetic M0-A witness fixture
3. one deterministic offline witness validator
```

The review manifest must bind the exact path and actual SHA-256 of all three
subjects and the F4 start decision. A fresh independent reviewer must recompute
every subject hash, run the validator without network/provider/runtime effects,
and review the complete atomic diff against the fixed F1/F2/F3 prerequisites.

The review must explicitly report:

```text
subject hashes: 3 / 3
proof DAG: PASS or BLOCK
M0-A witness: PASS or BLOCK
external-effect count: 0 or BLOCK
adversarial decisions: 49 / 49 or exact blockers
normative invariants: 64 / 64 or exact blockers
identity spoofing blockers
authority expansion blockers
revocation / compromise bypass blockers
fail-open currentness blockers
dual-writer blockers
circular-proof blockers
crash/replay ambiguity blockers
internal contradictions
implementation or downstream authority leakage
```

`PASS_NO_BLOCKER` makes the atomic bundle eligible for Jenn's later exact
acceptance/freeze decision. It does not itself accept or freeze F4. Any blocker
requires a scoped R2 amendment and a new full atomic hash-bound review. Partial
acceptance, report-only acceptance, subject substitution, or acceptance of only
the prose contract is forbidden.

F4 stops when TaskPermit, Host identity/authentication, Host-local admission,
fence/revocation, crash/replay, F3/F5 seams, and the zero-effect M0-A witness are
semantically closed with no blocker. Implementation profile questions, real
cryptography/key custody, Rust/database/index/performance work, F5 delivery,
F6 validation, runtime activation, provider readiness, production
authentication, and service startup do not by themselves require an F4
amendment.

Until Jenn accepts the complete hash-bound unit:

```yaml
F4_semantic_freeze: false
implementation_authorized: false
database_authorized: false
Resident_start_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
provider_or_service_authorized: false
F5_started: false
F6_started: false
commit_or_push_authorized_by_this_contract: false
```
