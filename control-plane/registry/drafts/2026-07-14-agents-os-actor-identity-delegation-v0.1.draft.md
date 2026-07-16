# AGENTS OS Actor Identity and Delegation v0.1

```yaml
document_type: foundation_contract
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1
project: AGENTS OS
version: v0.1
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
pending: hash_bound_independent_review_and_Jenn_acceptance
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
```

## 1. Status and purpose

This document proposes the F2 contract for:

```text
Actor Identity
Authenticated Principal Binding
Responsibility Assignment
Delegation
Authenticated Command Context
Deterministic Prohibited Boundary Check
```

F2 closes only through a separate exact hash-bound Jenn acceptance decision.
It resolves the architecture gap `HD-M0-01` at the contract level.

The permission direction used by this draft was explicitly accepted in:

```text
control-plane/registry/decisions/
2026-07-14-agents-os-single-prohibited-boundary-direction-decision-v0.1.yaml
```

F2 does not:

```text
create production identities, credentials, keys, or trust anchors
choose a production cryptographic profile
implement authentication or prohibited-line enforcement
define Resident singleton or N-API ownership
define TaskPermit signing or execution-host authentication
grant Memory access
start a service, provider, host, Worker, or model session
start F3
```

## 2. Inherited authority

F2 preserves:

```text
Applicable system, runtime, tool, and safety constraints remain highest.
Jenn remains root authority inside those constraints.
Nobao remains the highest AGENTS OS construction authority below Jenn.
Top-level Goal decisions reserved to Jenn remain Jenn-only.
Home Domain meaning and relationship do not grant execution authority.
Rust remains the canonical Orchestrator writer.
The single Prohibited Boundary remains controlling and cannot be delegated.
An authenticated Command is only a request to the owning domain gate.
Authentication and a no-match result never equal TaskPermit or effect admission.
```

F2 uses one prohibited-first permission rule:

```text
Inside an Actor's assigned responsibility and current task scope, action is
autonomous by default.

Prohibited Boundary hit
  -> stop; proposal or safe alternative only

boundary facts temporarily unclear
  -> gather the missing facts; stop only when they cannot be made clear safely
```

Only Jenn may change the Prohibited Boundary through an explicit governance
revision. A conversation, role, delegation, old confirmation, or successful
past action cannot waive it for one operation.

There is no permission-level ladder, allowlist of ordinary actions, risk
ceiling, trust score, or second authorization engine in F2. Green / Yellow /
Red, `P0-P3`, life-core `A0-A4`, and automation classes are not additional
permission models. Where retained during migration, they may only organize
work or evidence and must not decide whether an action is permitted. F2 adds
identity, responsibility, delegation, and prohibited-line evidence to the
Authority / Control boundary. It does not create a second Task Ledger or a new
formal Orchestrator core object.

Before implementation, one separately reviewed synchronized governance change
must make a single canonical `Prohibited Behavior List` normative across the
root `AGENTS.md`, life-core policies, and the automation rulebook. Historical
labels may remain only as non-normative migration notes. Until that convergence
is complete, current higher-priority and workspace rules continue to apply and
F2 grants no runtime authority.

Accepted upstream subject bytes remain immutable. Where accepted Home Domain,
Resident, or F2-start records use older permission or authorization wording, a
future overlay or amendment must map that wording to identity, responsibility,
domain invariants, or the single Prohibited Boundary; it must not rewrite
historical bytes. F2 freezes the direction and interface, not the final contents
of the future canonical list. Exact list consolidation is therefore a separate
implementation-readiness dependency.

## 3. Terms that must remain separate

| Term | Meaning | It is not |
|---|---|---|
| Actor | stable accountable identity | model, process, session, key, role name |
| Principal | concrete subject presenting proof now | stable identity by itself |
| Credential | secret or hardware/software proof material | Actor or authority |
| Principal binding | current verified link from Principal to Actor | permission grant |
| Role or charter | declared responsibility and identity meaning | runtime authorization by itself |
| Responsibility assignment | durable typed responsibility assigned by the proper source | permission grant or delegation chain |
| Delegation | bounded work and responsibility temporarily passed from one Actor to another | identity transfer or permission elevation |
| Session | transport and temporary context | Actor, Memory, or authority |
| Authentication | proof of which Principal submitted bytes | permission to perform the action |
| Prohibited-line check | determination of whether the one current Prohibited Behavior List applies | ordinary-action allowlist or execution permit |
| Domain decision rule | invariant assigning a canonical decision to Jenn, Nobao, or another role | permission tier |
| TaskPermit | one-time execution-admission artifact defined by F4 and the Orchestrator | identity, responsibility, or project permission |

