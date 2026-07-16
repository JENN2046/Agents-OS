# AGENTS OS F3 Resident Singleton / N-API / Identity Continuity v0.1 R2 Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R2_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r2
date: 2026-07-16
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
scope_locked: true
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F4_started: false
```

## 1. Scope, precedence, and fixed inputs

This amendment resolves exactly the six major findings in the fresh full
atomic independent review of F3 R1:

```text
F3-R1-FULL-ATOMIC-IR-M01 persisted rejected-Command replay
F3-R1-FULL-ATOMIC-IR-M02 frozen F2 authentication result exactness
F3-R1-FULL-ATOMIC-IR-M03 total Resident identity-continuity reducer
F3-R1-FULL-ATOMIC-IR-M04 authority-epoch anti-rollback currentness
F3-R1-FULL-ATOMIC-IR-M05 normative intake and replay schemas
F3-R1-FULL-ATOMIC-IR-M06 constructive synthetic pending-Delegation genesis
```

The fixed R1 subject remains byte-identical:

```text
control-plane/registry/drafts/
2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-v0.1-r1.draft.md

SHA-256:
e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
```

The blocking review remains byte-identical:

```text
control-plane/registry/reviews/
2026-07-16-yellow-agents-os-f3-r1-full-atomic-independent-review.yaml

SHA-256:
0be7f9e81bdd224e7d1beb83c06d1c8f3afae0ff802bdd5e8f701ff988a07c2e
```

R1 and R2 form one indivisible proposed acceptance unit. R2 replaces only the
clauses named below. Every R1 clause not explicitly replaced remains effective.
On conflict, this narrower R2 text governs.

The effective bundle version literal is:

```text
F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R2_ATOMIC_BUNDLE
```

Every R1 schema field named `F3_contract_version` uses that literal when the
R1+R2 bundle is read effectively. This substitution changes no frozen F2 field
name, field order, fingerprint domain, or authority meaning.

This amendment does not start F4, implement Rust or JavaScript, create or
migrate a database, start a Resident or service, activate runtime behavior,
configure authentication, access credentials, call a provider, expand a public
API/MCP surface, commit, push, merge, release, deploy, publish, or tag.

## 2. Closed intake, terminal disposition, and replay graph

This section replaces R1 Sections 13.1, 13.2, and 13.4 where they conflict,
and supplements R1 Section 13.3. It resolves M01 and M05 together so rejected
replay and committed replay use one canonical graph.

### 2.1 Global Command identity specialization

The accepted Resident Architecture defines `(source, command_id)` as the
minimum Inbox key. F3 v0.1 deliberately chooses the stricter specialization:

```text
replay key = (F3_GLOBAL_COMMAND_NAMESPACE, command_id)
```

`command_id` is globally unique across every F3 N-API source. The claimed
Principal Binding is recorded as `command_source_ref`, but changing source does
not create a second replay namespace. Therefore:

```text
same command_id + same canonical Command fingerprint
  -> replay the first terminal disposition

same command_id + different canonical Command fingerprint
  -> PROTOCOL_CONFLICT, even if command_source_ref differs
```

This is a narrowing of the accepted minimum, not a relaxation. A caller cannot
evade replay conflict by changing a claimed Principal, Binding, N-API request
ID, process, session, model, or incarnation.

Before a closed `CanonicalCommandV0_1` can be decoded and fingerprinted, no
Command identity exists. Unknown frame, method, schema, digest, enum, or field
therefore rejects before ledger use and creates no intake record. Once the
closed canonical Command identity exists, the terminal rules below apply.

### 2.2 Independent stable-reference derivation

The intake and replay references are identifiers, not content addresses. They
are derived before any envelope fingerprint:

```text
F3_intake_state_ref = lowercase SHA-256(JCS([
  "agents-os.f3-intake-state-ref.v0.1-r2",
  "F3_GLOBAL_COMMAND_NAMESPACE",
  command_id
]))

replay_entry_ref = lowercase SHA-256(JCS([
  "agents-os.command-replay-entry-ref.v0.1-r2",
  "F3_GLOBAL_COMMAND_NAMESPACE",
  command_id
]))
```

No fingerprint is used as either reference. This makes the graph order exact:

```text
Command fingerprint
-> independent intake/replay refs
-> committed context
-> envelope fingerprint containing F3_intake_state_ref
-> optional action/activation ref
-> intake fingerprint containing the completed result graph
-> replay-entry fingerprint containing the intake fingerprint
```

There is no edge from any earlier fingerprint input back to the intake or
replay fingerprint.

### 2.3 `CommandGateResultV0_1R2`

Every canonically identified first submission derives one closed gate result:

```yaml
CommandGateResultV0_1R2:
  interface_version: agents-os.command-gate-result.v0.1-r2
  gate_result_ref: stable_ref
  command_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  command_source_ref: stable_ref
  result: ADMITTED | REJECTED | INDETERMINATE
  reason_codes: sorted_unique_closed_values
  actor_identity_assessment_ref: stable_ref | null
  principal_binding_assessment_ref: stable_ref | null
  authentication_assessment_ref: stable_ref | null
  responsibility_assessment_ref: stable_ref | null
  temporary_worker_binding_assessment_ref: stable_ref | null
  prohibited_boundary_evidence_ref: stable_ref | null
  trusted_time_authority_ref: stable_ref | null
  evaluated_at_event_sequence: positive_safe_integer
  assessed_at_utc_ms: safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under:

```text
agents-os.command-gate-result.v0.1-r2
```

`gate_result_ref` is independently derived before that fingerprint:

```text
lowercase SHA-256(JCS([
  "agents-os.command-gate-result-ref.v0.1-r2",
  "F3_GLOBAL_COMMAND_NAMESPACE",
  command_id,
  canonical_command_fingerprint
]))
```

