# AGENTS OS F6 Validation Requirement Current Decision Contract v0.1 R6 Amendment

Status: fixed author subject for fresh full atomic hash-bound independent review.

R6 replaces only the same-revision immutability and contextual-assessment
schema-totality clauses identified by `F6-R5-IR-B01` and `F6-R5-IR-B02`.
R1 through R5 remain normative for every other clause.

## 1. Immutable revision anchor

Every R6 evaluation MUST consume an immutable, hash-bound R5 baseline. The
baseline is not supplied by the candidate graph and MUST be resolved from the
fixed R5 fixture bytes bound by the R6 package.

For each `ValidationAttemptRevisionV0_1R2` and
`ContextualEvidenceAssessmentInputV0_1R5`, the immutable history commits:

```yaml
identity:
revision:
ref:
fingerprint:
predecessor_ref:
predecessor_revision:
predecessor_fingerprint:
requirement_or_assessed_subject_fingerprint:
attempt_context_fingerprint:
```

If a candidate object reuses an identity and revision present in the immutable
history, its complete fingerprint and all committed fields MUST equal the
historical object exactly. Re-signing the object or any dependent object does
not change this rule.

Changing evidence, Requirement identity/revision/fingerprint or attempt context
MUST create both a new immutable attempt revision and a new contextual evidence
assessment revision. A new revision MUST be the unique contiguous successor of
the prior revision and bind the exact predecessor attempt and assessment
ref/revision/fingerprint. Same-revision replacement, branching, gaps, cycles,
predecessor substitution and history supplied only by the candidate are
`BLOCK`.

## 2. Contextual assessment closed schema

`ContextualEvidenceAssessmentInputV0_1R5` has exactly these wrapper fields:

```text
schema key ref payload fingerprint
```

Its payload has exactly:

```text
assessment_id assessment_revision
predecessor_ref predecessor_revision predecessor_fingerprint
is_current_head
owner_phase owner_contract_ref owner_contract_revision owner_contract_fingerprint
barrier_ref barrier_fingerprint observed_event_sequence
result assessed_subject
```

Its `assessed_subject` has exactly:

```text
evidence_ref evidence_revision evidence_fingerprint
requirement_id requirement_revision requirement_fingerprint
attempt_ref attempt_revision attempt_context_fingerprint
```

The attempt-to-contextual-assessment binding has exactly:

```text
attempt_ref attempt_revision attempt_context_fingerprint
evidence_ref evidence_revision evidence_fingerprint
assessment_ref assessment_revision assessment_fingerprint
binding_fingerprint
```

Unknown, missing or duplicate fields are forbidden. Strings are exact JSON
strings. Booleans require the JSON boolean type; integers MUST NOT substitute
for booleans. Revisions and Event sequences are non-negative safe JSON integers
with positive revision fields where specified. Nullable predecessor fields are
either all null for revision 1 or the exact typed predecessor tuple for later
revisions. Floats, non-finite numbers, integers outside the safe range, unknown
enums and malformed nested values are forbidden.

Duplicate JSON object keys MUST be rejected during parsing before fingerprint
or semantic validation. Every malformed input MUST return deterministic
`BLOCK`; an uncaught exception is not a valid rejection.

Schema validation precedes trust in wrapper, binding, history or root
fingerprints. Complete re-signing cannot legalize an invalid schema.

## 3. Required R6 adversarial closure

The offline validator MUST reject, at the target R6 layer:

1. complete candidate/context replacement with assessment subject and every
   dependent fingerprint updated while attempt and assessment revisions remain
   unchanged;
2. unknown assessment payload or wrapper fields after complete re-signing;
3. JSON integers `1` or `0` substituted for `is_current_head`;
4. missing required payload fields without an uncaught exception;
5. floats, out-of-range integers and invalid nullable predecessor tuples;
6. duplicate JSON keys before object construction;
7. unknown, missing, duplicated or reordered immutable-history rows.

The pre-R6 regression floor remains `62 + 17 + 7 + 1`, with zero exceptions.

## 4. Scope boundary

R6 adds no Validation state, permission class, identity authority, evidence
capability, runtime interface or effect. It consumes F1/F3/F5 authority as
opaque hash-bound inputs and does not recompute their authority semantics.

All fixture content remains `SYNTHETIC_TEST`, nonauthority, runtime unusable and
non-importable into recovery or production. R6 does not accept or freeze F6,
start F7, authorize implementation, activate runtime, access production
authentication, call a provider, write a database or execute a real Task,
Validation, Event or effect.