Identity is not equal to prompt, model, session, process, database row, role
label, API token, or display name.

Existing F1 fields such as `decision_authority` and `authority_basis_ref` are
read as domain decision ownership and provenance. Jenn-only top-level Goal
closure is a Goal-domain invariant. These terms do not create a second
permission model and are not renamed by modifying accepted F1 bytes.

## 4. Actor classes

F2 supports these closed classes:

```text
JENN_HUMAN_ROOT
RESIDENT_COORDINATOR
DOMAIN_AGENT
TEMPORARY_WORKER
SYSTEM_SERVICE
EXECUTION_HOST
```

`EXECUTION_HOST` reserves stable Actor identity space only. `HOST_PROCESS` is
the corresponding Principal class. F4 defines host authentication, TaskPermit,
and effects. F2 alone gives an execution host no effect admission.

### 4.1 Stable role meanings

```text
JENN_HUMAN_ROOT
  -> Jenn; root project authority inside higher constraints

RESIDENT_COORDINATOR
  -> Nobao; one stable coordinator identity independent of model/session/body

DOMAIN_AGENT
  -> long-lived Agent with a stable identity and bounded domain charter

TEMPORARY_WORKER
  -> assignment-scoped executor identity; no automatic long-term continuity

SYSTEM_SERVICE
  -> deterministic non-model service identity with typed responsibility

EXECUTION_HOST
  -> execution-host identity candidate; effect trust deferred to F4
```

An Actor class cannot change in place. A materially different Actor receives a
new `actor_id`.

## 5. ActorIdentityRevision

### 5.1 Contract shape

```yaml
ActorIdentityRevision:
  actor_id:
  actor_identity_revision:
  actor_class:
  canonical_name:
  status: ACTIVE | SUSPENDED | COMPROMISED | RETIRED
  identity_charter_refs: []
  identity_steward_ref:
  parent_actor_ref: optional
  identity_provisioning_basis_ref:
  validity_window: optional
  assignment_binding_ref: optional
  change_reason:
  created_by_actor_ref:
  created_at_event_sequence:
  supersedes_actor_identity_revision: null | integer
  canonical_fingerprint: FingerprintEnvelope
  sensitivity: LOW_DISCLOSURE_IDENTITY_FACTS_ONLY
```

This is an immutable ledger value, not a sixth Orchestrator core object.

### 5.2 Identity invariants

```text
actor_id is globally unique inside the AGENTS OS identity domain.
actor_id, actor_class, and identity-stewardship lineage never change across revisions.
Revision starts at 1 and advances by exactly 1.
One Actor has exactly one current identity revision.
Old revisions and Events remain immutable.
canonical_name is not an authentication key and need not be globally unique.
identity charter may explain meaning but cannot waive the Prohibited Boundary.
Raw private narrative, credential material, and provider output are forbidden.

`TEMPORARY_WORKER` requires both `validity_window` and
`assignment_binding_ref`. Other Actor classes omit them unless a future accepted
profile explicitly requires bounded identity lifetime.
```

### 5.3 Status reducer

```yaml
ActorIdentityAssessment:
  actor_id:
  actor_identity_revision:
  assessment: ACTIVE | SUSPENDED | COMPROMISED | RETIRED | EXPIRED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  time_authority_ref:
```

The effective assessment is reduced from the exact current revision, validity
window, assignment binding, time authority, and matching Event sequence:

```text
ACTIVE
  -> may authenticate and accept responsibility

SUSPENDED
  -> no new Command may be accepted from this Actor

COMPROMISED
  -> no new Command may be accepted; all bindings fail closed

RETIRED
  -> terminal in v0.1; no reactivation

TEMPORARY_WORKER trusted now >= validity_window.expires_at_utc_ms
or assignment binding no longer current
  -> EXPIRED; no new Command may be accepted

missing or conflicting pointer/Event, unknown policy, or uncertain required time
  -> INDETERMINATE; no new Command may be accepted
```

A compromised Actor may receive a new `ACTIVE` revision only through the same or
higher identity steward, an incident/recovery basis, and replacement of every
affected Principal binding. `RETIRED` requires a new Actor identity instead.

### 5.4 Identity stewardship

