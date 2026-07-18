# AGENTS OS F6 Validation Requirement Current Decision v0.1 R3 Amendment

Date: 2026-07-18  
Status: draft fixed only when bound by the R3 manifest  
Owner: Jenn  
Agent steward: Nobao  
Acceptance unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R3_ATOMIC_BUNDLE`

## 1. Amendment authority, precedence, and limit

This amendment closes only the seven blockers and one major finding in the
fixed F6 R2 independent review. The effective contract is:

```text
R3 explicit replacement clauses
then R2 clauses not explicitly replaced by R3
then R1 clauses not explicitly replaced by R2 or R3
```

The atomic review unit contains four immutable R1 subjects, four immutable R2
subjects and four new R3 subjects. Partial acceptance is forbidden. R3 does
not add a Validation state, Task state, waiver operation, evidence class,
delivery state, retry model, provider protocol, runtime interface, database
layout, service, implementation or F7 authority.

R3 consumes exact owner-issued facts. It does not reconstruct F1, F3 or F5,
classify an Actor or Task by permission level, or promote an F5 result into
Validation authority.

## 2. R2 finding closure map

```yaml
S1_MACHINE_VERIFIABLE_SCHEMA_AND_OUTPUT_TOTALITY:
  findings: [F6-R2-IR-B01]
S2_OWNER_ASSESSMENT_AND_CONTEXT_EXACTNESS:
  findings: [F6-R2-IR-B02]
S3_WAIVER_PROVENANCE_AND_EVENT_ORDER_ROOT_CLOSURE:
  findings: [F6-R2-IR-B03, F6-R2-IR-B04, F6-R2-IR-B05]
S4_F5_AND_CARRY_SOURCE_EXACTNESS:
  findings: [F6-R2-IR-B06, F6-R2-IR-B07]
S5_EVIDENCE_OBJECT_ASSESSMENT_AND_REVISION_IMMUTABILITY:
  findings: [F6-R2-IR-M01]
```

The fixed R2 author output `total_R2_mutations_rejected=30` means the 18 R1
independent regressions plus 12 R2 negatives. The complete fixed regression
count is `32 + 18 + 12 = 62`. R3 reports those counts separately.

## 3. R3 effective witness shape

The R3 fixture contains one complete R2 effective fixture plus R3 closure data:

```yaml
schema_version: agents-os.f6.validation-current-decision-r3-proof.v0.1
environment: SYNTHETIC_TEST
runtime_usable: false
r2_bindings: {}
effective_fixture: {}
schema_constraint_profiles: []
authority_root_bindings: []
context_assessment_bindings: []
attempt_commitments: []
event_order_edges: []
regression_catalog: {}
occurrence_assertions: {}
summary: {}
root_fingerprint: lowercase_sha256
```

The R2 fixture is not accepted merely because it is embedded. R3 revalidates
the entire R2 graph, then independently evaluates every R3 replacement rule
from the embedded raw objects.

## 4. Machine-verifiable schema constraint profiles

R3 replaces R2 profile rows that only carried field names. Each of the same ten
normative schemas MUST have exactly one profile containing:

```yaml
schema_name:
schema_revision: 3
closed_fields: []
field_constraints:
  <field>:
    value_kind: stable_string | stable_ref | lowercase_sha256 |
                boolean | positive_safe_integer |
                non_negative_safe_integer | object | array
    nullable: boolean
    allowed_values: null | []
    nested_profile: null | stable_string
    integer_min: null | integer
    integer_max: null | integer
nested_profiles: []
cross_field_rules: []
canonical_instance_ref:
canonical_instance_fingerprint:
schema_fingerprint:
```

`schema_fingerprint` binds the complete profile except itself. Every field in
every normative instance is checked against the bound constraint. Unknown
fields, unknown enum values, invalid nullability, booleans used as integers,
unsafe integers, malformed nested rows and incomplete nested objects reject
before a decision is trusted.

R3 defines closed nested profiles for provenance bindings, memberships, waiver
heads, evidence bindings, validation context, carry source, subject tuples,
decision bindings and the five-key completion count object. Tagged assessment
subject payloads are closed by assessment kind.

## 5. Owner assessment root and kind matrix

Every assessment kind has exactly one allowed owner phase and owner contract
root for this synthetic witness:

```text
F1 -> TASK_CURRENT_STATE
      CANDIDATE_COMMITMENT_CURRENTNESS
      DEPENDENCY_CLOSURE_CURRENTNESS