Assessment refs are present exactly when that gate was reached. A prior closed
failure makes later refs null. Unknown, stale, forked, conflicting, or
unavailable evidence yields `INDETERMINATE`; a proven closed negative predicate
yields `REJECTED`; all required gates current at one transaction watermark
yields `ADMITTED`. Raw proof, credential, secret, provider response, SQL, or
narrative text is forbidden.

For this record, gate evaluation includes the closed target-revision,
expected-version, domain-invariant, and deterministic reducer-precondition
decision. The reducer may compute an immutable proposed mutation value but
cannot write it before `ADMITTED` is fixed. A deterministic reducer rejection
therefore produces `REJECTED` and is persisted under Section 2.7; a reducer
input that cannot be reproduced produces `INDETERMINATE`. `ADMITTED` means all
gates and reducer preconditions produced exactly one closed mutation plan.

The result is immutable historical evidence. It is not a current authorization
cache and cannot admit another Command.

`reason_codes` is a sorted unique subset of this closed enum order:

```text
ACTOR_NOT_ACTIVE
ACTOR_CURRENTNESS_INDETERMINATE
PRINCIPAL_BINDING_NOT_ACTIVE
PRINCIPAL_BINDING_CURRENTNESS_INDETERMINATE
AUTHENTICATION_NOT_AUTHENTICATED
AUTHENTICATION_CURRENTNESS_INDETERMINATE
RESPONSIBILITY_NOT_ACTIVE
RESPONSIBILITY_CURRENTNESS_INDETERMINATE
TEMPORARY_WORKER_BINDING_NOT_ACTIVE
TEMPORARY_WORKER_BINDING_CURRENTNESS_INDETERMINATE
PROHIBITED_BOUNDARY_UNSATISFIED
PROHIBITED_BOUNDARY_INDETERMINATE
TRUSTED_TIME_OUTSIDE_VALIDITY
TRUSTED_TIME_INDETERMINATE
RESIDENT_LIFECYCLE_NOT_READY
RESIDENT_READINESS_INDETERMINATE
IDENTITY_CONTINUITY_DISCONTINUOUS
IDENTITY_CONTINUITY_INDETERMINATE
TARGET_REVISION_CONFLICT
DOMAIN_INVARIANT_REJECTED
REDUCER_INPUT_INDETERMINATE
COMMAND_DEFINITION_NOT_CURRENT
```

`ADMITTED` requires an empty list. `REJECTED` requires at least one proven
negative code and no `*_INDETERMINATE` code. `INDETERMINATE` requires at least
one `*_INDETERMINATE` code. `RESIDENT_LIFECYCLE_NOT_READY` and
`IDENTITY_CONTINUITY_DISCONTINUOUS` are proven negative codes; their
indeterminate counterparts are separate.
Unknown, mixed-inconsistent, duplicate, or out-of-order reason codes reject.

The intake/replay `low_disclosure_result_code` is exactly one of:

```text
COMMAND_COMMITTED
COMMAND_REJECTED
COMMAND_INDETERMINATE
```

It maps one-to-one to the terminal disposition in the displayed order.
`PROTOCOL_CONFLICT` is a response-only result for changed bytes against an
existing command ID; it does not replace the first entry or become its stored
low-disclosure result.

### 2.4 `F3CommandIntakeRecordV0_1R2`

```yaml
F3CommandIntakeRecordV0_1R2:
  interface_version: agents-os.command-intake-record.v0.1-r2
  F3_contract_version: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R2_ATOMIC_BUNDLE
  F3_intake_state_ref: stable_ref
  replay_entry_ref: stable_ref
  replay_namespace: F3_GLOBAL_COMMAND_NAMESPACE
  command_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  command_source_ref: stable_ref
  command_source_kind: CLAIMED_PRINCIPAL_BINDING
  gate_result_ref: stable_ref
  gate_result_fingerprint: lowercase_sha256
  terminal_disposition: COMMITTED | REJECTED | INDETERMINATE
  low_disclosure_result_code: closed_value
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  resident_authority_epoch: positive_safe_integer
  resident_authority_generation: positive_safe_integer
  recorded_at_event_sequence: positive_safe_integer
  command_envelope_ref: stable_ref | null
  command_envelope_fingerprint: lowercase_sha256 | null
  intake_event_sequence: positive_safe_integer | null
  action_or_activation_ref: stable_ref | null
  action_or_activation_fingerprint: lowercase_sha256 | null
  committed_result_ref: stable_ref | null
  committed_result_fingerprint: lowercase_sha256 | null
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under:

```text
agents-os.command-intake-record.v0.1-r2
```

The disposition shapes are closed:

| terminal disposition | gate result | envelope/Event/action/result refs |
|---|---|---|
| `COMMITTED` | `ADMITTED` | envelope and intake Event required; action/activation and result refs required exactly as the Command type defines |
| `REJECTED` | `REJECTED` | every envelope, Event, action/activation, and committed-result field null |
| `INDETERMINATE` | `INDETERMINATE` | every envelope, Event, action/activation, and committed-result field null |

`recorded_at_event_sequence` is the read-barrier watermark at which the first
terminal disposition was persisted. For `REJECTED` or gate-derived
`INDETERMINATE`, no Event is appended and this value is not a newly allocated
Event sequence.

An integrity failure that makes it impossible to prove absence of an existing
replay entry is not a new gate-derived `INDETERMINATE` submission. It closes
intake and writes nothing until recovery can establish the canonical graph.

### 2.5 `CommandReplayEntryV0_1R2`

```yaml
CommandReplayEntryV0_1R2:
  interface_version: agents-os.command-replay-entry.v0.1-r2
  replay_entry_ref: stable_ref
  replay_namespace: F3_GLOBAL_COMMAND_NAMESPACE
  command_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  first_command_source_ref: stable_ref
  terminal_disposition: COMMITTED | REJECTED | INDETERMINATE
  F3_intake_state_ref: stable_ref
  F3_intake_state_fingerprint: lowercase_sha256
  low_disclosure_result_code: closed_value
  command_envelope_ref: stable_ref | null
  command_envelope_fingerprint: lowercase_sha256 | null
  committed_result_ref: stable_ref | null
  committed_result_fingerprint: lowercase_sha256 | null
  first_resident_authority_epoch: positive_safe_integer
  first_resident_authority_generation: positive_safe_integer
  first_recorded_at_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under:

```text
agents-os.command-replay-entry.v0.1-r2
```

It is the immutable canonical Inbox entry. The replay index is a rebuildable
projection from these records and never owns disposition. A missing, duplicate,
forked, mismatched, or partially linked canonical entry is `INDETERMINATE` and
closes affected intake; recovery never invents or rewrites it.

### 2.6 Corrected envelope projection

R1 `CommandEnvelopeV0_1` remains closed and gains exactly one field immediately
after `resident_authority_epoch`:

```yaml
resident_authority_generation: positive_safe_integer
```

Its R2 fingerprint domain and order are:

```text
SHA-256(JCS([
  "agents-os.command-envelope.v0.1-r2",
  command_envelope_ref,
  F3_contract_version,
  "COMMITTED",
  command_id,
  canonical_command_fingerprint,
  command_type_definition_ref,
  command_type_definition_fingerprint,
  command_type_id,
  command_type_version,
  authenticated_command_context_ref,
  authenticated_command_context_fingerprint,
  resident_identity_ref,
  resident_identity_fingerprint,
  resident_authority_epoch,
  resident_authority_generation,
  intake_event_sequence,
  F3_intake_state_ref
]))
```

The envelope points only to the independent intake ref. The completed intake
record may contain the envelope fingerprint without a cycle.

The frozen F2 `AuthenticatedActorActionRefR4Effective` field set, order, and
fingerprint formula remain unchanged. Its existing `F3_intake_state_ref` binds
indirectly to the R2 intake record and therefore to the authority generation.
F3 does not add a field to the frozen F2 action reference.

### 2.7 Total first-submission and replay reducer

On the one Rust ledger thread, after canonical Command identity exists:

```text
1. begin the authoritative write transaction
2. recheck READY, lock, incarnation, epoch, authority generation, and heads
3. derive the global replay_entry_ref and look it up

existing entry + same fingerprint + COMMITTED
  -> return REPLAYED_COMMITTED with exact first envelope/result refs
  -> append no Event and perform no reducer mutation

existing entry + same fingerprint + REJECTED
  -> return the exact first low-disclosure REJECTED result
  -> do not reevaluate changed gates; append no Event; perform no mutation

existing entry + same fingerprint + INDETERMINATE
  -> return the exact first low-disclosure INDETERMINATE result
  -> do not reevaluate changed gates; append no Event; perform no mutation

existing entry + different fingerprint
  -> return REJECTED(PROTOCOL_CONFLICT)
  -> never replace the entry; append no Event; perform no mutation

no entry + gate result ADMITTED
  -> run reducer and atomically commit context, envelope, intake record,
     replay entry, action/activation ref, canonical domain facts, Current
     State, one Event, and any already-admitted ledger-only intent

no entry + gate result REJECTED
  -> atomically commit only gate result, REJECTED intake record, and replay entry
  -> no envelope, action, activation, Event, domain fact, or Current State change

no entry + gate result INDETERMINATE on an otherwise integrity-sound ledger
  -> atomically commit only gate result, INDETERMINATE intake record, and replay entry
  -> no envelope, action, activation, Event, domain fact, or Current State change

absence, uniqueness, or integrity not provable
  -> write nothing; close affected intake; return INDETERMINATE
```

After any persisted `REJECTED` or gate-derived `INDETERMINATE` result, changed
conditions require a new `command_id`. This exactly preserves the accepted
Resident Architecture rule. Lost response never authorizes resubmission with
changed bytes.

## 3. Exact frozen F2 authentication result

This section replaces the R1 Section 12 ordinary Command authentication line:

```text
authentication assessment VERIFIED and bound to this exact Command fingerprint
```

with:

```text
AuthenticationAssessmentV0_1R15.assessment = AUTHENTICATED
and the assessment is bound to this exact canonical Command fingerprint
```

The complete ordinary gate is therefore:

```text
ActorIdentityAssessmentV0_1R16.assessment = ACTIVE
effective Principal Binding assessment = ACTIVE for that exact Actor revision
AuthenticationAssessmentV0_1R15.assessment = AUTHENTICATED
responsibility assessment = ACTIVE for the exact target resource
current single Prohibited Behavior List boundary satisfied
trusted time inside the Command validity interval
Resident readiness = READY and identity continuity = CONTINUOUS
```

`VERIFIED` remains legal only in the frozen principal-control proof assessment
interface. It is not an alias for `AUTHENTICATED`, is never emitted as an
AuthenticationAssessment value, and cannot satisfy the Command gate.

The `AuthenticatedCommandContextV0_1` schema gains exactly one field after
`resident_authority_epoch`:

```yaml
resident_authority_generation: positive_safe_integer
```

Its effective fingerprint domain becomes
`agents-os.authenticated-command-context.v0.1-r2` and otherwise preserves the
displayed R1 field order with the new field in that exact position.

## 4. Total Resident identity-continuity reducer

This section replaces the reducer prose in R1 Section 15. The R1 assessment
schema remains, and its `reason_codes` field uses only the following closed
values in this canonical enum order:

```text
IDENTITY_GRAPH_MISSING
IDENTITY_GRAPH_DUPLICATE
IDENTITY_GRAPH_FORKED
IDENTITY_GRAPH_NONCONTIGUOUS
IDENTITY_GRAPH_FINGERPRINT_MISMATCH
CHARTER_NOT_CURRENT
F2_ACCEPTANCE_NOT_CURRENT
JENN_IDENTITY_DECISION_MISSING_OR_MISMATCHED
EXPLICIT_IDENTITY_DISCONTINUITY
COORDINATOR_NOT_YET_ACTIVE
COORDINATOR_SUSPENDED
COORDINATOR_COMPROMISED
COORDINATOR_RETIRED
COORDINATOR_EXPIRED
COORDINATOR_SUPERSEDED
COORDINATOR_ASSESSMENT_INDETERMINATE
AUTHORITY_WITNESS_STALE_OR_MISMATCHED
AUTHORITY_EPOCH_NOT_CURRENT
REQUIRED_ASSESSMENT_NOT_REPRODUCIBLE
ALL_CONTINUITY_FACTS_CURRENT
UNRECOGNIZED_INPUT_FAIL_CLOSED
```

The reducer is precedence-ordered and total:

```text
1. missing/duplicate/forked/noncontiguous/hash-mismatched identity, charter,
   F2 acceptance, Jenn decision, Event, epoch, or witness graph
     -> INDETERMINATE with the exact matching integrity reason(s)

2. current identity head continuity_transition = DISCONTINUITY
     -> DISCONTINUOUS(EXPLICIT_IDENTITY_DISCONTINUITY)

3. exact frozen coordinator Actor assessment:
     NOT_YET_ACTIVE -> INDETERMINATE(COORDINATOR_NOT_YET_ACTIVE)
     ACTIVE         -> continue to step 4
     SUSPENDED      -> INDETERMINATE(COORDINATOR_SUSPENDED)
     COMPROMISED    -> INDETERMINATE(COORDINATOR_COMPROMISED)
     RETIRED        -> INDETERMINATE(COORDINATOR_RETIRED)
     EXPIRED        -> INDETERMINATE(COORDINATOR_EXPIRED)
     SUPERSEDED     -> INDETERMINATE(COORDINATOR_SUPERSEDED)
     INDETERMINATE  -> INDETERMINATE(COORDINATOR_ASSESSMENT_INDETERMINATE)

4. current authority witness or epoch absent, stale, forked, mismatched, or
   not owned by this lock-holding incarnation
     -> INDETERMINATE with AUTHORITY_WITNESS_STALE_OR_MISMATCHED and/or
        AUTHORITY_EPOCH_NOT_CURRENT

5. current identity head transition is BOOTSTRAP or CONTINUE, the exact Jenn
   decision binds that transition, coordinator Actor assessment is ACTIVE,
   witness/epoch ownership is valid, and every required assessment is
   reproducible at one Event watermark
     -> CONTINUOUS(ALL_CONTINUITY_FACTS_CURRENT)

6. every input not matched above, including an unknown enum value
     -> INDETERMINATE(UNRECOGNIZED_INPUT_FAIL_CLOSED)
```

An exact Jenn continuity decision may create a new contiguous Resident identity
revision, including one referencing a current ACTIVE successor revision of the
same logical coordinator Actor ID. It does not rewrite or override a frozen F2
Actor assessment. A non-`ACTIVE` referenced Actor revision can never reach
`CONTINUOUS` or READY merely because a Jenn decision exists.

Reason codes are deduplicated and sorted by the closed enum order above. No
implementation-selected string, localized reason, or omitted final fallback is
allowed.

## 5. Durable authority-generation witness and restore boundary

This section replaces R1 Sections 7.2 and the epoch portions of Sections 8,
16.1, 16.3, and 19. It adds a ledger-external monotonic witness without
granting runtime or storage implementation authority.

### 5.1 Witness semantic primitive

One Resident uses exactly one
`ResidentAuthorityMonotonicWitnessV0_1R2`. It is a small, non-secret,
ledger-external durable journal excluded from canonical-ledger backup and
restore units. Its implementation profile may choose a platform primitive only
if it proves these semantics:

```text
one OS-lock holder can mutate it
append transitions are linearizable and durably ordered
witness_generation never decreases or repeats
a committed witness entry cannot be silently deleted by ledger restore
observe returns the unique committed high-watermark and at most one pending reservation
unknown, corrupt, duplicate, forked, truncated, or stale state fails closed
```

The locator, filesystem path, fsync/replace mechanism, and OS primitive are
implementation-private. They never enter a Command, Event, model context, or
public API. The semantic primitive contains no secret, credential, key,
provider output, private Memory, or permission grant.

### 5.2 Reservation, commit, and abandonment schemas

```yaml
ResidentAuthorityWitnessReservationV0_1R2:
  interface_version: agents-os.resident-authority-witness-reservation.v0.1-r2
  reservation_ref: stable_ref
  witness_id: stable_ref
  witness_generation: positive_safe_integer
  expected_previous_committed_generation: safe_integer
  previous_committed_witness_fingerprint: lowercase_sha256 | null
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  intended_authority_epoch: positive_safe_integer
  expected_previous_authority_epoch: positive_safe_integer | null
  expected_previous_epoch_fingerprint: lowercase_sha256 | null
  incarnation_id: stable_ref
  restore_decision_ref: stable_ref | null
  restore_decision_fingerprint: lowercase_sha256 | null
  state: RESERVED
  canonical_fingerprint: lowercase_sha256

ResidentAuthorityWitnessCommitV0_1R2:
  interface_version: agents-os.resident-authority-witness-commit.v0.1-r2
  witness_id: stable_ref
  witness_generation: positive_safe_integer
  reservation_ref: stable_ref
  reservation_fingerprint: lowercase_sha256
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  authority_epoch: positive_safe_integer
  authority_epoch_ref: stable_ref
  authority_epoch_fingerprint: lowercase_sha256
  incarnation_id: stable_ref
  ownership_started_event_sequence: positive_safe_integer
  state: COMMITTED
  canonical_fingerprint: lowercase_sha256

ResidentAuthorityWitnessAbandonV0_1R2:
  interface_version: agents-os.resident-authority-witness-abandon.v0.1-r2
  witness_id: stable_ref
  witness_generation: positive_safe_integer
  reservation_ref: stable_ref
  reservation_fingerprint: lowercase_sha256
  observed_ledger_epoch_ref: stable_ref | null
  observed_ledger_epoch_fingerprint: lowercase_sha256 | null
  reason: NO_MATCHING_LEDGER_EPOCH
  state: ABANDONED
  canonical_fingerprint: lowercase_sha256
```

