# AGENTS OS F6 Validation Requirement Current Decision v0.1 R2 Amendment

Date: 2026-07-17  
Status: draft fixed only when bound by the R2 manifest  
Owner: Jenn  
Agent steward: Nobao  
Acceptance unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R2_ATOMIC_BUNDLE`

## 1. Amendment authority, precedence, and limit

This amendment closes only the ten findings in the fixed F6 R1 independent
review. The effective contract is:

```text
R2 explicit replacement clauses
then R1 clauses not explicitly replaced by R2
```

The atomic review unit contains the four immutable R1 subjects and four new R2
subjects. Partial acceptance is forbidden. R2 does not add a Validation state,
Task state, waiver kind, delivery state, receipt semantic, provider protocol,
runtime interface, database layout, service, implementation or F7 authority.

R2 consumes owner-issued assessments. It does not recompute F1, F3 or F5
authority, classify an Actor or Task by permission level, or treat an F5
receipt as Validation authority.

## 2. R1 finding closure map

```yaml
S1_EXACT_VALIDATION_CONTEXT_BINDING:
  findings: [F6-R1-IR-B01]
S2_OWNER_ASSESSMENT_EXACTNESS:
  findings: [F6-R1-IR-B02, F6-R1-IR-B03]
S3_REQUIREMENT_WAIVER_PROVENANCE_GRAPH_CLOSURE:
  findings: [F6-R1-IR-B04, F6-R1-IR-B05, F6-R1-IR-B06]
S4_EXACT_EVIDENCE_AND_GRAPH_WITNESS_CLOSURE:
  findings: [F6-R1-IR-M01, F6-R1-IR-M02]
S5_REAL_SCHEMA_AND_CROSS_FIELD_PROOF:
  findings: [F6-R1-IR-B07, F6-R1-IR-m01]
```

The R1 self-review sentence that says `30` mutations is immutable historical
text. The effective regression count is `32` R1 mutations plus the 18 R1
independent defect probes.

## 3. Canonical validation order

Before trusting any identifier, fingerprint, assessment result or decision:

1. reject duplicate JSON object keys;
2. reject floats, booleans where integers are required, non-NFC strings,
   unsafe integers, unknown fields, unknown enums and invalid nullability;
3. validate the ten-entry schema registry and one closed canonical instance per
   schema;
4. recompute stable IDs, typed fingerprints and sorted-unique set fingerprints;
5. validate complete Requirement revision and Event partial-order graphs;
6. validate owner assessment subject, revision, result, current head,
   observation watermark and exact subject fingerprint;
7. reduce current attempt and waiver heads;
8. reduce Requirement decisions, Validation Set decision and Task completion
   eligibility from the same barrier and context;
9. validate stored canonical decision instances against the derived results;
10. only an implementation profile accepted later may perform the atomic Task
    transition. This synthetic contract never performs that transition.

An error, missing object, unavailable owner assessment, conflicting head or
unknown relation is fail-closed.

## 4. Ten closed normative schema profiles

R2 replaces the R1 hard-coded schema-count claim. The fixture MUST contain a
sorted, duplicate-free registry with exactly these ten profiles and a closed
canonical instance for each:

```text
F3CanonicalReadBarrierInputV0_1R2
TrustedTimeInputV0_1R2
OpaqueUpstreamAssessmentInputV0_1R2
ValidationRequirementRevisionV0_1R2
RequirementWaiverEventV0_1R2
ValidationSetSnapshotV0_1R2
ValidationAttemptRevisionV0_1R2
ValidationRequirementCurrentDecisionV0_1R2
ValidationSetCurrentDecisionV0_1R2
TaskCompletionEligibilityDecisionV0_1R2
```

Each profile binds:

```yaml
schema_name:
schema_revision: 2
closed_fields: []
canonical_instance_ref:
canonical_instance_fingerprint:
schema_fingerprint:
```

`schema_fingerprint` is the typed hash of the exact schema name, revision,
ordered field inventory, enum inventory, nullability and scalar constraints.
The validator derives `normative_schema_count` from validated registry rows;
no summary literal may substitute for the inventory.

## 5. Exact owner assessment consumption

`OpaqueUpstreamAssessmentInputV0_1R2` retains the R1 owner boundary but replaces
opaque unused revisions with exact typed subjects:

```yaml
assessment_id:
assessment_revision:
assessment_kind:
owner_phase:
subject_ref:
subject_revision:
subject_fingerprint:
result:
result_detail:
observed_at_event_sequence:
read_barrier_id:
read_barrier_fingerprint:
is_current_head:
assessment_fingerprint:
```

For every assessment consumed by F6, the consumer MUST supply an exact expected
tuple:

```text
(assessment_kind,
 owner_phase,
 subject_ref,
 subject_revision,
 subject_fingerprint,
 required result,
 read barrier,
 current head)
