# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R3 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R1 contract SHA-256: `3378396108f090469984facb8ddcb238ae122be9cab71afe2f8c3bd1cd577db3`  
Base R2 amendment SHA-256: `30cdbf0acb348d4c0c933f95bdcf51c7f3a6326ad678d8fca1f19faf4c85f705`  
Blocking R2 independent-review SHA-256: `df02df54a16f7f09db2575e304b7b1a210e43fdbd75af1a2a37f032c9a2b62d8`

## 1. Scope, precedence, and fixed inputs

This is the narrow R3 correction for:

```text
F4-R2-FULL-ATOMIC-IR-B01 PRESTART Host reason totality
F4-R2-FULL-ATOMIC-IR-B02 HostWorkStartDisposition result/reason totality
```

The effective reading order is:

```text
1. R3 explicit replacements
2. R2 other explicit replacements
3. R1 all other clauses
4. frozen F3 R1-R4 atomic bundle for F3-owned definitions and writer authority
5. frozen F2 R1-R22 atomic bundle for F2-owned identity and delegation authority
6. accepted F1 contract for F1-owned Task and commitment authority
```

The effective acceptance literal is:

```text
F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R3_ATOMIC_BUNDLE
```

All six R1/R2 subjects and both prior independent reviews remain immutable.
R3 changes no R1/R2 identifier, success-path field order, fingerprint formula,
acceptance, handoff, writer, replay, crash, or downstream ownership rule. Every
earlier clause not explicitly replaced here remains in force.

This document creates no implementation, database, runtime, Resident, service,
production-authentication, credential, provider, Host-executor, external-effect,
F5, or F6 authority.

## 2. PRESTART Host authentication reason closure

This section replaces the effective Host-authentication reason enum and R2
Sections 3.1-3.2 only where they classify `PRESTART` or order Host rejected
reasons. The effective closed Host reason enum is:

```text
MATCH
INTEGRITY_FAILURE
COMPROMISED
REVOKED
RETIRED
SUSPENDED
PRESTART
PROFILE_MISMATCH
CHALLENGE_MISMATCH
EXPIRED
NOT_YET_VALID
REVOCATION_UNAVAILABLE
VERIFIER_UNAVAILABLE
UNKNOWN
```

`PRESTART` is a `REJECTED` candidate exactly when the current canonical
`HostIdentityRevisionV0_1.lifecycle_state` is `PRESTART`. It is independent of
trusted-time classification: an in-window PRESTART Host remains PRESTART and
cannot authenticate. `NOT_YET_VALID` continues to mean trusted time before an
applicable validity start; it is not a lifecycle alias.

The sole effective Host rejected-reason precedence is:

```text
INTEGRITY_FAILURE
COMPROMISED
REVOKED
RETIRED
SUSPENDED
PRESTART
PROFILE_MISMATCH
CHALLENGE_MISMATCH
EXPIRED
NOT_YET_VALID
```

The R2 indeterminate precedence remains:

```text
REVOCATION_UNAVAILABLE
VERIFIER_UNAVAILABLE
UNKNOWN
```

Any rejected candidate, including `PRESTART`, dominates every concurrent
indeterminate candidate. Only current lifecycle `ACTIVE` plus every other R1
positive predicate can emit `AUTHENTICATED / MATCH`. The reason remains in the
existing fingerprint position.

## 3. HostWorkStartDisposition total reducer

This section replaces the effective reason enum and all result/reason
derivation prose in R1 Section 9.4. It applies the R2 negative-over-unavailable
lattice to `HostWorkStartDispositionFactV0_1` without changing the schema field
order, observation identity, fingerprint domain, atomic successful handoff, or
terminal observation rules.

### 3.1 Effective reason enum

```text
ALL_RECHECKS_PASS
INTEGRITY_FAILURE
ACCEPTANCE_MISSING
HOST_UNAUTHENTICATED
FENCED
EPOCH_STALE
EXPIRED
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
OBSERVATION_UNAVAILABLE
```

R3 adds `SECRET_HANDLE_STALE`, `ATTESTATION_STALE`, and
`HUMAN_PRESENCE_STALE`. No other result/reason pair is legal.

### 3.2 Closed normalized recheck observations

Immediately before disposition reduction, the canonical writer derives these
closed observations at one exact watermark from the fact's bound acceptance,
permit, Host, epoch, fence, secret-handle, attestation, and human-presence
inputs:

| Normalized observation | Allowed states | Proven negative reason |
|---|---|---|
| canonical/fingerprint/same-watermark integrity | `PASS | REJECTED | INDETERMINATE` | `INTEGRITY_FAILURE` |
| exact acceptance present and current | `PASS | REJECTED | INDETERMINATE` | `ACCEPTANCE_MISSING` |
| handoff deadline and every applicable expiry current | `PASS | REJECTED | INDETERMINATE` | `EXPIRED` |
| owner Host identity revision current | `PASS | REJECTED | INDETERMINATE` | `HOST_UNAUTHENTICATED` |
| owner Host authentication epoch current | `PASS | REJECTED | INDETERMINATE` | `HOST_UNAUTHENTICATED` |
| task fence generation matches | `PASS | REJECTED | INDETERMINATE` | `FENCED` |
| Host fence generation matches | `PASS | REJECTED | INDETERMINATE` | `FENCED` |
| effect fence generation matches | `PASS | REJECTED | INDETERMINATE` | `FENCED` |
| execution epoch matches | `PASS | REJECTED | INDETERMINATE` | `EPOCH_STALE` |
| `secret_handles_current` | `PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE` | `SECRET_HANDLE_STALE` |
| `permit_attestation_current` | `PASS | REJECTED | INDETERMINATE` | `ATTESTATION_STALE` |
| `human_presence_current` | `PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE` | `HUMAN_PRESENCE_STALE` |