Each fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under its `interface_version` domain.
`reservation_ref` is independently derived before the reservation fingerprint:

```text
lowercase SHA-256(JCS([
  "agents-os.resident-authority-witness-reservation-ref.v0.1-r2",
  witness_id,
  witness_generation
]))
```

The first reservation uses generation 1, expected previous committed
generation `0`, and a null previous witness fingerprint. Every later
reservation uses exactly the highest journal generation of any state plus 1,
while `expected_previous_committed_generation` and its fingerprint name the
unique latest COMMITTED entry. A crash-abandoned reservation consumes its
generation and the next reservation is therefore greater even when the latest
COMMITTED generation has not changed. One reservation has exactly one terminal
`COMMITTED` or `ABANDONED` transition, never both. Authority epoch still
advances exactly by one in the ledger and may not skip.

### 5.3 Corrected authority epoch

R2 replaces `ResidentAuthorityEpochV0_1` with:

```yaml
ResidentAuthorityEpochV0_1R2:
  interface_version: agents-os.resident-authority-epoch.v0.1-r2
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  authority_epoch: positive_safe_integer
  expected_previous_authority_epoch: positive_safe_integer | null
  previous_authority_epoch_fingerprint: lowercase_sha256 | null
  authority_generation: positive_safe_integer
  witness_reservation_ref: stable_ref
  witness_reservation_fingerprint: lowercase_sha256
  incarnation_id: stable_ref
  previous_incarnation_id: stable_ref | null
  restore_decision_ref: stable_ref | null
  restore_decision_fingerprint: lowercase_sha256 | null
  ownership_started_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under:

```text
agents-os.resident-authority-epoch.v0.1-r2
```

Genesis requires epoch 1, null predecessor epoch/fingerprint, the current
never-before-used reserved witness generation, and the exact Resident bootstrap
decision. Its generation is 1 when no earlier reservation crashed and may be
greater only when every smaller generation has one valid `ABANDONED` record.
Normal restart requires exact epoch `N + 1`, exact predecessor fingerprint, a
strictly greater reserved witness generation, null restore decision, and the
currently lock-holding incarnation.

### 5.4 Crash-total witness protocol

While holding `ResidentAuthorityLock`, startup performs:

```text
1. observe the durable witness before claiming canonical writer authority
2. verify the ledger head against the last COMMITTED witness
3. reserve one new never-before-used witness generation for intended epoch N+1
4. commit epoch N+1 in the one SQLite transaction, binding the reservation
5. durably append the witness COMMIT binding the exact epoch fingerprint
6. re-read witness and ledger at one recovery barrier
7. only then may continuity become CONTINUOUS and lifecycle become READY
```

Crash recovery is total:

```text
RESERVED generation G, no ledger epoch binds G
  -> mark G abandoned in the witness journal; never reuse G
  -> reserve a later generation for the same next ledger epoch

RESERVED G, exactly one ledger epoch binds G and all fingerprints match
  -> finalize the exact witness COMMIT for G; do not create a second epoch for G
  -> a new lock-holding incarnation must then reserve a later generation and
     commit the next authority epoch before it can reach READY

COMMITTED G, ledger head missing, older, or fingerprint-mismatched
  -> rollback detected; INDETERMINATE; no automatic epoch commit

ledger head ahead of COMMITTED witness with no exact pending reservation
  -> INDETERMINATE; no inferred or fabricated witness

duplicate/forked witness generation, reservation, commit, or epoch
  -> INDETERMINATE
```

Thus a coherent restore of an older ledger cannot reuse an historical epoch or
reach READY merely because its internal graph is consistent.

### 5.5 Explicit restore decision

An intentional older-ledger restore can proceed only from a new immutable Jenn
decision reference with this closed projection:

```yaml
ResidentLedgerRestoreDecisionRefV0_1R2:
  interface_version: agents-os.resident-ledger-restore-decision-ref.v0.1-r2
  decision_ref: stable_ref
  authorized_by: Jenn
  resident_identity_ref: stable_ref
  backup_artifact_ref: stable_low_disclosure_ref
  backup_sha256: lowercase_sha256
  restored_epoch_ref: stable_ref
  restored_epoch_fingerprint: lowercase_sha256
  observed_committed_witness_generation: positive_safe_integer
  observed_committed_witness_fingerprint: lowercase_sha256
  acknowledged_lost_event_range_start: positive_safe_integer | null
  acknowledged_lost_event_range_end: positive_safe_integer | null
  new_restore_lineage_id: stable_ref
  decision_sha256: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under its interface-version domain. The
decision binds the exact backup bytes and the witness state observed after
restore. Missing, mismatched, stale, reused, broad, or different-backup
decisions reject.

The witness journal records a new reservation containing that decision; the
restored ledger commits the next ledger epoch with a new witness generation and
the same decision ref/fingerprint. All F2 recovery, identity continuity,
replay, Event, and prohibited-boundary checks still run. The decision does not
fabricate lost facts, override F2 assessments, authorize implementation, or
activate runtime. This document performs no restore.

## 6. Constructive synthetic M0 genesis

This section replaces R1 Section 20. It also supplements the R1 Command
registry with the one ledger-only issuance type needed before activation.

### 6.1 Closed Delegation issuance Command