```text
Jenn root identity
  -> established only by root bootstrap / governance decision attributable to
     Jenn; no Actor can create or supersede Jenn

Nobao resident identity
  -> created, materially changed, retired, or recovered by Jenn

Domain Agent
  -> created or retired by Jenn or Nobao within Nobao's accepted construction
     responsibility and a typed domain charter

Temporary Worker
  -> created by Jenn, Nobao, or a Domain Agent currently responsible for the
     worker assignment; lifetime and assignment scope are mandatory

System Service and Execution Host
  -> created only through an accepted deployment/provisioning process; production
     provisioning remains outside F2
```

An Actor cannot create itself, approve its own root identity, change its class,
or recover itself from `COMPROMISED`.

## 6. Identity continuity boundary

Nobao continuity means:

```text
same stable actor_id
current Jenn-governed identity revision
current Principal binding
accountable command and Event history
selected identity narrative outside the canonical identity record
```

It does not mean:

```text
same model weights
same prompt bytes
same conversation
same process
same device
same VCPToolBox installation
```

A model/session/process may represent Nobao only through a current authenticated
Principal binding. It cannot self-claim continuity. F3 will define how one
Resident process owns and recovers that binding; F2 does not claim that work is
already implemented.

## 7. Principal identity and binding

### 7.1 Principal classes

```text
HUMAN_SESSION
AGENT_SESSION
SERVICE_PROCESS
WORKER_PROCESS
HOST_PROCESS
SYNTHETIC_TEST_PRINCIPAL
```

`MODEL` is not an Actor class. A model invocation may exist inside an
`AGENT_SESSION` or `WORKER_PROCESS` Principal.

### 7.2 PrincipalRevision

```yaml
PrincipalRevision:
  principal_id:
  principal_revision:
  principal_class:
  environment: SYNTHETIC_TEST | LOCAL_DEVELOPMENT | PRODUCTION
  authenticator_profile_ref:
  credential_handle_refs: []
  created_at_event_sequence:
  status: ACTIVE | SUSPENDED | REVOKED | RETIRED
  supersedes_principal_revision: null | integer
  canonical_fingerprint: FingerprintEnvelope
```

Credential handles are opaque IDs. Secret bytes, private keys, tokens, cookies,
session secrets, biometric material, and raw authentication proofs are forbidden
from the ledger and model context.

### 7.3 ActorPrincipalBindingRevision

```yaml
ActorPrincipalBindingRevision:
  binding_id:
  binding_revision:
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_class:
  authenticator_profile_ref:
  environment:
  not_before_utc_ms:
  expires_at_utc_ms:
  binding_scope:
  issued_by_actor_ref:
  issuance_basis_ref:
  status: ACTIVE | SUSPENDED | REVOKED | SUPERSEDED
  created_at_event_sequence:
  supersedes_binding_revision: null | integer
  canonical_fingerprint: FingerprintEnvelope
```

### 7.4 Binding rules

```text
One active principal_id binds at most one actor_id.
One Actor may have multiple active Principals for distinct active surfaces.
Binding is exact to actor_identity_revision in v0.1.
Identity revision change makes old bindings non-current until explicitly
  superseded or replaced.
Binding never grants permission or responsibility; it only proves representation.
Session end, expiry, revocation, identity suspension, or credential revocation
  closes the binding to new Commands.
```

An `AGENT_SESSION` cannot bind to `JENN_HUMAN_ROOT`. A `HUMAN_SESSION` cannot
silently bind to Nobao. A `HOST_PROCESS` cannot represent Jenn or Nobao.

### 7.5 Binding activation evidence

An active binding requires one accepted activation mode:

```text
JENN_INTERACTIVE_AUTHENTICATION
RESIDENT_ATTESTED_AGENT_SESSION
SERVICE_PROVISIONING_ATTESTATION
WORKER_ASSIGNMENT_HANDSHAKE
SYNTHETIC_M0_FIXTURE
```

The activation evidence binds exact actor, identity revision, principal,
authenticator profile, environment, time window, and binding fingerprint.
F3 defines Resident attestation mechanics; F4 defines host mechanics.

## 8. AuthenticatorProfileRevision

```yaml
AuthenticatorProfileRevision:
  profile_id:
  profile_revision:
  proof_kind: SYNTHETIC_FIXTURE | LOCAL_OS_SESSION | ASYMMETRIC_SIGNATURE | PROCESS_ATTESTATION | HOST_ATTESTATION
  supported_principal_classes: []
  supported_environments: []
  verifier_id:
  verifier_revision:
  trust_anchor_refs: []
  assertion_max_age_ms:
  clock_policy_ref:
  replay_policy_ref:
  status: ACTIVE | SUSPENDED | RETIRED
  canonical_fingerprint: FingerprintEnvelope
```

