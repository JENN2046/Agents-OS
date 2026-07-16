# AGENTS OS F3 Resident Singleton / N-API / Identity Continuity v0.1 R1

```yaml
contract_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R1
date: 2026-07-16
status: proposed_final_draft
owner: Jenn
agent_steward: Nobao
closure_mode: atomic_bundle
partial_acceptance: forbidden
depends_on:
  - F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE
closes:
  - HD-M0-02
implementation_authorized: false
runtime_activation_authorized: false
database_change_authorized: false
production_authentication_authorized: false
provider_or_service_authorized: false
F4_started: false
```

## 1. Authority, purpose, and atomic scope

Jenn explicitly started F3 on 2026-07-16. The immutable start record is:

```text
control-plane/registry/decisions/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-start-decision-v0.1.yaml
```

F3 closes one indivisible correctness boundary:

```text
one logical AGENTSOSResident identity
+ one live canonical writer incarnation
+ one Rust-owned ledger thread and authoritative connection
+ one closed, versioned N-API boundary
+ one deterministic Command intake and replay boundary
+ one fail-closed identity-continuity and recovery decision
```

Accepting only part of that boundary is forbidden. Singleton ownership without
identity continuity would let a replacement process claim an undefined person.
Identity continuity without singleton ownership would let two writers speak as
the same person. Command intake without the writer and continuity gates would
let an unqualified shell create canonical facts.

This contract specializes the accepted Resident Operating Architecture. It
does not reopen that architecture and does not modify any frozen F2 subject.

## 2. Governing sources and precedence

Normative inputs, in descending order for this contract, are:

```text
1. Jenn's immutable F3 start decision
2. frozen F2 R1-R22 acceptance subjects under their recorded precedence
3. accepted Resident Operating Architecture v0.1
4. accepted Foundational Direction and Phase 3 Construction Readiness graph
5. accepted Home Domain Direction for identity-continuity meaning
6. this F3 subject for the surfaces assigned to F3
```

F3 owns the exact shapes of `CommandTypeDefinition`, `CanonicalCommand`,
`AuthenticatedCommandContext`, the committed Command envelope, Resident
singleton ownership, the Rust/N-API boundary, and Resident identity continuity.
F2 remains authoritative for Actor, Principal, Authenticator Profile, Binding,
Assignment, Delegation, authentication assessment, responsibility assessment,
canonicalization primitives, and all F2 action-assurance requirements.

If this document conflicts with F2, F2 wins and F3 is not acceptable until the
conflict is corrected. F3 may consume F2 values; it may not restate them into a
second identity or responsibility ledger.

## 3. Explicit exclusions

F3 does not define or authorize:

```text
F4 TaskPermit, production host identity, host authentication, or effect fencing
F5 Outbox claim, delivery, retry, dead-letter, or external-effect recovery
F6 current Validation decision or Task completion eligibility
F7+ Home, Memory, Presence, relationship, or governed-memory behavior
Rust, JavaScript, napi-rs, rusqlite, SQLite schema, migration, or test code
VCPToolBox integration changes or Resident/service startup
production authentication, crypto, keys, credentials, or trust provisioning
provider, plugin, executor, shell, Codex, network, or external-effect execution
public API or public MCP expansion
```

The accepted architecture names future implementation components. Their names
in this semantic contract do not authorize creating or running them.

## 4. Closed terminology

| Term | Meaning |
|---|---|
| `ResidentIdentity` | The stable logical AGENTSOSResident identity, not a process, model, session, prompt, row, or database file |
| `ResidentIncarnation` | One process-lifetime embodiment attempting to serve one Resident identity |
| `ResidentAuthorityEpoch` | A monotonically increasing canonical writer generation held by one incarnation |
| `ResidentAuthorityLock` | The exclusive process-lifetime lock that prevents a second live writer from opening the authoritative ledger |
| `ledger thread` | The one Rust-owned serialization owner of the authoritative connection and all canonical writes |
| `authoritative connection` | The sole read-write connection to the canonical ledger |
| `Command` | An authenticated request for one registered canonical reducer action; never a direct state write |
| `CommandEnvelope` | The immutable canonical proof that one exact Command was COMMITTED |
| `intake disposition` | A response about one submission; only `COMMITTED` creates a referenceable envelope |
| `identity continuity` | Evidence-backed continuity of the same logical Resident identity across incarnation, model, or session changes |

The words `leader`, `lease`, `primary`, `lock file`, `process ID`, `database
row`, `session`, or `model` are not synonyms for `ResidentIdentity`.

## 5. Canonical scalar and encoding profile

F3 adopts the frozen F2 canonicalization profile without variation:

```text
UTF-8 only
LF line endings for bound text artifacts
Unicode NFC before comparison or hashing
RFC 8785 JCS for JSON fingerprint projections
duplicate JSON keys rejected
normalized-key collisions rejected
unknown fields rejected on every closed schema
SHA-256 lowercase hexadecimal digests
JSON numbers restricted to exact integers from 0 through 2^53 - 1
negative zero, fractions, exponent aliases, NaN, and Infinity rejected
```