F3 R2 admits exactly this additional Command type:

```yaml
F3JennRootDirectionCommandAssessmentV0_1R2:
  interface_version: agents-os.f3-jenn-root-direction-command-assessment.v0.1-r2
  assessment_ref: stable_ref
  root_direction_ref: stable_ref
  root_direction_fingerprint: lowercase_sha256
  Jenn_actor_identity_assessment_ref: stable_ref
  Jenn_actor_identity_assessment_fingerprint: lowercase_sha256
  Jenn_principal_binding_assessment_ref: stable_ref
  Jenn_principal_binding_assessment_fingerprint: lowercase_sha256
  Jenn_root_relation_ref: stable_ref
  Jenn_root_relation_fingerprint: lowercase_sha256
  assessment: ACTIVE | INDETERMINATE
  reason_codes: sorted_unique_closed_values
  based_on_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under its interface-version domain. It is
`ACTIVE` only when the exact root direction is current and the frozen F2
Jenn-root Actor, effective Binding, root relation, and required assurance facts
all reproduce as current at the same watermark. Every missing, stale, forked,
mismatched, non-active, or indeterminate input yields `INDETERMINATE`.

This is an F3 admission projection for the already-frozen first Jenn-root
Delegation branch. It creates no F2 subject, responsibility source, permission,
or alternative root authority and cannot be used by another Command type.

Its `reason_codes` field is a sorted unique subset of this closed order:

```text
ROOT_DIRECTION_MISSING_OR_NOT_CURRENT
JENN_ACTOR_NOT_ACTIVE
JENN_BINDING_NOT_ACTIVE
JENN_ROOT_RELATION_MISSING_OR_MISMATCHED
ROOT_ASSURANCE_NOT_REPRODUCIBLE
ALL_ROOT_DIRECTION_FACTS_CURRENT
```

`ACTIVE` requires exactly `[ALL_ROOT_DIRECTION_FACTS_CURRENT]`.
`INDETERMINATE` requires one or more of the other five values and forbids
`ALL_ROOT_DIRECTION_FACTS_CURRENT`.

```yaml
DelegationIssuanceCommandTypeV0_1R2:
  registry_revision: 2
  command_type_id: DELEGATION_ISSUANCE
  command_type_version: 1
  owner_contract_ref: frozen_F2_R1_R22_atomic_bundle
  owner_contract_sha256: 95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1
  payload_schema_ref: agents-os.delegation-issuance-command-payload.v0.1-r2
  allowed_target_kinds: [DELEGATION_GRANT]
  expected_target_revision_policy: REQUIRED
  responsibility_mode: REQUIRED
  effect_class: LEDGER_ONLY
  reducer_ref: frozen_F2_Delegation_issuance_reducer_R19_effective
  required_gate_refs:
    - F2_actor_identity_ACTIVE
    - F2_principal_binding_ACTIVE
    - F2_authentication_AUTHENTICATED
    - F3_Jenn_root_direction_command_assessment_ACTIVE
    - current_prohibited_boundary
    - trusted_time
    - F3_READY_CONTINUOUS
  maximum_validity_duration_ms: 60000
  unknown_fields_policy: REJECT
```

Its closed payload is the exact pre-action F2 issuance intent:

```yaml
DelegationIssuanceCommandPayloadV0_1R2:
  payload_schema_version: agents-os.delegation-issuance-command-payload.v0.1-r2
  delegation_id: stable_ref
  delegation_revision: positive_safe_integer
  expected_previous_delegation_revision: positive_safe_integer | null
  supersedes_delegation_revision: positive_safe_integer | null
  delegator_actor_id: stable_ref
  delegator_identity_revision: positive_safe_integer
  delegate_actor_id: stable_ref
  delegate_identity_revision: positive_safe_integer
  parent_delegation_ref: stable_ref | null
  source_responsibility_ref: stable_ref
  responsibility_kind: stable_ref
  responsibility_scope: F2_ResponsibilityScopeV0_1R7
  may_redelegate: boolean
  remaining_depth: safe_integer
  not_before_utc_ms: safe_integer
  expires_at_utc_ms: safe_integer
  activation_mode: EXPLICIT_ACK | WORKER_ASSIGNMENT_HANDSHAKE
  issued_by_actor_id: stable_ref
  issued_by_actor_identity_revision: positive_safe_integer
  issued_by_principal_binding_ref: stable_ref
  issuer_currentness_event_sequence: positive_safe_integer
  root_direction_ref: stable_ref | null
  root_direction_fingerprint: lowercase_sha256 | null
  source_assignment_ref: stable_ref | null
  source_assignment_fingerprint: lowercase_sha256 | null
  reason_code: TASK_HANDOFF | RUN_EXECUTION | DOMAIN_OPERATION | INCIDENT_RESPONSE | MAINTENANCE
  reason_artifact_ref: F2_ResponsibilityResourceRefV0_1 | null
  status: ACTIVE
```

Unknown fields and unknown enum values reject. The reducer recomputes the exact
frozen F2 R19 issuance-intent fingerprint from this payload. The Command cannot
supply an issuance action ref, envelope ref, Event sequence, final Delegation
fingerprint, activation evidence, or current assessment.

After all gates pass, F3 creates the committed envelope and exact frozen
`AuthenticatedActorActionRefR4Effective`; that action binds the issuance intent.
The frozen F2 reducer then creates the pending Delegation subject and Event in
the same transaction. The graph is forward-only:

```text
Command -> context -> envelope -> issuance action -> Delegation subject -> Event
```

The Delegation subject has no activation-evidence backward ref. The later
`DELEGATION_ACTIVATION_ACK` remains a distinct Command.

### 6.2 Exact fixture namespace and constants

The constructive witness uses only the namespace:

```text
agents-os.synthetic.f3-r2.m0
```

and these fixed semantic constants:

```yaml
fixture_time:
  T0_utc_ms: 2000000000000
  command_issued_at_utc_ms: 2000000001000
  command_expires_at_utc_ms: 2000000061000
  delegation_not_before_utc_ms: 2000000000000
  delegation_expires_at_utc_ms: 2000003600000