`NOT_APPLICABLE` is valid only on the two R1 fields that explicitly admit it.
Unknown inputs, unknown enums, invalid `NOT_APPLICABLE`, or malformed canonical
bytes reject before a disposition fact can be emitted.

Reproducibly incompatible canonical facts at one claimed watermark are
`REJECTED / INTEGRITY_FAILURE`. If facts cannot be read or reproduced well
enough to prove either compatibility or incompatibility, the corresponding
observation is `INDETERMINATE`; it does not become an integrity rejection.

### 3.3 Total result lattice

For every schema-valid normalized recheck tuple:

```text
1. Any REJECTED observation
   -> NOT_STARTED
   -> first present reason in the fixed rejected precedence

2. Else any INDETERMINATE observation
   -> INDETERMINATE / OBSERVATION_UNAVAILABLE

3. Else every applicable observation PASS or permitted NOT_APPLICABLE
   -> START_AUTHORITY_CURRENT / ALL_RECHECKS_PASS
```

A proven negative always dominates concurrent unavailable evidence. Known
expired, absent, unauthenticated, fenced, stale-epoch, stale-secret,
stale-attestation, or missing-human-presence evidence is never
`INDETERMINATE`.

### 3.4 Exact rejected-reason precedence

For `NOT_STARTED`, choose the first present candidate in this exact order:

```text
INTEGRITY_FAILURE
ACCEPTANCE_MISSING
HOST_UNAUTHENTICATED
FENCED
EPOCH_STALE
EXPIRED
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
```

Duplicate candidates collapse. The reason is reducer-derived, never caller
selected. If no rejected candidate exists, `NOT_STARTED` is illegal. If no
indeterminate observation exists, `INDETERMINATE` is illegal.

### 3.5 Fingerprint, first-fact, and replay uniqueness

The selected disposition and reason remain in the existing R1 fingerprint
field order. One exact observation identity and normalized recheck tuple must
therefore yield one canonical fact fingerprint. A supplied fact with another
result, lower-priority reason, or fingerprint rejects.

Identical replay returns the same fact. Changed result, reason, or bytes under
one `observation_id` is an integrity conflict, not idempotent success. A
`NOT_STARTED` fact still commits only while the unique handoff key is absent.
Successful `START_AUTHORITY_CURRENT` plus handoff still share one serializable
transaction. None of these facts proves a physical effect started or ended.

## 4. Replacement invariant

R3 replaces R2 `I20-R2` with:

20. **I20-R3** In Host authentication, TaskPermit currentness, Host-local
    admission, and Host-work start disposition, any reproducibly proven
    negative is the reducer's closed rejected/non-started result and dominates
    every concurrent indeterminate observation; the first present candidate in
    that reducer's fixed rejected-reason precedence is the only canonical
    reason. `PRESTART` is a proven Host-authentication negative.

R2 `I19-R2` and every other effective R1/R2 invariant remain unchanged.

## 5. Additional adversarial decisions A60-A69

60. In-window lifecycle PRESTART -> Host `REJECTED / PRESTART`.
61. PRESTART plus verifier unavailable -> Host `REJECTED / PRESTART`.
62. Start recheck secret handle REJECTED -> `NOT_STARTED / SECRET_HANDLE_STALE`.
63. Start recheck attestation REJECTED -> `NOT_STARTED / ATTESTATION_STALE`.
64. Start recheck human presence REJECTED -> `NOT_STARTED / HUMAN_PRESENCE_STALE`.
65. Secret handle REJECTED plus attestation INDETERMINATE -> `NOT_STARTED / SECRET_HANDLE_STALE`.
66. Host unauthenticated plus fenced plus expired -> `NOT_STARTED / HOST_UNAUTHENTICATED`.
67. Fence mismatch plus stale execution epoch -> `NOT_STARTED / FENCED`.
68. With no negative, any unavailable start recheck -> `INDETERMINATE / OBSERVATION_UNAVAILABLE`.
69. All start rechecks PASS or permitted NOT_APPLICABLE -> `START_AUTHORITY_CURRENT / ALL_RECHECKS_PASS`.

## 6. Evidence and next gate

The immutable R1 M0-A positive witness and R2 23-vector proof remain fixed.
R3 adds a separate synthetic fixture and deterministic offline validator for
PRESTART and the start-disposition reducer. No validator issues a permit,
authenticates a real Host, writes a database, starts a service, calls a
provider, or executes an effect.

The indivisible R3 acceptance unit is:

```text
R1 contract + M0-A fixture + M0-A validator
+ R2 amendment + totality fixture + totality validator
+ R3 amendment + closure fixture + closure validator
= F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R3_ATOMIC_BUNDLE
```

Partial acceptance is forbidden. Author review is not independent review.
Passing validators does not accept or freeze F4. The next gate is a fresh full
atomic hash-bound independent review of all nine subjects. Only Jenn may later
accept and freeze the complete bundle.

R3 does not start F5/F6 and authorizes no implementation, runtime activation,
production authentication, credential change, database, service, provider,
Host executor, external effect, public API, MCP, commit, push, PR, merge,
release, deploy, publish, tag, or formal Memory action.