Stable refs are non-empty NFC strings and never contain secrets, raw private
Memory, provider responses, signed URLs, credentials, or absolute database
paths. Every displayed fingerprint formula is over the semantic values in the
displayed order. The fingerprint field itself is excluded from its own input.

## 6. Resident identity facts

### 6.1 `ResidentIdentityRevisionV0_1`

```yaml
ResidentIdentityRevisionV0_1:
  interface_version: agents-os.resident-identity-revision.v0.1
  resident_identity_id: stable_ref
  revision: positive_safe_integer
  expected_previous_revision: positive_safe_integer | null
  resident_kind: AGENTS_OS_RESIDENT
  logical_coordinator_actor_id: stable_ref
  logical_coordinator_actor_identity_revision: positive_safe_integer
  identity_charter_ref: stable_low_disclosure_ref
  identity_charter_sha256: lowercase_sha256
  resident_architecture_decision_ref: stable_ref
  resident_architecture_decision_sha256: lowercase_sha256
  F2_acceptance_decision_ref: stable_ref
  F2_acceptance_decision_sha256: lowercase_sha256
  continuity_parent_ref: stable_ref | null
  continuity_transition: BOOTSTRAP | CONTINUE | DISCONTINUITY
  Jenn_identity_decision_ref: stable_ref
  created_at_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is:

```text
SHA-256(JCS([
  "agents-os.resident-identity-revision.v0.1",
  resident_identity_id,
  revision,
  expected_previous_revision,
  "AGENTS_OS_RESIDENT",
  logical_coordinator_actor_id,
  logical_coordinator_actor_identity_revision,
  identity_charter_ref,
  identity_charter_sha256,
  resident_architecture_decision_ref,
  resident_architecture_decision_sha256,
  F2_acceptance_decision_ref,
  F2_acceptance_decision_sha256,
  continuity_parent_ref,
  continuity_transition,
  Jenn_identity_decision_ref,
  created_at_event_sequence
]))
```

The first revision requires `revision = 1`, null previous/parent values,
`BOOTSTRAP`, and an immutable Jenn bootstrap decision. Every later revision
requires exact current-head CAS and one immutable Jenn identity decision.
`CONTINUE` preserves `resident_identity_id` and the logical coordinator Actor.
`DISCONTINUITY` records that continuity is not being claimed; it never silently
creates a replacement identity.

No Agent, model, shell, adapter, process, recovery routine, or database
migration may mint, merge, split, retire, or declare continuity for the root
Resident identity without Jenn's exact decision.

### 6.2 Identity meaning and data boundary

Resident identity continuity is supported by stable canonical identity facts,
the versioned charter, F2 Actor binding, accepted authority boundaries, and
accountable action history. Selected Memory and relationship context may later
help a model recognize the identity, but neither is a writer of this fact.

The canonical identity record contains refs and digests only. It must not
contain raw chats, raw private Memory, prompts, provider responses, credentials,
or a full narrative history.

## 7. Singleton writer ownership

### 7.1 Dual gate

An incarnation has canonical write authority only while both gates hold:

```text
process gate: it exclusively holds ResidentAuthorityLock
canonical gate: it owns the current committed ResidentAuthorityEpoch
```

Neither gate alone is sufficient. A stale lock marker, process ID, timestamp,
hostname, open database handle, or current epoch row cannot prove live
authority by itself.

`ResidentAuthorityLock` must be an operating-system-enforced exclusive lock
whose ownership ends when the owning process dies or closes the lock handle.
Its locator is implementation-private and never enters a Command, Event,
Receipt, projection, or model context. Implementations may choose the exact
lock primitive only if deterministic crash, fork, and dual-start fixtures prove
the contract above.

### 7.2 `ResidentAuthorityEpochV0_1`

```yaml
ResidentAuthorityEpochV0_1:
  interface_version: agents-os.resident-authority-epoch.v0.1
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  authority_epoch: positive_safe_integer
  expected_previous_authority_epoch: positive_safe_integer | null
  incarnation_id: stable_ref
  previous_incarnation_id: stable_ref | null
  ownership_started_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is:

```text
SHA-256(JCS([
  "agents-os.resident-authority-epoch.v0.1",
  resident_identity_ref,
  resident_identity_fingerprint,
  authority_epoch,
  expected_previous_authority_epoch,
  incarnation_id,
  previous_incarnation_id,
  ownership_started_event_sequence
]))
```

Epoch 1 requires a null predecessor. A later epoch is exactly previous + 1 and
is committed by exact current-head CAS after the incarnation holds the process
gate. Overflow, missing predecessor, duplicate epoch, fork, rollback, or an
unresolved current head makes ownership `INDETERMINATE` and keeps intake shut.