fixture_ids:
  resident_identity_id: f3-r2-m0-resident
  Jenn_actor_id: f3-r2-m0-jenn-actor
  Jenn_principal_id: f3-r2-m0-jenn-principal
  Jenn_binding_ref: f3-r2-m0-jenn-binding
  coordinator_actor_id: f3-r2-m0-coordinator-actor
  coordinator_principal_id: f3-r2-m0-coordinator-principal
  coordinator_binding_ref: f3-r2-m0-coordinator-binding
  root_direction_ref: f3-r2-m0-root-direction
  delegation_id: f3-r2-m0-delegation
  issuance_command_id: f3-r2-m0-delegation-issue-command
  activation_command_id: f3-r2-m0-delegation-activation-command
  responsibility_kind: f3-r2-m0-resident-coordination
  responsibility_resource_id: f3-r2-m0-resident-contract-resource
```

IDs are stable fixture strings. Every canonical fingerprint is recomputed from
the exact frozen F2 or effective F3 schema; no fingerprint is accepted merely
because it appears in the fixture manifest.

### 6.3 Complete pre-issuance genesis

The witness does not start from the F2 synthetic manifest alone. It starts from
this complete, ordered, closed synthetic genesis, all inside one fixed fixture:

```text
1. exact frozen F2 synthetic Jenn bootstrap facts:
   - JENN_HUMAN_ROOT Actor revision 1, ACTIVE
   - synthetic Authenticator Profile and HUMAN_SESSION Principal
   - exact Jenn Principal Binding and synthetic activation evidence, ACTIVE
   - exact Jenn root relation and current JENN_ROOT_DIRECTION
   - exact synthetic trusted-time decision at T0
   - exact current synthetic Prohibited Boundary revision/evidence

2. exact frozen F2 R21 synthetic DOMAIN_AGENT Actor bootstrap:
   - coordinator Actor revision 1, ACTIVE
   - JENN_GOVERNANCE_DECISION_BASIS in SYNTHETIC_TEST
   - IDENTITY_BOOTSTRAP permitted

3. one accepted frozen F2 synthetic M0 manifest containing the exact
   coordinator Profile, Principal, and Binding specs:
   - manifest CREATE and ACCEPT graph complete
   - coordinator Binding revision 1 ACTIVE
   - SyntheticM0ActorEligibilityAssessment = ELIGIBLE
   - current R22 manifest-derived assurance projection complete

4. exact synthetic authentication fixtures for both Bindings:
   - assertion values contain no raw credential or proof bytes
   - verifier/profile/principal/binding/replay assessments reproduce
   - AuthenticationAssessmentV0_1R15.assessment = AUTHENTICATED

5. Resident identity revision 1 and Jenn fixture decision:
   - logical coordinator = exact coordinator Actor revision 1
   - continuity_transition = BOOTSTRAP
   - continuity assessment = CONTINUOUS only after witness/epoch checks

6. ResidentAuthorityLock held by synthetic incarnation 1
   - witness generation 1 RESERVED then COMMITTED
   - authority epoch 1 committed and cross-bound to generation 1
   - lifecycle reaches READY only after the final barrier
```

Each line names an already-frozen F2 branch or an R1+R2 F3 branch. The fixture
must serialize the complete objects, refs, fingerprints, assessments, Events,
and watermarks; a narrative shortcut, omitted Actor, invented pending grant,
or bare `ACTIVE` label rejects.

These are synthetic contract fixtures only. They are not a real Jenn
authentication, production credential, runtime identity, provider call,
service, database, host, TaskPermit, or permission grant.

### 6.4 Constructive issuance before acknowledgement

Starting from Section 6.3, the fixture executes the exact
`DELEGATION_ISSUANCE` Command:

```text
issuer/delegator = exact synthetic Jenn Actor revision 1
issuer Principal Binding = exact synthetic Jenn Binding
delegate = exact synthetic coordinator Actor revision 1
source responsibility = exact current JENN_ROOT_DIRECTION
root_direction ref/fingerprint = exact fixture direction
source Assignment fields = null
parent Delegation = null
delegation revision = 1; predecessor fields = null
CommandTarget expected_target_revision = 0 for the required creation target
scope = EXACT_SET containing only the fixed resident-contract resource
remaining_depth = frozen policy.maximum_edges_per_chain - 1
may_redelegate = false
activation_mode = EXPLICIT_ACK
reason_code = DOMAIN_OPERATION
reason_artifact_ref = null
responsibility claim binds the exact JENN_ROOT_DIRECTION and scope
authentication assessment = AUTHENTICATED
```

The one writer atomically commits:

```text
gate result ADMITTED
authenticated context
Command envelope
F2 AuthenticatedActorActionRefR4Effective
F2 DelegationGrantRevisionV0_1R19Effective
F2 issuance Event
COMMITTED F3 intake record
COMMITTED replay entry
```

The grant is now an exact immutable pending Delegation: its issuance subject is
valid and current, but no `DelegationActivationEvidence` exists. It cannot be
its own activation responsibility source.

### 6.5 Activation, replay, restart, and dual-start trace

Only after Section 6.4 does the fixture execute the R1 closed
`DELEGATION_ACTIVATION_ACK` Command:

```text
command actor/principal/binding = exact synthetic coordinator
responsibility mode = NONE_ACTIVATION_PURPOSE_ONLY
every responsibility source/scope/delegation-chain field = null
payload activation mode = EXPLICIT_ACK
payload binds exact pending Delegation ref/fingerprint
AuthenticationAssessmentV0_1R15 = AUTHENTICATED
current prohibited boundary and trusted time verify
```

The activation transaction creates exactly one committed envelope, exact F2
activation acknowledgement projection, `DelegationActivationEvidence`, Event,
intake record, and replay entry. It creates no TaskPermit, host admission,
effect intent, provider call, or external operation.

The remaining trace is fixed:

```text
byte-identical activation Command replay
  -> exact first envelope/result, no second Event

