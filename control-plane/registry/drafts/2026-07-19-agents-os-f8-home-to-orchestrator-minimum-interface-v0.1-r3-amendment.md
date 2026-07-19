# AGENTS OS F8 Home-to-Orchestrator Minimum Interface v0.1 R3 Amendment

Status: fixed only when bound by an F8 R3 atomic manifest
Date: 2026-07-19
Owner: Jenn
Agent steward: Nobao

## 1. Boundary and precedence

R3 closes only the accepted portions of `F8-R2-B01`, `F8-R2-B02` and the
review-package accessibility portion of `F8-R2-B04`.

```text
R3 explicit replacement clauses
-> R2 explicit replacement clauses not replaced by R3
-> R1 all other clauses
```

All R1 and R2 subjects and manifests remain exact immutable historical bytes.
R3 does not reopen those review units and does not accept or freeze F8.

`F8-R2-B03` is excluded. The fixed contract already defines a minimum
watermark. R3 may clarify its name but must not change greater-than-or-equal to
exact equality.

## 2. Authority ownership

F8 remains a consumer of upstream owner facts. It does not issue, revise,
supersede or interpret the authority basis of an F1, F2, F3, policy or Jenn
assessment.

F8 may verify only:

```text
exact assessment reference / revision / fingerprint
exact owner-issued immutable revision commitment
exact owner Event commitment
exact current-head and minimum-watermark facts exposed by the owner
closed owner result value
exact subject and context binding required by F8
```

F8 must not:

```text
rebuild upstream lifecycle or assessment history
decide whether an upstream owner should have issued a result
recompute Actor, Principal, responsibility, policy, Jenn or F3 authority
create a substitute owner ledger
accept a caller-authored commitment as owner evidence
```

## 3. Owner-issued immutable assessment revision commitment

R3 adds the following minimal consumption projection. It is issued and owned by
the same owner contract as the assessment. F8 never writes it.

```yaml
OwnerAssessmentRevisionCommitmentV0_1R3:
  commitment_ref: stable_ref
  commitment_revision: positive_safe_integer
  owner_contract: closed_owner_contract
  assessment_id: stable_ref
  assessment_revision: positive_safe_integer
  assessment_fingerprint: lowercase_sha256
  predecessor_commitment_ref: stable_ref_or_null
  predecessor_commitment_fingerprint: lowercase_sha256_or_null
  issued_event_ref: stable_ref
  issued_event_sequence: positive_safe_integer
  issued_event_fingerprint: lowercase_sha256
  commitment_fingerprint: lowercase_sha256
```

Revision 1 has null predecessor fields. A later commitment revision binds the
exact prior owner-issued commitment. Commitment identity, immutability,
predecessor validity and Event issuance remain owned by the upstream owner.
F8 consumes the owner store's exact resolved record; it does not derive those
facts from the assessment graph.

R3 replaces `AssessmentConsumerV0_1R2` with:

```yaml
AssessmentConsumerV0_1R3:
  assessment_id: stable_ref_or_null
  expected_assessment_revision: positive_safe_integer_or_null
  expected_assessment_fingerprint: lowercase_sha256_or_null
  owner_commitment_ref: stable_ref_or_null
  expected_owner_commitment_revision: positive_safe_integer_or_null
  expected_owner_commitment_fingerprint: lowercase_sha256_or_null
```

All six fields are null or all six fields are non-null. For every non-null
consumer, F8 must resolve both objects from the declared upstream owner source
and require:

```text
resolved assessment id / revision / fingerprint == consumer commitment
resolved owner commitment ref / revision / fingerprint == consumer commitment
owner commitment owner_contract == resolved assessment owner_contract
owner commitment assessment id / revision / fingerprint == resolved assessment
owner commitment issued Event exists in the owner immutable Event source
owner commitment is the exact current immutable record for its ref and revision
```

Only after those checks may F8 read the owner assessment result. A result,
subject, context, current-head marker, watermark or other assessment field
change at the same `(assessment_id, assessment_revision)` cannot be accepted by
re-signing the assessment and consumer: it no longer matches the immutable
owner commitment. Changing the commitment at the same commitment revision also
fails the owner source resolution.

Missing, unavailable, conflicting or unverified owner commitment evidence is
fail-closed. It never falls back to an internally self-consistent row.

## 4. Synthetic owner-source witness

The R3 fixture contains synthetic assessment rows and synthetic owner
commitments only. The offline validator carries separate fixed
`trusted_owner_commitment_anchors` representing a read-only owner store outside
the caller-controlled fixture graph.

These anchors are constructive test evidence only:

```text
SYNTHETIC owner commitment anchor
!= production owner Event
!= authenticated Actor or Principal
!= accepted F3 intake outcome
!= runtime authority
```

Fixture section and root hashes may be fully recomputed by an attacker. The
trusted owner anchors must still reject a same-revision assessment and
commitment rewrite. Disabling ordinary fixture inventory anchors must not
disable owner-source commitment verification.

Production use remains unimplemented and unauthorized. A future implementation
must obtain the commitment through the accepted upstream owner interface; it
must not compile synthetic anchors into a runtime authority source.

## 5. Canonical candidate-history resolution

Before interpreting any F3 outcome assessment, acknowledgement must resolve the
exact candidate tuple from F8's canonical immutable candidate history:

```text
handoff_candidate_ref
handoff_candidate_revision
handoff_candidate_fingerprint
```

Resolution rules:

```text
exactly one canonical history entry must match ref and revision
its stored candidate_fingerprint must equal the acknowledgement input
its immutable predecessor chain must be valid under the F8 history owner
the candidate must remain runtime_usable=false and command_authority=false
missing, duplicate, conflicting or unavailable history is INDETERMINATE
```

Only the resolved canonical tuple may be used to compute the F3 outcome context
and compare the F3 assessment subject. A caller cannot introduce a candidate
that exists only in acknowledgement input or only in an F3 assessment.

The R3 synthetic validator uses separate fixed
`trusted_candidate_history_anchors` to represent the immutable F8 history
source. Fully adding or rewriting a candidate in the fixture graph cannot make
it canonical.

## 6. R3 acknowledgement input and reducer

R3 replaces the acknowledgement input with:

```yaml
HomeIntentHandoffAcknowledgementRawInputV0_1R3:
  handoff_candidate_ref: stable_ref
  handoff_candidate_revision: positive_safe_integer
  handoff_candidate_fingerprint: lowercase_sha256
  minimum_trusted_event_sequence: positive_safe_integer
  F3_outcome_consumer: AssessmentConsumerV0_1R3
```

The reducer order is normative:

```text
1. Resolve exact candidate from canonical F8 history.
2. Resolve exact F3 assessment and owner commitment from F3-owned stores.
3. Verify the owner commitment binds the resolved assessment.
4. Verify assessment owner, kind, subject and context equal the canonical candidate.
5. Require is_current_head == true.
6. Require based_on_event_sequence >= minimum_trusted_event_sequence.
7. Project the closed F3 owner result without recomputing it.
```

`ACKNOWLEDGED_COMMITTED` remains a low-disclosure projection of the synthetic
fixture result. It creates no Command, Task, permission, authentication fact,
effect authority or runtime usability.

## 7. Minimum watermark clarification

R3 replaces the ambiguous consumer field name `trusted_event_sequence` with
`minimum_trusted_event_sequence` in R3 inputs.

The semantic rule remains exactly:

```text
resolved assessment based_on_event_sequence
>= acknowledgement minimum_trusted_event_sequence
```

A higher owner watermark is valid and must remain valid. A lower watermark is
`ACKNOWLEDGED_INDETERMINATE`. R3 must include positive witnesses for equality
and a higher watermark plus a negative witness for a lower watermark.

## 8. Deterministic reasons

The R3 acknowledgement closed primary reasons are:

```text
CANDIDATE_HISTORY_MISSING
CANDIDATE_HISTORY_CONFLICT
CANDIDATE_HISTORY_FINGERPRINT_MISMATCH
OWNER_COMMITMENT_MISSING
OWNER_COMMITMENT_REVISION_MISMATCH
OWNER_COMMITMENT_FINGERPRINT_MISMATCH
OWNER_COMMITMENT_ASSESSMENT_MISMATCH
OWNER_COMMITMENT_NOT_TRUSTED
F3_OUTCOME_MISSING
F3_OUTCOME_REVISION_MISMATCH
F3_OUTCOME_FINGERPRINT_MISMATCH
F3_OUTCOME_SUBJECT_MISMATCH
F3_OUTCOME_WATERMARK_BEHIND
F3_OUTCOME_NOT_CURRENT
F3_OWNER_REPORTED_SYNTHETIC_COMMITTED
F3_OWNER_REPORTED_REJECTED
F3_OWNER_REPORTED_NOT_SUBMITTED
F3_OWNER_REPORTED_INDETERMINATE
```

The first applicable reason in this list is the primary reason. All favorable
outputs keep `command_authority`, `task_write_authority`, `effect_authority`
and `runtime_usable` false.

## 9. Required R3 regressions

The validator must fully re-sign and reject or fail-close at least:

```text
same-revision F7 assessment rewrite with consumer propagation
same-revision F7 assessment and owner commitment rewrite with full propagation
same-revision F3 outcome rewrite with consumer propagation
same-revision F3 outcome and owner commitment rewrite with full propagation
owner commitment ref, revision or fingerprint substitution
owner commitment bound to another assessment
caller-created commitment absent from trusted owner source
acknowledgement candidate absent from canonical history
phantom candidate added to caller graph and fully re-signed
candidate revision or fingerprint mismatch
minimum watermark below / equal / above cases
old trusted_event_sequence field substitution
unknown, missing, duplicate and wrong-type fields
integer-as-boolean, float, NaN and duplicate JSON key
runtime_usable, Command, Task or effect authority set true
nonzero real runtime, database, provider, sensing, private Memory or effect count
```

Rejection must arise from the R3 owner-source, history, schema or boundary rule,
not stale hashes, incomplete dependency propagation, ordinary fixture anchors
or an exception.

## 10. Review package gate

The R3 package must include all R1, R2 and R3 subjects, all mandatory authority
inputs, the R2 review/disposition lineage, author evidence, manifest,
`ARCHIVE_MAP.yaml`, `CHECKSUMS.sha256` and package-local validator commands.

The exact ZIP must be delivered as a downloadable attachment. A reviewer that
cannot independently hash the ZIP, verify every declared input, fully read all
mandatory inputs and execute every fixed command cannot issue
`PASS_NO_BLOCKER`.

## 11. Stop rule

```yaml
F8_started: true
F8_R3_started: true
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
database_or_provider_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
real_effect_authorized: false
```

R3 stops at one fresh full atomic hash-bound independent review. Author PASS is
only package readiness evidence and cannot accept or freeze F8.
