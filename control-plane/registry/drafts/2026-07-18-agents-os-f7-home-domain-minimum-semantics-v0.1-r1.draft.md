# AGENTS OS F7 Home Domain Minimum Semantics v0.1 R1

Status: fixed only when bound by an F7 R1 atomic manifest
Date: 2026-07-18
Owner: Jenn
Agent steward: Nobao

## 1. Contract boundary

F7 defines the minimum semantics of the Home Domain as a logical bounded
context. It does not define a process, database, service, provider, sensor,
memory store, permission system, identity authority, Task writer or second
ledger.

```yaml
contract_id: F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R1
home_domain_classification: LOGICAL_BOUNDED_CONTEXT
runtime_usable: false
implementation_authorized: false
production_profile_included: false
F8_started: false
```

F7 consumes accepted or frozen upstream facts. It may verify exact references,
fingerprints, revisions, current-head assessments and closed results. It must
not rebuild F1–F6 reducers or infer authority from identity name, relationship,
trust, role, urgency, sentiment, history or apparent usefulness.

## 2. Canonical semantic classes

The closed F7 R1 semantic classes are:

```text
STABLE_IDENTITY_FACT
IDENTITY_NARRATIVE
FORMAL_RELATIONSHIP_FACT
SUBJECTIVE_RELATIONSHIP_MEMORY
PRESENCE_POLICY
PRESENCE_CONSENT
DEVICE_SENSING_STATE
SESSION_CONTENT
LIFE_STREAM_CANDIDATE
MEMORY_CONTENT
MEMORY_ACCESS_AUTHORITY
MEMORY_CANDIDATE
INTENT_CANDIDATE
ORCHESTRATOR_COMMAND
GROWTH_EVENT
BEHAVIOR_POLICY_REVISION
AGENT_MEMBER_STATE
ARTIFACT
HOME_PROJECTION
TASK_CANONICAL_FACT
```

No implementation may add an unknown class or treat an unknown class as a
known broader class.

## 3. Fact authority profile

Every semantic class has exactly one authority profile. `writer_status` is one
of:

```text
UPSTREAM_CANONICAL
HOME_CANDIDATE_WRITER
POLICY_AUTHORITY
TARGET_NOT_IMPLEMENTED
DEFERRED_EXTERNAL_AUTHORITY
PROJECTION_ONLY
```

The normative mapping is:

| Class | Semantic owner/writer | writer_status | May trigger action alone |
|---|---|---|---|
| `STABLE_IDENTITY_FACT` | F2 identity authority | `UPSTREAM_CANONICAL` | No |
| `IDENTITY_NARRATIVE` | identified Agent self-record candidate | `HOME_CANDIDATE_WRITER` | No |
| `FORMAL_RELATIONSHIP_FACT` | future Resident Home relationship reducer | `TARGET_NOT_IMPLEMENTED` | No |
| `SUBJECTIVE_RELATIONSHIP_MEMORY` | identified Agent self-record candidate | `HOME_CANDIDATE_WRITER` | No |
| `PRESENCE_POLICY` | Jenn-governed policy | `POLICY_AUTHORITY` | No |
| `PRESENCE_CONSENT` | future authenticated consent authority | `TARGET_NOT_IMPLEMENTED` | No |
| `DEVICE_SENSING_STATE` | authenticated physical host, accepted upstream | `TARGET_NOT_IMPLEMENTED` | No |
| `SESSION_CONTENT` | session host transient authority | `DEFERRED_EXTERNAL_AUTHORITY` | No |
| `LIFE_STREAM_CANDIDATE` | exact candidate creator | `HOME_CANDIDATE_WRITER` | No |
| `MEMORY_CONTENT` | governed VCP-native Memory authority | `DEFERRED_EXTERNAL_AUTHORITY` | No |
| `MEMORY_ACCESS_AUTHORITY` | future governed Memory bridge | `DEFERRED_EXTERNAL_AUTHORITY` | No |
| `MEMORY_CANDIDATE` | exact candidate creator | `HOME_CANDIDATE_WRITER` | No |
| `INTENT_CANDIDATE` | exact candidate creator | `HOME_CANDIDATE_WRITER` | No |
| `ORCHESTRATOR_COMMAND` | F3 command authority | `UPSTREAM_CANONICAL` | Only after F3/F4 admission |
| `GROWTH_EVENT` | exact event observer candidate | `HOME_CANDIDATE_WRITER` | No |
| `BEHAVIOR_POLICY_REVISION` | Jenn or accepted delegated policy authority | `POLICY_AUTHORITY` | No direct action |
| `AGENT_MEMBER_STATE` | future Resident Home member reducer | `TARGET_NOT_IMPLEMENTED` | No |
| `ARTIFACT` | corresponding artifact storage authority | `DEFERRED_EXTERNAL_AUTHORITY` | No |
| `HOME_PROJECTION` | deterministic projection only | `PROJECTION_ONLY` | No |
| `TASK_CANONICAL_FACT` | F1/F3 task authority | `UPSTREAM_CANONICAL` | Through accepted contracts only |

