# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R6 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R5 amendment SHA-256: `90715a14279af382d3286e5024bc6cd136447c7f7e42930ebb05aa7c381bb047`  
Blocking R5 review SHA-256: `aae988bcbd98199a3e56a5225e895d5f6755ad8f6c6c27ce51432ebadb915517`

## 1. Scope and precedence

R6 closes only `F4-R5-FULL-ATOMIC-IR-B01` through `B05`. Effective order is
R6, R5, R4, R3, R2, R1. All fifteen R1-R5 subjects remain immutable. The
effective acceptance literal is
`F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R6_ATOMIC_BUNDLE`.

## 2. Total effect-authorization resolution and canonical matrix

Before an authorization-requirement object exists, the canonical evaluator
returns this non-persisted transport result:

```yaml
EffectAuthorizationRequirementResolutionV0_1R6:
  outcome: REQUIREMENT_RESOLVED | NO_REQUIREMENT_OBJECT
  reason: RESOLVED | MODE_INPUT_UNAVAILABLE | MODE_INPUT_INTEGRITY_CONFLICT | INVALID_INPUT
  requirement_fingerprint: lowercase_sha256 | null
```

`REQUIREMENT_RESOLVED / RESOLVED` is the sole pair with a non-null fingerprint.
Every other reason pairs only with `NO_REQUIREMENT_OBJECT` and null. A no-object
result has no ledger identity, permit, currentness claim, handoff, authority,
or effect. Policy/PBL/basis unavailability cannot be coerced to a mode.

R6 adds `currentness_reason` to the R5 requirement and freezes this complete
matrix:

| Derived mode/evidence | Jenn fields | currentness | currentness_reason | issuance |
|---|---|---|---|---|
| `NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED` | all null | `NOT_APPLICABLE` | `NO_SEPARATE_REQUIRED` | eligible if all other checks pass |
| `EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED`, exact decision current | all non-null | `CURRENT` | `JENN_DECISION_CURRENT` | eligible if all other checks pass |
| same mode, reproducibly no decision | all null | `REJECTED` | `JENN_DECISION_MISSING` | reject |
| same mode, present but scope mismatch | decision identity fields non-null; time/revocation as observed | `REJECTED` | `JENN_SCOPE_MISMATCH` | reject |
| same mode, present but expired | all non-null | `REJECTED` | `JENN_DECISION_EXPIRED` | reject |
| same mode, present but revoked | all non-null | `REJECTED` | `JENN_DECISION_REVOKED` | reject |
| `PROHIBITED_NON_ISSUABLE` | all null | `REJECTED` | `PROHIBITED` | permanently non-issuable |

The closed reason enum is exactly the seven reasons printed above. If exact
mode has potentially relevant decision evidence but its existence, bytes,
scope, time, or revocation state cannot be reproduced, resolution is
`NO_REQUIREMENT_OBJECT / MODE_INPUT_UNAVAILABLE`; no requirement fingerprint
is created. Any other tuple rejects as non-canonical.

R6 explicitly replaces every surviving R1/R5 downstream reference:

```text
Jenn_authorization_binding_fingerprint
  -> effect_authorization_requirement_fingerprint
Jenn authorization deadline/currentness
  -> exact current R6 requirement deadline/currentness when mode requires it
```

This replacement applies to TaskPermit, currentness, admission, acceptance,
start disposition, `F4AcceptedEffectHandoff`, physical-boundary seam, outcome
binding, fingerprints, fixtures, and all prose/invariants.

## 3. Frozen F2 RECOVER compatibility and separate F4 eligibility

R6 withdraws any claim that frozen F2 Actor `COMPROMISED` is terminal. Frozen
F2 alone decides its lifecycle and may accept `RECOVER -> ACTIVE` under its
existing typed authority and assurance rules.

F4 separately derives:

```yaml
F4HostEffectTrustEligibilityAssessmentV0_1R6:
  host_actor_identity_ref: stable_ref
  host_actor_identity_fingerprint: lowercase_sha256
  current_F2_actor_assessment_ref: stable_ref
  current_F2_actor_assessment_fingerprint: lowercase_sha256
  F2_compromise_history_head_ref: stable_ref
  F2_compromise_history_head_fingerprint: lowercase_sha256
  F4_host_trust_head_ref: stable_ref
  F4_host_trust_head_fingerprint: lowercase_sha256
  result: ELIGIBLE | INELIGIBLE | INDETERMINATE
  reason: NEVER_COMPROMISED_AND_ALL_CURRENT | F2_COMPROMISE_HISTORY_PRESENT | F4_COMPROMISE_HISTORY_PRESENT | CURRENT_F2_INPUT_UNAVAILABLE | HISTORY_UNAVAILABLE | INTEGRITY_FAILURE
  assessment_fingerprint: lowercase_sha256
```

A same-lineage F2 Actor may be validly recovered and ACTIVE in F2 while being
`INELIGIBLE` for F4 effect trust because its exact compromise history remains.
This does not relabel, amend, or contradict F2. F4 Host authentication requires
`ELIGIBLE / NEVER_COMPROMISED_AND_ALL_CURRENT`. New F4 eligibility after
compromise requires a new F2 EXECUTION_HOST Actor identity and new F4 Host
trust lineage; it is an F4 admission rule only.