An incarnation ID identifies a process lifetime; it is not identity evidence.
A normal restart creates a new incarnation and epoch but preserves the exact
current Resident identity revision.

### 7.3 One thread and one connection

Exactly one Rust-owned ledger thread owns exactly one authoritative read-write
connection. The following are forbidden:

```text
JavaScript opening the canonical ledger
another Rust thread using or moving the authoritative connection
a read pool opening the canonical ledger independently
Dashboard, Workbench, VCPChat, VCPMobile, host, or adapter direct database use
two writer connections serialized only by convention
async work holding a transaction while awaiting JavaScript or external I/O
```

All mutating N-API requests are serialized onto that ledger thread. Read-only
queries also execute through the controlled Rust query contract; an
implementation may not introduce a second connection in v0.1 merely because a
query is read-only.

## 8. Resident lifecycle and readiness

The closed lifecycle projection is:

```text
COLD -> RECOVERING -> READY -> DRAINING -> STOPPED
                    \-> INDETERMINATE
RECOVERING ---------\-> INDETERMINATE
```

`INDETERMINATE` is fail-closed and requires an evidence-backed repair or a new
Jenn decision; it does not auto-transition to READY. There is no canonical
command intake in `COLD`, `RECOVERING`, `DRAINING`, `STOPPED`, or
`INDETERMINATE`.

READY requires all of these at one read barrier:

```text
exclusive ResidentAuthorityLock held
one current Resident identity head and continuity assessment = CONTINUOUS
one current authority epoch owned by this incarnation
one ledger thread and authoritative connection
schema and accepted-contract versions exactly supported
F2 recovery/currentness checks complete
Event, current pointer, replay index, envelope, and action-ref integrity complete
no unresolved duplicate writer, fork, fingerprint mismatch, or prohibited boundary version
control/recovery lane available
```

Readiness is a derived projection, not a caller flag. JavaScript cannot set it.

## 9. Closed N-API boundary

F3 keeps the accepted in-process N-API surface:

```text
execute_command
execute_query
claim_outbox
acknowledge_outbox
reconcile
```

The exact F3 availability is:

| Method | F3 status | Rule |
|---|---|---|
| `execute_command` | defined | only READY; canonical intake below |
| `execute_query` | defined | controlled read-only query; never direct SQL |
| `claim_outbox` | reserved | unavailable until F5 acceptance |
| `acknowledge_outbox` | reserved | unavailable until F5 acceptance |
| `reconcile` | reserved | unavailable until the owning downstream recovery contract is accepted |

Reserved methods return `CONTRACT_NOT_ACTIVE`; they do not perform a partial
operation. F3 acceptance cannot activate them.

Every call uses a closed versioned request/response frame:

```yaml
NapiRequestFrameV0_1:
  interface_version: agents-os.napi-request-frame.v0.1
  method_id: closed_method_id
  request_id: stable_ref
  payload_schema_ref: stable_ref
  payload_schema_sha256: lowercase_sha256
  payload: closed_schema_value

NapiResponseFrameV0_1:
  interface_version: agents-os.napi-response-frame.v0.1
  method_id: closed_method_id
  request_id: stable_ref
  disposition: COMMITTED | REPLAYED_COMMITTED | QUERY_OK | REJECTED | INDETERMINATE | CONTRACT_NOT_ACTIVE
  result_schema_ref: stable_ref
  result_schema_sha256: lowercase_sha256
  result: closed_low_disclosure_value
```

Frames are canonical UTF-8 JSON values under Section 5. Unknown methods,
versions, schemas, digests, enum values, or fields reject before ledger use.
The shell cannot pass executable callbacks, SQL, filesystem paths, provider
handles, credentials, or arbitrary objects through the frame.

N-API is a correctness and module boundary. It is not a sandbox against code
that fully controls the VCPToolBox process or operating-system user.

## 10. Command registry

### 10.1 `CommandTypeDefinitionV0_1`