`TARGET_NOT_IMPLEMENTED` names a required logical owner. It is not evidence
that a writer, store, service or runtime currently exists.

## 4. Immutable revision envelope

Any F7-owned candidate uses:

```yaml
HomeCandidateRevisionV0_1:
  candidate_id: string
  candidate_revision: positive_safe_integer
  predecessor_ref: string_or_null
  predecessor_fingerprint: lowercase_sha256_or_null
  semantic_class: closed_enum
  creator_actor_assessment_ref: string
  creator_actor_assessment_fingerprint: lowercase_sha256
  source_subject_ref: string
  source_subject_revision: positive_safe_integer
  source_subject_fingerprint: lowercase_sha256
  created_event_ref: string
  created_event_fingerprint: lowercase_sha256
  payload_commitment: lowercase_sha256
  candidate_fingerprint: lowercase_sha256
```

Revision 1 requires null predecessor fields. Revision N greater than 1 requires
revision N-1 and the exact immutable predecessor fingerprint. Same-revision
resigning with changed source, creator, class, context or payload is forbidden.

Synthetic fixtures use a disjoint domain tag and cannot become production
facts even when every fingerprint is otherwise valid.

## 5. Nonpromotion reducer

The reducer consumes raw current inputs and derives one result:

```text
CANDIDATE_ACCEPTED
REJECTED
DEFERRED
INDETERMINATE
```

Closed reason codes are sorted and unique. `primary_reason` is the first code
under this precedence:

```text
UNKNOWN_OR_MALFORMED_INPUT
SYNTHETIC_DOMAIN_ONLY
UPSTREAM_CURRENTNESS_UNAVAILABLE
SOURCE_NOT_CURRENT
CREATOR_NOT_CURRENT
EXPLICIT_CHOICE_MISSING
TARGET_OUTSIDE_F7
TARGET_WRITER_NOT_IMPLEMENTED
RELATIONSHIP_CANNOT_EXPAND_AUTHORITY
IDENTITY_NARRATIVE_CANNOT_REWRITE_IDENTITY
SESSION_CANNOT_CREATE_TASK
MEMORY_CANDIDATE_IS_NOT_MEMORY
PRESENCE_CONSENT_IS_NOT_SENSING_STATE
GROWTH_EVENT_IS_NOT_POLICY_REVISION
CANDIDATE_ONLY_NO_ACTION_AUTHORITY
VALID_HOME_CANDIDATE
```

All simultaneously true failure reasons are included. Input order cannot change
the reason set, primary reason or result.

### 5.1 Allowed F7 candidate formations

F7 may return `CANDIDATE_ACCEPTED` only for these exact pairs:

```text
SESSION_CONTENT -> LIFE_STREAM_CANDIDATE
SESSION_CONTENT -> MEMORY_CANDIDATE
SESSION_CONTENT -> INTENT_CANDIDATE
SUBJECTIVE_RELATIONSHIP_MEMORY -> MEMORY_CANDIDATE
GROWTH_EVENT -> MEMORY_CANDIDATE
```

Requirements:

```text
source is current
creator assessment is current
explicit subject choice is true
synthetic or authorized future profile is exact
result remains candidate-only
action authority remains false
```

`CANDIDATE_ACCEPTED` never means accepted Memory, Task, Command, formal
relationship, sensing state, identity fact or policy revision.

### 5.2 Mandatory rejection and deferral

```text
IDENTITY_NARRATIVE -> STABLE_IDENTITY_FACT
  REJECTED / IDENTITY_NARRATIVE_CANNOT_REWRITE_IDENTITY

SUBJECTIVE_RELATIONSHIP_MEMORY -> FORMAL_RELATIONSHIP_FACT
  DEFERRED / TARGET_WRITER_NOT_IMPLEMENTED

any relationship fact or memory -> authority or permission scope
  REJECTED / RELATIONSHIP_CANNOT_EXPAND_AUTHORITY

SESSION_CONTENT -> TASK_CANONICAL_FACT
  REJECTED / SESSION_CANNOT_CREATE_TASK

MEMORY_CANDIDATE -> MEMORY_CONTENT
  DEFERRED / MEMORY_CANDIDATE_IS_NOT_MEMORY

INTENT_CANDIDATE -> ORCHESTRATOR_COMMAND
  DEFERRED / TARGET_OUTSIDE_F7

PRESENCE_CONSENT -> DEVICE_SENSING_STATE
  DEFERRED / PRESENCE_CONSENT_IS_NOT_SENSING_STATE

GROWTH_EVENT -> BEHAVIOR_POLICY_REVISION
  DEFERRED / GROWTH_EVENT_IS_NOT_POLICY_REVISION
```

