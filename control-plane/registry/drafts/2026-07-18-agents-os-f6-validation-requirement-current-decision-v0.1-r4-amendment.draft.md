# AGENTS OS F6 Validation Requirement Current Decision Contract v0.1 R4 Amendment

Status: fixed author subject for fresh full atomic hash-bound independent review.

R4 replaces only the five clauses identified by `F6-R3-IR-B01` through
`F6-R3-IR-B05`. R3, R2 and R1 remain normative for every other clause.

## 1. Exact Task identity closure

One evaluation transaction MUST derive one `task_id` from the current F1
`TASK_CURRENT_STATE` assessment. The exact same value MUST contain every
current Requirement revision. Every Validation Set snapshot MUST have an exact,
nonempty membership whose Requirements all carry that value. Every attempt and
Requirement decision MUST resolve its Requirement and Set to that same value.
The Set decision MUST resolve its Set to that value. Completion MUST carry that
value directly. Missing, mixed, substituted or caller-invented Task identity is
`INDETERMINATE` and MUST NOT produce `SATISFIED`, `WAIVED` or `ELIGIBLE`.

F6 consumes the F1 assessment as an opaque hash-bound authority result. It MUST
NOT reconstruct F1 lifecycle or identity authority.

## 2. Resolved assessment revision equality

For every field ending in `_assessment_ref`, the sibling
`_assessment_fingerprint` and `_assessment_revision` form one tuple. The ref
MUST resolve to exactly one assessment wrapper. The declared fingerprint MUST
equal the wrapper fingerprint and the declared revision MUST equal the
wrapper's actual `assessment_revision`. This rule applies recursively to F1,
F3, F5, provenance, waiver, evidence, attempt and completion consumers.

No consumer-supplied revision is currentness evidence by itself.

## 3. TrustedTime-derived waiver currentness

Waiver currentness MUST be derived using the exact current TrustedTime input:

```text
valid_from_sequence <= TrustedTime.observed_event_sequence < expires_at_sequence
```

The TrustedTime input MUST remain bound to the current F3 barrier. `WAIVED` and
any completion result depending on it MUST be rejected when the waiver is not
yet valid, expired, indeterminate, not current head or outside that barrier.
No fixed literal evaluation sequence may substitute for TrustedTime.

## 4. Evidence subject closure

Every evidence binding consumed by an attempt MUST resolve to an evidence
object whose `validation_subject` equals the attempt's exact Requirement ID.
The R4 evidence-subject binding additionally commits the Requirement revision,
Requirement fingerprint and attempt context fingerprint. Changing any of these
requires a new evidence assessment and a new immutable attempt revision.

Evidence for one Requirement MUST NOT satisfy another Requirement.

## 5. Strict attempt and carry Event order

For every non-base attempt revision:

```text
predecessor.created_event_sequence < current.created_event_sequence
```

For every carry-forward attempt:

```text
original_source.created_event_sequence < carry_revision.created_event_sequence
```

The source and predecessor refs, revisions and fingerprints MUST resolve to the
same immutable objects already required by R3. Equality, reversal, missing
objects or unknown ordering MUST reject the favorable result.

## 6. Determinism and fail-closed rule

The R4 closure inventory is an audit commitment, not caller authority. The
validator MUST independently derive all five inventories from the fixed inner
graph before comparing fingerprints. Any missing, extra, duplicate, unresolved
or contradictory binding is `BLOCK`.

## 7. Scope boundary

R4 adds no Task, Validation, waiver, evidence, delivery or completion state. It
does not redefine F1, F3 or F5 authority, create a permission ladder, authorize
implementation, activate runtime, call a provider, access production
authentication, execute an effect or start F7. The fixture is synthetic
nonauthority evidence and is never runtime usable.