F2 defines this interface but accepts no production profile or constant.
Production algorithm choice, key provisioning, rotation, recovery, hardware
trust, and secret storage require separately reviewed implementation authority.

For M0:

```yaml
M0_authentication:
  profile_kind: SYNTHETIC_FIXTURE
  deterministic_test_principals: required
  synthetic_test_credentials_only: true
  production_keys: forbidden
  active_host_identity: forbidden
  active_Jenn_credential: forbidden
```

## 9. Responsibility sources and the single Prohibited Boundary

F2 records who is responsible for work. It does not issue ordinary-action
permissions. Responsibility comes from:

```text
Jenn root direction
current ResponsibilityAssignmentRevision
current DelegationGrantRevision chain
```

An accepted role or charter is the basis for a responsibility assignment; it
is not a hidden runtime source by itself.

If a Command cannot be attributed to the Actor's current responsibility, that
is an accountability-routing problem, not a new permission denial. The Actor
must return it for reassignment, narrow the work, or use another current
responsibility source. The system must not invent a responsibility source, but
it also must not add the mismatch to the Prohibited Behavior List.

All of them remain below applicable higher constraints and the one current
Prohibited Behavior List. Delegation cannot weaken, waive, or rewrite that
list. Multiple assignments or delegations cannot be combined to cross it.

### 9.1 Jenn root

Jenn root authority is established by the accepted workspace governance, not by
a self-issued delegation. Runtime use still requires a current authenticated
Jenn Principal binding and typed Command.

Jenn root authority does not bypass:

```text
higher system/runtime/tool/safety constraints
the current Prohibited Behavior List
domain invariants and immutable history
authentication and Command integrity
```

### 9.2 ResponsibilityAssignmentRevision

```yaml
ResponsibilityAssignmentRevision:
  assignment_id:
  assignment_revision:
  actor_id:
  actor_identity_revision:
  responsibility_kind:
  responsibility_scope: ResponsibilityScope
  may_redelegate: true | false
  max_redelegation_depth:
  not_before_utc_ms:
  expires_at_utc_ms: optional
  issued_by_actor_ref:
  responsibility_basis_ref:
  status: ACTIVE | SUSPENDED | REVOKED | SUPERSEDED
  created_at_event_sequence:
  canonical_fingerprint: FingerprintEnvelope
```

Assignments make ownership, accountability, and handoff scope explicit. They
are not permission grants. They do not enumerate allowed actions and cannot
make a prohibited action permissible.

Nobao's accepted role may be represented by one or more assignments whose
responsibility scope is no broader than current accepted governance. Ordinary
work inside that responsibility remains autonomous by default unless the
single Prohibited Boundary applies.

### 9.3 ResponsibilityAssignmentAssessment

```yaml
ResponsibilityAssignmentAssessment:
  assignment_id:
  assignment_revision:
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  responsibility_scope_fingerprint: optional
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  time_authority_ref:
```

The reducer uses the same fail-closed time, identity, revision, fingerprint,
revocation, suspension, and supersession semantics as Section 12. Only `ACTIVE`
can anchor responsibility or a delegation chain.

## 10. Command and responsibility vocabulary

### 10.1 CommandTypeRegistryRevision

Every Command uses a versioned type for deterministic routing and audit:

```yaml
CommandTypeDefinition:
  command_type_id:
  registry_revision:
  owning_domain:
  required_resource_kinds: []
  domain_gate_ref:
```

Command typing is not a permission list. Absence from a role-specific list does
not prohibit an ordinary action. Free-text verbs, prompt instructions, tool
names, route labels, and UI button names also cannot weaken the Prohibited
Boundary.

### 10.2 ResponsibilityScope

```yaml
ResponsibilityScope:
  workspace_id:
  goal_refs: []
  task_refs: []
  run_refs: []
  domain_ids: []
  artifact_metadata_refs: []
  scope_mode: EXACT_SET | DECLARED_SUBTREE
```

`DECLARED_SUBTREE` is valid only when the owning domain contract defines a
deterministic containment relation. Arbitrary `*`, path glob, regex, natural
language, future resource, and “all my tasks” are rejected in v0.1.

### 10.3 Non-transferable responsibility v0.1