Missing, stale, conflicting, unknown or unavailable inputs never become a
candidate by default.

## 6. Relationship minimum

A future formal relationship fact must bind:

```text
relationship ID and revision
all affected Actor IDs and current F2 assessment fingerprints
relationship kind and exact semantic scope
proposal Event
each affected-party acknowledgement, dispute or pause Event
current head and predecessor
Jenn decision when root governance changes
```

Until that reducer is accepted and implemented, formal relationship mutation is
`TARGET_NOT_IMPLEMENTED`. Subjective memory cannot establish another party's
formal relationship fact. Formal or subjective relationship never changes
F1–F6 authority, capability, permit, delegation or Task scope.

## 7. Presence minimum

Presence policy, consent and physical sensing state are three different facts:

```text
policy does not create consent
consent does not prove sensing is active
sensing state does not authorize recording
sensing state does not create Memory
revoked, expired, stale, unknown or mismatched consent is unusable
```

F7 defines semantic separation only. No fixture or decision in F7 authorizes a
sensor, microphone, camera, device report, retention or provider call.

## 8. Session, Memory and Artifact minimum

Session content is transient authority owned by its session host. It is not
Memory, Artifact, Life Stream, Task, evidence or formal identity by default.

A candidate contains only a commitment and low-disclosure provenance needed by
its decision path. The F7 fixture contains no raw conversation or private
Memory. Formal Memory content and Memory access authority remain external to F7
and require the governed Memory contract. Artifact bytes remain with their
artifact authority; F7 may carry only an exact `ArtifactRef` commitment.

Deletion, retention, import, export, recall and access control are not inferred
from candidate formation.

## 9. Home projection

`HOME_PROJECTION` is deterministic, read-only and rebuildable. It has no
canonical-write authority. It may not become a source assessment merely because
it displays a canonical fact.

## 10. HD-M0 disposition

R1 records only the following contract ownership disposition:

```yaml
HD-M0-01: RESOLVED_BY_F2_FROZEN_CONTRACT
HD-M0-02: RESOLVED_BY_F3_FROZEN_CONTRACT
HD-M0-03: F7_SEMANTIC_BOUNDARY_CANDIDATE_PENDING_ACCEPTANCE
HD-M0-04: DEFERRED_TO_GOVERNED_MEMORY_ACCESS_CONTRACT
HD-M0-05: DEFERRED_TO_F8_HOME_TO_ORCHESTRATOR_INTERFACE
HD-M0-06: F7_SEMANTIC_BOUNDARY_CANDIDATE_NO_SENSING_IMPLEMENTATION
HD-M0-07: F7_SEMANTIC_BOUNDARY_CANDIDATE_WRITER_TARGET_NOT_IMPLEMENTED
```

This does not claim that R1 is accepted, that deferred contracts are complete,
or that M0 is implementation-ready.

## 11. Synthetic proof profile

The fixed fixture must satisfy:

```yaml
environment: SYNTHETIC_TEST
domain_tag: F7_R1_SYNTHETIC_NONAUTHORITY
runtime_usable: false
accepted_real_identity_count: 0
real_session_content_count: 0
private_raw_memory_count: 0
formal_memory_write_count: 0
real_relationship_mutation_count: 0
sensing_or_recording_count: 0
Task_or_Command_mutation_count: 0
database_write_count: 0
provider_call_count: 0
external_effect_count: 0
terminal_outcome: NOT_EXECUTED
```

## 12. Closed schema and canonicalization

All root, section, row and nested object fields are closed. Unknown fields,
unknown enum values, duplicate JSON keys, float values, non-finite numbers,
non-NFC strings, booleans used as integers, unsafe integers, malformed hashes,
wrong nullability and cross-field contradictions reject before semantic trust.

Canonical JSON uses UTF-8, NFC strings, sorted object keys, no insignificant
whitespace and integers within `0..9007199254740991`. Object and root
fingerprints are SHA-256 over the declared domain tag plus canonical JSON with
the fingerprint field omitted.

## 13. Required adversarial coverage

The validator must reject fully re-signed mutations for at least:

```text
identity narrative rewriting stable identity
relationship expanding permission
subjective relationship memory becoming formal fact
Session becoming Task
Memory Candidate becoming Memory
Intent Candidate becoming Command inside F7
Presence consent becoming active sensing
sensing creating recording or Memory
Growth Event becoming policy revision
projection writing source facts
unknown class, writer or reducer result
same revision with changed source or payload
synthetic fixture marked runtime usable
any nonzero real/private/provider/database/effect count
unknown root/row field, duplicate key, float, non-NFC or bool-as-int
```

## 14. Acceptance boundary

R1 author validation and self-review cannot accept F7. A fresh independent
review must read all fixed subjects and authority inputs and return exactly
`PASS_NO_BLOCKER` or `BLOCK`. Only a later exact Jenn decision may accept and
freeze an atomic F7 bundle. Partial acceptance is forbidden.