```yaml
CommandTypeDefinitionV0_1:
  interface_version: agents-os.command-type-definition.v0.1
  registry_revision: positive_safe_integer
  command_type_id: stable_ref
  command_type_version: positive_safe_integer
  owner_contract_ref: stable_ref
  owner_contract_sha256: lowercase_sha256
  payload_schema_ref: stable_ref
  payload_schema_sha256: lowercase_sha256
  allowed_target_kinds: sorted_unique_closed_values
  expected_target_revision_policy: REQUIRED | OPTIONAL | FORBIDDEN
  responsibility_mode: REQUIRED | NONE_ACTIVATION_PURPOSE_ONLY
  effect_class: LEDGER_ONLY | EFFECT_INTENT
  reducer_ref: stable_ref
  reducer_sha256: lowercase_sha256
  required_gate_refs: sorted_unique_stable_refs
  maximum_validity_duration_ms: positive_safe_integer
  unknown_fields_policy: REJECT
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is:

```text
SHA-256(JCS([
  "agents-os.command-type-definition.v0.1",
  registry_revision,
  command_type_id,
  command_type_version,
  owner_contract_ref,
  owner_contract_sha256,
  payload_schema_ref,
  payload_schema_sha256,
  allowed_target_kinds,
  expected_target_revision_policy,
  responsibility_mode,
  effect_class,
  reducer_ref,
  reducer_sha256,
  required_gate_refs,
  maximum_validity_duration_ms,
  "REJECT"
]))
```

Command definitions are admitted only by an accepted contract and an exact
registry revision. There is no runtime self-registration. Unknown, superseded,
or digest-mismatched definitions reject. `EFFECT_INTENT` definitions remain
inadmissible until F4 and every other owning contract is accepted; F3 cannot
turn a ledger Command into effect authority.

### 10.2 Target and responsibility values

```yaml
CommandTargetV0_1:
  target_kind: closed_value_from_type_definition
  target_ref: stable_ref
  target_subject_fingerprint: lowercase_sha256 | null
  expected_target_revision: safe_integer | null

CommandResponsibilityClaimV0_1:
  mode: REQUIRED | NONE_ACTIVATION_PURPOSE_ONLY
  responsibility_source_ref: stable_ref | null
  responsibility_source_fingerprint: lowercase_sha256 | null
  delegation_chain_fingerprint: lowercase_sha256 | null
  bound_resource_ref: F2_ResponsibilityResourceRefV0_1 | null
```

`REQUIRED` requires the exact current F2 responsibility source and bound
resource. `NONE_ACTIVATION_PURPOSE_ONLY` requires every other field null and is
legal only for the closed `DELEGATION_ACTIVATION_ACK` type. It cannot carry a
domain mutation, effect request, provider request, or another Command.

## 11. Canonical Command and submission

### 11.1 `CanonicalCommandV0_1`

```yaml
CanonicalCommandV0_1:
  interface_version: agents-os.canonical-command.v0.1
  F3_contract_version: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R1
  command_id: stable_ref
  command_type_definition_ref: stable_ref
  command_type_definition_fingerprint: lowercase_sha256
  command_type_id: stable_ref
  command_type_version: positive_safe_integer
  claimed_actor_id: stable_ref
  claimed_actor_identity_revision: positive_safe_integer
  claimed_principal_id: stable_ref
  claimed_principal_revision: positive_safe_integer
  claimed_principal_binding_ref: stable_ref
  issued_at_utc_ms: safe_integer
  expires_at_utc_ms: safe_integer
  target: CommandTargetV0_1
  responsibility_claim: CommandResponsibilityClaimV0_1
  payload_schema_ref: stable_ref
  payload_schema_sha256: lowercase_sha256
  payload: closed_schema_value
  canonical_command_fingerprint: lowercase_sha256
```

Its fingerprint is:

```text
SHA-256(JCS([
  "agents-os.canonical-command.v0.1",
  F3_contract_version,
  command_id,
  command_type_definition_ref,
  command_type_definition_fingerprint,
  command_type_id,
  command_type_version,
  claimed_actor_id,
  claimed_actor_identity_revision,
  claimed_principal_id,
  claimed_principal_revision,
  claimed_principal_binding_ref,
  issued_at_utc_ms,
  expires_at_utc_ms,
  target,
  responsibility_claim,
  payload_schema_ref,
  payload_schema_sha256,
  payload
]))
```

The exact F2 `AuthenticationAssertionValue.command_fingerprint` binds this
fingerprint. The assertion is therefore not embedded in the fingerprinted
Command and cannot create a circular proof.

`expires_at_utc_ms` must be greater than `issued_at_utc_ms`; the interval must
not exceed the type definition maximum. Admission uses the exact current F2
trusted-time decision inside the writer transaction. Missing, stale,
conflicting, or unavailable time is `INDETERMINATE`, never a caller-selected
clock fallback.

### 11.2 `CommandSubmissionV0_1`

```yaml
CommandSubmissionV0_1:
  interface_version: agents-os.command-submission.v0.1
  canonical_command: CanonicalCommandV0_1
  authentication_assertion: F2_AuthenticationAssertionValue