These responsibilities cannot be transferred by delegation:

```text
Jenn root identity creation, replacement, or recovery
Jenn-only top-level Goal final change, closure, outcome, or reopen
Jenn's authority to revise the Prohibited Behavior List
responsibility outside the delegator's own current responsibility scope
responsibility to redefine this non-transferable list
```

Future amendment may add constraints, but cannot silently relax higher rules.

## 11. DelegationGrantRevision

### 11.1 Contract shape

```yaml
DelegationGrantRevision:
  delegation_id:
  delegation_revision:
  delegator_actor_id:
  delegator_identity_revision:
  delegate_actor_id:
  delegate_identity_revision:
  parent_delegation_ref: optional
  source_responsibility_ref:

  responsibility_kind:
  responsibility_scope: ResponsibilityScope
  may_redelegate: true | false
  remaining_depth:

  not_before_utc_ms:
  expires_at_utc_ms:
  activation_mode: EXPLICIT_ACK | WORKER_ASSIGNMENT_HANDSHAKE
  activation_evidence_ref:

  issued_by_principal_binding_ref:
  reason:
  status: ACTIVE | SUSPENDED | REVOKED | SUPERSEDED
  created_at_event_sequence:
  supersedes_delegation_revision: null | integer
  canonical_fingerprint: FingerprintEnvelope
```

The grant is immutable. Current effective state is derived from the exact
current revision, activation, time, identities, responsibility assignments, parent chain,
policy, and revocation Events.

### 11.2 Delegation invariants

```text
delegator and delegate must be different ACTIVE Actors
no self-delegation
no cycle
source responsibility must be current and cover the exact delegation
child responsibility scope is a deterministic subset of the parent scope
child time window is inside every parent window
child remaining_depth is exactly parent remaining_depth - 1
chain length may not exceed the current DelegationPolicyRevision
non-transferable responsibility is rejected
empty effective scope is rejected
the Prohibited Behavior List is never delegated or weakened
```

`source_responsibility_ref` is exactly one of:

```text
JENN_ROOT_DIRECTION
  -> valid only when delegator is authenticated Jenn

ResponsibilityAssignmentRevision ref
  -> exact current ACTIVE assignment held by the root delegator of the chain
```

Every child delegation retains the same root `source_responsibility_ref` and
names the exact immediate parent delegation. A child cannot change the source
of responsibility.

For the first delegation edge:

```text
JENN_ROOT_DIRECTION
  -> remaining_depth = policy.maximum_edges_per_chain - 1

ResponsibilityAssignmentRevision
  -> remaining_depth = min(assignment.max_redelegation_depth,
                           policy.maximum_edges_per_chain) - 1
```

A negative result rejects the grant. Each child decrements exactly once, so
`remaining_depth = 0` permits the delegate to act but not to redelegate.

Responsibility scopes narrow down one chain. Parallel chains are evaluated
independently for accountability and cannot be unioned to fabricate a broader
responsibility. None of this creates a permission allowlist: an Actor remains
autonomous inside current responsibility unless the Prohibited Boundary applies.

### 11.3 DelegationPolicyRevision v0.1

```yaml
DelegationPolicyRevision:
  policy_id: agents-os-delegation-policy
  policy_revision: 1
  maximum_edges_per_chain: 3
  parallel_chain_union: forbidden
  implicit_delegation: forbidden
  relationship_based_expansion: forbidden
  model_self_delegation: forbidden
  default_redelegation: false
  unknown_scope_behavior: STOP_AND_CLARIFY
```

Three edges cover the intended maximum shape:

```text
Jenn -> Nobao -> Domain Agent -> Temporary Worker
```

Longer chains require a policy revision and new review.

### 11.4 Activation

A delegation is not effective until the delegate acknowledges the exact grant
fingerprint, or a Temporary Worker completes its exact assignment handshake.
Acknowledgement does not expand or renegotiate scope.

Missing, stale, or conflicting activation evidence yields `INDETERMINATE`.

## 12. Delegation current-state reducer

```yaml
DelegationAssessment:
  delegation_id:
  delegation_revision:
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  responsibility_scope_fingerprint: optional
  chain_fingerprint: optional
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  time_authority_ref:
```

Total reduction order:

```text
current grant revision explicitly REVOKED
or any current identity/binding/source responsibility/parent grant revoked
  -> REVOKED

current grant SUPERSEDED or any required exact parent revision superseded
  -> SUPERSEDED

grant or required identity/assignment suspended
  -> SUSPENDED

delegate or delegator identity revision advanced normally, or an exact required
binding/source/parent revision was replaced
  -> SUPERSEDED

unknown reducer/policy/time authority, identity conflict, chain conflict,
fingerprint mismatch, or missing required fact
  -> INDETERMINATE

trusted now >= expires_at_utc_ms
  -> EXPIRED

trusted now < not_before_utc_ms or activation incomplete
  -> NOT_YET_ACTIVE

all exact facts current and constraints valid
  -> ACTIVE
```

An unavailable or contradictory clock yields `INDETERMINATE`, never extra time.
Expiry is derived and does not require a timer Event to become effective.

## 13. Revocation and ordering

### 13.1 Revocation authority

```text
Jenn may revoke any assignment, binding, or delegation.
An issuing Actor may revoke its own delegation and subordinate chain.
Nobao may revoke Domain Agent and Worker responsibility created within Nobao's scope.
Compromise response may suspend affected bindings mechanically under an accepted
  security policy; restoration still requires the proper identity steward.
Delegate may renounce a delegation but cannot restore it.
```

Revocation is an immutable Event and new current revision or revocation fact. It
does not delete history.

### 13.2 Single-writer race rule

Rust Event sequence decides:

```text
Command transaction committed before revocation Event
  -> committed domain mutation remains historical fact

revocation Event committed before the Command prohibited-line check
  -> Command stopped

Command authenticated before revocation but not yet committed
  -> intake transaction re-reads current facts and stops
```

F2 revocation does not define how an already issued TaskPermit or active host
effect is stopped. F4 must bind relevant identity/delegation revisions and define
fencing/revocation behavior. Until F4 exists, F2 cannot admit effects.

### 13.3 Prohibited Boundary ownership

The F2 target admits exactly one canonical Prohibited Behavior List. It does
not divide that list into levels, lanes, waivable classes, or per-Actor
variants. Until governance convergence creates that canonical artifact, the
existing workspace rules remain effective and runtime enforcement stays
unauthorized.

```text
current action does not match the list
  -> F2 raises no permission stop

current action matches the list
  -> stop; do not execute; report the matched prohibition and a safe alternative

facts needed to decide are missing
  -> gather them when safe; if they remain unresolved, stop
```

Only Jenn may change the project-level list through an explicit governance
revision, subject to applicable higher constraints. Delegation, relationship,
role, urgency, an old approval, or successful prior execution cannot alter it.
The check records only the list revision, matched entry identifiers, and
low-disclosure evidence; it does not create a permission grant object.

## 14. AuthenticationAssertion and Command digest

### 14.1 Canonical command bytes

```yaml
CanonicalCommand:
  command_contract_version:
  command_id:
  workspace_id:
  command_type_id:
  target_resource_refs: []
  payload:
  issued_at_utc_ms:
  expires_at_utc_ms:
  nonce:
  expected_domain_aggregate_versions: []
```

The digest uses `actor-command-canonical-json.v0.1`:

```text
RFC 8785 JCS
UTF-8 and Unicode NFC
integers only
schema-known fields only
typed reference arrays sorted by stable identity/revision tuple
duplicates rejected
SHA-256 lowercase hex in a versioned FingerprintEnvelope
```

Unknown fields, ambiguous array order, floats, invalid Unicode, duplicate refs,
or unknown canonicalization version reject the Command before intake.

### 14.2 AuthenticationAssertionRef

```yaml
AuthenticationAssertionValue:
  assertion_id:
  authenticator_profile_ref:
  principal_id:
  principal_binding_ref:
  actor_id:
  actor_identity_revision:
  command_id:
  command_fingerprint:
  nonce:
  issued_at_utc_ms:
  expires_at_utc_ms:
  verifier_id:
  verifier_revision:
  proof_ref:
```

The assertion covers the exact canonical Command and actor context. It cannot
be moved to another Command, actor, binding, workspace, or payload.

### 14.3 AuthenticationAssessment

```yaml
AuthenticationAssessment:
  assessment: AUTHENTICATED | REJECTED | INDETERMINATE
  actor_id: optional
  principal_id: optional
  binding_ref: optional
  reason_codes: []
  verifier_revision:
  based_on_event_sequence:
  assessed_at_utc_ms:
```