## 4. Complete effective start disposition and handoff schemas

R6 replaces the effective `HostWorkStartDispositionFact` field list with this
exact order:

```yaml
HostWorkStartDispositionFactV0_1R6:
  interface_version: agents-os.host-work-start-disposition-fact.v0.1-r6
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
  final_handoff_authority_assessment_ref: stable_ref
  final_handoff_authority_assessment_fingerprint: lowercase_sha256
  secret_handles_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  permit_attestation_current: PASS | REJECTED | INDETERMINATE
  human_presence_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  final_handoff_authority_current: PASS | REJECTED | INDETERMINATE
  disposition: START_AUTHORITY_CURRENT | NOT_STARTED | INDETERMINATE
  reason: ALL_RECHECKS_PASS | INTEGRITY_FAILURE | AUTHORITY_STALE | HOST_UNAUTHENTICATED | FENCED | EPOCH_STALE | EXPIRED | SECRET_HANDLE_STALE | ATTESTATION_STALE | HUMAN_PRESENCE_STALE | OBSERVATION_UNAVAILABLE
  observed_at_utc_ms: non_negative_safe_integer
  observation_event_sequence: non_negative_safe_integer
  host_observation_attestation_ref: stable_ref
  host_observation_attestation_fingerprint: lowercase_sha256
  fact_fingerprint: lowercase_sha256
```

`fact_fingerprint = SHA256(JCS(["agents-os.host-work-start-disposition-fact.v0.1-r6", every preceding field value in printed order]))`.
The R5 twelve-check reducer and precedence apply. The assessment fingerprint
must equal the referenced exact same-watermark assessment; mismatch is
`INTEGRITY_FAILURE`.

R6 replaces the effective accepted handoff field list only by adding, in this
exact position after `human_presence_binding_fingerprint`:

```text
effect_authorization_requirement_fingerprint
final_handoff_authority_assessment_fingerprint
```

The old `Jenn_authorization_binding_fingerprint` field is removed. All later
R1 handoff fields retain their order. The handoff canonical fingerprint covers
the complete resulting list and therefore binds the exact final assessment.

## 5. Canonical authority/source-set entries and formulas

R6 replaces R5 bare source ref arrays with:

```yaml
AuthoritySourceBindingV0_1R6:
  role: F1_TASK | F2_RESPONSIBILITY | F2_DELEGATION | F3_COMMAND | POLICY | PROHIBITED_BEHAVIOR_LIST | JENN_DECISION
  source_ref: stable_ref
  source_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

The entry fingerprint is
`SHA256(JCS(["agents-os.f4-authority-source-binding.v0.1-r6", role, source_ref, source_fingerprint]))`.
Entries sort by UTF-8 bytes of `role`, then `source_ref`, then fingerprint.
Duplicate role/ref pairs or duplicate entry fingerprints reject.

Every capability and resource set requires exactly one each of `F1_TASK`,
`F2_RESPONSIBILITY`, `F3_COMMAND`, `POLICY`, and
`PROHIBITED_BEHAVIOR_LIST`; it requires exactly one `F2_DELEGATION` when the
actor authority binding uses delegation and forbids it otherwise; it requires
exactly one `JENN_DECISION` only for a current exact-Jenn authorization mode
and forbids it otherwise. Missing or extra roles reject.

```text
source_authority_set_fingerprint =
  SHA256(JCS(["agents-os.f4-capability-source-authority-set.v0.1-r6",
              sorted_authority_source_binding_fingerprints]))

source_scope_set_fingerprint =
  SHA256(JCS(["agents-os.f4-resource-source-scope-set.v0.1-r6",
              sorted_authority_source_binding_fingerprints]))
```

The capability subset proof and resource containment assessment MUST bind the
corresponding exact set fingerprint, definition fingerprint, operation
registry fingerprint, operation set, and constraint/selector fingerprint.

## 6. Full effective R6 M0-A materialization

R6 adds a complete zero-effect overlay witness. It first verifies the exact
immutable R1 M0-A fixture and validator result, then materializes every R5/R6
replacement in one acyclic graph: authorization resolution and requirement,
F2 Host Actor/Principal/Binding extension, F4 effect-trust eligibility, Host
trust and authentication, capability/resource source bindings and grants,
single-invocation permit, full final authority assessment, acceptance, the
complete R6 disposition, the R6 handoff, and a no-effect boundary stub.

Each overlay node binds the immutable R1 base-fixture file and canonical
digests plus every predecessor fingerprint. No replaced R1 object is treated
as effective output. The final stub is `NOT_EXECUTED`, external-effect,
provider-call, and raw-secret counts are zero, and it grants no F5 authority.

The R6 fixture and validator are new subjects. All earlier validators remain
historical/focused evidence. Only a fresh review of all eighteen subjects may
judge full effective constructibility.

## 7. Gate and non-authorization

The next gate is a fresh full atomic hash-bound independent review of R1-R6.
Partial acceptance is forbidden. Only Jenn may later accept/freeze F4.
Nothing here starts F5/F6 or authorizes implementation, runtime, database,
service, Host, provider, authentication, credentials, keys, physical effects,
commit, push, merge, release, or deploy.
