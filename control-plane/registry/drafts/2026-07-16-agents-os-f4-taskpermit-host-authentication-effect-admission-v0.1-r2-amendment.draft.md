# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R2 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R1 contract SHA-256: `3378396108f090469984facb8ddcb238ae122be9cab71afe2f8c3bd1cd577db3`  
Base R1 M0-A fixture SHA-256: `e13f501ebf5d120778a9971f9d5884764b8635a557dc2fa387f3adfb0873fd75`  
Base R1 validator SHA-256: `a39b860c627124c0c0304a5bca51bda6fa806d0f7c778078706e60c9235e89aa`  
Blocking R1 independent-review SHA-256: `8de188ef677113e288a5df1a0f73591e884c1fee04b5d167291eb9f4288263a0`

## 1. Scope, precedence, and fixed inputs

This is the narrow R2 correction for
`F4-R1-FULL-ATOMIC-IR-B01`. It closes only deterministic result and reason
selection for:

```text
HostAuthenticationAssessmentV0_1
TaskPermitCurrentnessAssessmentV0_1
HostLocalAdmissionDecisionV0_1
R1 invariants I19 and I20
mixed negative/unavailable and multiple-negative adversarial evidence
```

The effective reading order is:

```text
1. R2 explicit replacements
2. R1 all other clauses
3. frozen F3 R1-R4 atomic bundle for F3-owned definitions and writer authority
4. frozen F2 R1-R22 atomic bundle for F2-owned identity and delegation authority
5. accepted F1 contract for F1-owned Task and commitment authority
```

The effective acceptance literal is:

```text
F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R2_ATOMIC_BUNDLE
```

R1, its M0-A fixture, its validator, and the R1 independent review remain
immutable inputs. R2 does not alter any R1 success-path field order, fingerprint
formula, identifier, acceptance, handoff, replay, crash, writer, or boundary
rule. Every R1 clause not explicitly replaced here remains in force.

This document creates no implementation, database, runtime, Resident, service,
production-authentication, credential, provider, Host-executor, external-effect,
F5, or F6 authority.

## 2. Total tri-state reducer shared rule

This section replaces the result-selection sentences in R1 Sections 5.2, 7.2,
and 9.2. Each reducer first decodes only its closed schema and normalizes every
applicable evidence observation into exactly one of:

```text
PASS
NOT_APPLICABLE  only where the R1 field enum explicitly permits it
REJECTED        a reproducibly proven negative
INDETERMINATE   required evidence is absent, unreadable, unavailable, or not reproducible
```

Unknown fields, unknown enum values, invalid `NOT_APPLICABLE`, invalid field
types, or invalid canonical bytes reject before a canonical assessment or
decision can be emitted. They are not caller-selectable reducer inputs.

For every schema-valid normalized tuple, the sole result lattice is:

```text
1. If any applicable observation is REJECTED, emit the reducer's REJECTED result.
2. Else if any applicable observation is INDETERMINATE, emit INDETERMINATE.
3. Else, only if every applicable observation is PASS or permitted
   NOT_APPLICABLE, emit AUTHENTICATED, VALID, or ADMITTED respectively.
```

Therefore a proven negative always dominates every concurrent unavailable or
unknown input. Known stale, revoked, expired, mismatched, denied, prohibited,
or exhausted evidence is `REJECTED`; it is never `INDETERMINATE`. An
unavailable input cannot hide or downgrade a separately proven negative.

Reason selection is not caller supplied. The evaluator builds the closed
candidate set defined below and chooses the first candidate in the applicable
ordered precedence list. A candidate cannot appear unless its mapped predicate
is true. Duplicate candidates collapse. Thus each schema-valid normalized
tuple has exactly one result and one reason.

Evidence conflict has only two closed meanings:

```text
reproducibly proven incompatible canonical facts at one claimed watermark
  -> REJECTED / INTEGRITY_FAILURE

facts cannot be obtained or reproduced well enough to prove compatibility or incompatibility
  -> INDETERMINATE using the reducer's closed unavailable reason,
     but only when no proven negative candidate exists
```

No generic word such as `stale`, `conflicting`, or `unavailable` may override
these rules.

## 3. Host authentication totality

This section replaces only the result/reason derivation prose of R1 Section
5.2. The schema, field order, fingerprint coverage, authentication-epoch
allocation, and all other R1 Host rules remain unchanged.

### 3.1 Closed observation classes

The canonical verifier derives these reason candidates:

| Candidate | Class | Exact predicate |
|---|---|---|
| `INTEGRITY_FAILURE` | REJECTED | canonical bytes, bound fingerprint, revision linkage, or same-watermark facts are reproducibly incompatible |
| `COMPROMISED` | REJECTED | the current Host revision or authentication lineage has a current compromise fact |
| `REVOKED` | REJECTED | the current revocation head proves this Host revision or authentication epoch revoked |
| `RETIRED` | REJECTED | the bound Host revision is retired |
| `SUSPENDED` | REJECTED | the bound Host revision is suspended |
| `PROFILE_MISMATCH` | REJECTED | the verifier or authenticator profile does not equal the bound current profile |
| `CHALLENGE_MISMATCH` | REJECTED | the response does not bind the exact current challenge |
| `EXPIRED` | REJECTED | trusted time is at or after an applicable exclusive expiry bound |
| `NOT_YET_VALID` | REJECTED | trusted time is before an applicable inclusive validity start |
| `REVOCATION_UNAVAILABLE` | INDETERMINATE | the required revocation head cannot be read reproducibly |
| `VERIFIER_UNAVAILABLE` | INDETERMINATE | the required verifier or verification evidence cannot be read reproducibly |
| `UNKNOWN` | INDETERMINATE | another required Host-authentication fact is unavailable and no more specific unavailable candidate applies |
| `MATCH` | PASS | every R1-required Host identity, profile, challenge, trusted-time, epoch, evidence, and revocation predicate passes |

`MATCH` cannot coexist with a non-PASS candidate in a canonical candidate set.
If raw inputs imply both, `INTEGRITY_FAILURE` is added and `MATCH` is removed.

### 3.2 Exact Host reason precedence

For `REJECTED`, choose the first present candidate in this exact order:

```text
INTEGRITY_FAILURE
COMPROMISED
REVOKED
RETIRED
SUSPENDED
PROFILE_MISMATCH
CHALLENGE_MISMATCH
EXPIRED
NOT_YET_VALID
```

If there is no rejected candidate and result is `INDETERMINATE`, choose:

```text
REVOCATION_UNAVAILABLE
VERIFIER_UNAVAILABLE
UNKNOWN
```

Only the all-positive state emits `AUTHENTICATED / MATCH`.

## 4. TaskPermit currentness totality

This section replaces the effective `reason` enum and the result/reason
derivation prose of R1 Section 7.2. The effective closed reason enum is:

```text
ALL_CURRENT
INTEGRITY_FAILURE
PROHIBITED
TERMINAL
EXPIRED
NOT_YET_VALID
INVOCATIONS_EXHAUSTED
TASK_STALE
ACTOR_STALE
COMMAND_STALE
HOST_STALE
AUTH_STALE
POLICY_STALE
CAPABILITY_STALE
RESOURCE_STALE
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
AUTHORIZATION_STALE
EPOCH_STALE
FENCE_STALE
UNAVAILABLE
```

R2 adds the five values `CAPABILITY_STALE`, `RESOURCE_STALE`,
`SECRET_HANDLE_STALE`, `ATTESTATION_STALE`, and
`HUMAN_PRESENCE_STALE`; this closes explicit reason coverage for all 19
currentness checks. The field position and fingerprint coverage remain the R1
field position and coverage.

### 4.1 Exact check-to-reason mapping

| Proven negative predicate | Candidate reason |
|---|---|
| reproducible canonical/fingerprint/same-watermark incompatibility | `INTEGRITY_FAILURE` |
| `prohibited_boundary_current = REJECTED` | `PROHIBITED` |
| lifecycle `REVOKED` or `SUPERSEDED` | `TERMINAL` |
| lifecycle `EXPIRED` | `EXPIRED` |
| lifecycle `CONSUMED` | `INVOCATIONS_EXHAUSTED` |
| `task_binding_current = REJECTED` | `TASK_STALE` |
| `actor_binding_current = REJECTED` | `ACTOR_STALE` |
| `resident_command_binding_current = REJECTED` | `COMMAND_STALE` |
| `host_identity_current = REJECTED` | `HOST_STALE` |
| `host_authentication_current = REJECTED` | `AUTH_STALE` |
| `policy_current = REJECTED` | `POLICY_STALE` |
| `capability_grants_current = REJECTED` | `CAPABILITY_STALE` |
| `resource_grants_current = REJECTED` | `RESOURCE_STALE` |
| `secret_handle_bindings_current = REJECTED` | `SECRET_HANDLE_STALE` |
| `permit_attestation_current = REJECTED` | `ATTESTATION_STALE` |
| `human_presence_current = REJECTED` | `HUMAN_PRESENCE_STALE` |
| `Jenn_authorization_current = REJECTED` | `AUTHORIZATION_STALE` |
| `time_window_current = REJECTED` and trusted time is before `not_before_utc_ms` | `NOT_YET_VALID` |
| `time_window_current = REJECTED` and trusted time is at or after `expires_at_utc_ms` | `EXPIRED` |
| `invocation_available = REJECTED` | `INVOCATIONS_EXHAUSTED` |
| `execution_epoch_current = REJECTED` | `EPOCH_STALE` |
| any of `host_fence_current`, `effect_fence_current`, or `task_fence_current` is `REJECTED` | `FENCE_STALE` |

