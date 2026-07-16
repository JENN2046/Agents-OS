# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R4 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R1 contract SHA-256: `3378396108f090469984facb8ddcb238ae122be9cab71afe2f8c3bd1cd577db3`  
Base R2 amendment SHA-256: `30cdbf0acb348d4c0c933f95bdcf51c7f3a6326ad678d8fca1f19faf4c85f705`  
Base R3 amendment SHA-256: `4a65021d5c15640531aa59c3641f1ef1ab6dae86421a4ebfc4f6a3af25dd9939`  
Blocking R3 review SHA-256: `0d8914f751991eaa53cd3478668b5a6d047d5327e5dd80b593e935d2d73bbd4a`

## 1. Scope and precedence

This is the sole correction for `F4-R3-FULL-ATOMIC-IR-B01`. Effective reading
order is R4 explicit replacements, then R3, R2, and R1. All nine prior subject
bytes remain immutable. The effective acceptance literal is
`F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R4_ATOMIC_BUNDLE`.

R4 defines the boundary before `HostWorkStartDispositionFactV0_1` exists. It
does not alter the successful handoff transaction, writer ownership, fences,
permit semantics, Host authentication, or any physical-effect rule.

## 2. Acceptance-reference resolution is a no-fact precondition

`observeStartAuthority(acceptance_ref)` MUST resolve the exact canonical
`HostWorkAcceptanceFactV0_1` before deriving `observation_id`, allocating an
observation attempt, normalizing start rechecks, or writing any canonical fact.

Resolution has this closed transport-only result:

```text
HostWorkStartObservationPreflightV0_1R4
  interface_version = F4_START_OBSERVATION_PREFLIGHT_V0_1_R4
  acceptance_ref
  outcome = FACT_INPUT_RESOLVED | NO_FACT
  reason = ACCEPTANCE_RESOLVED
         | ACCEPTANCE_NOT_FOUND
         | ACCEPTANCE_LOOKUP_UNAVAILABLE
         | ACCEPTANCE_INTEGRITY_CONFLICT
         | INVALID_ACCEPTANCE_REF
  acceptance_fingerprint = lowercase SHA-256 | null
```

The only legal resolved pair is
`FACT_INPUT_RESOLVED / ACCEPTANCE_RESOLVED` with the exact canonical
`acceptance_fingerprint`. Every other reason pairs only with `NO_FACT` and a
null fingerprint. `INVALID_ACCEPTANCE_REF` means the reference is not
schema-valid. `ACCEPTANCE_NOT_FOUND` requires a reproducible canonical lookup
showing absence. Lookup failure or inability to prove absence is
`ACCEPTANCE_LOOKUP_UNAVAILABLE`. Existing bytes that reproducibly conflict
with the reference, schema, or fingerprint are `ACCEPTANCE_INTEGRITY_CONFLICT`.

This result is a non-persisted transport response. It has no ledger identity,
fingerprint, idempotency key, receipt, handoff, reservation, authority, or
effect. It MUST NOT be used as evidence that a Host work start was accepted,
rejected, observed, or terminal. Retrying the same reference repeats lookup;
it cannot replay a fact that was never created.

Only `FACT_INPUT_RESOLVED / ACCEPTANCE_RESOLVED` enters the canonical start
observation writer. At that boundary, R1's unchanged formula derives
`observation_id` from the resolved acceptance fingerprint. Lost-reply replay
then uses the existing observation identity and fact rules. Thus no first fact
is ever required to derive identity from absent bytes.

## 3. Canonical start-disposition reducer replacement

This section replaces R3 Sections 3.1-3.4 only. `ACCEPTANCE_MISSING` is removed
from the effective fact reason enum, normalized observations, and precedence.
Acceptance resolution is the Section 2 precondition, not a fact observation.

The effective reason enum is:

```text
ALL_RECHECKS_PASS
INTEGRITY_FAILURE
HOST_UNAUTHENTICATED
FENCED
EPOCH_STALE
EXPIRED
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
OBSERVATION_UNAVAILABLE
```

After exact acceptance resolution, the eleven normalized rechecks are the R3
twelve with `exact acceptance present and current` removed. Their allowed
states and mappings are otherwise unchanged. The total lattice remains:

```text
any REJECTED -> NOT_STARTED -> first fixed rejected reason
else any INDETERMINATE -> INDETERMINATE / OBSERVATION_UNAVAILABLE
else all PASS or permitted NOT_APPLICABLE
  -> START_AUTHORITY_CURRENT / ALL_RECHECKS_PASS
```

The sole rejected precedence is:

```text
INTEGRITY_FAILURE
HOST_UNAUTHENTICATED
FENCED
EPOCH_STALE
EXPIRED
SECRET_HANDLE_STALE
ATTESTATION_STALE
HUMAN_PRESENCE_STALE
```

Malformed or unknown preflight or reducer input rejects before fact creation.
It cannot be coerced into `INDETERMINATE`. Every fact remains fingerprinted,
first-fact unique, replay-safe, and terminal under the unchanged R1/R3 rules.

## 4. Replacement invariant and adversarial decisions

R4 replaces `I20-R3` with:

20. **I20-R4** Start observation identity is derived only after exact canonical
    acceptance resolution. An unresolved acceptance reference produces one of
    the closed non-persisted `NO_FACT` transport outcomes and no canonical
    identity, fact, handoff, reservation, authority, or effect. Within every
    canonical Host, permit, admission, and start reducer, a proven negative
    dominates unavailable evidence and fixed precedence selects the sole reason.

Additional decisions:

70. Valid reference, reproducible absence -> `NO_FACT / ACCEPTANCE_NOT_FOUND`.
71. Valid reference, unavailable lookup -> `NO_FACT / ACCEPTANCE_LOOKUP_UNAVAILABLE`.
72. Conflicting referenced bytes -> `NO_FACT / ACCEPTANCE_INTEGRITY_CONFLICT`.
73. Malformed reference -> `NO_FACT / INVALID_ACCEPTANCE_REF`.
74. Exact fact resolved -> fingerprint returned and only then observation identity derived.
75. Any `NO_FACT` result -> no observation id, fact, handoff, reservation, authority, or effect.
76. `ACCEPTANCE_MISSING` supplied as a fact reason -> reject as unknown enum.
77. Resolved acceptance plus any unavailable recheck and no negative -> canonical indeterminate fact.
78. Resolved acceptance plus negative and unavailable -> canonical negative fact.

## 5. Atomic unit and non-authorization

The indivisible R4 unit is all R1, R2, R3 subjects plus this amendment, its
fixture, and validator: twelve subjects total. Partial acceptance is forbidden.
The next gate is fresh full atomic hash-bound independent review. Only Jenn may
later accept and freeze the bundle.

Nothing here authorizes implementation, database writes, Host/Resident/service
startup, runtime activation, production authentication, provider calls,
physical effects, F5, F6, commit, push, or merge.
