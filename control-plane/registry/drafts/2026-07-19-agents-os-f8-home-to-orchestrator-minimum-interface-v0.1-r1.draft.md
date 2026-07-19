# AGENTS OS F8 Home-to-Orchestrator Minimum Interface v0.1 R1

Status: fixed only when bound by an F8 R1 atomic manifest  
Date: 2026-07-19  
Owner: Jenn  
Agent steward: Nobao

## 1. Contract boundary

F8 defines the minimum logical interface between an F7 `INTENT_CANDIDATE` and
a future F3-owned Orchestrator intake submission. F8 does not define a runtime,
transport, database, queue, service, provider adapter, Task writer, Command
writer, permission system, identity authority or effect authority.

```yaml
contract_id: F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R1
interface_classification: LOGICAL_NONRUNTIME_CANDIDATE_HANDOFF
runtime_usable: false
implementation_authorized: false
production_profile_included: false
Phase_5A_started: false
```

The interface is deliberately asymmetric:

```text
F7 INTENT_CANDIDATE
  -> F8 may form a nonauthoritative handoff candidate
  -> an adapter may later construct an F3 CommandSubmission candidate
  -> F3 alone authenticates, admits, commits, rejects and replays a Command
  -> F1/F4/F5/F6 remain the owners of Task, effect, delivery and validation facts
```

`CANDIDATE_FORMED` is not permission, authentication, admission, Command
commitment, Task creation, effect admission or proof that F3 is ready.

## 2. Upstream authority consumption

F8 consumes exact hash-bound owner assessments. It may verify:

```text
reference existence
exact subject ref / revision / fingerprint
assessment revision and immutable fingerprint
current-head marker
event watermark
closed result value
exact context binding where the owner assessment is contextual
```

F8 must not:

```text
rebuild F1 Task state
rebuild F2 Actor, Principal, Binding, responsibility or delegation state
authenticate a Command
rebuild F3 Resident readiness, intake or replay state
rebuild F4 effect admission
rebuild F5 delivery or recovery state
rebuild F6 validation or completion state
reclassify an F7 semantic object
infer authority from actor class, role name, relationship, trust, urgency,
historical success, sentiment, proximity or a permission level
```

Missing, stale, conflicting, malformed, unavailable or context-mismatched
authority fails closed. A Prohibited Behavior List no-match is only one required
input; it never creates permission.

## 3. Closed synthetic assessment input

The R1 constructive witness uses only the following closed assessment shape:

```yaml
UpstreamOwnerAssessmentV0_1:
  assessment_id: stable_ref
  assessment_revision: positive_safe_integer
  owner_contract: F2 | F3 | F7 | POLICY | JENN_DECISION
  assessment_kind: closed_enum
  subject_ref: stable_ref
  subject_revision: positive_safe_integer
  subject_fingerprint: lowercase_sha256
  context_fingerprint: lowercase_sha256_or_null
  result: closed_value_for_assessment_kind
  based_on_event_sequence: positive_safe_integer
  is_current_head: strict_json_boolean
  row_fingerprint: lowercase_sha256
```

The closed kind/result map is:

| assessment_kind | owner | accepted favorable result | other closed results |
|---|---|---|---|
| `F7_INTENT_CURRENTNESS` | F7 | `CURRENT_ACCEPTED` | `STALE`, `INDETERMINATE` |
| `F2_ACTOR_IDENTITY` | F2 | `ACTIVE` | `INACTIVE`, `INDETERMINATE` |
| `F2_PRINCIPAL_BINDING` | F2 | `ACTIVE` | `INACTIVE`, `INDETERMINATE` |
| `F2_RESPONSIBILITY` | F2 | `ACTIVE` | `INACTIVE`, `INDETERMINATE` |
| `F3_RESIDENT_READINESS` | F3 | `READY_CONTINUOUS` | `NOT_READY`, `INDETERMINATE` |
| `PBL_CURRENTNESS` | POLICY | `CURRENT_NO_MATCH` | `PROHIBITED`, `INDETERMINATE` |
| `JENN_REQUIREMENT` | POLICY | `NO_EXACT_DECISION_REQUIRED`, `EXACT_DECISION_REQUIRED` | `INDETERMINATE` |
| `JENN_EXACT_DECISION` | JENN_DECISION | `CURRENT_ACCEPTED` | `REJECTED`, `INDETERMINATE` |
| `F3_INTAKE_OUTCOME` | F3 | `SYNTHETIC_TEST_COMMITTED`, `REJECTED`, `NOT_SUBMITTED` | `INDETERMINATE` |

These fixture assessments are synthetic nonauthority evidence. They do not
assert that a real owner emitted any assessment.