```

The assessment is acceptable only when every tuple component matches. Merely
matching a ref and fingerprint while carrying another revision is invalid.

Task completion replaces caller-supplied `task_lifecycle` with a current F1
`TASK_CURRENT_STATE` assessment whose exact subject binds:

```yaml
task_id:
task_revision:
task_state_revision:
task_lifecycle: VERIFYING
candidate_commitment_ref:
candidate_commitment_revision:
candidate_commitment_fingerprint:
dependency_closure_ref:
dependency_closure_revision:
dependency_closure_fingerprint:
```

F6 reads this assessment; it does not derive or write the F1 Task state.

## 6. Exact validation context binding

Every terminal attempt used as `PASSED` binds one
`ValidationContextBindingV0_1R2` tuple:

```yaml
requirement_id:
requirement_revision:
validation_set_snapshot_id:
validation_set_snapshot_revision:
validation_set_snapshot_fingerprint:
task_candidate_ref:
task_candidate_revision:
task_candidate_fingerprint:
dependency_closure_ref:
dependency_closure_revision:
dependency_closure_fingerprint:
validator_contract_ref:
validator_contract_revision:
validator_contract_fingerprint:
evidence_set_fingerprint:
context_fingerprint:
```

The current Requirement reducer and completion reducer MUST use the same exact
snapshot, candidate and dependency tuple. Separately current candidate A and
candidate B are not interchangeable. The same applies to dependency closures.

## 7. Requirement revision and provenance closure

The effective Requirement graph contains every revision from 1 through the
current revision. For each `requirement_id`:

```text
revision 1 -> predecessor ref/revision/fingerprint are null
revision N -> predecessor is exact revision N-1 object
```

Revision values are exact positive JSON integers; booleans are invalid. The
graph rejects gaps, branches, duplicate revisions, missing predecessors,
cycles, mismatched predecessor fingerprints and more than one current head.

Each Requirement provenance row binds an owner-issued current assessment:

```yaml
source_kind:
source_ref:
source_revision:
source_fingerprint:
source_owner_assessment_ref:
source_owner_assessment_revision:
source_owner_assessment_fingerprint:
creation_command_ref:
creation_command_fingerprint:
creation_event_ref:
creation_event_sequence:
creation_event_fingerprint:
```

Allowed source kinds remain the R1 closed set. A source label such as
`JENN_EXPLICIT` never proves its own authority. The exact owner assessment and
authenticated F3 Command/Event binding are mandatory.

The Validation Set source closure is the sorted, duplicate-free exact union of
all current Requirement provenance rows. Omission, substitution, duplication,
conflicting fingerprints or unassessed extra provenance is invalid.

## 8. Waiver authority and current head

A waiver GRANT binds:

```yaml
requirement_id:
requirement_revision:
waivability: WAIVABLE
jenn_decision_ref:
jenn_decision_revision:
jenn_decision_fingerprint:
jenn_authority_assessment_ref:
jenn_authority_assessment_revision:
jenn_authority_assessment_fingerprint:
command_ref:
command_fingerprint:
event_ref:
event_sequence:
event_fingerprint:
valid_from_sequence:
expires_at_sequence:
```

The Jenn authority assessment MUST assess the exact immutable decision bytes,
revision and fingerprint as `CURRENT_ACCEPTED`. The committed F3 Command/Event
must bind that same decision and exact Requirement revision. Caller-selected
decision refs, labels or fingerprints are invalid.

Only the unique terminal waiver head may be used. Expired, revoked,
superseded, branched, stale, unknown or indeterminate heads fail closed; an old
GRANT is never revived. `WAIVED` is not `PASSED`, cannot waive `NON_WAIVABLE`,
and an empty or all-waived required set is not satisfied.

## 9. Cross-object Event partial order

For every accepted graph the validator MUST enforce:

```text
Requirement predecessor Event
< Requirement revision creation Event
<= every Validation Set snapshot containing that revision

base Validation Set snapshot
< Jenn waiver decision
<= waiver Command
<= waiver Event
<= WAIVER_CHANGE snapshot consuming the waiver head

current Validation Set snapshot
<= attempt creation Event
<= evidence observation
<= trusted evaluation sequence
<= F3 read barrier high watermark
```

The exact relation may be equality only where explicitly shown. Missing or
unreproducible Event sequence data blocks the decision.

## 10. Exact evidence set

An attempt contains a sorted, duplicate-free `evidence_bindings` array. Each
row contains the exact evidence ref, revision, fingerprint, assessment ref,
assessment revision and assessment fingerprint. The attempt binds the typed
hash of the complete array as `evidence_set_fingerprint`.

The consumed evidence set MUST equal that array exactly. Extra unassessed refs,
missing refs, duplicate refs, unsorted refs, digest substitution or a partially
assessed set is invalid.

## 11. Method and authority cross-field matrix

The Requirement reducer replaces the incomplete R1 matrix with these mandatory
relations:

```text
latest_attempt_state=PASSED
  -> authority_result=CURRENT_ACCEPTED
  -> evidence_set=EXACT_CURRENT
  -> context=EXACT_CURRENT