same activation command_id + altered payload
  -> PROTOCOL_CONFLICT, no mutation

crash/restart after committed activation
  -> lock released; witness generation 2 reserved/committed; epoch 2 committed;
     identity remains CONTINUOUS after full recovery; replay remains exact

second concurrent incarnation
  -> cannot hold process gate and canonical witness/epoch gate together;
     no Command intake and no write
```

This supplies a pending-Delegation genesis before acknowledgement and is
constructible from declared inputs without real secrets, runtime, provider,
host, private Memory, or external effects.

### 6.6 Fixed synthetic genesis manifest schema

The final fixture is summarized only after every leaf object exists:

```yaml
F3SyntheticM0GenesisManifestV0_1R2:
  interface_version: agents-os.f3-synthetic-m0-genesis-manifest.v0.1-r2
  fixture_namespace: agents-os.synthetic.f3-r2.m0
  frozen_F2_acceptance_decision_ref: stable_ref
  frozen_F2_acceptance_decision_sha256: lowercase_sha256
  frozen_F2_atomic_manifest_ref: stable_ref
  frozen_F2_atomic_manifest_sha256: lowercase_sha256
  Jenn_fixture_decision_ref: stable_ref
  Jenn_fixture_decision_sha256: lowercase_sha256
  fixed_time_constants: closed_object
  ordered_genesis_subjects:
    - kind: closed_subject_kind
      subject_ref: stable_ref
      subject_fingerprint: lowercase_sha256
  issuance_command_ref: stable_ref
  issuance_command_fingerprint: lowercase_sha256
  pending_delegation_ref: stable_ref
  pending_delegation_fingerprint: lowercase_sha256
  activation_command_ref: stable_ref
  activation_command_fingerprint: lowercase_sha256
  final_event_sequence: positive_safe_integer
  expected_final_state_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

`ordered_genesis_subjects` uses one closed enum and dependency-topological
order. It contains every object named in Sections 6.3-6.5 exactly once. The
manifest fingerprint is SHA-256 JCS over the complete displayed order,
excluding `canonical_fingerprint`, under its interface-version domain. The
manifest is evidence, not an authority source, writer, permission, or shortcut.

## 7. R2 invariants and mandatory negative cases

The effective R1+R2 bundle adds:

```text
F3-I20 every canonically identified first REJECTED Command persists one terminal replay entry
F3-I21 changed conditions never change a persisted command_id disposition
F3-I22 global command_id conflict cannot be evaded by changing source
F3-I23 intake and replay refs are independent of envelope/intake fingerprints
F3-I24 every terminal intake graph has one closed versioned schema and fingerprint
F3-I25 ordinary authentication uses exact F2 AUTHENTICATED, never VERIFIED
F3-I26 continuity reducer is total over all eight frozen F2 Actor results
F3-I27 Jenn continuity decisions never override a non-ACTIVE F2 Actor assessment
F3-I28 READY implies one matching durable COMMITTED authority witness generation
F3-I29 committed witness ahead of ledger is rollback and fails closed
F3-I30 crash-abandoned witness generations are never reused
F3-I31 synthetic activation has a constructible committed issuance predecessor
F3-I32 synthetic fixture evidence never becomes real runtime or production authority
```

Mandatory negative tests or proof traces include:

```text
rejected Command retried unchanged after gate becomes active -> first rejection
rejected Command retried with changed payload -> PROTOCOL_CONFLICT
same command_id from another claimed Binding -> first disposition or conflict
AUTHENTICATED compared with VERIFIED -> contract/schema failure
each of eight frozen Actor assessment values -> exactly one continuity result
unknown Actor enum -> INDETERMINATE final fallback
valid ledger backup N restored after COMMITTED witness N+1 -> INDETERMINATE
crash after witness reservation before epoch commit -> reservation abandoned, no reuse
crash after epoch commit before witness finalization -> exact pending reservation finalized
ledger epoch with no reservation -> INDETERMINATE
intake record/envelope fingerprint disagreement -> affected intake closed
content-addressing F3_intake_state_ref -> schema failure
activation ACK before issuance -> REJECTED with no envelope/action/Event
synthetic issuance with same delegator/delegate -> REJECTED
synthetic issuance missing Jenn root direction or AUTHENTICATED assessment -> REJECTED
synthetic pending Delegation used as ACK responsibility source -> REJECTED
synthetic witness containing real credential/provider/host/runtime input -> REJECTED
```

## 8. Atomic acceptance and stopping rule

```yaml
acceptance_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R2_ATOMIC_BUNDLE
subjects:
  - F3_R1_exact_sha256_e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
  - this_exact_R2_document_sha256_after_author_closeout
precedence:
  - R2_explicit_replacements
  - R1_all_other_clauses
partial_acceptance: forbidden
acceptance_authority: Jenn
fresh_full_atomic_independent_review_required: true
review_must_be_hash_bound: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F4_automatic_start: forbidden
```

The F3 core freeze gate is satisfied only when a fresh independent reviewer
recomputes the fixed R1 and R2 hashes, reviews the entire effective bundle, and
finds no remaining identity spoofing, dual writer, rollback/currentness,
replay ambiguity, circular proof, authority expansion, downstream boundary
leak, synthetic M0 impossibility, or internal contradiction.

Passing that review creates only a Jenn atomic decision surface. It does not
accept or freeze F3 automatically and does not authorize implementation,
database work, runtime activation, production authentication, service start,
provider execution, commit, push, or merge.