```

The caller supplies claims and evidence, not an authenticated context. Rust
must derive every assessment and committed reference from canonical current
facts. A caller-supplied `AuthenticatedCommandContext`, envelope, intake state,
Event sequence, action ref, assessment result, readiness value, or authority
epoch is an unknown field and rejects.

## 12. Authenticated Command context

```yaml
AuthenticatedCommandContextV0_1:
  interface_version: agents-os.authenticated-command-context.v0.1
  context_id: stable_ref
  F3_contract_version: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R1
  command_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  command_type_definition_ref: stable_ref
  command_type_definition_fingerprint: lowercase_sha256
  actor_id: stable_ref
  actor_identity_revision: positive_safe_integer
  actor_identity_assessment_ref: stable_ref
  actor_identity_assessment_fingerprint: lowercase_sha256
  principal_id: stable_ref
  principal_revision: positive_safe_integer
  principal_binding_ref: stable_ref
  principal_binding_assessment_ref: stable_ref
  principal_binding_assessment_fingerprint: lowercase_sha256
  authentication_assertion_ref: stable_ref
  authentication_assessment_ref: stable_ref
  authentication_assessment_fingerprint: lowercase_sha256
  responsibility_mode: REQUIRED | NONE_ACTIVATION_PURPOSE_ONLY
  responsibility_source_ref: stable_ref | null
  responsibility_source_fingerprint: lowercase_sha256 | null
  responsibility_assessment_ref: stable_ref | null
  responsibility_assessment_fingerprint: lowercase_sha256 | null
  delegation_chain_fingerprint: lowercase_sha256 | null
  temporary_worker_binding_assessment_ref: stable_ref | null
  temporary_worker_binding_assessment_fingerprint: lowercase_sha256 | null
  prohibited_behavior_list_revision: stable_ref
  prohibited_boundary_evidence_ref: stable_ref
  trusted_time_authority_ref: stable_ref
  assessed_at_utc_ms: safe_integer
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  resident_authority_epoch: positive_safe_integer
  based_on_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

The context fingerprint is SHA-256 JCS over the complete ordered field set
above excluding `canonical_fingerprint`, with domain:

```text
agents-os.authenticated-command-context.v0.1
```

All effective assessments are recomputed at one transaction watermark. Every
ordinary Command requires:

```text
Actor identity ACTIVE
Principal binding ACTIVE and bound to that exact Actor identity revision
authentication assessment VERIFIED and bound to this exact Command fingerprint
responsibility assessment ACTIVE for the exact target resource
current single Prohibited Behavior List boundary satisfied
trusted time inside the Command validity interval
Resident readiness and identity continuity still valid
```

A Temporary Worker ordinary Command additionally requires the exact frozen F2
`TemporaryWorkerResponsibilityBindingAssessmentV0_1R18.assessment = ACTIVE` for
the exact Task or Run. Actor ACTIVE, a matching source ref, or a historical
binding alone is insufficient.

The context is immutable evidence of the commit-time assessment. It never
becomes a current authorization cache. Future Commands always reassess current
facts.

## 13. Intake, envelope, action reference, and replay

### 13.1 Canonical writer transaction

`execute_command` performs this total order:

```text
1. outside the transaction, decode and canonicalize the closed submission
2. verify supported F3, Command-definition, payload-schema, and digest versions
3. enqueue the canonical bytes to the one ledger thread
4. on that thread begin the authoritative write transaction
5. recheck READY identity, lock ownership, incarnation, epoch, and contract heads
6. look up command_id and canonical_command_fingerprint in the replay index
7. evaluate current F2 identity, binding, authentication, responsibility, time,
   prohibited-boundary, Temporary Worker, target, and expected-version gates
8. run the exact registered deterministic reducer
9. create the committed context, envelope, intake record, action or activation
   reference, canonical domain facts, Current State, Event, and any allowed
   ledger-only intent atomically
10. commit once
11. return only committed stable refs and low-disclosure typed results
```

No JavaScript, model, provider, host, filesystem, network, callback, or other
connection is consulted while the transaction is open. Any failed gate rolls
back the whole mutation. There is no partially committed envelope, action ref,
domain fact, Event, or replay reservation.

### 13.2 `CommandEnvelopeV0_1`

```yaml
CommandEnvelopeV0_1:
  interface_version: agents-os.command-envelope.v0.1
  command_envelope_ref: stable_ref
  F3_contract_version: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R1
  intake_state: COMMITTED
  command_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  command_type_definition_ref: stable_ref
  command_type_definition_fingerprint: lowercase_sha256
  command_type_id: stable_ref
  command_type_version: positive_safe_integer
  authenticated_command_context_ref: stable_ref
  authenticated_command_context_fingerprint: lowercase_sha256
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  resident_authority_epoch: positive_safe_integer
  intake_event_sequence: positive_safe_integer
  F3_intake_state_ref: stable_ref
  command_envelope_fingerprint: lowercase_sha256
```

Its fingerprint is:

```text
SHA-256(JCS([
  "agents-os.command-envelope.v0.1",
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
  intake_event_sequence,
  F3_intake_state_ref
]))
```

`F3_intake_state_ref` points to the immutable COMMITTED intake record for the
same command, envelope, fingerprint, epoch, and Event sequence. PENDING,
REJECTED, and INDETERMINATE submissions never produce a referenceable envelope
or action ref.

### 13.3 Exact F2 action reference projection

For ordinary Commands, F3 emits the frozen F2
`AuthenticatedActorActionRefR4Effective` from immutable committed bytes. Its
fingerprint remains exactly:

```text
canonical_action_ref_fingerprint = SHA-256(JCS([
  "agents-os.authenticated-actor-action-ref.v0.1",
  interface_version,
  action_ref_id,
  F3_contract_version,
  command_id,
  command_envelope_ref,
  command_envelope_fingerprint,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_binding_ref,
  authentication_assertion_ref,
  authentication_assessment_ref,
  responsibility_source_ref,
  delegation_chain_fingerprint_or_null,
  prohibited_behavior_list_revision,
  prohibited_boundary_evidence_ref,
  F3_intake_event_sequence,
  F3_intake_state_ref
]))
```

Every value is copied from the committed envelope/context graph; none is
accepted from the caller. The action ref points to the envelope. The envelope
does not point to the action ref, so the proof graph is acyclic.

### 13.4 Replay reducer

The replay index has one canonical entry per `command_id`:

```text
no entry:
  evaluate and either commit one entry atomically or roll back with no entry

same command_id + byte-identical canonical_command_fingerprint + COMMITTED:
  return REPLAYED_COMMITTED with the exact existing envelope/result refs
  append no Event and perform no reducer mutation

same command_id + different fingerprint:
  return REJECTED(PROTOCOL_CONFLICT)
  perform no domain mutation and never replace the original entry

entry/envelope/Event/action fingerprint disagreement or incomplete graph:
  return INDETERMINATE
  close affected intake until recovery resolves the integrity failure
```

If commit succeeds but the N-API response is lost, replay of the same canonical
Command returns the committed result. Absence of a response is never proof that
the transaction did not commit.

## 14. Closed Delegation activation Command

### 14.1 Definition and payload

F3 registers exactly one activation-purpose type:

```yaml
command_type_id: DELEGATION_ACTIVATION_ACK
command_type_version: 1
responsibility_mode: NONE_ACTIVATION_PURPOSE_ONLY
effect_class: LEDGER_ONLY
allowed_target_kind: F2_DELEGATION_REVISION
expected_target_revision_policy: REQUIRED
```

Its closed payload is:

```yaml
DelegationActivationAckPayloadV0_1:
  interface_version: agents-os.delegation-activation-ack-payload.v0.1
  activation_mode: EXPLICIT_ACK | WORKER_ASSIGNMENT_HANDSHAKE
  delegation_ref: stable_ref
  delegation_subject_fingerprint: lowercase_sha256
  delegate_actor_id: stable_ref
  delegate_actor_identity_revision: positive_safe_integer
  responsibility_source_mode: NONE_ACTIVATION_PURPOSE_ONLY
```

`WORKER_ASSIGNMENT_HANDSHAKE` is a payload mode, not a second Command type. It
requires the delegate Actor class to be `TEMPORARY_WORKER` and binds this exact
mode into the committed envelope and acknowledgement. It does not make the
pending grant its own responsibility source. Only later ordinary Worker
Commands require the resulting exact F2 responsibility binding assessment to
be ACTIVE.

The payload rejects additional responsibility, domain mutation, effect,
provider, host, permit, secret, credential, arbitrary metadata, or unknown
fields.

### 14.2 Atomic activation reducer

In one writer transaction, the reducer must:

```text
authenticate the exact Principal and current ACTIVE binding
verify the binding belongs to the exact delegate Actor identity revision
verify the exact Delegation revision is current, pending activation, unexpired,
  unrecalled, unsuspended, unrevoked, unrenounced, and not superseded
verify the exact delegation subject fingerprint and payload activation mode
require responsibility_source_mode = NONE_ACTIVATION_PURPOSE_ONLY
verify the current single Prohibited Behavior List boundary
reserve both command_id and activation replay identity
commit the context, envelope, acknowledgement, activation evidence,
  activation assessment, current projection, and activation Event atomically
```

The activation replay identity remains the exact frozen F2 formula:

```text
SHA-256(JCS([
  "agents-os.delegation-activation-ack.v0.1",
  command_envelope_fingerprint,
  delegation_ref,
  delegation_subject_fingerprint,
  acknowledging_principal_binding_ref
]))
```

The acknowledgement ref is the exact frozen F2
`DelegationActivationAcknowledgementRefR4Effective`. Its companion fingerprint
uses the exact F2 field order and values, including the committed envelope,
exact activation mode through the closed payload, `COMMITTED` state,
`NONE_ACTIVATION_PURPOSE_ONLY`, current prohibited-boundary evidence, and replay
identity.

It rejects every F2-required negative case, including wrong/stale/indeterminate
binding, Actor, Delegation, fingerprint, mode, replay, time, or prohibited
boundary; a grant already active or no longer pending; and the pending grant or
another responsibility fact offered as the acknowledgement authority.

## 15. Identity continuity assessment

