# AGENTS OS F6 Validation Requirement Current Decision Contract v0.1 R5 Amendment

Status: fixed author subject for fresh full atomic hash-bound independent review.

R5 replaces only the R4 evidence-assessment context clause identified by
`F6-R4-IR-B01`. R1 through R4 remain normative for every other clause.

## ContextualEvidenceAssessmentInputV0_1R5

Each evidence object consumed by an attempt MUST have an F3-owned opaque
assessment whose immutable assessed subject is exactly:

```yaml
evidence_ref:
evidence_revision:
evidence_fingerprint:
requirement_id:
requirement_revision:
requirement_fingerprint:
attempt_ref:
attempt_revision:
attempt_context_fingerprint:
```

The assessment also binds its own `assessment_id`, contiguous
`assessment_revision`, predecessor tuple, current-head status, exact F3 owner
contract, exact F3 barrier, observation sequence and `EXACT_CURRENT` result.

An attempt evidence binding MUST resolve the assessment by exact
ref/revision/fingerprint and MUST compare every assessed-subject field with the
resolved evidence object, Requirement revision and attempt context.

Changing the Requirement revision or fingerprint, attempt context fingerprint,
or evidence tuple invalidates the old assessment. A favorable result requires a
new contextual assessment revision and a new immutable attempt revision. An
outer inventory or recomputed summary is not evidence that F3 assessed the new
context.

F6 only consumes this F3 assessment. It does not recompute F3 authority or
evidence validity.

## Scope boundary

R5 adds no state, permission class, evidence capability, runtime interface or
effect. It does not change F1, F3 or F5 frozen authority, start F7, authorize
implementation, activate runtime, access production authentication, call a
provider, write a database or execute a real Task, Validation, Event or effect.
All fixture content is synthetic, nonauthority and runtime unusable.