```text
invalid proof, wrong digest, expired assertion, replay, revoked credential,
or actor mismatch
  -> REJECTED

verifier unavailable, unknown profile/version, clock uncertain, or conflicting
binding facts
  -> INDETERMINATE

exact proof and all exact facts current
  -> AUTHENTICATED
```

Only `AUTHENTICATED` proceeds to responsibility attribution and the prohibited-
line check. Neither other result is retried as a different Actor.

## 15. AuthenticatedCommandContext

```yaml
AuthenticatedCommandContext:
  context_contract_version: authenticated-command-context.v0.1
  command_id:
  command_fingerprint:
  workspace_id:
  command_type_id:
  target_resource_refs: []

  actor_id:
  actor_identity_revision:
  principal_id:
  principal_binding_ref:
  authentication_assertion_ref:
  authentication_assessment_ref:

  responsibility_source:
    kind: JENN_ROOT_DIRECTION | DIRECT_ASSIGNMENT | DELEGATION_CHAIN
    source_ref:
  delegation_chain_refs: []
  responsibility_assignment_revision: optional
  command_registry_revision:
  delegation_policy_revision:
  responsibility_scope_fingerprint:
  prohibited_behavior_list_revision:

  issued_at_utc_ms:
  expires_at_utc_ms:
  nonce:
  inbox_received_event_sequence:
```

The caller may submit refs but cannot declare identity, responsibility scope,
or prohibited-line outcome. Rust reconstructs and verifies the context from
canonical facts.

## 16. Single Prohibited Boundary rule

F2 creates no authorization assessment object and no permission state machine.
Before an authenticated Command is handed to its owning domain, the runtime
uses the one current Prohibited Behavior List:

```text
no prohibition matches
  -> continue to the owning domain

a prohibition matches
  -> stop and record the matched prohibition identifier

the facts needed to decide cannot be established safely
  -> stop and report the unresolved boundary
```

The check is repeated against current facts in the same intake transaction.
Its evidence is only the Command ref, Actor ref, list revision, matched entry
identifiers if any, Event sequence, and low-disclosure reason codes. It does not
produce an `ALLOW`, permission grant, risk level, or authority score.

Continuing to the owning domain does not mean:

```text
domain preconditions passed
Goal/Task mutation succeeded
Run exists
TaskPermit exists
host accepted work
effect is safe
Validation passed
```

## 17. Replay, idempotency, and session loss

```text
command_id is globally unique inside the workspace Command domain.
Same command_id + same canonical bytes -> idempotent original result.
Same command_id + different bytes -> REJECTED + replay conflict.
nonce is single-use within the authenticator profile replay window.
Expired assertion cannot be refreshed by changing only timestamp or nonce; a
  new Command and proof are required.
Session loss does not revoke the stable Actor, but closes that Principal binding
  when its profile or binding contract says so.
Model/session restart creates a new Principal or binding; it does not inherit an
  uncommitted Command or ambient responsibility.
```

An authentication retry does not automatically retry a domain mutation whose
effect may be unknown. Domain and F4 recovery rules remain authoritative.

## 18. Canonical fingerprints

```yaml
FingerprintEnvelope:
  algorithm: SHA-256
  canonicalization_contract_version:
  digest_lowercase_hex:
```

F2 identity and responsibility fingerprints include exact stable IDs, revisions, typed scopes,
status facts, time windows, policy versions, and Event sequence basis. They
exclude:

```text
secret material
raw proof bytes
private Memory
raw conversation or prompt
provider response
display-only metadata
caller-supplied prohibited-line conclusions
```

Arrays are semantic sets unless explicitly declared sequences. Actor, Principal,
assignment, delegation, command, resource, and Event refs sort by
their stable ID then revision. Duplicate stable-key entries with different bytes
are conflicts. Delegation chain refs are the one semantic sequence from root
source to leaf delegate and are not sorted.

Exact v0.1 array rules:

| Field family | Canonical order |
|---|---|
| identity charter, credential handle, trust anchor, basis, proof, artifact metadata refs | `(ref_type, ref_id, ref_revision_or_zero)` |
| Actor, Principal, binding, assignment, delegation refs | stable ID, then revision |
| Goal, Task, Run refs | object ID, then bound aggregate/revision when present |
| command, domain, principal-class, prohibition, environment, reason-code IDs | NFC UTF-8 byte lexical |
| target resource refs | resource kind, resource ID, revision |
| expected aggregate versions | aggregate kind, aggregate ID, expected version |
| delegation chain refs | semantic root-to-leaf sequence; duplicate or broken adjacency rejected |