```yaml
ResidentIdentityContinuityAssessmentV0_1:
  interface_version: agents-os.resident-identity-continuity-assessment.v0.1
  assessment_ref: stable_ref
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  identity_head_revision: positive_safe_integer
  identity_head_fingerprint: lowercase_sha256
  logical_coordinator_actor_identity_assessment_ref: stable_ref
  logical_coordinator_actor_identity_assessment_fingerprint: lowercase_sha256
  current_authority_epoch_ref: stable_ref
  current_authority_epoch_fingerprint: lowercase_sha256
  assessment: CONTINUOUS | DISCONTINUOUS | INDETERMINATE
  reason_codes: sorted_unique_closed_values
  based_on_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

The reducer is:

```text
missing, duplicate, forked, corrupt, noncontiguous, or hash-mismatched identity
  head, charter, F2 acceptance, Jenn decision, epoch, or Event -> INDETERMINATE
identity head continuity_transition = DISCONTINUITY -> DISCONTINUOUS
coordinator Actor COMPROMISED, RETIRED, or identity assessment INDETERMINATE
  without an exact Jenn continuity decision -> INDETERMINATE
all exact identity facts current and transition = BOOTSTRAP or CONTINUE,
  epoch ownership valid, and required assessments reproducible -> CONTINUOUS
```

A process restart, authority-epoch increment, N-API reload, model change,
context-window change, session change, or model-provider change does not by
itself change the logical identity assessment. It also cannot prove continuity.

`DISCONTINUOUS` and `INDETERMINATE` deny ordinary Command intake. Queries may
surface only typed low-disclosure diagnosis; they cannot repair or override the
assessment.

## 16. Startup, recovery, and shutdown contract

### 16.1 Startup order

The future implementation must preserve this order:

```text
1. enter COLD with no Command intake
2. acquire the exclusive ResidentAuthorityLock
3. create the one ledger thread and open the one authoritative connection
4. verify supported schema/contract versions and database integrity
5. verify Resident identity chain, Jenn decisions, charter, and F2 freeze basis
6. commit the next ResidentAuthorityEpoch by exact CAS
7. execute the complete F2 fail-closed recovery checks
8. verify Event/current-state/replay/envelope/action-ref continuity
9. rebuild only derived indexes and projections from canonical facts
10. reconcile crash-window facts through already accepted contracts only
11. take a final recovery read barrier and repeat if canonical inputs changed
12. derive continuity and readiness; open intake only when both pass
```

The order may be implemented in smaller internal steps but may not publish
READY early. Failure after acquiring the lock closes the connection and
releases the lock; it never leaves a fabricated READY projection.

### 16.2 Mandatory F2 recovery dependency

Before intake opens, F3 must satisfy the complete frozen F2 recovery contract,
including one current contiguous head per identity/responsibility stream,
valid transition/CAS/Event ordering, reproducible current assessments, complete
compromise-impact sets, exact scopes, bounded acyclic delegation, exact numeric
profile, and accepted synthetic-M0 subject membership.

Duplicate head, fork, missing Event, unresolved assurance, fingerprint
disagreement, replay-index corruption, or unknown schema makes affected intake
`INDETERMINATE`. Recovery never silently rewrites history.

### 16.3 Crash and shutdown

Crash safety rules:

```text
transaction committed -> canonical facts survive and identical replay returns them
transaction not committed -> no partial envelope/fact/Event/replay reservation survives
commit outcome unknown to caller -> caller retries the exact same Command
old process still holds lock -> new process cannot acquire writer authority
old process dead -> lock releases; new process creates a higher epoch and recovers
```

Orderly shutdown stops new Commands, drains the bounded current transaction,
records only already-authorized shutdown facts, closes the authoritative
connection, releases the process lock, and reaches STOPPED. Shutdown does not
start Outbox delivery or create effect authority.

## 17. Downstream seams

F3 supplies these stable outputs:

```text
F4: current Resident identity/epoch, committed Command envelope, authenticated
    context, and immutable action ref; F4 still owns permit/host/fence admission

F5: one canonical writer transaction and reserved N-API method names; F5 still
    owns claim/delivery/retry/dead-letter/effect recovery

F6: deterministic Event and current-read barrier; F6 still owns Validation
    current decision and Task completion eligibility

F9: authenticated Command intake; F9 still owns Home-to-Orchestrator mapping
```

No downstream contract may bypass F3 by writing the ledger, constructing an
action ref, declaring READY, or treating an N-API call receipt as a canonical
commit.

## 18. Normative invariants

```text
F3-I01 one Resident identity has at most one current identity head
F3-I02 at most one live incarnation can hold both writer gates
F3-I03 exactly one Rust ledger thread owns exactly one authoritative connection
F3-I04 JavaScript and every external surface have zero direct ledger access
F3-I05 READY implies identity continuity = CONTINUOUS at the same read barrier
F3-I06 only COMMITTED intake creates an envelope or action reference
F3-I07 one command_id binds forever to at most one canonical Command fingerprint
F3-I08 replay of identical committed bytes creates no second Event or mutation
F3-I09 a changed payload under the same command_id is a protocol conflict
F3-I10 all identity/authentication/responsibility/time/policy gates are current
        inside the same writer transaction as the domain mutation