Every consumer binds both `assessment_id` and its exact
`expected_assessment_revision`. The revision must equal the resolved owner
assessment revision. A consumer cannot select a historical or invented value.

## 4. Prospective F3 interface requirement

F8 R1 records, but does not accept on F3's behalf, this downstream seam:

```yaml
ProspectiveF3HomeIntentInterfaceRequirementV0_1:
  requirement_id: F3_HOME_INTENT_HANDOFF_COMMAND_TYPE
  owner: F3
  status: UNACCEPTED_DOWNSTREAM_REQUIREMENT
  usable_in_runtime: false
  synthetic_fixture_only: true
  required_F3_contract: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
  required_submission_interface: agents-os.command-submission.v0.1
  required_intake_results:
    - COMMITTED
    - REJECTED
    - INDETERMINATE
  F8_may_mint_command: false
  F8_may_mint_authentication: false
  F8_may_commit_intake: false
```

This object is an interface requirement, not a frozen F3 Command type, registry
revision, payload schema, replay ledger or temporary Command authority. A future
F3 compatibility decision must own and accept any concrete Command type before
runtime use. Synthetic fixtures cannot satisfy that future gate.

## 5. Handoff input and context

```yaml
AssessmentConsumerV0_1:
  assessment_id: stable_ref_or_null
  expected_assessment_revision: positive_safe_integer_or_null

HomeIntentHandoffRawInputV0_1:
  environment: SYNTHETIC_TEST
  intent_candidate_ref: stable_ref
  intent_candidate_revision: positive_safe_integer
  intent_candidate_fingerprint: lowercase_sha256
  intent_semantic_class: INTENT_CANDIDATE_or_closed_wrong_class_for_negative_case
  creator_actor_ref: stable_ref
  creator_actor_revision: positive_safe_integer
  creator_actor_fingerprint: lowercase_sha256
  principal_ref: stable_ref
  principal_revision: positive_safe_integer
  principal_fingerprint: lowercase_sha256
  target_kind: ORCHESTRATOR_INTAKE_CANDIDATE_or_closed_wrong_target_for_negative_case
  target_ref: stable_ref
  target_revision: positive_safe_integer
  target_fingerprint: lowercase_sha256
  payload_schema_ref: stable_ref
  payload_schema_fingerprint: lowercase_sha256
  payload_commitment: lowercase_sha256
  explicit_action_choice: strict_json_boolean
  direct_task_write_requested: strict_json_boolean
  direct_command_commit_requested: strict_json_boolean
  effect_execution_requested: strict_json_boolean
  relationship_or_trust_used_as_authority: strict_json_boolean
  pbl_no_match_used_as_sufficient: strict_json_boolean
  production_profile_requested: strict_json_boolean
  runtime_usable_requested: strict_json_boolean
  trusted_event_sequence: positive_safe_integer
  context_fingerprint: lowercase_sha256
  assessment_consumers:
    f7_intent_currentness: AssessmentConsumerV0_1
    actor_identity: AssessmentConsumerV0_1
    principal_binding: AssessmentConsumerV0_1
    responsibility: AssessmentConsumerV0_1
    f3_readiness: AssessmentConsumerV0_1
    pbl_currentness: AssessmentConsumerV0_1
    jenn_requirement: AssessmentConsumerV0_1
    jenn_exact_decision: AssessmentConsumerV0_1
```

`context_fingerprint` is SHA-256 over the exact intent tuple, creator tuple,
principal tuple, target tuple, payload schema tuple, payload commitment,
explicit action choice and trusted handoff Event sequence. It excludes
assessment results, so owner assessments can bind the subject without a
result/fingerprint cycle. Every consumed assessment must be based on an Event
sequence greater than or equal to `trusted_event_sequence`; an older watermark
rejects even when `is_current_head` is true.

The F7 assessment must bind the exact intent tuple. Actor and Principal
assessments bind their exact tuples. Responsibility and any Jenn requirement or
decision bind the exact target and context. F3 readiness binds the exact frozen
F3 contract subject. PBL currentness binds the exact current PBL revision.

## 6. Total handoff reducer

The closed results are:

```text
CANDIDATE_FORMED
REJECTED
DEFERRED
INDETERMINATE
```

The closed reason precedence is:

```text
UNKNOWN_OR_MALFORMED_INPUT
SYNTHETIC_DOMAIN_VIOLATION
EXPLICIT_ACTION_CHOICE_MISSING
DIRECT_TASK_WRITE_FORBIDDEN
DIRECT_COMMAND_COMMIT_FORBIDDEN
EFFECT_EXECUTION_FORBIDDEN
RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY
PBL_NO_MATCH_IS_NOT_PERMISSION
INTENT_SEMANTIC_CLASS_MISMATCH
TARGET_KIND_OUTSIDE_F8
CONTEXT_FINGERPRINT_MISMATCH
ASSESSMENT_MISSING_OR_UNRESOLVABLE
ASSESSMENT_REVISION_MISMATCH
ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH
ASSESSMENT_WATERMARK_BEHIND
UPSTREAM_ASSESSMENT_NOT_CURRENT
UPSTREAM_CURRENTNESS_UNAVAILABLE
F7_INTENT_NOT_CURRENT
ACTOR_IDENTITY_NOT_ACTIVE
PRINCIPAL_BINDING_NOT_ACTIVE
RESPONSIBILITY_NOT_ACTIVE
F3_NOT_READY
PBL_PROHIBITED
EXACT_JENN_DECISION_MISSING_OR_INVALID
F3_INTERFACE_REQUIREMENT_UNACCEPTED
VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE
```

All simultaneously true reasons are emitted as a sorted unique closed set.
`primary_reason` is the first by this precedence.

Reduction order:

```text
closed schema and canonical value validation
-> exact context recomputation
-> assessment resolution and revision equality
-> exact subject/context binding
-> current-head and closed result interpretation
-> Jenn exact decision check only when the owner requirement says REQUIRED
-> prospective F3 production-profile deferral
-> result/reason totality
```

Result selection is deterministic:

```text
any structural authority-expansion or direct-write reason
  -> REJECTED

otherwise any missing, unresolvable or INDETERMINATE currentness input
  -> INDETERMINATE

otherwise production_profile_requested while the F3 requirement is unaccepted
  -> DEFERRED / F3_INTERFACE_REQUIREMENT_UNACCEPTED

otherwise every favorable input and synthetic nonruntime profile
  -> CANDIDATE_FORMED / VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE

otherwise
  -> REJECTED
```

The output always includes:

```yaml
command_authority: false
task_write_authority: false
effect_authority: false
runtime_usable: false
F3_recheck_required: true
F3_command_ref: null
F3_intake_ref: null
```

## 7. Immutable handoff candidate revision

Only a favorable synthetic reduction may construct:

```yaml
HomeIntentHandoffCandidateRevisionV0_1:
  handoff_candidate_id: stable_ref
  handoff_candidate_revision: positive_safe_integer
  predecessor_ref: stable_ref_or_null
  predecessor_fingerprint: lowercase_sha256_or_null
  intent_candidate_ref: stable_ref
  intent_candidate_revision: positive_safe_integer
  intent_candidate_fingerprint: lowercase_sha256
  target_ref: stable_ref
  target_revision: positive_safe_integer
  target_fingerprint: lowercase_sha256
  payload_commitment: lowercase_sha256
  context_fingerprint: lowercase_sha256
  assessment_set_fingerprint: lowercase_sha256
  created_event_ref: stable_ref
  created_event_fingerprint: lowercase_sha256
  runtime_usable: false
  command_authority: false
  candidate_fingerprint: lowercase_sha256
```

Revision 1 has null predecessor fields. Revision N greater than 1 binds exact
revision N-1. Changing intent, target, payload, context, assessment set or Event
requires a new immutable candidate revision. Same-revision re-signing is
forbidden. The manifest-bound fixture contains fixed history anchors so a fully
re-signed same-revision rewrite is rejected by the offline validator.

The candidate never contains an authentication assertion, authenticated
context, Command envelope, intake record, replay entry, Task mutation, permit,
delivery record or validation result.

## 8. F3 acknowledgement projection

F8 may project a low-disclosure acknowledgement only from an exact current
F3-owner assessment bound to the same handoff candidate:

```yaml
HomeIntentHandoffAcknowledgementRawInputV0_1:
  handoff_candidate_ref: stable_ref
  handoff_candidate_fingerprint: lowercase_sha256
  F3_outcome_assessment_id: stable_ref
  expected_assessment_revision: positive_safe_integer

HomeIntentHandoffAcknowledgementDecisionV0_1:
  result: NOT_SUBMITTED | ACKNOWLEDGED_COMMITTED | ACKNOWLEDGED_REJECTED | ACKNOWLEDGED_INDETERMINATE
  reason_codes: sorted_unique_closed_set
  primary_reason: closed_reason
  command_authority: false
  task_write_authority: false
  effect_authority: false
  runtime_usable: false
```

The assessment subject must equal the exact candidate ref and fingerprint. The
assessment revision must equal the resolved owner assessment revision. Missing,
stale, mismatched or unavailable owner evidence becomes
`ACKNOWLEDGED_INDETERMINATE`; a caller-supplied outcome label is never trusted.