F3 -> REQUIREMENT_PROVENANCE_CURRENTNESS
      JENN_WAIVER_AUTHORITY_CURRENTNESS
      EVIDENCE_SET_CURRENTNESS
      VALIDATION_AUTHORITY_CURRENTNESS
      COMPLETION_GUARD_CURRENTNESS

F5 -> F5_DELIVERY_CURRENTNESS
      F5_COMPLETION_BLOCKING_CURRENTNESS
```

For each consumed assessment, R3 validates this exact tuple:

```text
(kind,
 owner phase,
 owner contract ref + fingerprint + revision,
 subject ref + revision + fingerprint + typed payload,
 result,
 assessment ref + revision + fingerprint,
 current-head flag,
 exact read barrier,
 observed sequence within that barrier)
```

Missing kinds, duplicate heads, phase/contract mismatch, wrong subject or an
unresolved owner root fail closed.

## 6. Candidate and dependency assessment cross-binding

Each Validation attempt and the completion decision has one R3 binding row:

```yaml
consumer_ref:
consumer_revision:
consumer_fingerprint:
candidate_assessment_ref:
candidate_assessment_revision:
candidate_assessment_fingerprint:
dependency_assessment_ref:
dependency_assessment_revision:
dependency_assessment_fingerprint:
binding_fingerprint:
```

The candidate and dependency tuples inside the attempt, F1 Task state and
completion decision MUST equal the exact subjects of those two assessments.
The same assessment refs and fingerprints are required for every current
PASSED attempt and completion. A separately current but different subject is
not interchangeable. Missing either assessment rejects.

## 7. Closed provenance source and typed creation graph

The allowed source kinds remain exactly the R1 set:

```text
NOBAO_TASK_SPEC
RUST_POLICY
GOAL_DOMAIN_CONTRACT
JENN_EXPLICIT
```

The R3 synthetic positive graph uses `NOBAO_TASK_SPEC`. Every provenance row
MUST resolve and validate:

```text
source object
current source owner assessment
CREATE_OR_REVISE_REQUIREMENT Command
REQUIREMENT_COMMITTED Event
exact Requirement id and revision
exact source ref, revision, kind and fingerprint
```

The Command subject and Event subject are typed hashes of that exact natural
subject. Unknown source kinds, wrong purposes, wrong Event kinds, unassessed
sources and source substitution reject.

## 8. Exact Jenn waiver root

A current waiver `GRANT` is valid only when all of these bytes agree:

```text
waiver Requirement id and revision
Jenn decision Requirement id and revision
Jenn decision result = CURRENT_ACCEPTED
waiver Command purpose = GRANT_REQUIREMENT_WAIVER
waiver Command subject = exact decision + Requirement tuple
waiver Event kind = WAIVER_COMMITTED
waiver Event Command and subject = exact Command and tuple
Jenn authority assessment subject = exact decision/Command/Event tuple
Jenn authority assessment owner = exact F3 owner root
```

The Jenn decision carries a synthetic decision Event sequence so the offline
proof can establish:

```text
base snapshot < Jenn decision <= waiver Event <= consuming snapshot
```

This field is proof-only and does not define production authentication.

## 9. Trusted time and complete typed Event order

`TrustedTimeInput` MUST resolve the exact F3 read barrier. Its observed sequence
must be within the barrier start/end interval. Every assessment and decision
must bind the same barrier and may not observe beyond trusted time.

The validator derives and verifies, rather than accepting labels for, these
relations:

```text
Requirement predecessor Event < Requirement revision Event
Requirement revision Event <= every containing snapshot freeze Event
base snapshot freeze Event < Jenn decision Event
Jenn decision Event <= waiver Event
waiver Event <= consuming snapshot freeze Event
current snapshot freeze Event <= attempt Event
attempt Event <= evidence assessment observation
evidence assessment observation <= trusted evaluation
trusted evaluation <= F3 barrier high watermark
```

Every supporting Command/Event must resolve to its typed subject. Missing or
incomparable relations fail closed. No runtime clock is introduced.

## 10. Exact F5 delivery support

For an effectful Requirement, the F5 assessment subject ref, revision,
fingerprint and typed payload MUST equal the exact delivery subject bound by
that Requirement. The assessment MUST be the current F5-owned head at the same
barrier and return `APPLIED_CURRENT`.

`APPLIED_CURRENT` remains supporting evidence. Independent Validation authority
and exact evidence are still mandatory before `PASSED`.

## 11. Exact original carry source

Carry-forward resolves both `source` and `root_source` tuples. Both tuples MUST
equal one and the same original `FRESH_VALIDATION` + `PASSED` attempt across:

```text
ref
revision
fingerprint
Requirement id and revision
```

That original source cannot itself carry forward. Any ref, revision or
fingerprint mismatch rejects before `PASSED` is derived.

## 12. Evidence object and assessment closure

Each evidence binding contains:

```yaml
evidence_ref:
evidence_revision:
evidence_fingerprint:
evidence_assessment_ref:
evidence_assessment_revision:
evidence_assessment_fingerprint:
```

The evidence object and its F3-owned current assessment MUST both resolve. The
assessment binds the exact evidence ref, revision, fingerprint, barrier and
observation sequence. The aggregate evidence assessment binds the exact sorted
unique array and its typed set fingerprint.

Each attempt revision also has an exact immutable commitment binding its
attempt ref/revision, predecessor, context, evidence set and committed Event.
Changing the evidence set requires a new contiguous attempt revision with the
prior revision as exact predecessor. Reusing an existing revision with changed
evidence rejects.

## 13. Closed decision and completion matrices

R3 validates these output relations independently:

```text
SATISFIED
  -> attempt head and context present
  -> waiver head absent
  -> primary reason = VALIDATION_PASSED