F3-I11 revocation before Command commit denies; Command commit before revocation
        remains historical evidence and gains no future authority
F3-I12 action refs are emitted only from immutable committed bytes
F3-I13 the envelope/action/evidence proof graph is acyclic
F3-I14 Temporary Worker ordinary Commands require exact ACTIVE F2 responsibility
F3-I15 Delegation activation uses no responsibility source and no domain/effect payload
F3-I16 WORKER_ASSIGNMENT_HANDSHAKE binds that exact mode in the committed payload
F3-I17 model, prompt, or session continuity cannot write Resident identity
F3-I18 identity uncertainty, ownership ambiguity, or recovery corruption fails closed
F3-I19 reserved F5 N-API methods perform no operation before F5 acceptance
F3-I20 F3 never creates TaskPermit, host fence, provider, service, or runtime authority
```

## 19. Mandatory validation matrix

An implementation plan and future implementation must cover at least:

```text
two simultaneous incarnations; exactly one obtains the process gate
stale marker with no live lock owner does not block safe recovery
epoch duplicate, gap, rollback, overflow, fork, and wrong-incarnation rejection
second writer thread, second connection, JavaScript direct DB, and read-pool rejection
READY publication before every recovery sub-gate is impossible
identity restart across new process/model/session remains CONTINUOUS with evidence
missing charter/F2/Jenn/Actor/epoch evidence becomes INDETERMINATE
explicit DISCONTINUITY never reports CONTINUOUS
unknown N-API method/version/schema/field and digest mismatch rejection
reserved outbox/reconcile methods return CONTRACT_NOT_ACTIVE with no mutation
same command_id same bytes before/after lost response returns one commit
same command_id changed payload/auth target/type/expiry returns PROTOCOL_CONFLICT
trusted time missing, before issue, at expiry, after expiry, and duration overflow
authentication/current-binding/responsibility/prohibited-boundary race ordering
revocation-before-commit versus commit-before-revocation total ordering
Temporary Worker ACTIVE identity without ACTIVE exact responsibility denial
activation ACK wrong mode/ref/fingerprint/Actor/binding/time/replay denial
pending grant offered as its own responsibility source denial
WORKER_ASSIGNMENT_HANDSHAKE exact mode binding and later ordinary-use gate
transaction failure at every step leaves no partial canonical graph
envelope, context, action-ref, Event, and replay-index fingerprint corruption
crash before commit, after commit before response, during recovery, and during shutdown
cross-language canonical byte identity for every F3 fingerprint projection
```

These are contract requirements only. This document does not run or authorize
the implementation tests.

## 20. Constructive synthetic M0 witness

F3 is constructible without real identity, credentials, provider, host, or
database state. A future fixed synthetic fixture must demonstrate:

```text
accepted F2 synthetic M0 manifest only
one synthetic Resident identity revision 1 with immutable Jenn fixture decision
one synthetic coordinator Actor from the accepted F2 manifest
one synthetic incarnation acquiring lock and committing authority epoch 1
one closed LEDGER_ONLY DELEGATION_ACTIVATION_ACK definition
one synthetic pending Delegation activated in one committed transaction
one exact replay returning the same envelope with no second Event
one altered replay rejected as PROTOCOL_CONFLICT
one crash/restart creating epoch 2 while preserving identity CONTINUOUS
one second concurrent incarnation denied writer authority
zero TaskPermit, host, provider, secret, service, runtime, or external effect
```

The witness may be expressed as fixed schemas, reducer traces, and proofs before
implementation. It cannot use a real Jenn credential, active host identity,
production authenticator, or private Memory.

## 21. Acceptance and stopping rule

```yaml
acceptance_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R1
subjects:
  - this_exact_document_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
review_must_be_hash_bound: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F4_start_by_acceptance: false
```

If a later amendment is required, R1 plus every amendment becomes one new
indivisible proposed acceptance unit under explicit precedence. Fixed earlier
subject bytes are not edited.

F3 may stop revising when a fresh independent review finds no identity spoofing,
dual writer, fail-open continuity/currentness, replay ambiguity, circular proof,
authority expansion, F4 leakage, M0 impossibility, or internal contradiction.
Only Jenn may then accept and freeze the exact hash-bound atomic unit.

## 22. Non-authorization

This R1 subject is a contract proposal. It does not accept or freeze F3, start
F4, authorize implementation, create or access a database, modify runtime
source or active configuration, start Resident or any service, enable
production authentication, touch credentials, call a provider or executor,
expand a public API/MCP surface, read private raw Memory, or authorize commit,
push, merge, tag, release, deploy, or publication.