An invalid time interval, impossible same-watermark time classification, or a
`time_window_current = REJECTED` value matching neither closed time predicate
is `INTEGRITY_FAILURE`. Lifecycle `INDETERMINATE` is an indeterminate
observation. `ISSUED` and `ACTIVE` are the only lifecycle values eligible for
`VALID`.

Any of the 19 currentness fields equal to `INDETERMINATE`, lifecycle equal to
`INDETERMINATE`, or a required watermark input being unavailable adds the sole
currentness indeterminate candidate `UNAVAILABLE`.

### 4.2 Exact currentness reason precedence

For `REJECTED`, choose the first present candidate in this exact order:

```text
INTEGRITY_FAILURE
PROHIBITED
TERMINAL
EXPIRED
NOT_YET_VALID
INVOCATIONS_EXHAUSTED
TASK_STALE
ACTOR_STALE
COMMAND_STALE
HOST_STALE
AUTH_STALE
POLICY_STALE
CAPABILITY_STALE
RESOURCE_STALE
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
AUTHORIZATION_STALE
EPOCH_STALE
FENCE_STALE
```

If no rejected candidate exists and any indeterminate observation exists, emit
`INDETERMINATE / UNAVAILABLE`. Only lifecycle `ISSUED` or `ACTIVE` with every
applicable currentness field PASS or permitted `NOT_APPLICABLE` emits
`VALID / ALL_CURRENT`.

## 5. Host-local admission totality

This section replaces only the result/reason derivation prose of R1 Section
9.2. The R1 schema, field order, closed enum, fingerprint coverage, advisory
status, writer boundary, and expiry rule remain unchanged.

### 5.1 Exact check-to-reason mapping

| Proven negative predicate | Candidate reason |
|---|---|
| reproducible canonical/fingerprint/same-watermark incompatibility outside the request-validity predicate | `INTEGRITY_FAILURE` |
| `prohibited_boundary = REJECTED` | `PROHIBITED` |
| `request_integrity = REJECTED` | `INVALID_REQUEST` |
| `permit_currentness = REJECTED` | `PERMIT_INVALID` |
| `host_authentication = REJECTED` | `HOST_UNAUTHENTICATED` |
| `host_ownership = REJECTED` | `HOST_NOT_OWNER` |
| any fence-match field is `REJECTED` | `STALE_FENCE` |
| `execution_epoch_match = REJECTED` | `STALE_EPOCH` |
| `capability_subset = REJECTED` | `CAPABILITY_DENIED` |
| `resource_subset = REJECTED` | `RESOURCE_DENIED` |
| `secret_handle_scope = REJECTED` | `SECRET_HANDLE_DENIED` |
| `permit_attestation = REJECTED` | `ATTESTATION_INVALID` |
| `human_presence = REJECTED` | `HUMAN_PRESENCE_MISSING` |
| `effect_intent_exact_match = REJECTED` | `EFFECT_MISMATCH` |
| `idempotency_identity_match = REJECTED` | `IDEMPOTENCY_CONFLICT` |
| `invocation_slot_available = REJECTED` | `INVOCATION_UNAVAILABLE` |
| `Jenn_authorization = REJECTED` | `AUTHORIZATION_MISSING` |

Any of the 18 admission checks equal to `INDETERMINATE`, or a required
same-watermark input being unavailable, adds the sole admission indeterminate
candidate `CURRENTNESS_UNAVAILABLE`.

### 5.2 Exact admission reason precedence

For `REJECTED`, choose the first present candidate in this exact order:

```text
INTEGRITY_FAILURE
PROHIBITED
INVALID_REQUEST
PERMIT_INVALID
HOST_UNAUTHENTICATED
HOST_NOT_OWNER
STALE_FENCE
STALE_EPOCH
CAPABILITY_DENIED
RESOURCE_DENIED
SECRET_HANDLE_DENIED
ATTESTATION_INVALID
HUMAN_PRESENCE_MISSING
EFFECT_MISMATCH
IDEMPOTENCY_CONFLICT
INVOCATION_UNAVAILABLE
AUTHORIZATION_MISSING
```

If no rejected candidate exists and any indeterminate observation exists, emit
`INDETERMINATE / CURRENTNESS_UNAVAILABLE`. Only every applicable check PASS or
permitted `NOT_APPLICABLE` emits `ADMITTED / ALL_CHECKS_PASS`.

Known stale fence or epoch evidence is therefore `REJECTED / STALE_FENCE` or
`REJECTED / STALE_EPOCH`; it is not `INDETERMINATE`.

## 6. Canonical fingerprint and replay consequences

The selected result and reason remain inside the existing R1 fingerprint field
order. An evaluator MUST derive them from the same normalized evidence tuple
and MUST reject a supplied object whose result or reason differs from this R2
reduction. A caller cannot select a lower-priority reason, downgrade REJECTED to
INDETERMINATE, or upgrade either non-success result.

For one exact evidence tuple and watermark:

```text
same normalized candidates
  -> same result
  -> same first-priority reason
  -> same canonical assessment or decision bytes
  -> same canonical fingerprint
```

A replay with the same identity but different derived result, reason, or
fingerprint is conflict, never idempotent success. Existing R1 replay, lost
reply, crash lookup, canonical-writer, and no-blind-retry rules remain in force.

The immutable R1 M0-A fixture remains valid constructive evidence for the
unchanged all-positive success path. R2 adds a separate fixed negative vector
subject and deterministic offline validator for the amended result/reason
surface. Neither validator issues a permit, authenticates a Host, writes a
database, starts a service, calls a provider, or executes an effect.

## 7. Replacement invariants

R2 replaces R1 I19 and I20 with exactly:

19. **I19-R2** When no proven negative exists, a required missing, unreadable,
    unavailable, or non-reproducible input is fail-closed `INDETERMINATE` with
    the reducer's unique unavailable reason. Known stale is not an unavailable
    input.
20. **I20-R2** Any reproducibly proven negative is `REJECTED` and dominates
    every concurrent `INDETERMINATE` observation; the first present reason in
    the reducer's fixed rejected-reason precedence is the only canonical
    reason.

All other R1 invariants remain unchanged.

## 8. Additional adversarial decisions A50-A59

50. Task binding REJECTED plus policy INDETERMINATE -> `REJECTED / TASK_STALE`.
51. Host REVOKED plus verifier unavailable -> `REJECTED / REVOKED`.
52. Host COMPROMISED plus REVOKED -> `REJECTED / COMPROMISED`.
53. Prohibited plus Host-authentication rejection -> currentness `REJECTED / PROHIBITED`.
54. Capability rejection has the explicit currentness reason `CAPABILITY_STALE`.
55. Resource, secret-handle, attestation, and human-presence rejections each use their explicit closed currentness reason.
56. Permit rejection plus Host-authentication INDETERMINATE -> admission `REJECTED / PERMIT_INVALID`.
57. Admission prohibited plus invalid request -> `REJECTED / PROHIBITED`.
58. Stale fence plus stale epoch -> `REJECTED / STALE_FENCE`.
59. With no proven negative, any applicable INDETERMINATE check remains fail-closed with the reducer's unique unavailable reason.

## 9. Acceptance, exclusions, and next gate

The R2 acceptance unit is indivisible:

```text
R1 contract
+ R1 M0-A fixture
+ R1 M0-A validator
+ R2 amendment
+ R2 totality vector fixture
+ R2 totality vector validator
= F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R2_ATOMIC_BUNDLE
```

Partial acceptance is forbidden. Author review is not independent review.
Passing local validators does not accept or freeze F4. The next gate is a fresh
full atomic hash-bound independent review of all six subjects. Only Jenn may
later accept and freeze the whole R2 bundle.

This R2 amendment does not start F5 or F6 and authorizes no implementation,
runtime activation, production authentication, credential change, database,
service, provider, Host executor, external effect, public API, MCP, commit,
push, PR, merge, release, deploy, publish, tag, or formal Memory action.