WAIVED
  -> attempt head and context absent
  -> current waiver head present
  -> primary reason = CURRENT_WAIVER

UNSATISFIED
  -> attempt and waiver heads absent
  -> primary reason = NO_CURRENT_PASS

Validation Set SATISFIED
  -> exact complete Requirement decision set
  -> each required member SATISFIED or validly WAIVED

Task ELIGIBLE
  -> exact F1 VERIFYING assessment
  -> exact candidate and dependency assessments
  -> exact current Validation Set decision
  -> exact F5 blocker CLEAR assessment
  -> exact completion guard CURRENT_ZERO assessment
  -> quiescence_counts has exactly five required keys, each exact integer zero
```

Result, reason, nullable bindings and booleans form one total matrix. A
`SATISFIED` decision carrying a waiver head, an empty count object or an unknown
result/reason combination rejects even when all hashes are recomputed.

## 14. Required R3 regressions

R3 acceptance evidence MUST execute normally and reject:

```yaml
R1_fixed_mutations: 32/32
R1_independent_regressions: 18/18
R2_additional_negatives: 12/12
fixed_total: 62/62
R2_independent_coordinated_probes: 17/17
mutation_or_probe_exceptions: 0
```

The 17 coordinated probes are evidence-bound by the fixed R2 review. A probe
counts only when all intended dependent references and fingerprints were
propagated and the target semantic rule, rather than a stale outer hash, caused
rejection.

## 15. Constructive witness and non-authorization

The R3 fixture remains deterministic `SYNTHETIC_TEST` evidence. It contains no
accepted real Task, Task transition, provider call, external effect, database
write, runtime activation, production credential or authentication occurrence.

```yaml
runtime_usable: false
accepted_real_task_count: 0
task_done_mutation_count: 0
runtime_activation_count: 0
external_effect_count: 0
provider_call_count: 0
database_write_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

R3 review success can only make the twelve-subject semantic bundle eligible
for Jenn's later atomic freeze decision. It cannot itself accept or freeze F6,
start F7, authorize implementation, activate runtime, create a database or
service, call a provider, perform an effect or authorize Git delivery.