`ACKNOWLEDGED_COMMITTED` reports only an F3-owned synthetic fixture result. It
does not itself create a Command, Task, permission or effect and cannot be
copied into a production profile.

## 9. Schema and canonicalization closure

R1 freezes ten schema profiles:

```text
UpstreamOwnerAssessmentV0_1
AssessmentConsumerV0_1
HomeIntentHandoffRawInputV0_1
HomeIntentHandoffDecisionV0_1
HomeIntentHandoffDecisionCaseV0_1
HomeIntentHandoffCandidateRevisionV0_1
ProspectiveF3HomeIntentInterfaceRequirementV0_1
HomeIntentHandoffAcknowledgementRawInputV0_1
HomeIntentHandoffAcknowledgementDecisionV0_1
BoundaryAssertionsV0_1
```

Every object uses exact fields. Unknown fields, duplicate JSON keys, floats,
NaN/Infinity, non-NFC strings, booleans represented as 0/1, out-of-range
integers, unknown enum values, invalid nullability and cross-field
contradictions reject before fingerprints are trusted.

Canonical bytes are UTF-8 JSON with sorted keys, no insignificant whitespace,
NFC strings, no floats and safe integers. Fingerprints are SHA-256 over a
domain tag, one NUL byte and the canonical bytes.

## 10. Required R1 case inventory

The fixed fixture contains exactly `H01` through `H25` in order. It covers:

```text
one valid synthetic nonauthority candidate
wrong semantic class
missing explicit action choice
direct Task write
direct Command commit
effect execution request
relationship/trust authority expansion
PBL no-match treated as permission
unknown and stale F7 currentness
inactive Actor
inactive Principal binding
inactive Responsibility
Responsibility target/context mismatch
unknown F3 readiness
PBL prohibition
required Jenn decision missing
Jenn decision target/context mismatch
target outside F8
payload/context mismatch
production-profile deferral
consumer assessment revision mismatch
intent subject/fingerprint mismatch
runtime-usable synthetic-domain violation
current-head assessment with a watermark behind the trusted Event sequence
```

The validator anchors the exact ID set, order and complete raw input for all 25
cases. Replacing a rejection case with a locally valid positive case, renaming,
reordering or deleting a case fails even after all row, section and root hashes
are recomputed.

## 11. Required adversarial validation

At minimum the offline validator must fully re-sign and reject:

```text
case claim substitution for every H01-H25 row
assessment watermark behind the trusted handoff observation sequence
case deletion, rename, reorder and positive-case substitution
unknown root, section, row and nested fields
duplicate JSON key
float, NaN and integer-as-boolean
assessment revision substitution
assessment subject/context substitution
same-revision assessment rewrite
same-revision handoff candidate rewrite
prospective F3 requirement runtime_usable=true
prospective F3 requirement status changed to accepted
F8 Command or Task authority set true
nonzero runtime/provider/database/private-memory/sensing/effect occurrence
acknowledgement outcome changed without F3-owner assessment
acknowledgement assessment bound to another candidate
```

Rejection must arise from the target semantic or schema rule, not stale hashes,
missing dependent-reference propagation or an unhandled exception.

## 12. Constructive M0-B interface witness

The synthetic witness proves only:

```text
one F7-shaped synthetic INTENT_CANDIDATE tuple
-> exact owner-assessment consumption
-> one nonauthoritative F8 handoff candidate history
-> one synthetic-only acknowledgement projection
-> zero real Command, Task, permit, provider, database, sensing or effect
```

It does not prove Phase 5A or Phase 5B implementation readiness. It does not
create a production Command type. Its terminal outcome is `NOT_EXECUTED`.

## 13. Authority and privacy invariants

```yaml
second_permission_system: false
second_identity_authority: false
second_Task_writer: false
second_Command_writer: false
F1_through_F7_reducer_reimplementation: false
relationship_or_trust_expands_authority: false
PBL_no_match_creates_permission: false
synthetic_fixture_becomes_production_authority: false
private_raw_memory_read_or_write: false
runtime_or_service_started: false
database_created_or_written: false
provider_called: false
sensing_or_recording_started: false
real_effect_executed: false
```

## 14. Acceptance and downstream boundary

Author validation and author self-review do not accept F8. Independent
`PASS_NO_BLOCKER` also does not accept or freeze F8. Only an exact later Jenn
atomic decision may accept and freeze the complete hash-bound unit.

F8 acceptance, if later granted, still does not authorize:

```text
Phase 5A or Phase 5B start
Rust or JavaScript implementation
database schema or migration
F3 registry or Command type activation
runtime, service, provider or host execution
production authentication or credential changes
private Memory access
sensing or recording
real Task, Command or effect creation
commit, push, PR or merge without separate delivery authority
```