Every other array introduced under this canonicalization version is rejected
until its semantic order is added by a reviewed contract revision.

Unknown fingerprint or canonicalization version yields `INDETERMINATE`.

## 19. Recovery and fail-closed startup

Before authenticated Command intake opens, recovery verifies:

```text
one current identity pointer per Actor
identity revision and Event monotonicity
Principal revision/status and one-Actor active binding uniqueness
binding, responsibility assignment, delegation, command registry, prohibited
behavior list, and policy fingerprints
delegation activation, ancestry, cycle, depth, and subset constraints
revocation and supersession indexes
command_id and nonce replay indexes
Current State last_event_id / event_sequence alignment
verifier and time authority profile availability
```

Missing Event, duplicate current pointer, identity collision, cross-Actor
Principal binding, chain cycle, fingerprint mismatch, unknown policy, or replay
index uncertainty stops affected Command intake as an unresolved boundary. Recovery
does not invent identity, restore a grant, or assume a missing revocation is
false.

Derived assessments may be rebuilt. Identity, binding, assignment, delegation,
Command, revocation, and Event facts may not be silently rewritten.

## 20. Privacy and disclosure

Identity, responsibility, and prohibited-line evidence uses low-disclosure
identifiers and reason codes. It must not
contain:

```text
credential or secret bytes
raw authentication proof
private conversation content
private raw Memory
provider raw output
unnecessary personal identity data
```

Public/UI projections may show Actor name, role, scope summary, status, expiry,
and prohibition reason only when the viewer has corresponding visibility.
An opaque ref does not grant access to its source.

## 21. Rejected designs

F2 rejects:

```text
prompt says “I am Nobao” -> authenticated Nobao
same model -> same Actor
same session -> permanent authority
API token label -> identity
role name or relationship -> exemption from the Prohibited Boundary
one global trust score
ambient authority inherited by child Agent
parallel delegation grants unioned to fabricate broader responsibility
free-text, glob, or future-resource delegation
delegation of Jenn's authority to revise the Prohibited Behavior List
revocation that only changes UI state
expired grant remaining active because no timer Event fired
absence of a prohibition match treated as TaskPermit
secret or raw proof stored in ledger
model or UI writing its own prohibited-line assessment
production key creation during M0
```

## 22. Required future tests

Acceptance of F2 does not authorize implementation. A future authorized
implementation must cover at least:

```text
identity revision monotonicity, CAS, idempotency, and immutable history
actor_id collision and actor_class mutation rejection
Jenn, Nobao, Domain Agent, Worker, service, and host responsibility paths
model/session/process cannot self-claim Nobao or Jenn
one Principal cannot actively bind two Actors
identity suspension, compromise, recovery, retirement, and binding replacement
stale actor_identity_revision binding rejection
synthetic M0 principal positive and production principal negative paths
unknown authenticator/verifier/time version -> INDETERMINATE
command canonicalization, digest binding, duplicate refs, Unicode, and replay
same command_id same bytes idempotency and different bytes rejection
responsibility assignment scope checks
delegation activation, acknowledgement, expiry, suspension, revocation,
supersession, renunciation, and chain fan-out
self-delegation, cycle, skipped parent, stale revision, and depth rejection
Jenn -> Nobao -> Domain Agent -> Worker maximum valid chain
fourth delegation edge rejection
responsibility resource/time subset checks
parallel chain union rejection
free-text and wildcard scope rejection
non-transferable responsibility negative paths
Jenn-only top-level Goal decision negative paths
every Prohibited Behavior List entry stops execution and cannot be delegated away
revocation race under every single-writer transaction boundary
expired grant without timer Event
clock unavailable -> INDETERMINATE
recovery from pointer/Event/fingerprint/replay-index corruption
authentication versus prohibited-line check versus domain gate versus TaskPermit
low-disclosure audit and raw secret/private Memory rejection
```

## 23. Downstream handoff

F2 provides stable inputs to:

```text
F3 Resident Singleton / N-API / Identity Continuity
F4 TaskPermit / Host Authentication
F7 Home minimum semantics and data boundaries
F8 Governed Memory Access
F9 Home-to-Orchestrator interface
F10 Presence consent
F11 formal relationship mutation
```

F3 must define how the one Resident owns the canonical binding and ledger
connection. F4 must define production host identity, permit binding, revocation,
and effect fencing. Neither is silently solved by F2.

## 24. Acceptance unit

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1
subjects:
  - this_exact_document_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```