method=FRESH_VALIDATION
  -> carry_forward_status=NOT_APPLICABLE

method=EVIDENCE_CARRY_FORWARD_REVIEW
  -> original source is one FRESH_VALIDATION PASSED attempt
  -> source is not another carry-forward
  -> evidence is not HUMAN_ACCEPTANCE
  -> evidence is not effectful delivery evidence

effectful=false
  -> F5 binding and F5 assessment are NOT_APPLICABLE

effectful=true
  -> exact F5 subject binding is required
  -> F5 result must be APPLIED_CURRENT supporting evidence
  -> independent Validation authority and evidence remain mandatory
```

`NOT_APPLICABLE`, `REJECTED`, `INDETERMINATE`, missing or unknown authority can
never produce `PASSED`, `SATISFIED` or `ELIGIBLE`.

## 12. Canonical decision instances

R2 requires closed canonical instances for all three output decisions. Each
decision binds exact subject refs/revisions/fingerprints, read barrier, trusted
time, sorted reason codes, deterministic primary reason and decision
fingerprint.

The validator derives the result and reasons independently, then requires exact
equality with the stored instance. It rejects any contradictory combination,
including:

```text
SATISFIED with authority other than CURRENT_ACCEPTED
SATISFIED with context or evidence closure mismatch
WAIVED without current authenticated Jenn decision
ELIGIBLE without F1-owned VERIFYING current state
ELIGIBLE with a different candidate or dependency context
```

## 13. Required graph witnesses

The R2 fixture contains three positive synthetic, nonauthority, nonruntime
graphs:

1. an original `FRESH_VALIDATION` current `PASSED` Requirement;
2. a legal carry-forward whose source resolves directly to that original fresh
   PASSED attempt and whose review evidence is independently exact;
3. an effectful Requirement whose exact F5 subject is `APPLIED_CURRENT`
   supporting evidence while independent Validation authority produces PASS.

It also contains graph-level negative regression specifications for chain
carry-forward, human/effectful evidence reuse, wrong F5 subject,
`HISTORY_ONLY`, `INDETERMINATE`, non-effectful F5 attachment and F5-as-PASS.

Synthetic data is domain-separated as `SYNTHETIC_TEST`, has
`runtime_usable=false`, and cannot be restored or consumed as real authority.

## 14. R2 regression floor

The offline validator MUST independently execute:

```yaml
R1_fixed_mutations: 32/32_REJECTED
R1_independent_defect_probes: 18/18_REJECTED
mutation_exceptions: 0
```

It must additionally reject schema inventory mismatch, unknown output fields,
output cross-field contradictions, Requirement branch/gap/cycle, unassessed
provenance, invalid Event order, extra evidence and context mismatch. Mutation
failures are counted only when the mutated fully re-signed object reaches a
normal validator rejection; an exception is a validator failure.

## 15. Atomic completion seam

The R1 same-transaction rule remains, with the bound input set replaced by the
R2 exact context:

```text
current F1 Task state assessment proves VERIFYING
+ current Validation Set decision is SATISFIED
+ every PASSED attempt uses the same current candidate/dependency context
+ dependency owner assessment is CURRENT_CONFIRMED
+ exact completion guard and F5 blocker assessments are current
+ all five quiescence counts are zero
+ all assessment revisions and watermarks match
-> eligibility only
```

An implementation accepted later must re-read and revalidate all inputs in the
same transaction as the completion Event and Task transition. Any revision,
head, snapshot, candidate, dependency, assessment, watermark or count change
returns `NOT_ELIGIBLE` or `INDETERMINATE`; no real transition is performed by
this R2 fixture or validator.

## 16. Stop rule and non-authorization

R2 is freeze-eligible only after a fresh independent reviewer verifies all
eight subjects, all manifest authority inputs, both fixed commands, all 50
carried regressions and all R2 negative cases with `PASS_NO_BLOCKER`.

R3 is not preplanned. Only a new independent reproducible safety
counterexample may justify R3. Implementation-profile questions do not.

Nothing in R2 authorizes F6 acceptance or freeze, F7, implementation, runtime
activation, production authentication, database or service work, provider or
effect execution, real Task/Run/Validation/Event/waiver/completion mutation,
commit, push, PR, merge, tag, release, deploy or publish.
